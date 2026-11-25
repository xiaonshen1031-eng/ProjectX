#!/usr/bin/env python3
"""Read-only structural comparison for a bounded Word revision or highlight pair."""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from audit_word_citations import Formatting, Story, W

M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
O = "{urn:schemas-microsoft-com:office:office}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
STORY_PART = re.compile(r"word/(?:document|footnotes|endnotes|header\d+|footer\d+)\.xml")
LAYOUT_PROPERTIES = frozenset(W + name for name in ("pPr", "rPr", "tcPr", "trPr", "tblPr", "tblGrid"))
CATEGORIES = ("math", "drawings", "embeddings", "media", "relationships",
              "fields", "bookmarks", "table_content")


def xml_signature(node, *, omit=frozenset()):
    return [node.tag, sorted((k, v) for k, v in node.attrib.items() if not k.startswith(W + "rsid")),
            node.text, [xml_signature(child, omit=omit) for child in node if child.tag not in omit]]


def part_bytes(path):
    data = Path(path).read_bytes()
    with ZipFile(BytesIO(data)) as archive:
        contents = {part: archive.read(part) for part in archive.namelist()}
    if "word/document.xml" not in contents:
        raise ValueError("The Word package lacks word/document.xml.")
    return sha256(data).hexdigest(), contents


def protected_inventory(package):
    signatures = {category: [] for category in CATEGORIES}
    styles = ET.fromstring(package["word/styles.xml"]) if "word/styles.xml" in package else None
    fmt = Formatting(styles)
    for name, data in sorted(package.items()):
        if name.startswith(("word/embeddings/", "word/media/")) and not name.endswith("/"):
            category = "embeddings" if name.startswith("word/embeddings/") else "media"
            signatures[category].append((name, sha256(data).hexdigest()))
        if name.startswith("word/") and name.endswith(".rels"):
            node = ET.fromstring(data)
            signatures["relationships"].append((name, sorted(sorted(child.attrib.items()) for child in node)))
        if name.startswith("word/charts/") and name.endswith(".xml"):
            signatures["drawings"].append((name, xml_signature(ET.fromstring(data))))
        if not STORY_PART.fullmatch(name):
            continue
        root = ET.fromstring(data)
        story = Story(name, root, fmt)
        if story.errors:
            raise ValueError(f"{name} contains an incomplete field or bookmark: {story.errors[0]}")
        for bookmark in story.bookmarks:
            content = "".join(g["char"] for g in story.glyphs[bookmark["start"]:bookmark["end"]])
            signatures["bookmarks"].append((name, bookmark["name"], content))
        for node in root.iter():
            if node.tag in (M + "oMath", O + "OLEObject"):
                signatures["math"].append((name, xml_signature(node)))
            elif node.tag in (W + "drawing", W + "pict", W + "object"):
                signatures["drawings"].append((name, xml_signature(node)))
            elif node.tag in (W + "bookmarkStart", W + "bookmarkEnd"):
                signatures["bookmarks"].append((name, xml_signature(node)))
            elif node.tag == W + "tbl":
                signatures["table_content"].append((name, xml_signature(node, omit=LAYOUT_PROPERTIES)))
        glyph_formats = defaultdict(list)
        for glyph in story.glyphs:
            for index in glyph["fields"]:
                glyph_formats[index].append(glyph["superscript"])
        signatures["fields"].extend((name, field.code, field.result, field.locked, field.instruction_formats,
            glyph_formats[index])
            for index, field in enumerate(story.fields))
    return signatures


def ordinary_text_run(run):
    return run.tag == W + "r" and any(child.tag == W + "t" for child in run) and all(
        child.tag in (W + "rPr", W + "t") for child in run)


