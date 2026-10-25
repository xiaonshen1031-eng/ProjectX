#!/usr/bin/env python3
"""Number converted Project MathType paragraphs without touching OLE parts.

Only ordinary one-column body display paragraphs are supported. This is a
layout pass, not a conversion, authenticity check or visual approval.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "o": "urn:schemas-microsoft-com:office:office",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}


def tag(name):
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"


def element(qualified_name, **attrs):
    node = etree.Element(tag(qualified_name))
    for key, value in attrs.items():
        node.set(tag("w:" + key), str(value))
    return node


def child(parent, name):
    node = parent.find(tag(name))
    if node is None:
        node = element(name)
        if name == "w:pPr":
            parent.insert(0, node)
        else:
            parent.append(node)
    return node


def number_run(text=None, *, tab=False):
    run, props = element("w:r"), element("w:rPr")
    props.extend([
        element("w:rFonts", ascii="Times New Roman", hAnsi="Times New Roman", eastAsia="SimSun"),
        element("w:b", val="0"), element("w:bCs", val="0"),
        element("w:i", val="0"), element("w:iCs", val="0"), element("w:color", val="000000"),
        element("w:position", val="0"),
        element("w:sz", val="24"), element("w:szCs", val="24"),
        element("w:u", val="none"),
    ])
    run.append(props)
    node = element("w:tab" if tab else "w:t")
    if not tab:
        node.text = text
    run.append(node)
    return run


def section_width(paragraph, body, *, gutter_at_top=False):
    if paragraph.getparent() is not body:
        raise ValueError("Display equation is not an ordinary body paragraph; use template-specific layout")
    section = None
    for sibling in list(body)[body.index(paragraph):]:
        section = sibling.find("w:pPr/w:sectPr", NS)
        if section is not None:
            break
    if section is None:
        section = body.find("w:sectPr", NS)
    if section is None:
        raise ValueError("Current section page geometry is missing")
    columns = section.find("w:cols", NS)
    if columns is not None and (int(columns.get(tag("w:num"), "1")) != 1 or len(columns.findall("w:col", NS)) > 1):
        raise ValueError("Multi-column sections require template-specific equation layout")
    page, margins = section.find("w:pgSz", NS), section.find("w:pgMar", NS)
    if page is None or margins is None:
        raise ValueError("Current section width or margins are missing")
    width = int(page.get(tag("w:w"))) - int(margins.get(tag("w:left"))) - int(margins.get(tag("w:right")))
    if not gutter_at_top:
        width -= int(margins.get(tag("w:gutter"), "0"))
    if width <= 0:
        raise ValueError("Current text-area width is not positive")
    return width


def inherited_tabs(paragraph, styles):
    positions = {node.get(tag("w:pos")) for node in paragraph.findall("w:pPr/w:tabs/w:tab", NS)}
    if styles is not None:
        positions.update(n.get(tag("w:pos")) for n in styles.findall("w:docDefaults/w:pPrDefault/w:pPr/w:tabs/w:tab", NS))
        style_id = paragraph.find("w:pPr/w:pStyle", NS)
        by_id = {s.get(tag("w:styleId")): s for s in styles.findall("w:style", NS)}
        current = style_id.get(tag("w:val")) if style_id is not None else next(
            (s.get(tag("w:styleId")) for s in by_id.values()
             if s.get(tag("w:type")) == "paragraph" and s.get(tag("w:default")) in {"1", "true", "on"}), None)
        seen = set()
        while current in by_id and current not in seen:
            seen.add(current)
            style = by_id[current]
            positions.update(n.get(tag("w:pos")) for n in style.findall("w:pPr/w:tabs/w:tab", NS))
            based = style.find("w:basedOn", NS)
            current = based.get(tag("w:val")) if based is not None else None
    return {int(p) for p in positions if p is not None}


def format_paragraph(paragraph, equation, width, number, styles):
    run = equation.xpath("ancestor::w:r[1]", namespaces=NS)[0]
    if run.getparent() is not paragraph:
        raise ValueError("Nested/revised equation runs require template-specific layout")
    if any(re.search(r"position\s*:\s*absolute", n.get("style", ""), re.I)
           for n in run.xpath(".//*[local-name()='shape']")) or run.xpath(".//*[local-name()='anchor']"):
        raise ValueError("Floating equations require template-specific layout")
    if len(paragraph.xpath(".//o:OLEObject", namespaces=NS)) != 1:
        raise ValueError("A display paragraph must contain one MathType object")
    if paragraph.find("w:pPr/w:numPr", NS) is not None:
        raise ValueError("List-numbered display paragraphs require template-specific layout")
    for start in paragraph.findall("w:bookmarkStart", NS):
        end = next((n for n in paragraph.findall("w:bookmarkEnd", NS)
                    if n.get(tag("w:id")) == start.get(tag("w:id"))), None)
        if end is None or not paragraph.index(start) < paragraph.index(run) < paragraph.index(end):
            raise ValueError("A number/text bookmark requires template-specific cross-reference handling")
    allowed = {tag(n) for n in ["w:pPr", "w:r", "w:fldSimple", "w:bookmarkStart", "w:bookmarkEnd", "w:proofErr"]}
    removable, text = [], []
    for node in paragraph:
        if node.tag not in allowed:
            raise ValueError("Unrecognized display paragraph content; nothing was written")
        if node is run or node.tag in {tag("w:pPr"), tag("w:bookmarkStart"), tag("w:bookmarkEnd"), tag("w:proofErr")}:
            continue
        if node.xpath(".//w:object | .//w:drawing | .//w:pict | .//m:oMath", namespaces=NS):
            raise ValueError("Unexpected object outside the display formula")
        if node.tag == tag("w:r") and any(n.tag not in {tag(t) for t in
                ["w:rPr", "w:t", "w:tab", "w:fldChar", "w:instrText"]} for n in node):
            raise ValueError("Unexpected non-text content outside the display formula")
        text.extend(node.xpath(".//w:t/text()", namespaces=NS))
        instructions = node.xpath(".//w:instrText/text()", namespaces=NS)
        if node.tag == tag("w:fldSimple"):
            instructions.append(node.get(tag("w:instr"), ""))
        if any(not re.fullmatch(r"\s*SEQ\s+Equation\b(?:\s+\\(?:\*\s+ARABIC|r\s+\d+))*\s*", value, re.I)
               for value in instructions):
            raise ValueError("An unrelated field occurs in the equation paragraph")
        removable.append(node)
    if not re.fullmatch(r"\s*(?:[（(]\s*\d+\s*[)）])?\s*", "".join(text)):
        raise ValueError("Text around the equation is not an unnumbered or numeric display label")
    old_positions = inherited_tabs(paragraph, styles)
    props = child(paragraph, "w:pPr")
    ind = child(props, "w:ind")
    ind.attrib.clear()
    for key in ["left", "right", "firstLine", "leftChars", "rightChars", "firstLineChars"]:
        ind.set(tag("w:" + key), "0")
    child(props, "w:jc").set(tag("w:val"), "left")
    child(props, "w:keepLines").set(tag("w:val"), "1")
    spacing = child(props, "w:spacing")
    spacing.set(tag("w:line"), "240"); spacing.set(tag("w:lineRule"), "auto")
    tabs = child(props, "w:tabs")
    tabs.clear()
    center = round(width / 2)
    for pos in sorted(old_positions - {center, width}):
        tabs.append(element("w:tab", val="clear", pos=pos))
    tabs.extend([element("w:tab", val="center", pos=center), element("w:tab", val="right", pos=width)])
    for node in removable:
        paragraph.remove(node)
    paragraph.insert(paragraph.index(run), number_run(tab=True))
    # Preserve equation bookmark endpoints; numbering is outside the object.
    paragraph.extend([number_run(tab=True), number_run("(")])
    instruction = " SEQ Equation " + (r"\r 1 " if number == 1 else "") + r"\* ARABIC "
    field = element("w:fldSimple", instr=instruction, dirty="true")
    field.append(number_run(str(number)))
    paragraph.extend([field, number_run(")")])
    # Keep the WordprocessingML pPr sequence valid when adding direct overrides.
    order = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle",
             "rPr", "sectPr", "pPrChange"]
    ranks = {tag("w:" + name): i for i, name in enumerate(order)}
    props[:] = sorted(list(props), key=lambda n: ranks.get(n.tag, len(ranks)))


def number_docx(source: Path, manifest_path: Path, output: Path):
    source, output = source.resolve(), output.resolve()
    if source == output or output.exists():
        raise FileExistsError("Use a new output path; the original and existing outputs are preserved")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    formulas = manifest.get("formulas", [])
    if not formulas or manifest.get("formula_count") != len(formulas):
        raise ValueError("An ordered formula inventory with an exact count is required")
    ids = [f.get("formula_id") for f in formulas]
    if any(not v for v in ids) or len(set(ids)) != len(ids) or any(
            f.get("placement") not in {"inline", "display"} for f in formulas):
        raise ValueError("Formula IDs/placements are missing, duplicate or unsupported")
    with ZipFile(source) as archive:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(archive.read("word/document.xml"), parser)
        if root.xpath(".//m:oMath | .//m:oMathPara", namespaces=NS):
            raise ValueError("This helper requires converted native MathType, not OMML or mixed backends")
        objects = root.xpath(".//o:OLEObject[@ProgID='Equation.DSMT4']", namespaces=NS)
        if len(objects) != len(formulas):
            raise ValueError("MathType tag count differs from the ordered formula inventory")
        styles = etree.fromstring(archive.read("word/styles.xml"), parser) if "word/styles.xml" in archive.namelist() else None
        settings = etree.fromstring(archive.read("word/settings.xml"), parser) if "word/settings.xml" in archive.namelist() else None
        gutter = settings.find("w:gutterAtTop", NS) if settings is not None else None
        gutter_at_top = gutter is not None and gutter.get(tag("w:val"), "true") not in {"false", "0", "off"}
        body, count = root.find("w:body", NS), 0
        for formula, equation in zip(formulas, objects):
            if formula["placement"] == "display":
                paragraph = equation.xpath("ancestor::w:p[1]", namespaces=NS)[0]
                width = section_width(paragraph, body, gutter_at_top=gutter_at_top)
                count += 1
                format_paragraph(paragraph, equation, width, count, styles)
        if count == 0:
            raise ValueError("No display equation requires numbering")
        payload = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, "x") as final:
            for info in archive.infolist():
                final.writestr(info, payload if info.filename == "word/document.xml" else archive.read(info.filename))
    return {"status": "layout_applied_review_pending", "display_equations_numbered": count,
            "inline_equations_unchanged": len(formulas) - count,
            "native_parts_and_previews": "copied_byte_for_byte",
            "requires": ["current-file native evidence", "Word render and equation-number checks", "cross-reference checks", "save-close-reopen"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(number_docx(args.docx, args.manifest, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
