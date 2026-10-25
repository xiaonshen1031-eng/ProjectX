#!/usr/bin/env python3
"""Audit native MathType objects against independent and reviewed evidence."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import posixpath
import struct
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

NS = {
    "o": "urn:schemas-microsoft-com:office:office",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_native(blob: bytes) -> bytes:
    """Read genuine compound storage; reject renamed images and empty streams."""
    import olefile

    with olefile.OleFileIO(io.BytesIO(blob)) as ole:
        if not ole.exists("Equation Native"):
            raise ValueError("Missing Equation Native stream")
        return ole.openstream("Equation Native").read()


def mtef_bytes(native: bytes) -> bytes:
    if len(native) < 33:
        raise ValueError("Truncated Equation Native header/payload")
    header = struct.unpack_from("<I", native, 0)[0]
    length = struct.unpack_from("<I", native, 8)[0]
    if header < 28 or header > len(native) - 5 or length != len(native) - header:
        raise ValueError("Invalid Equation Native payload bounds")
    data = native[header:]
    if data[0] not in {3, 4, 5}:
        raise ValueError("Unrecognized MTEF version")
    if len(data) < 12:
        raise ValueError("Empty/truncated MTEF equation")
    return data


def objects(path: Path) -> list[dict]:
    result: list[dict] = []
    with ZipFile(path) as package:
        for part in package.namelist():
            if not part.startswith("word/") or not part.endswith(".xml") or "/_rels/" in part:
                continue
            root = etree.fromstring(package.read(part))
            nodes = root.xpath(".//o:OLEObject", namespaces=NS)
            if not nodes:
                continue
            relname = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
            relationships = (
                {item.get("Id"): item for item in etree.fromstring(package.read(relname))}
                if relname in package.namelist()
                else {}
            )
            for node in nodes:
                progid = node.get("ProgID", "")
                if not progid.lower().startswith("equation."):
                    continue
                rid = node.get("{" + NS["r"] + "}id", "")
                target = relationships.get(rid)
                item = {
                    "key": part + "#" + rid,
                    "progid": progid,
                    "errors": [],
                    "native": None,
                    "mtef": None,
                    "preview": None,
                }
                try:
                    if progid != "Equation.DSMT4":
                        raise ValueError("Object is not Equation.DSMT4")
                    if target is None or target.get("TargetMode") == "External":
                        raise ValueError("Missing or external OLE target")
                    name = posixpath.normpath(posixpath.join(posixpath.dirname(part), target.get("Target", "")))
                    item["native"] = read_native(package.read(name))
                    item["mtef"] = mtef_bytes(item["native"])
                    parent = node.getparent()
                    images = parent.xpath(".//v:imagedata", namespaces=NS)
                    if not images:
                        raise ValueError("Missing visible equation preview")
                    preview = relationships.get(images[0].get("{" + NS["r"] + "}id"))
                    if preview is None or preview.get("TargetMode") == "External":
                        raise ValueError("Missing internal preview target")
                    preview_name = posixpath.normpath(
                        posixpath.join(posixpath.dirname(part), preview.get("Target", ""))
                    )
                    item["preview"] = package.read(preview_name)
                    if not item["preview"]:
                        raise ValueError("Empty preview")
                except (ValueError, KeyError, OSError, ImportError, struct.error) as exc:
                    item["errors"].append(str(exc))
                result.append(item)
    return result


def audit_mathtype(path: Path, evidence_path: Path | None = None) -> dict:
    path = path.resolve()
    items = objects(path)
    evidence: dict = {}
    base = path.parent
    if evidence_path:
        evidence_path = evidence_path.resolve()
        base = evidence_path.parent
        evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    records = evidence.get("equations", {})
    errors: list[str] = []
    if evidence.get("schema") != "senior_projectx.project.mathtype_review.v1":
        errors.append("Missing or unexpected review evidence schema")
    if evidence.get("primary_docx_sha256") != sha256(path):
        errors.append("Review evidence does not bind the current primary DOCX")
    reopened_items: list[dict] = []
    reopened_path = evidence.get("reopened_docx")
    if reopened_path:
        try:
            reopened_items = objects((base / reopened_path).resolve())
        except (OSError, ValueError, KeyError) as exc:
            errors.append("Cannot inspect reopened DOCX: " + str(exc))
    if not items:
        errors.append("No native MathType equation objects found")
    if reopened_items and len(reopened_items) != len(items):
        errors.append("Reopened DOCX equation count differs from the primary DOCX")

    results = []
    for index, item in enumerate(items):
        failures = list(item["errors"])
        record = records.get(item["key"], {})
        try:
            expected_file = record.get("expected_native_file")
            if not expected_file:
                raise ValueError("Missing independently converted Equation Native export")
            expected = mtef_bytes((base / expected_file).read_bytes())
            if item["mtef"] != expected:
                raise ValueError("Native MTEF does not match the independent conversion")
        except (OSError, ValueError, struct.error) as exc:
            failures.append(str(exc))
        if not record.get("expected_tex", "").strip():
            failures.append("Missing intended mathematical expression")
        if record.get("expected_source") != "independent_mathtype_conversion":
            failures.append("Independent conversion provenance is not established")
        render = record.get("render_artifact", "")
        if not render or not (base / render).is_file():
            failures.append("Missing inspected Word-render artifact")
        for gate in ("native_meaning_checked", "preview_matches_native", "word_render_checked"):
            if record.get(gate) is not True:
                failures.append("Unverified inspection: " + gate)
        if index >= len(reopened_items):
            failures.append("Reopen persistence is not available")
        else:
            other = reopened_items[index]
            if other["errors"] or other["mtef"] != item["mtef"] or other["preview"] != item["preview"]:
                failures.append("Reopen persistence failed for native content or preview")
        results.append(
            {
                "key": item["key"],
                "formula_id": record.get("formula_id"),
                "progid": item["progid"],
                "native_structure_valid": item["mtef"] is not None and not item["errors"],
                "status": "pass" if not failures else "unverified_or_failed",
                "issues": failures,
            }
        )
    if len(records) != len(items):
        errors.append("Evidence formula count differs from the primary DOCX")
    status = "pass" if items and not errors and all(item["status"] == "pass" for item in results) else "unverified_or_failed"
    return {
        "schema": "senior_projectx.project.mathtype_audit.v1",
        "status": status,
        "object_count": len(items),
        "equations": results,
        "issues": errors,
        "scope": "Native MathType structure, independent MTEF equality, recorded visual review, and reopen persistence only.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    result = audit_mathtype(args.docx, args.evidence)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        if args.json_out.exists():
            raise FileExistsError(f"Refusing to overwrite {args.json_out}")
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload)
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

