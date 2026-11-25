"""Exercise figure output, renderer measurements and bounded Word replacement."""
from hashlib import sha256
from pathlib import Path
import csv
import json
import re
import struct
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm
from PIL import Image

SKILL = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SKILL/"templates"), str(SKILL/"scripts")]

from audit_figure_layout import audit_layout
from inspect_emf_text import inspect_emf
from replace_docx_figures import replace_figures
from research_figure_composition import blank_result_slots, new_figure, save
from research_figure_evidence import demo_spec, generate
from research_workflow_replay import calculation, workflow
from validate_figure_manifest import validate_publication_encoding


class FigureCraftTests(unittest.TestCase):
    def test_production_release_branches_and_measured_exports(self):
        spec = {
            "unit": "kW", "reference": .1, "canvas": {"width_mm": 161, "font_pt": 9},
            "provenance": {"kind": "synthetic fixture", "source": "unit test"},
            "cases": [
                {"name": "Stable", "old": [-.5,-.3], "added": [-.55,-.4], "released_upper": -.1},
                {"name": "Open", "old": [-.2,.3], "added": [0,.4], "released_upper": .05},
                {"name": "Exceeded", "old": [.01,.05], "added": [.3,.45], "released_upper": .13},
            ],
        }
        with TemporaryDirectory() as temporary:
            path = Path(temporary)/"limits"
            report = generate("release", "project", spec, path, language="en", dpi=200)
            records = report["release_records"]
            self.assertEqual([row["expanded_limit_relation"] for row in records], ["within", "unresolved", "breach"])
            self.assertEqual([row["active"] for row in records], [None, None, "added"])
            self.assertEqual([row["released_within"] for row in records], [True, True, False])
            self.assertTrue(audit_layout(report)["measurement_checks_passed"], audit_layout(report))
            self.assertEqual(report["canvas_mm"][0], 161)
            for fmt, artifact in report["artifacts"].items():
                self.assertEqual(sha256((path.parent/artifact["file"]).read_bytes()).hexdigest(), artifact["sha256"])
            pdf = path.with_suffix(".pdf").read_bytes()
            self.assertIsNone(re.search(rb"/Subtype\s*/Image\b", pdf))
            self.assertIn("Stable", path.with_suffix(".svg").read_text(encoding="utf-8"))
            with Image.open(path.with_suffix(".png")) as png:
                self.assertAlmostEqual(png.width, 161/25.4*200, delta=1)

    def test_production_data_and_interval_states_are_validated_before_export(self):
        spec = demo_spec("sensitivity", "english")
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "Bind production input"):
                generate("sensitivity", "project", spec, root/"unbound", language="en")
            spec["provenance"] = {"kind": "synthetic fixture", "source": "unit test"}
            spec["metrics"][0]["rows"][2]["estimate"] = 1.23
            with self.assertRaisesRegex(ValueError, "identical estimate"):
                generate("sensitivity", "project", spec, root/"inconsistent", language="en")
            self.assertEqual(list(root.iterdir()), [])

    def test_projection_and_empty_slots(self):
        data = calculation({
            "reports": [[0,.8,.1],[.2,.6,.6],[.3,.1,.9]], "weights": [.2,.3,.5],
            "lower": [.25,0,0], "upper": [1,.4,1], "focus_index": 1,
            "provenance": {"kind": "synthetic fixture", "source": "unit test"},
        })
        self.assertAlmostEqual(float(data["proposal"][1]), .39)
        self.assertAlmostEqual(float(data["issued"][0]), .25)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = save(workflow("project", data, language="en", width_mm=166), root/"ops", formats=("svg",))
            self.assertTrue(audit_layout(report)["measurement_checks_passed"], audit_layout(report))
            blank = save(blank_result_slots(), root/"draft", formats=("png",))
            self.assertTrue(audit_layout(blank)["measurement_checks_passed"])
            self.assertEqual([item["result_artist_count"] for item in blank["pending_results"]], [0,0])
            blank["pending_results"][0]["result_artist_count"] = 1
            self.assertFalse(audit_layout(blank)["measurement_checks_passed"])

    def test_direct_view_exception_is_scoped(self):
        figure = {"plot_type": "line", "direct_view": {
            "authority": "customer_template", "requirement": "Template 4.2 requests a load trace",
            "reading_task": "Show the four-hour recovery trajectory against the scheduled steps",
        }}
        errors = []
        validate_publication_encoding(figure,"fig",errors)
        self.assertTrue(errors)
        errors = []
        validate_publication_encoding(figure,"fig",errors,allow_project_direct=True)
        self.assertEqual(errors,[])
        figure["plot_type"] = "pareto_2d"
        validate_publication_encoding(figure,"fig",errors,allow_project_direct=True)
        self.assertTrue(errors)

    def test_missing_glyph_is_rejected_before_export(self):
        fig = new_figure(80, 40, font="DejaVu Serif")
        fig.text(.5, .5, "网", fontfamily="DejaVu Serif")
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "required glyph"):
                save(fig, root/"missing", formats=("png",))
            self.assertEqual(list(root.iterdir()), [])

    def test_emf_glyph_indices_differ_from_unicode(self):
        header = bytearray(88)
        record = bytearray(80)
        eof = struct.pack("<IIIII",14,20,0,0,20)
        struct.pack_into("<II", header, 0, 1, len(header))
        struct.pack_into("<4i", header, 24, 0, 0, 16500, 7000)
        struct.pack_into("<I", header, 40, 0x464D4520)
        struct.pack_into("<II", header, 48, len(header)+len(record)+len(eof), 3)
        struct.pack_into("<II", record, 0, 84, len(record))
        struct.pack_into("<III", record, 44, 2, 76, 0x10)
        report = inspect_emf(bytes(header)+bytes(record)+eof)
        self.assertEqual(report["frame_width_mm"],165)
        self.assertEqual(report["glyph_index_text_records"],1)
        self.assertEqual(report["unicode_wide_text_records"],0)
        with self.assertRaises(ValueError):
            inspect_emf(bytes(header)+bytes(record)+eof[:-1])


