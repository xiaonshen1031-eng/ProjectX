#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


VALID_STATUS = {"R&D draft", "Evidence candidate", "Submission candidate"}
ADVANCED_WITH_JUSTIFICATION = {"3d", "3d_pareto", "bubble", "sankey"}
PROHIBITED_PUBLICATION_TYPES = {
    "bar", "bar_chart", "simple_bar", "simple_bar_chart", "basic_bar",
    "basic_bar_chart", "grouped_bar", "grouped_bar_chart", "horizontal_bar",
    "barplot", "barh", "bars", "bar_graph", "bar_with_errorbars", "bar_with_ci",
    "column_chart", "line", "line_chart", "line_graph", "line_with_ci", "simple_line", "simple_line_chart",
    "basic_line", "basic_line_chart", "pareto", "pareto_2d", "2d_pareto",
    "pareto_scatter", "pareto_scatter_2d", "pareto_frontier", "pareto_frontier_2d",
    "accuracy_cost_scatter", "accuracy_latency_pareto", "scatter", "scatter_plot", "sparse_scatter", "simple_scatter",
}
COMPOSITE_TYPES = {"composite", "composite_diagnostic", "temporal_diagnostic",
                   "trajectory_diagnostic", "response_diagnostic", "calibration_diagnostic"}
ANALYTIC_ROLES = {"residual", "uncertainty", "conditional_distribution", "conditional_response",
                  "coverage", "constraint_margin", "paired_effect", "additive_composition",
                  "event_regime", "tail_distribution"}
PRIMITIVE_LINE_ROLES = ANALYTIC_ROLES | {"observed_time_series", "trajectory", "regression_fit",
                                       "calibration", "identity_reference", "analytic_reference"}
MAIN_PURPOSES = {"main_performance", "main_comparison"}


def normalized_type(value: Any) -> str:
    """Normalize spelling separators, not scientific semantics."""
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def prohibited_publication_type(kind: str) -> bool:
    if kind in PROHIBITED_PUBLICATION_TYPES:
        return True
    if kind.startswith(("simple_bar", "simple_line", "basic_bar", "basic_line", "grouped_bar", "plain_bar", "plain_line")):
        return True
    return "pareto" in kind and "3d" not in kind and "three_dimensional" not in kind


def publication_policy(data: dict[str, Any], errors: list[str]) -> bool:
    # All routes share the same minimum scientific-information rule.
    value = data.get("manuscript_mode", data.get("branch", data.get("document_type", "project")))
    mode = normalized_type(value)
    if mode in {"project", "project_word"}:
        return True
    if mode not in {"journal", "journal_word", "journal_latex", "revision_package",
                    "conference", "conference_latex"}:
        errors.append("manuscript_mode/branch must identify journal, conference or project.")
    return True


