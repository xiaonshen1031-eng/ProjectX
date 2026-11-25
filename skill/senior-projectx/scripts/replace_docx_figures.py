#!/usr/bin/env python3
"""Replace exact caption-adjacent inline pictures in a new DOCX copy."""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from io import BytesIO
import math
from pathlib import Path
import posixpath
from shutil import copyfileobj
from tempfile import TemporaryFile
from zipfile import ZipFile

from lxml import etree
from PIL import Image

from inspect_emf_text import inspect_emf


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
PIC = "{http://schemas.openxmlformats.org/drawingml/2006/picture}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"
IMAGE_REL = R[1:-1] + "/image"
CONTENT_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                 "tif": "image/tiff", "tiff": "image/tiff", "emf": "image/x-emf"}
IMAGE_FORMATS = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF", "tiff": "TIFF"}
DOCUMENT = "word/document.xml"
RELATIONSHIPS = "word/_rels/document.xml.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"
EMU_PER_CM = 360_000
LOCAL_DPI = "{http://schemas.microsoft.com/office/drawing/2010/main}useLocalDpi"


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    captions = [(row.get("caption") or "").strip() for row in rows]
    if not rows or not all(captions) or len(set(captions)) != len(rows):
        raise ValueError("Supply one row per unique, complete caption")
    if any(not (row.get("file_path") or "").strip() for row in rows):
        raise ValueError("Each replacement needs a file_path")
    return rows


def visible_text(paragraph):
    return "".join(text.text or "" for text in paragraph.iter(W + "t")).strip()


def picture_before_caption(body, caption):
    matches = [p for p in body.iter(W + "p") if visible_text(p) == caption]
    if len(matches) != 1 or matches[0].getparent() is not body:
        raise ValueError(f"Caption must match exactly one top-level paragraph: {caption}")
    previous = matches[0].getprevious()
    if previous is None or previous.tag != W + "p" or visible_text(previous):
        raise ValueError(f"Expected the inline image paragraph immediately before: {caption}")
    runs = previous.findall(W + "r")
    if any(el.tag not in {W + "pPr", W + "r", W + "bookmarkStart", W + "bookmarkEnd"} for el in previous):
        raise ValueError(f"Caption-adjacent paragraph contains other objects: {caption}")
    contents = [el for run in runs for el in run if el.tag != W + "rPr"]
    if len(contents) != 1 or contents[0].tag != W + "drawing":
        raise ValueError(f"Caption-adjacent paragraph needs exactly one drawing: {caption}")
    inline = contents[0].find(WP + "inline")
    picture = None if inline is None else inline.find(f"{A}graphic/{A}graphicData/{PIC}pic")
    if picture is None:
        raise ValueError(f"Expected an inline picture rather than grouped/floating objects: {caption}")
    fill = picture.find(PIC + "blipFill")
    blip = None if fill is None else fill.find(A + "blip")
    crop = None if fill is None else fill.find(A + "srcRect")
    transform = picture.find(f"{PIC}spPr/{A}xfrm")
    if (blip is None or not blip.get(R + "embed") or blip.get(R + "link") is not None
            or any(node.tag not in {A + "extLst", A + "ext", LOCAL_DPI} for node in blip.iterdescendants())
            or (crop is not None and any(int(value) for value in crop.attrib.values()))
            or transform is None or any(value not in {"0", "false"} for value in transform.attrib.values())):
        raise ValueError(f"Use the native editor for a linked, cropped, rotated, alternate-format or transformed image: {caption}")
    extent = inline.find(WP + "extent")
    shape_extent = transform.find(A + "ext")
    if extent is None or shape_extent is None:
        raise ValueError(f"Missing drawing geometry: {caption}")
    return blip, extent, shape_extent


def image_payload(path):
    suffix = path.suffix.lower().removeprefix(".")
    if suffix not in CONTENT_TYPES:
        raise ValueError(f"Choose PNG, JPEG, TIFF or EMF for this inline replacement: {path.name}")
    payload = path.read_bytes()
    if suffix == "emf":
        left, top, right, bottom = inspect_emf(payload)["frame_0_01_mm"]
        width, height = right-left, bottom-top
    else:
        with Image.open(BytesIO(payload)) as image:
            if image.format != IMAGE_FORMATS[suffix] or getattr(image, "n_frames", 1) != 1:
                raise ValueError(f"Image type or frame count conflicts with delivery format: {path.name}")
            if image.getexif().get(274, 1) != 1:
                raise ValueError(f"Export an image with its orientation applied: {path.name}")
            width, height = image.size
            image.load()
    if width <= 0 or height <= 0:
        raise ValueError(f"Expected positive image dimensions: {path.name}")
    return suffix, payload, width, height


