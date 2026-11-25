#!/usr/bin/env python3
"""Compare protected evidence in the displayed slide order of two PPTX packages."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

OO = "{http://schemas.openxmlformats.org/"
P = OO + "presentationml/2006/main}"
A = OO + "drawingml/2006/main}"
C = OO + "drawingml/2006/chart}"
R = OO + "officeDocument/2006/relationships}"
M = OO + "officeDocument/2006/math}"


def relationships(package, part):
    folder, name = posixpath.split(part)
    path = posixpath.join(folder, "_rels", name + ".rels")
    try:
        root = ET.fromstring(package.read(path))
    except KeyError:
        return {}
    return {node.attrib["Id"]: (
        node.attrib["Target"] if node.get("TargetMode") == "External"
        else posixpath.join(folder, node.attrib["Target"]).lstrip("/"),
        node.get("TargetMode") == "External",
        node.attrib["Type"].rsplit("/", 1)[-1],
    ) for node in root}


def bound_payload(package, relation):
    path, external, role = relation
    if external:
        return {"role": role, "external_target": path}
    return {"role": role, "sha256": hashlib.sha256(package.read(posixpath.normpath(path))).hexdigest()}


def chart_evidence(package, part):
    root = ET.fromstring(package.read(part))
    data_roles = ("tx", "cat", "val", "xVal", "yVal", "bubbleSize")
    series = []
    for node in root.iter(C + "ser"):
        data = {}
        for role in data_roles:
            source = node.find(C + role)
            if source is not None:
                data[role] = {
                    "references": [ref.text for ref in source.iter(C + "f")],
                    "cache": [[v.get("idx"), v.findtext(C + "v")] for v in source.iter(C + "pt")],
                    "literal": source.findtext(C + "v"),
                }
        series.append(data)
    rel = relationships(package, part)
    books = [bound_payload(package, rel[node.attrib[R + "id"]])
             for node in root.iter(C + "externalData")]
    return series, books


def slide_evidence(package, part):
    root = ET.fromstring(package.read(part))
    rel = relationships(package, part)
    charts, data_files = [], []
    for chart in root.iter(C + "chart"):
        uri, external, _ = rel[chart.attrib[R + "id"]]
        if external:
            raise ValueError("External chart parts cannot be audited")
        series, workbooks = chart_evidence(package, posixpath.normpath(uri))
        charts.append(series)
        data_files.append(workbooks)
    extended = []
    for relation in rel.values():
        uri, external, role = relation
        if role == "chartEx":
            linked = [] if external else [bound_payload(package, ref)
                      for ref in relationships(package, posixpath.normpath(uri)).values()
                      if ref[2] in {"package", "oleObject"}]
            extended.append({"chart": bound_payload(package, relation), "linked_data": linked})
    tables = [[[tuple("".join(t.itertext()) for t in cell.iter(A + "t"))
                for cell in row.findall(A + "tc")] for row in table.findall(A + "tr")]
              for table in root.iter(A + "tbl")]
    return {
        "chart_series": charts,
        "chart_workbooks": data_files,
        "table_cells": tables,
        "pictures": [bound_payload(package, rel[key]) for image in root.iter(A + "blip")
                     for key in [image.get(R + "embed") or image.get(R + "link")] if key],
        "ole_objects": [{"class": ole.get("progId"), **bound_payload(package, rel[ole.attrib[R + "id"]])}
                        for ole in root.iter(P + "oleObj") if ole.get(R + "id")],
        "editable_equations": [ET.canonicalize(ET.tostring(equation, encoding="unicode"))
                               for equation in root.iter(M + "oMath")],
        "extended_charts": extended,
    }


def inventory(path):
    with ZipFile(path) as package:
        part = "ppt/presentation.xml"
        root = ET.fromstring(package.read(part))
        rel = relationships(package, part)
        slide_list = root.find(P + "sldIdLst")
        if slide_list is None or not len(slide_list):
            raise ValueError("Presentation contains no slides")
        parts = []
        for slide in slide_list:
            uri, external, role = rel[slide.attrib[R + "id"]]
            if external or role != "slide":
                raise ValueError("Invalid presentation slide relationship")
            parts.append(posixpath.normpath(uri))
        size = root.find(P + "sldSz")
        return {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_emu": [int(size.attrib[key]) for key in ("cx", "cy")],
            "slides": [slide_evidence(package, slide) for slide in parts],
        }


def compare(source, revised):
    before, after = map(inventory, (source, revised))
    differences = []
    if before["size_emu"] != after["size_emu"]:
        differences.append({"kind": "page_size"})
    old, new = before["slides"], after["slides"]
    if len(old) != len(new):
        differences.append({"kind": "slide_count"})
    for index, (left, right) in enumerate(zip(old, new), 1):
        fields = [field for field in left if left[field] != right[field]]
        if fields:
            differences.append({"slide": index, "kind": "protected_content", "fields": fields})
    return {
        "status": "review_required" if differences else "protected_evidence_matches",
        "source_sha256": before["sha256"],
        "revised_sha256": after["sha256"],
        "source_slide_count": len(old),
        "revised_slide_count": len(new),
        "differences": differences,
        "scope": "Slide-order structural comparison; verify final rendered pages and native edits separately.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revised", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = compare(args.source, args.revised)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        with args.json_out.open("x", encoding="utf-8") as out:
            out.write(text + "\n")
    print(text)
    return 2 if result["differences"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