def validate_publication_encoding(fig: dict[str, Any], prefix: str, errors: list[str]) -> None:
    """Validate declared encodings; pixels still require scientific visual review."""
    def validate_layers(node: dict[str, Any], where: str) -> None:
        kind = normalized_type(node.get("plot_type", ""))
        if kind not in COMPOSITE_TYPES and "plot_layers" not in node:
            return
        layers = node.get("plot_layers")
        if not isinstance(layers, list) or len(layers) < 2 or not all(isinstance(item, dict) for item in layers):
            errors.append(f"{where}: a composite diagnostic requires at least two scientific plot_layers with role, encoding and saved evidence.")
            return
        scientific_layers = 0
        analytical_layer = False
        for index, item in enumerate(layers, 1):
            location = f"{where}.plot_layers[{index}]"
            role = normalized_type(item.get("role", ""))
            if role in {"title", "legend", "decoration", "panel_label", "smoothing"}:
                errors.append(f"{location}: {role} is not a scientific evidence layer and cannot qualify a simple chart.")
                continue
            missing = [field for field in ("role", "encoding", "evidence_source", "evidence_definition") if not populated(item.get(field))]
            if missing:
                errors.append(f"{location}: scientific layer missing or placeholder fields {missing}.")
            else:
                scientific_layers += 1
                analytical_layer |= role in ANALYTIC_ROLES
            if role == "additive_composition" and (item.get("additive_definition_documented") is not True or item.get("component_totals_checked") is not True):
                errors.append(f"{location}: additive_composition requires additive_definition_documented=true and component_totals_checked=true.")
        if scientific_layers < 2 or not analytical_layer:
            errors.append(f"{where}: composite requires two sourced scientific layers including a real residual/uncertainty/conditional/coverage/constraint/effect/composition diagnostic; decorative references cannot qualify it.")

    def inspect(node: dict[str, Any], where: str, *, layer: bool = False) -> None:
        validate_layers(node, where)
        role = normalized_type(node.get("role", ""))
        for field in ("plot_type", "chart_type", "encoding"):
            if field not in node:
                continue
            kind = normalized_type(node[field])
            # Lines/segments are legitimate primitives inside a real diagnostic.
            line_primitive = layer and field == "encoding" and kind in {"line", "line_chart"} and role in PRIMITIVE_LINE_ROLES
            composition_primitive = layer and field == "encoding" and kind in {"bar", "stacked_bar"} and role == "additive_composition"
            point_primitive = layer and field == "encoding" and kind in {"scatter", "scatter_plot"} and role in {"conditional_distribution", "paired_effect", "conditional_response"}
            if prohibited_publication_type(kind) and not (line_primitive or composition_primitive or point_primitive):
                errors.append(f"{where}: prohibited {field}={node[field]!r}; use a scientific diagnostic or table. CUSTOM, decoration and multi-panel wrapping cannot waive this rule.")
        if node.get("is_simple_bar") is True or node.get("is_simple_line") is True or node.get("is_2d_pareto") is True:
            errors.append(f"{where}: declared simple bar/line or two-dimensional Pareto encoding is prohibited for this figure policy.")
        node_kind = normalized_type(node.get("plot_type", ""))
        if node_kind in {"stacked_bar", "stacked_contribution", "additive_composition", "error_regime_composition"}:
            if node.get("additive_definition_documented") is not True or node.get("component_totals_checked") is not True:
                errors.append(f"{where}: composition requires a documented additive definition and checked component totals; renaming method-ranking bars is insufficient.")
        for field in ("panels", "subfigures", "plot_layers"):
            if field not in node:
                continue
            items = node[field]
            if not isinstance(items, list) or not items or not all(isinstance(item, dict) for item in items):
                errors.append(f"{where}: {field} must be a non-empty list of declared objects.")
                continue
            for index, item in enumerate(items, 1):
                inspect(item, f"{where}.{field}[{index}]", layer=field == "plot_layers")

    inspect(fig, prefix)


def declared_layer_paths(node: dict[str, Any], location: str):
    """Yield only source files actually declared by composite scientific layers."""
    for field in ("plot_layers", "panels", "subfigures"):
        values = node.get(field, [])
        if not isinstance(values, list):
            continue
        for index, item in enumerate(values, 1):
            if not isinstance(item, dict):
                continue
            where = f"{location}.{field}[{index}]"
            if field == "plot_layers":
                source = item.get("evidence_source")
                role = normalized_type(item.get("role", ""))
                # A stated analytic reference, e.g. y=x, has no data file.
                analytic = role in {"identity_reference", "analytic_reference"} and isinstance(source, str) and source.startswith("analytic:")
                if not analytic:
                    yield f"{where}:evidence_source", source
            yield from declared_layer_paths(item, where)


def registered_recipe_ids() -> set[str]:
    pool = Path(__file__).resolve().parent.parent / "references" / "figure-pattern-pool.md"
    return set(re.findall(r"^## ([A-Z][A-Z0-9_]+)\s*$", pool.read_text(encoding="utf-8"), re.MULTILINE))


def format_set(value: Any, label: str, errors: list[str]) -> set[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip().lstrip(".") for item in value):
        errors.append(f"{label} must be a non-empty list of format names.")
        return set()
    return {item.strip().lower().lstrip(".") for item in value}


