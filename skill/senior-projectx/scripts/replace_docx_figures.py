#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def replace_figures(docx_path: Path, mapping_csv: Path, output_path: Path) -> None:
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        raise RuntimeError("win32com is required for Word figure replacement on Windows.") from exc

    rows = load_rows(mapping_csv)
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(str(docx_path.resolve()))
    try:
        for row in rows:
            caption = row["caption"].strip()
            file_path = Path(row["file_path"]).expanduser().resolve()
            width_cm = float(row.get("width_cm") or 0)
            find = word.Selection.Find
            find.ClearFormatting()
            find.Text = caption
            find.Forward = True
            find.Wrap = 1
            found = find.Execute()
            if not found:
                continue

            caption_start = word.Selection.Range.Start
            inline_shapes = list(doc.InlineShapes)
            candidate = None
            best_distance = None
            for shape in inline_shapes:
                distance = caption_start - shape.Range.Start
                if distance >= 0 and (best_distance is None or distance < best_distance):
                    best_distance = distance
                    candidate = shape
            if candidate is not None:
                candidate.Delete()

            rng = doc.Range(caption_start, caption_start)
            rng.InsertParagraphBefore()
            rng = doc.Range(caption_start, caption_start)
            shape = doc.InlineShapes.AddPicture(str(file_path), False, True, rng)
            if width_cm > 0:
                shape.Width = word.CentimetersToPoints(width_cm)
        doc.SaveAs(str(output_path.resolve()))
    finally:
        doc.Close(False)
        word.Quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Replace result figures in a DOCX by matching caption text.")
    parser.add_argument("docx_path")
    parser.add_argument("mapping_csv")
    parser.add_argument("output_path")
    args = parser.parse_args()
    replace_figures(Path(args.docx_path), Path(args.mapping_csv), Path(args.output_path))


if __name__ == "__main__":
    main()