def xml(data):
    return etree.fromstring(data, parser=etree.XMLParser(resolve_entities=False, no_network=True))


def replace_figures(docx_path: Path, mapping_csv: Path, output_path: Path) -> None:
    rows = load_rows(mapping_csv)
    if docx_path.resolve() == output_path.resolve() or output_path.exists():
        raise FileExistsError("Choose a new DOCX output filename")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(docx_path) as original, TemporaryFile(dir=output_path.parent) as staged:
        document = xml(original.read(DOCUMENT))
        body = document.find(W + "body")
        if body is None:
            raise ValueError("DOCX main document body is missing")
        rels = xml(original.read(RELATIONSHIPS))
        types = xml(original.read(CONTENT_TYPES_PART))
        relationships = {rel.attrib["Id"]: rel for rel in rels}
        extensions = {node.attrib["Extension"].lower(): node.attrib["ContentType"]
                      for node in types.findall(CT + "Default")}
        original_names = set(original.namelist())
        new_data = {}
        new_links = {}
        figures = set()
        next_id = 1
        for row in rows:
            caption = row["caption"].strip()
            blip, extent, shape_extent = picture_before_caption(body, caption)
            if blip in figures:
                raise ValueError(f"Picture has already been selected by another caption: {caption}")
            figures.add(blip)
            current = relationships.get(blip.attrib[R + "embed"])
            if (current is None or current.get("Type") != IMAGE_REL or current.get("TargetMode") == "External"
                    or posixpath.normpath(posixpath.join("word", current.get("Target", ""))).lstrip("/") not in original_names):
                raise ValueError(f"Image relationship is not a supported embedded picture: {caption}")

            path = mapping_csv.parent / Path(row["file_path"].strip()).expanduser()
            suffix, payload, intrinsic_width, intrinsic_height = image_payload(path)
            width_setting = (row.get("width_cm") or "").strip()
            width = int(extent.attrib["cx"])
            if width_setting:
                value = float(width_setting)
                if not math.isfinite(value) or value <= 0:
                    raise ValueError(f"width_cm must be positive: {caption}")
                width = round(EMU_PER_CM * value)
            height = round(width * intrinsic_height / intrinsic_width)
            if min(width, height) <= 0:
                raise ValueError(f"Invalid placed dimensions: {caption}")

            part = "word/media/projectx-" + sha256(payload).hexdigest() + "." + suffix
            if part in original_names and original.read(part) != payload:
                raise ValueError(f"Image part name collision: {part}")
            if part not in new_links:
                while f"rId{next_id}" in relationships:
                    next_id += 1
                relationship_id = f"rId{next_id}"
                rel = etree.SubElement(rels, REL + "Relationship", Id=relationship_id,
                                       Type=IMAGE_REL, Target=part.removeprefix("word/"))
                relationships[relationship_id] = rel
                new_links[part] = relationship_id
                if part not in original_names:
                    new_data[part] = payload
            if suffix not in extensions:
                etree.SubElement(types, CT + "Default", Extension=suffix, ContentType=CONTENT_TYPES[suffix])
                extensions[suffix] = CONTENT_TYPES[suffix]
            elif extensions[suffix] != CONTENT_TYPES[suffix] and (suffix, extensions[suffix]) != ("emf", "image/emf"):
                raise ValueError(f"Existing content type disagrees with the new {suffix} part")
            blip.set(R + "embed", new_links[part])
            for size in (extent, shape_extent):
                size.set("cx", str(width))
                size.set("cy", str(height))

        for name, root in ((DOCUMENT, document), (RELATIONSHIPS, rels), (CONTENT_TYPES_PART, types)):
            new_data[name] = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with ZipFile(staged, "w") as result:
            for info in original.infolist():
                data = new_data.pop(info.filename) if info.filename in new_data else original.read(info)
                result.writestr(info, data)
            for name, data in new_data.items():
                result.writestr(name, data)
        staged.seek(0)
        with output_path.open("xb") as stream:
            try:
                copyfileobj(staged, stream)
            except OSError:
                stream.close()
                output_path.unlink()
                raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx_path", type=Path)
    parser.add_argument("mapping_csv", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()
    try:
        replace_figures(args.docx_path, args.mapping_csv, args.output_path)
    except (KeyError, OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
