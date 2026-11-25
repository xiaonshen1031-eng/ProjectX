"""Replay two evidence-rich, physically sized result compositions from matched records.

Adapted from the NPS Research Paper v3.2.4 Project figure workflow by XiaoN.
"""

from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
import json
from math import ceil
from pathlib import Path

from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import Bbox
import numpy as np

from research_figure_composition import (
    PROJECT_FONTS, _style_figure, _style_text, axes_mm, canvas_axes, new_figure, palette_catalog, save,
)


BRANCHES = {
    "project": {"width_mm": 166, "font_pt": 9, "font": PROJECT_FONTS},
}
LABELS = {
    "en": {
        "effect": "Paired difference", "edge": "Upper endpoint", "setting": "Block length", "old": "Old branch",
        "added": "Added branch", "expanded": "Expanded max", "release": "Release upper",
        "within": "Before release: within limit", "breach": "Before release: breach", "unresolved": "Before release: undetermined",
        "release_ok": "Release upper bound within limit", "release_uncertain": "Release upper bound above limit",
        "fixture": "Illustrative data",
    },
    "zh": {
        "effect": "配对差值", "edge": "区间上端点", "setting": "区块长度", "old": "原风险分支",
        "added": "新增风险分支", "expanded": "扩展风险上界", "release": "发报风险上界",
        "within": "发报前未越限", "breach": "发报前确认越限", "unresolved": "发报前未判定",
        "release_ok": "发报上界位于限值内", "release_uncertain": "发报上界高于限值",
        "fixture": "示例数据",
    },
}


def signed_limits(values, reference):
    lo, hi = min(reference, min(values)), max(reference, max(values))
    span = hi - lo or max(abs(reference), 1)
    return lo - .12 * span, hi + .12 * span


def ranges(value):
    pair = np.array(value, dtype=float)
    if pair.shape != (2,) or not np.isfinite(pair).all() or pair[0] > pair[1]:
        raise ValueError("A bound must contain two finite, ordered endpoints")
    return pair


