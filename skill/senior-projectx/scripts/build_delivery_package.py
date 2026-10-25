#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def copy_list(paths: list[str], target_dir: Path) -> list[str]:
    copied = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in paths:
        src = Path(item).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(src)
        dst = target_dir / src.name
        shutil.copy2(src, dst)
        copied.append(str(dst))
    return copied


def build(spec_path: Path) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    root = Path(spec["output_dir"]).expanduser().resolve()
    code_dir = root / "code"
    figure_dir = root / "figure"
    data_dir = root / "data"
    for folder in [code_dir, figure_dir, data_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    result = {
        "paper_title": spec.get("paper_title", ""),
        "output_dir": str(root),
        "code": copy_list(spec.get("code_files", []), code_dir),
        "figure": copy_list(spec.get("figure_files", []), figure_dir),
        "data": copy_list(spec.get("data_files", []), data_dir),
    }
    provenance = spec.get("figure_provenance", [])
    if provenance:
        (data_dir / "figure_provenance.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble a code/figure/data delivery package from a JSON spec.")
    parser.add_argument("spec_json")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    result = build(Path(args.spec_json).resolve())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
