#!/usr/bin/env python3
"""Create a Senior-ProjectX engineering workspace without replacing existing work."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path

PROJECT_SECTIONS = ["项目概述与研究任务", "研究对象、资料与数据", "研究专题", "综合技术评价与工程建议", "结论"]


def slugify(text: str) -> str:
    display = unicodedata.normalize("NFKC", text).strip().lower()
    safe = re.sub(r"[^\w\u3400-\u9fff]+", "-", display, flags=re.UNICODE)
    safe = re.sub(r"-{2,}", "-", safe).strip("-_")
    return safe[:64].rstrip("-_") if safe else "untitled-" + hashlib.sha256(display.encode("utf-8")).hexdigest()[:10]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--title", default="项目技术报告")
    parser.add_argument("--idea", default="")
    parser.add_argument("--template-path", default="", type=str)
    parser.add_argument("--language", choices=["chinese", "english"], default="chinese")
    parser.add_argument("--stack", default="python+matlab")
    parser.add_argument("--task-stage", choices=["initial", "analysis", "interim_report", "final_report", "revision"], default="initial")
    parser.add_argument("--equation-backend", choices=["mathtype_native", "office_math"], default="mathtype_native")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = args.output_dir.resolve()
    manifest_path = root / "project_manifest.json"
    if manifest_path.exists():
        if args.resume:
            print(root)
            return 0
        raise FileExistsError("project_manifest.json already exists; use --resume to preserve existing work")
    skill_root = Path(__file__).resolve().parent.parent
    source = Path(args.template_path).resolve() if args.template_path else skill_root / "templates/project_report.docx"
    if not source.is_file():
        raise FileNotFoundError(f"Project template not found: {source}")
    skeleton = root / "manuscript/project_report_skeleton.docx"
    if skeleton.exists():
        raise FileExistsError(f"Existing skeleton is protected: {skeleton}")
    folders = {
        "manuscript": "manuscript", "code_python": "code/python", "code_matlab": "code/matlab",
        "figure_final": "figure/final", "figure_redraw": "figure/redraw", "data_raw": "data/raw",
        "data_processed": "data/processed", "data_results": "data/results", "literature": "literature", "review": "review",
    }
    for rel in folders.values():
        (root / rel).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, skeleton)
    manifest = {
        "schema": "senior_projectx.workspace.v1", "paper_title": args.title, "paper_slug": slugify(args.title),
        "template_path": str(source), "document_type": "project", "language": args.language,
        "task_stage": args.task_stage, "output_format": "docx", "solver_stack": args.stack,
        "idea_summary": args.idea, "folders": folders, "manuscript_mode": "project_word",
        "equation_backend": args.equation_backend, "expected_sections": PROJECT_SECTIONS,
        "expected_result_figures": [], "review_files": {},
        "project": {"tasks": [], "lineage": [], "report_sections": PROJECT_SECTIONS},
        "notes": ["客户模板优先；按任务书和技术问题增删章节。", "原生公式后端按明确选择执行。"],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