def canvas(items, width, font_pt, font, row_height, *, left_padding):
    columns = 2 if width >= 144 and len(items) > 1 else 1
    gutter, right_padding = 8, 5
    panel_width = (width - columns * left_padding - (columns - 1) * gutter - right_padding) / columns
    if panel_width < 35:
        raise ValueError("Panel width is too small for the selected evidence recipe")
    fig = new_figure(width, row_height * ceil(len(items) / columns) + 8, font_pt, font)
    positions = [
        (left_padding + (i % columns) * (panel_width + left_padding + gutter), 6 + (i // columns) * row_height)
        for i in range(len(items))
    ]
    return fig, canvas_axes(fig), positions, panel_width


def frame(ax, colors, *, grid_axis):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, lw=.48, color=colors["grid"], zorder=0)
    ax.set_axisbelow(True)


def label_upper_ends(fig, ax, locations, intervals, estimates, reference, colors):
    """Keep precise cap labels within their actual axes and outside existing marks."""
    renderer = fig.canvas.get_renderer()
    pixels_per_point = fig.dpi / 72
    ref_y = ax.transData.transform((0, reference))[1]
    avoided = []
    for x, (low, high), estimate in zip(locations, intervals, estimates, strict=True):
        center, y_low = ax.transData.transform((x, low))
        _, y_high = ax.transData.transform((x, high))
        _, y_estimate = ax.transData.transform((x, estimate))
        cap_half = abs(ax.transData.transform((x+.085, low))[0] - center)
        radius = 2.4 * pixels_per_point
        avoided.extend([
            Bbox.from_extents(center-.6, y_low, center+.6, y_high),
            Bbox.from_extents(center-cap_half, y_low-.8, center+cap_half, y_low+.8),
            Bbox.from_extents(center-cap_half, y_high-.8, center+cap_half, y_high+.8),
            Bbox.from_extents(center-radius, y_estimate-radius, center+radius, y_estimate+radius),
        ])
    font_size = fig._nps_physical["font_pt"]
    data_boxes = list(avoided)
    annotations = []
    for x, y, color in zip(locations, intervals[:, 1], colors, strict=True):
        below = y < reference
        if below:
            options = [(5*side, offset, "left" if side > 0 else "right")
                       for offset in (-1.5, -font_size-2.5, -2*font_size-3.5) for side in (1, -1)]
        else:
            options = [(horizontal, offset, align)
                       for offset in (3, font_size+4)
                       for horizontal, align in ((0, "center"), (5, "left"), (-5, "right"))]
        label = ax.annotate(f"{y:+.3g}", (x, y), xytext=(0, 0), textcoords="offset points",
                            va="top" if below else "bottom", color=color)
        _style_text(label, fig._nps_physical)
        annotations.append(label)
        for dx, dy, align in options:
            label.set_position((dx, dy))
            label.set_ha(align)
            box = label.get_window_extent(renderer).padded(.65)
            off_reference = box.y1 < ref_y if below else box.y0 > ref_y
            if off_reference and ax.bbox.contains(*box.min) and ax.bbox.contains(*box.max) and not any(
                box.overlaps(other) for other in avoided
            ):
                avoided.append(box)
                break
        else:
            for item in annotations:
                item.remove()
            break
    else:
        return

    # Dense small-magnitude caps can share the clear space at the top of the
    # same data axes. Each value remains horizontally keyed to its own cap.
    for x, y, color in zip(locations, intervals[:, 1], colors, strict=True):
        y_cap = ax.transData.transform((x, y))[1]
        label = ax.annotate(f"{y:+.3g}", (x, y), xytext=(0, 0), textcoords="offset points",
                            ha="center", va="top", color=color)
        _style_text(label, fig._nps_physical)
        for row in (0, 1):
            upper_y = ax.bbox.y1 - (2.5 + row*(font_size+2))*pixels_per_point
            label.set_position((0, (upper_y-y_cap)/pixels_per_point))
            box = label.get_window_extent(renderer).padded(.65)
            if box.y0 > ref_y and ax.bbox.contains(*box.min) and ax.bbox.contains(*box.max) and not any(
                box.overlaps(other) for other in data_boxes
            ):
                data_boxes.append(box)
                break
        else:
            raise ValueError("Endpoint labels need more room at this width. Reflow the labels within the plot.")


def sensitivity(metrics, levels, *, labels, width_mm, font_pt, font, reference=0., endpoint_view="inline"):
    """Preserve each interval and directly identify its upper end at the same setting."""
    if not 1 <= len(metrics) <= 6 or not 2 <= len(levels) <= 6 or len(set(levels)) != len(levels):
        raise ValueError("Choose one to six metrics and two to six distinct matched levels")
    if not np.isfinite(reference) or len({m["name"] for m in metrics}) != len(metrics):
        raise ValueError("The reference must be finite and metric names must be distinct")
    if endpoint_view not in {"inline", "separate"}:
        raise ValueError("Endpoint view must be inline or explicitly separate")
    separate = endpoint_view == "separate"
    c = palette_catalog()["colors"]
    fig, sheet, positions, width = canvas(metrics, width_mm, font_pt, font, 61 if separate else 47, left_padding=18)
    locations = np.arange(len(levels))
    for spec, (left, top) in zip(metrics, positions, strict=True):
        rows = spec["rows"]
        if [row["level"] for row in rows] != list(levels):
            raise ValueError("Every metric must use the supplied order and complete level roster")
        intervals = np.array([ranges([row["lower"], row["upper"]]) for row in rows])
        estimates = np.array([row["estimate"] for row in rows], dtype=float)
        if not np.isfinite(estimates).all():
            raise ValueError("Point estimates must be finite")
        suffix = f' ({spec["unit"]})' if spec.get("unit") else ""
        sheet.text(left, top - 1.5, spec["name"] + suffix, va="center", weight="bold", color=c["ink"])
        full = axes_mm(fig, left, top+4, width, 21 if separate else 26)
        edge = axes_mm(fig, left, top+33, width, 13) if separate else full
        for axis in ((full, edge) if separate else (full,)):
            frame(axis, c, grid_axis="y")
            axis.axhline(reference, color=c["ink"], lw=.7, ls=(0, (3, 2)), zorder=1)
            side_room = .4 if separate else .58
            axis.set(xlim=(-side_room, len(levels)-1+side_room), xticks=locations)
            axis.yaxis.set_major_locator(MaxNLocator(3))
        lower_plot, upper_plot = signed_limits(np.r_[intervals.ravel(), estimates], reference)
        full.set(ylim=(lower_plot, upper_plot if separate else upper_plot+.2*(upper_plot-lower_plot)),
                 ylabel=labels["effect"])
        full.tick_params(labelbottom=not separate, length=2)
        common = spec.get("common_estimate_levels", [])
        if common:
            guide = [levels.index(name) for name in common]
            if len(guide) < 2 or guide != list(range(guide[0], guide[-1]+1)) or np.any(estimates[guide] != estimates[guide[0]]):
                raise ValueError("A common-estimate guide needs adjacent settings with an identical estimate")
            full.plot([guide[0], guide[-1]], [estimates[guide[0]]]*2,
                      color=c["cobalt"], lw=.7, ls=(0, (3, 2)), zorder=1)
        full.vlines(locations, *intervals.T, color=c["ink"], lw=.9, zorder=2)
        full.hlines(intervals[:, 0], locations-.085, locations+.085, color=c["ink"], lw=.65)
        upper = intervals[:, 1]
        edge_colors = np.select((upper > reference, upper < reference),
                                (c["raspberry"], c["cobalt"]), default=c["iris"])
        full.hlines(upper, locations-.085, locations+.085, color=edge_colors, lw=1.06)
        full.scatter(locations, estimates, s=18, facecolor=c["jade"], edgecolor=c["ink"], lw=.55, zorder=3)
        edge.set(xticklabels=levels, xlabel=spec.get("setting_label", labels["setting"]))
        if separate:
            edge.set(ylim=signed_limits(upper, reference), ylabel=labels["edge"])
            edge.vlines(locations, np.minimum(reference, upper), np.maximum(reference, upper),
                        color=c["grid"], lw=1, zorder=1)
            edge.scatter(locations, upper, s=15, marker="D", edgecolor=c["ink"], lw=.55,
                         facecolor=edge_colors, zorder=3)
        else:
            label_upper_ends(fig, full, locations, intervals, estimates, reference, edge_colors)
    _style_figure(fig)
    return fig


def release_traces(cases, *, labels, width_mm, font_pt, font, reference=0., unit=""):
    """Show certified branch dominance, a common limit, and the released upper bound."""
    if not 1 <= len(cases) <= 8 or len({case["name"] for case in cases}) != len(cases) or not np.isfinite(reference):
        raise ValueError("Choose one to eight distinct cases and a finite reference")
    c = palette_catalog()["colors"]
    has_detail = any("detail_radius" in case for case in cases)
    fig, sheet, positions, width = canvas(cases, width_mm, font_pt, font, 70 if has_detail else 53, left_padding=29)
    bounds = [(ranges(case["old"]), ranges(case["added"]), float(case["released_upper"])) for case in cases]
    combined = np.array([[*old, *added, released] for old, added, released in bounds])
    if not np.isfinite(combined).all():
        raise ValueError("Release certificate must be a finite upper bound")
    xlim = signed_limits(combined.ravel(), reference)
    records = []
    for case, (left, top), (old, added, released) in zip(cases, positions, bounds, strict=True):
        expanded = np.maximum(old, added)
        winner = 3 if old[0] > added[1] else (2 if added[0] > old[1] else None)
        verdict = "breach" if expanded[0] > reference else ("within" if expanded[1] <= reference else "unresolved")
        records.append({"case": case["name"], "active": {3: "old", 2: "added", None: None}[winner],
                        "expanded_bounds": expanded.tolist(), "expanded_limit_relation": verdict,
                        "released_upper": released, "released_within": released <= reference})
        sheet.text(left, top-1.5, case["name"], va="center", weight="bold", color=c["ink"])
        plot = axes_mm(fig, left, top+4, width, 23)
        positions_y = (3, 2, 1, 0)
        ticks = [labels[key] for key in ("old", "added", "expanded", "release")]
        upper = [old[1], added[1], expanded[1], released]
        frame(plot, c, grid_axis="y")
        plot.set(xlim=xlim, ylim=(-.48, 3.48), yticks=positions_y, yticklabels=ticks)
        plot.tick_params(axis="y", length=0)
        plot.xaxis.set_major_locator(MaxNLocator(4))
        plot.axvspan(reference, xlim[1], color=c["raspberry_wash"], zorder=0)
        plot.axvline(reference, color=c["ink"], lw=.78)
        if winner is not None:
            plot.vlines(expanded[1], 1, winner, lw=.8, ls=(0, (2.4, 1.8)), color=c["ink"])
        hues = [c[key] for key in ("sun", "raspberry", "jade", "iris")]
        for y, value, hue, marker in zip(positions_y, upper, hues, ("o", "D", "D", "s"), strict=True):
            plot.hlines(y, min(reference, value), max(reference, value), color=c["grid"], lw=.86, zorder=1)
            plot.plot(value, y, marker=marker, ms=4.15, mfc=hue, mec=c["ink"], mew=.55, zorder=4)
        for y, (low, high), hue in zip(positions_y[:3], (old, added, expanded), hues[:3], strict=True):
            plot.hlines(y, low, high, color=hue, lw=1.9, zorder=3)
            plot.vlines(low, y-.13, y+.13, color=c["ink"], lw=.65, zorder=3)
        if case.get("annotate_margin") and "detail_radius" not in case:
            offset = -8 if reference >= sum(xlim)/2 else 8
            for y, value in ((3, old[1]), (0, released)):
                plot.annotate(f"{value:+.4g}", (value, y), xytext=(offset, -6 if y == 3 else 6),
                              textcoords="offset points",
                              ha="right" if offset < 0 else "left", va="center", color=c["ink"],
                              arrowprops={"arrowstyle": "-", "color": c["grid"], "lw": .58,
                                          "shrinkA": 2, "shrinkB": 3}, zorder=5)
        plot.set_xlabel(unit, labelpad=2)
        radius = case.get("detail_radius")
        if radius is not None:
            detail = axes_mm(fig, left, top+38, width, 9)
            frame(detail, c, grid_axis="y")
            detail.set(yticks=[1, 0], yticklabels=[labels["old"], labels["release"]], ylim=(-.5, 1.5))
            detail.tick_params(axis="y", length=0)
            detail.xaxis.set_major_locator(MaxNLocator(3))
            detail.axvline(reference, color=c["ink"], lw=.75, ls=(0, (2, 1.5)))
            if not np.isfinite(radius) or radius <= max(abs(old[1]-reference), abs(released-reference)):
                raise ValueError("A magnified threshold view must contain both shown bounds")
            detail.set_xlim(reference-radius, reference+radius)
            detail.plot(old[1], 1, "o", ms=4, mfc=c["sun"], mec=c["ink"], mew=.55)
            detail.plot(released, 0, "s", ms=4, mfc=c["iris"], mec=c["ink"], mew=.55)
        verdict_y = top + (57 if radius is not None else 39)
        sheet.text(left, verdict_y, labels[verdict], va="center", color=c["ink"], weight="bold")
        release_label = "release_ok" if released <= reference else "release_uncertain"
        sheet.text(left, verdict_y+4, labels[release_label], va="center", color=c["ink"])
    fig._nps_release_records = records
    _style_figure(fig)
    return fig


def demo_spec(recipe, branch):
    project = branch == "project"
    if recipe == "sensitivity":
        levels = ["半长", "基准", "双长"] if project else ["½×", "1×", "2×"]
        examples = [("均方误差" if project else "Squared error", -.82, (-1.9, -2.05, -2.2), (.22, .35, .52)),
                    ("绝对误差" if project else "Absolute error", -1.41, (-2.24, -2.36, -2.51), (-.58, -.46, -.29))]
        return {"levels": levels, "metrics": [
            {"name": name, "unit": "×10⁻³", "common_estimate_levels": levels,
             "rows": [{"level": label, "estimate": est, "lower": lo, "upper": hi}
                                                 for label, lo, hi in zip(levels, low, high, strict=True)]}
            for name, est, low, high in examples
        ]}
    return {"unit": "风险差" if project else "Risk minus limit", "cases": [
        {"name": "常态" if project else "Nominal", "old": [-.7, -.65], "added": [-1.1, -1.03], "released_upper": -.65},
        {"name": "窄边界" if project else "Tight boundary", "old": [-.015, -.012],
         "added": [.2, .24], "released_upper": -.004, "annotate_margin": True},
    ]}


def generate(recipe, branch, spec, output, *, demo=False, language="zh", formats=("pdf", "svg", "png"), dpi=240):
    if recipe not in {"sensitivity", "release"}:
        raise ValueError("Choose sensitivity or release")
    provenance = spec.get("provenance", {})
    if not demo and not all(isinstance(provenance.get(k), str) and provenance[k].strip() for k in ("kind", "source")):
        raise ValueError("Bind production input to a named source and its observation or calculation type")
    input_hash = sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False,
                                  allow_nan=False).encode("utf-8")).hexdigest()
    config = {**BRANCHES[branch], **spec.get("canvas", {})}
    labels = {**LABELS[language], **spec.get("labels", {})}
    if recipe == "sensitivity":
        fig = sensitivity(spec["metrics"], spec["levels"], labels=labels, **config,
                          reference=spec.get("reference", 0.), endpoint_view=spec.get("endpoint_view", "inline"))
    else:
        fig = release_traces(spec["cases"], labels=labels, **config,
                             reference=spec.get("reference", 0.), unit=spec.get("unit", ""))
    illustrative = demo or provenance.get("kind") == "illustrative"
    if illustrative:
        fig.text(.98, .014, labels["fixture"], ha="right", va="bottom")
        _style_figure(fig)
    report = save(fig, output, formats=formats, dpi=dpi)
    report["recipe"] = recipe
    report["branch"] = branch
    report["source"] = {"kind": "illustrative"} if demo else provenance
    report["illustrative"] = illustrative
    report["input_sha256"] = input_hash
    if hasattr(fig, "_nps_release_records"):
        report["release_records"] = fig._nps_release_records
    output.with_suffix(".layout.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    return report


def main():
    cli = ArgumentParser(description=__doc__)
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true")
    mode.add_argument("--config", type=Path)
    cli.add_argument("--recipe", choices=("sensitivity", "release"), required=True)
    cli.add_argument("--branch", choices=tuple(BRANCHES), default="project")
    cli.add_argument("--language", choices=tuple(LABELS), default="zh")
    cli.add_argument("--output-dir", type=Path, required=True)
    cli.add_argument("--formats", nargs="+", choices=("pdf", "svg", "png", "tiff"), default=("pdf", "svg", "png"))
    cli.add_argument("--dpi", type=float, default=240)
    args = cli.parse_args()
    spec = demo_spec(args.recipe, "project" if args.language == "zh" else "english") if args.demo else json.loads(args.config.read_text(encoding="utf-8-sig"))
    if not args.demo:
        provenance = spec.get("provenance", {})
        if not provenance.get("kind") or not provenance.get("source"):
            cli.error("Bind production input to a named source and its observation or calculation type")
    stem = f"{args.branch}_{args.recipe}" + ("_illustrative" if args.demo else "")
    try:
        generate(args.recipe, args.branch, spec, args.output_dir / stem, demo=args.demo,
                 language=args.language, formats=args.formats, dpi=args.dpi)
    except ValueError as exc:
        cli.error(str(exc))


if __name__ == "__main__":
    main()
