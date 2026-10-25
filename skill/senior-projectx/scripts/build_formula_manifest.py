#!/usr/bin/env python3
"""Inventory Toggle TeX formulas in the main story of a source DOCX."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "o": "urn:schemas-microsoft-com:office:office",
}
TOKEN_RE = re.compile(r"\\\[(?P<display>[\s\S]*?)\\\]|\$(?P<inline>[^$\r\n]+)\$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def balanced_braces(value: str) -> bool:
    depth = 0
    escaped = False
    for char in value:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def visible_text(root: etree._Element) -> str:
    return "".join(root.xpath(".//w:t/text()", namespaces=NS))


def build_manifest(source: Path, output: Path) -> dict:
    source = source.resolve()
    output = output.resolve()
    if source.suffix.lower() != ".docx" or not source.is_file():
        raise ValueError("Source must be an existing .docx file")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")

    formulas: list[dict] = []
    with ZipFile(source) as package:
        names = set(package.namelist())
        if "word/document.xml" not in names:
            raise ValueError("DOCX is missing word/document.xml")
        if any(name.startswith("word/vbaProject") or name.startswith("word/activeX/") for name in names):
            raise ValueError("Macro or ActiveX content is outside this conversion contract")

        for name in sorted(names):
            if not name.startswith("word/") or not name.endswith(".xml") or "/_rels/" in name:
                continue
            root = etree.fromstring(package.read(name))
            if root.xpath(".//o:OLEObject | .//m:oMath | .//m:oMathPara", namespaces=NS):
                raise ValueError(f"Existing OLE/OMML equation content is not allowed: {name}")
            if name != "word/document.xml" and TOKEN_RE.search(visible_text(root)):
                raise ValueError(f"Toggle TeX outside the main Word story is unsupported: {name}")

        root = etree.fromstring(package.read("word/document.xml"))
        for paragraph_index, paragraph in enumerate(root.xpath(".//w:body//w:p", namespaces=NS), 1):
            text = "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
            for match in TOKEN_RE.finditer(text):
                tex = (match.group("display") if match.group("display") is not None else match.group("inline")).strip()
                if not tex or not balanced_braces(tex):
                    raise ValueError(f"Malformed Toggle TeX in paragraph {paragraph_index}: {match.group(0)}")
                formulas.append(
                    {
                        "formula_id": f"eq{len(formulas) + 1:03d}",
                        "tex": tex,
                        "placement": "display" if match.group("display") is not None else "inline",
                        "context": "table" if paragraph.xpath("ancestor::w:tc", namespaces=NS) else "body",
                        "paragraph_index": paragraph_index,
                    }
                )

    if not formulas:
        raise ValueError("No Toggle TeX formulas found in the main Word story")
    record = {
        "schema": "senior_projectx.project.equation_source.v1",
        "equation_backend": "mathtype_toggle_tex",
        "source_docx_path": os.path.relpath(source, output.parent).replace("\\", "/"),
        "source_docx_sha256": sha256(source),
        "story_scope": "word/document.xml",
        "formula_count": len(formulas),
        "formulas": formulas,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_docx", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    result = build_manifest(args.source_docx, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