def name_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def populated(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        text = value.strip().lower()
        return len(text) >= 3 and not text.startswith("replace with") and not text.startswith("path to")
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def validate_figure_manifest(data: dict[str, Any], base_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    publication = publication_policy(data, errors)
    status = data.get("status")
    if status not in VALID_STATUS:
        errors.append(f"status must be one of {sorted(VALID_STATUS)}.")
    submission = status == "Submission candidate"
    figures = data.get("figures", [])
    if not isinstance(figures, list) or not figures:
        return {"status": status, "submission_candidate_ready": False, "error_count": 1, "warning_count": 0, "errors": ["figures must be a non-empty list."], "warnings": []}

    numbers: list[int] = []
    purposes: list[str] = []
    plot_types: list[str] = []
    recipe_ids: set[str] | None = None
    for i, fig in enumerate(figures, 1):
        if not isinstance(fig, dict):
            errors.append(f"figures[{i}] must be an object.")
            continue
        num = fig.get("number")
        if not isinstance(num, int) or num < 1:
            errors.append(f"figures[{i}].number must be a positive integer.")
            num = i
        numbers.append(num)
        prefix = f"Figure {num}"
        if publication:
            validate_publication_encoding(fig, prefix, errors)
        # Per-figure contracts override the legacy global contract. No backend
        # implicitly adds editable MATLAB or Word formats.
        required_formats = format_set(fig.get("required_formats", data.get("required_formats")), f"{prefix}: required_formats", errors)
        backend = fig.get("plot_backend")
        if backend is not None and backend not in ("matlab", "python"):
            errors.append(f"{prefix}: plot_backend must be matlab or python when supplied.")
        recipe = fig.get("recipe_id")
        if recipe is not None:
            if recipe_ids is None:
                recipe_ids = registered_recipe_ids()
            if not isinstance(recipe, str) or recipe not in recipe_ids | {"CUSTOM"}:
                errors.append(f"{prefix}: recipe_id must be registered in figure-pattern-pool.md or CUSTOM.")
            if recipe == "CUSTOM":
                justification = fig.get("plot_type_justification", "")
                if not isinstance(justification, str) or len(justification.strip()) < 20 or len(justification.split()) < 4 or not populated(justification):
                    errors.append(f"{prefix}: CUSTOM requires a specific scientific plot_type_justification.")
        if "reference_pool_ids" in fig and (not isinstance(fig["reference_pool_ids"], list) or not all(isinstance(item, str) and item.strip() for item in fig["reference_pool_ids"])):
            errors.append(f"{prefix}: reference_pool_ids must list design references, not replace data_source.")
        if recipe == "REGRESSION_ALL_BASELINES":
            comparators = fig.get("comparator_set")
            if not name_list(comparators) or len(set(comparators)) < 2:
                errors.append(f"{prefix}: REGRESSION_ALL_BASELINES requires comparator_set naming the proposed method and all fair baselines.")
            expected = data.get("comparator_set")
            if expected is not None:
                if not name_list(expected):
                    errors.append("Top-level comparator_set must name the benchmark methods.")
                elif name_list(comparators) and not set(expected) <= set(comparators):
                    errors.append(f"{prefix}: comparator_set omits benchmark methods {sorted(set(expected) - set(comparators))}.")
            if not populated(fig.get("shared_scale_group")) or fig.get("common_limits_documented") is not True:
                errors.append(f"{prefix}: regression requires shared_scale_group and common_limits_documented=true.")
        for field in ("caption", "scientific_question", "purpose", "plot_type", "plot_type_justification", "claim_ids", "data_source", "generator_script", "evaluation_unit"):
            if not populated(fig.get(field)):
                errors.append(f"{prefix}: missing or placeholder field {field}.")
        purpose = str(fig.get("purpose", "")).lower()
        plot_type = normalized_type(fig.get("plot_type", ""))
        purposes.append(purpose)
        plot_types.append(plot_type)
        if fig.get("values_from_saved_results") is not True:
            errors.append(f"{prefix}: values_from_saved_results must be true.")
        if fig.get("manual_value_entry") is not False:
            errors.append(f"{prefix}: manual_value_entry must be false.")
        if not isinstance(fig.get("sample_size"), (int, float)) or fig.get("sample_size", 0) <= 0:
            errors.append(f"{prefix}: sample_size must be positive.")
        if purpose in MAIN_PURPOSES and fig.get("strongest_comparator_visible") is not True:
            errors.append(f"{prefix}: main comparison must show the strongest fair comparator.")
        if fig.get("is_stochastic") is True:
            if fig.get("uncertainty_visible") is not True:
                errors.append(f"{prefix}: stochastic evidence must show uncertainty.")
            if fig.get("raw_points_or_distribution_visible") is not True:
                warnings.append(f"{prefix}: stochastic evidence hides raw points/distribution; justify aggregation.")
        if fig.get("is_heatmap") is True and fig.get("heatmap_text_contrast_checked") is not True:
            errors.append(f"{prefix}: heatmap text contrast has not passed.")
        if fig.get("is_spatial") is True and fig.get("aspect_ratio_preserved") is not True:
            errors.append(f"{prefix}: spatial aspect ratio has not been preserved.")
        if plot_type in ADVANCED_WITH_JUSTIFICATION and len(str(fig.get("plot_type_justification", "")).strip()) < 20:
            errors.append(f"{prefix}: {plot_type} requires a scientific-dimension justification.")
        formats = format_set(fig.get("formats"), f"{prefix}: formats", errors)
        missing_formats = sorted(required_formats - formats)
        if missing_formats:
            errors.append(f"{prefix}: missing required formats {missing_formats}.")
        artifacts = fig.get("artifacts", {})
        if not isinstance(artifacts, dict):
            errors.append(f"{prefix}: artifacts must map each format to a file path.")
            artifacts = {}
        if submission:
            missing_artifacts = sorted(required_formats - {str(x).lower().lstrip('.') for x in artifacts})
            if missing_artifacts:
                errors.append(f"{prefix}: missing artifact paths for {missing_artifacts}.")
        if base_dir is not None:
            path_fields = [("data_source", fig.get("data_source")), ("generator_script", fig.get("generator_script"))]
            path_fields.extend((f"artifact:{ext}", value) for ext, value in artifacts.items())
            if publication:
                path_fields.extend(declared_layer_paths(fig, prefix))
            for label, value in path_fields:
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix}: {label} is not a valid path.")
                    continue
                candidate = Path(value)
                if not candidate.is_absolute():
                    candidate = base_dir / candidate
                if not candidate.is_file() or candidate.stat().st_size == 0:
                    errors.append(f"{prefix}: missing or empty file for {label}: {candidate}")
        width = fig.get("final_width_cm")
        if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(width) or width <= 0:
            errors.append(f"{prefix}: final_width_cm must be positive.")

        if submission:
            if fig.get("placeholder") is not False:
                errors.append(f"{prefix}: placeholder must be false for submission.")
            for field in ("physical_units_present", "no_clipping", "no_overlap", "color_accessibility_checked", "standalone_vector_qa"):
                if fig.get(field) is not True:
                    errors.append(f"{prefix}: submission gate {field} must be true.")
            if fig.get("manuscript_rendered_qa", fig.get("word_rendered_qa")) is not True:
                errors.append(f"{prefix}: submission gate manuscript_rendered_qa (legacy word_rendered_qa) must be true.")
            if recipe is not None and fig.get("annotation_readability_checked") is not True:
                errors.append(f"{prefix}: recipe submission requires annotation_readability_checked=true at final width.")
            if not populated(fig.get("body_discussion_reference")):
                errors.append(f"{prefix}: body_discussion_reference is missing.")
            if publication and data.get("publication_profile_version") == "3.1.3":
                height = fig.get("final_height_cm")
                if isinstance(height, bool) or not isinstance(height, (int, float)) or not math.isfinite(height) or height <= 0:
                    errors.append(f"{prefix}: final_height_cm must be positive for the publication physical-size profile.")
                for field in ("aspect_ratio_preserved", "final_size_typography_checked", "full_frame_visible", "legend_data_clearance_checked"):
                    if fig.get(field) is not True:
                        errors.append(f"{prefix}: publication size/geometry gate {field} must be true.")

    duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
    if duplicates:
        errors.append(f"Duplicate figure numbers: {duplicates}")
    if numbers != sorted(numbers):
        errors.append(f"Figure numbers are out of order: {numbers}")
    if numbers:
        start = data.get("expected_start_number", min(numbers))
        expected = list(range(start, max(numbers) + 1))
        missing = sorted(set(expected) - set(numbers))
        if missing:
            errors.append(f"Missing figure numbers: {missing}")

    if len(figures) >= 6:
        if len(set(purposes)) < 3:
            warnings.append("Figure family has fewer than three scientific purpose classes.")
        if len(set(plot_types)) < 3:
            warnings.append("Figure family has fewer than three plot families.")
        # Uncertainty follows each figure's stochastic evidence, checked above.
        # A large family of exact/deterministic results does not create random
        # trials, and finite-expert spread is not predictive coverage.

    return {
        "status": status,
        "publication_chart_policy_applied": publication,
        "figure_count": len(figures),
        "purpose_count": len(set(purposes)),
        "plot_type_count": len(set(plot_types)),
        "submission_candidate_ready": submission and not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate figure provenance, diversity, and render QA gates.")
    parser.add_argument("manifest")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--base-dir", default="", help="Project root used to verify data, script, and figure artifact paths.")
    args = parser.parse_args()
    path = Path(args.manifest).resolve()
    base_dir = Path(args.base_dir).resolve() if args.base_dir else None
    result = {"manifest": str(path), **validate_figure_manifest(json.loads(path.read_text(encoding="utf-8")), base_dir=base_dir)}
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    sys.stdout.buffer.write((payload + "\n").encode("utf-8", errors="replace"))
    if args.json_out:
        Path(args.json_out).write_text(payload, encoding="utf-8")
    if result["error_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
