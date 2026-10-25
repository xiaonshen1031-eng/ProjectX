"""Final-language coverage of actual DOCX structure across all branches."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_writing_quality as writing


class DocxLanguageStructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "source.docx"

    def tearDown(self):
        self.temp.cleanup()

    def save(self, paragraphs):
        document = Document()
        for text in paragraphs:
            document.add_paragraph(text)
        document.save(self.path)

    def all_results(self):
        return [(branch, writing.inspect_writing(self.path, manuscript_mode=branch))
                for branch in ("project",)]

    def test_appendix_after_bibliography_is_screened_and_reference_is_excluded(self):
        for reference, appendix in [("References", "Appendix A. Technical analysis"),
                                    ("参考文献：", "附录A 技术分析")]:
            self.save(["3 Results", "At H24, baseline MAE is lower than fusion MAE.", reference,
                       '1. Paper titled "Evidence chain" and the use of valuable insights.',
                       appendix, "The framework provides valuable insights into prediction."])
            for branch, result in self.all_results():
                with self.subTest(branch=branch, appendix=appendix):
                    self.assertTrue(any(c["paragraph"] == 6 and c["type"] == "ai_formulaic_prose"
                                        for c in result["editorial_candidates"]))
                    self.assertFalse(any(c.get("paragraph") == 4 for c in result["editorial_candidates"]))

    def test_inline_abstract_is_body_even_if_a_heading_style_was_applied(self):
        for text in ["摘要：本方法为电网运行提供了坚实支撑，具有重要意义。",
                     "Abstract: The framework provides valuable insights into prediction."]:
            document = Document()
            paragraph = document.add_paragraph(text)
            paragraph.style = "Heading 1"
            document.save(self.path)
            for branch, result in self.all_results():
                with self.subTest(branch=branch, text=text):
                    self.assertTrue(any(c["type"] == "ai_formulaic_prose" and c["section"] == "abstract"
                                        for c in result["editorial_candidates"]))

    def test_pure_abstract_heading_and_concrete_summary_are_preserved(self):
        for heading, text in [("Abstract", "The residual-weighted forecast reduces point error across the evaluated charging-demand conditions."),
                              ("摘要", "容量约束限定各时段的供能上限，能量平衡将分配结果与总充电需求关联。")]:
            self.save([heading, text])
            self.assertTrue(writing.load_paragraphs(self.path)[0]["is_heading"])
            self.assertFalse(writing.load_paragraphs(self.path)[1]["is_heading"])
            for branch, result in self.all_results():
                with self.subTest(branch=branch, heading=heading):
                    self.assertEqual(result["editorial_candidate_count"], 0)

    def test_bibliography_entries_alone_do_not_become_language_candidates(self):
        self.save(["3 Results", "At H24, baseline MAE is lower than fusion MAE.", "References",
                   "1. The framework provides valuable insights into prediction."])
        for branch, result in self.all_results():
            with self.subTest(branch=branch):
                self.assertEqual(result["editorial_candidate_count"], 0)

    def test_appendix_table_and_note_are_also_screened(self):
        document = Document()
        document.add_paragraph("References")
        document.add_paragraph("1. Technical model specification.")
        document.add_heading("Appendix A. Technical data", 1)
        document.add_table(rows=1, cols=1).cell(0, 0).text = "首先构建证据链。"
        document.add_paragraph("Notes: The framework cannot support operational decisions.")
        document.save(self.path)
        for branch, result in self.all_results():
            with self.subTest(branch=branch):
                self.assertTrue(any(c.get("table") == 1 for c in result["editorial_candidates"]))
                self.assertTrue(any(c["type"] == "defensive_prose" for c in result["editorial_candidates"]))


if __name__ == "__main__":
    unittest.main()