def review_story(data, *, allowed_color=None):
    root = ET.fromstring(data)
    active_fields = 0
    marked = 0
    ordinary = set()

    def visit(node, protected=False):
        nonlocal active_fields, marked
        protected = protected or node.tag in (W + "fldSimple", W + "ins", W + "del",
                                               W + "moveFrom", W + "moveTo", M + "oMath")
        if node.tag == W + "fldChar":
            marker = node.get(W + "fldCharType")
            active_fields += int(marker == "begin") - int(marker == "end")
        if ordinary_text_run(node) and not protected and not active_fields:
            ordinary.add(node)
            properties = node.find(W + "rPr")
            marking = properties.find(W + "highlight") if properties is not None else None
            if allowed_color and marking is not None and marking.get(W + "val") == allowed_color:
                properties.remove(marking)
                marked += len("".join(text.text or "" for text in node.findall(W + "t")))
        for child in node:
            visit(child, protected)
    visit(root)

    # Highlighting a substring may split an otherwise identical ordinary run.
    # Only coalesce adjacent plain-text runs with the same effective direct properties.
    for parent in root.iter():
        previous = None
        for run in list(parent):
            if run not in ordinary:
                previous = None
                continue
            props = run.find(W + "rPr")
            if props is not None and not len(props) and not props.attrib:
                run.remove(props)
                props = None
            text = "".join(t.text or "" for t in run.findall(W + "t"))
            for t in run.findall(W + "t"):
                run.remove(t)
            t = ET.SubElement(run, W + "t")
            t.text = text
            t.set(XML_SPACE, "preserve")
            prior_props = previous.find(W + "rPr") if previous is not None else None
            if previous is not None and run.attrib == previous.attrib and (
                (props is None and prior_props is None)
                or (props is not None and prior_props is not None and xml_signature(props) == xml_signature(prior_props))
            ):
                prior_text = previous.find(W + "t")
                prior_text.text = (prior_text.text or "") + text
                parent.remove(run)
            else:
                previous = run
    return xml_signature(root), marked


def audit(before, after, *, allow_change=(), highlight_color=None):
    before_digest, baseline = part_bytes(before)
    after_digest, revised = part_bytes(after)
    left, right = (protected_inventory(p) for p in (baseline, revised))
    summary = {}
    for category in CATEGORIES:
        same = left[category] == right[category]
        summary[category] = {"before": len(left[category]), "after": len(right[category]),
                             "same": same, "change_declared": category in allow_change}
    differences = [category for category, state in summary.items() if not state["same"] and not state["change_declared"]]
    marked = 0
    changed_parts = []
    if highlight_color:
        for part in sorted(baseline.keys() | revised.keys()):
            old, new = baseline.get(part), revised.get(part)
            if old is not None and new is not None and STORY_PART.fullmatch(part):
                old, _ = review_story(old)
                new, count = review_story(new, allowed_color=highlight_color)
                marked += count
            if old != new:
                changed_parts.append(part)
        # Table text-run splits are already compared under the stricter marked-copy normalization.
        differences = [category for category in differences if category not in ("table_content", "fields")]
    return {"structural_status": "fail" if differences or changed_parts else "pass",
            "before_sha256": before_digest, "after_sha256": after_digest,
            "protected_content": summary, "unexpected_changes": differences,
            "review_copy_unexpected_parts": changed_parts, "ordinary_highlight_chars": marked,
            "scope": "Structural preservation only. Check replacement wording, span coverage and rendered pages separately.",
            "word_reopened": False, "visual_reviewed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--allow-change", action="append", choices=CATEGORIES, default=[])
    parser.add_argument("--highlight-color", help="The explicit color of ordinary-text changes in AFTER.")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.highlight_color and args.allow_change:
        parser.error("A highlight pair should differ only in its requested ordinary-text marks.")
    if args.json_out and (args.json_out.suffix.lower() != ".json" or any(
        args.json_out.resolve() == source.resolve()
        or (args.json_out.exists() and source.exists() and args.json_out.samefile(source))
        for source in (args.before, args.after)
    )):
        parser.error("Choose a new JSON report path separate from both inputs.")
    try:
        result = audit(args.before, args.after, allow_change=args.allow_change, highlight_color=args.highlight_color)
    except (OSError, BadZipFile, ET.ParseError, ValueError) as exc:
        parser.error(str(exc))
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["structural_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
