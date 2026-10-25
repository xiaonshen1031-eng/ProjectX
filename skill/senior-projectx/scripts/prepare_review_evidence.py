#!/usr/bin/env python3
"""Bind primary, independent, reopened, and inspected render evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from audit_native_mathtype import objects


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_render_map(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Render mapping must be formula_id=path: {value}")
        formula_id, raw_path = value.split("=", 1)
        if not formula_id or formula_id in result:
            raise ValueError(f"Missing or duplicate formula id: {formula_id}")
        path = Path(raw_path).resolve()
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Render artifact does not exist or is empty: {path}")
        result[formula_id] = path
    return result


def relative(path: Path, base: Path) -> str:
    return os.path.relpath(path.resolve(), base.resolve()).replace("\\", "/")


def prepare(args: argparse.Namespace) -> dict:
    primary = args.primary_docx.resolve()
    independent = args.independent_docx.resolve()
    reopened = args.reopened_docx.resolve()
    manifest_path = args.source_manifest.resolve()
    primary_receipt_path = args.primary_receipt.resolve()
    independent_receipt_path = args.independent_receipt.resolve()
    output = args.out.resolve()
    expected_dir = args.expected_dir.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    if expected_dir.exists() and any(expected_dir.iterdir()):
        raise FileExistsError(f"Expected-native directory is not empty: {expected_dir}")
    for path in (primary, independent, reopened, manifest_path, primary_receipt_path, independent_receipt_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("schema") not in {"senior_projectx.project.equation_source.v1", "nps.project.equation_source.v1"}:
        raise ValueError("Unexpected source-manifest schema")
    source_path = Path(manifest.get("source_docx_path", ""))
    if not source_path.is_absolute():
        source_path = (manifest_path.parent / source_path).resolve()
    if not source_path.is_file() or manifest.get("source_docx_sha256") != sha256(source_path):
        raise ValueError("Source manifest no longer binds the original source DOCX")
    formulas = manifest.get("formulas", [])
    manifest_hash = sha256(manifest_path)
    primary_receipt = json.loads(primary_receipt_path.read_text(encoding="utf-8-sig"))
    independent_receipt = json.loads(independent_receipt_path.read_text(encoding="utf-8-sig"))
    for label, receipt, docx in (
        ("primary", primary_receipt, primary),
        ("independent", independent_receipt, independent),
    ):
        if receipt.get("schema") != "senior_projectx.project.mathtype_conversion.v1":
            raise ValueError(f"Unexpected {label} conversion-receipt schema")
        if receipt.get("source_manifest_sha256") != manifest_hash:
            raise ValueError(f"{label.capitalize()} conversion receipt does not bind the source manifest")
        if receipt.get("final_docx_sha256") != sha256(docx):
            raise ValueError(f"{label.capitalize()} conversion receipt does not bind its DOCX")
        if receipt.get("conversion_command_count") != 1:
            raise ValueError(f"{label.capitalize()} conversion did not record exactly one toggle command")
    primary_items, independent_items, reopened_items = objects(primary), objects(independent), objects(reopened)
    if not (len(formulas) == len(primary_items) == len(independent_items) == len(reopened_items)):
        raise ValueError("Formula/object counts differ across source, primary, independent, or reopened artifacts")
    if any(item["errors"] for group in (primary_items, independent_items, reopened_items) for item in group):
        raise ValueError("One or more native objects failed structural extraction")
    render_map = parse_render_map(args.render_map)
    missing_renders = [formula["formula_id"] for formula in formulas if formula["formula_id"] not in render_map]
    if missing_renders:
        raise ValueError("Missing render mappings for: " + ", ".join(missing_renders))
    confirmations = [args.confirm_native_meaning, args.confirm_preview_match, args.confirm_word_render]
    if any(confirmations) and not all(confirmations):
        raise ValueError("The three review confirmations must be supplied together after inspection")
    if all(confirmations) and not args.reviewer.strip():
        raise ValueError("A reviewer name is required for confirmed review evidence")

    expected_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict] = {}
    for index, (formula, primary_item, independent_item, reopened_item) in enumerate(
        zip(formulas, primary_items, independent_items, reopened_items), 1
    ):
        if primary_item["mtef"] != independent_item["mtef"]:
            raise ValueError(f"Independent MTEF mismatch for {formula['formula_id']}")
        if primary_item["mtef"] != reopened_item["mtef"] or primary_item["preview"] != reopened_item["preview"]:
            raise ValueError(f"Reopen persistence mismatch for {formula['formula_id']}")
        native_path = expected_dir / f"equation_{index:03d}.native"
        native_path.write_bytes(independent_item["native"])
        records[primary_item["key"]] = {
            "formula_id": formula["formula_id"],
            "expected_tex": formula["tex"],
            "expected_source": "independent_mathtype_conversion",
            "expected_native_file": relative(native_path, output.parent),
            "native_meaning_checked": bool(args.confirm_native_meaning),
            "preview_matches_native": bool(args.confirm_preview_match),
            "word_render_checked": bool(args.confirm_word_render),
            "render_artifact": relative(render_map[formula["formula_id"]], output.parent),
        }
    reviewed = all(confirmations)
    return {
        "schema": "senior_projectx.project.mathtype_review.v1",
        "status": "reviewed" if reviewed else "pending_review",
        "reviewer": args.reviewer.strip() or None,
        "reviewed_at": datetime.now(timezone.utc).isoformat() if reviewed else None,
        "primary_docx": relative(primary, output.parent),
        "primary_docx_sha256": sha256(primary),
        "independent_docx": relative(independent, output.parent),
        "independent_docx_sha256": sha256(independent),
        "reopened_docx": relative(reopened, output.parent),
        "reopened_docx_sha256": sha256(reopened),
        "source_manifest": relative(manifest_path, output.parent),
        "source_manifest_sha256": manifest_hash,
        "primary_conversion_receipt": relative(primary_receipt_path, output.parent),
        "primary_conversion_receipt_sha256": sha256(primary_receipt_path),
        "independent_conversion_receipt": relative(independent_receipt_path, output.parent),
        "independent_conversion_receipt_sha256": sha256(independent_receipt_path),
        "equations": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-docx", required=True, type=Path)
    parser.add_argument("--independent-docx", required=True, type=Path)
    parser.add_argument("--reopened-docx", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--primary-receipt", required=True, type=Path)
    parser.add_argument("--independent-receipt", required=True, type=Path)
    parser.add_argument("--render-map", action="append", default=[])
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--confirm-native-meaning", action="store_true")
    parser.add_argument("--confirm-preview-match", action="store_true")
    parser.add_argument("--confirm-word-render", action="store_true")
    parser.add_argument("--expected-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    result = prepare(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