class InlineWordFigureTests(unittest.TestCase):
    def test_only_the_selected_picture_is_retargeted(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGB",(40,40),"navy").save(root/"same.png")
            Image.new("RGB",(120,60),"green").save(root/"replacement.png")
            doc = Document()
            doc.add_picture(str(root/"same.png"),width=Cm(3))
            doc.add_paragraph("Figure 1 — shared source")
            formula = doc.add_paragraph()
            math = OxmlElement("m:oMath")
            run = OxmlElement("m:r")
            token = OxmlElement("m:t")
            token.text = "x"
            run.append(token)
            math.append(run)
            formula._p.append(math)
            doc.add_picture(str(root/"same.png"),width=Cm(4))
            doc.add_paragraph("Figure 2 — selected picture")
            doc.save(root/"source.docx")
            before = (root/"source.docx").read_bytes()
            with (root/"mapping.csv").open("w", newline="", encoding="utf-8") as output:
                csv.writer(output).writerows([["caption","file_path","width_cm"],
                    ["Figure 2 — selected picture","replacement.png",5.0]])
            replace_figures(root/"source.docx",root/"mapping.csv",root/"changed.docx")
            self.assertEqual((root/"source.docx").read_bytes(),before)
            changed = Document(root/"changed.docx")
            self.assertEqual([p.text for p in changed.paragraphs], [p.text for p in doc.paragraphs])
            self.assertEqual((changed.inline_shapes[0].width,changed.inline_shapes[0].height),(Cm(3),Cm(3)))
            self.assertEqual((changed.inline_shapes[1].width,changed.inline_shapes[1].height),(Cm(5),Cm(2.5)))
            self.assertEqual([node.text for node in changed.element.iter(qn("m:t"))],["x"])
            with ZipFile(root/"source.docx") as original, ZipFile(root/"changed.docx") as result:
                self.assertEqual([p for p in original.namelist() if original.read(p)!=result.read(p)],
                                 ["word/document.xml","word/_rels/document.xml.rels"])
            with self.assertRaises(FileExistsError):
                replace_figures(root/"source.docx", root/"mapping.csv", root/"changed.docx")
            (root/"mapping.csv").write_text("caption,file_path\nAbsent,replacement.png\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Caption must match exactly one"):
                replace_figures(root/"source.docx",root/"mapping.csv",root/"absent.docx")
            self.assertFalse((root/"absent.docx").exists())


if __name__ == "__main__":
    unittest.main()
