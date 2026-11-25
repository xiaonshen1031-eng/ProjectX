"""Narrow OOXML preservation and marked-copy regressions."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_word_revision import audit

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
O = "urn:schemas-microsoft-com:office:office"
SEQ = '<w:fldSimple w:instr="SEQ Equation"><w:r><w:t>1</w:t></w:r></w:fldSimple>'
FORMULA = "<m:oMath><m:r><m:t>P</m:t></m:r></m:oMath>"
TABLE = "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>10.5 MW</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"


class WordRevisionTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.baseline = Path(temporary.name) / "baseline.docx"
        self.revised = Path(temporary.name) / "revised.docx"

    def write(self, path, body, *, image=b"original image", embedded=b"original equation"):
        with ZipFile(path, "w") as z:
            z.writestr("word/document.xml", f'<w:document xmlns:w="{W}" xmlns:m="{M}" xmlns:o="{O}"><w:body>{body}</w:body></w:document>')
            z.writestr("word/media/image1.png", image)
            z.writestr("word/embeddings/oleObject1.bin", embedded)

    def test_local_edit_keeps_mixed_paragraph_and_table_data(self):
        original = f"<w:p><w:r><w:t>模型计算量</w:t></w:r>{FORMULA}{SEQ}</w:p>{TABLE}"
        changed = original.replace("模型计算量", "有功输入").replace(
            "<w:tc><w:p>", '<w:tc><w:p><w:pPr><w:keepNext/></w:pPr>')
        self.write(self.baseline, original)
        self.write(self.revised, changed)
        before = self.baseline.read_bytes()
        after = self.revised.read_bytes()
        report = audit(self.baseline, self.revised)
        self.assertEqual(report["structural_status"], "pass")
        self.assertTrue(report["protected_content"]["table_content"]["same"])
        self.assertEqual(before, self.baseline.read_bytes())
        self.assertEqual(after, self.revised.read_bytes())

    def test_same_counts_do_not_hide_math_media_fields_or_value_replacement(self):
        original = f"<w:p>{FORMULA}{SEQ}</w:p>{TABLE}"
        changed = original.replace(">P<", ">Q<").replace(">1<", ">2<").replace("10.5 MW", "9.5 MW")
        self.write(self.baseline, original)
        self.write(self.revised, changed, image=b"replacement", embedded=b"different native payload")
        report = audit(self.baseline, self.revised)
        self.assertEqual(set(report["unexpected_changes"]), {"math", "media", "embeddings", "table_content", "fields"})
        self.assertEqual(audit(self.baseline, self.revised, allow_change=("math",))["structural_status"], "fail")

    def test_changed_bookmark_target_text_counts_even_with_same_id_and_location(self):
        original = '<w:p><w:bookmarkStart w:id="1" w:name="src"/><w:r><w:t>1</w:t></w:r><w:bookmarkEnd w:id="1"/></w:p>'
        self.write(self.baseline, original)
        self.write(self.revised, original.replace(">1<", ">2<"))
        self.assertEqual(audit(self.baseline, self.revised)["unexpected_changes"], ["bookmarks"])

    def test_marked_text_spans_may_split_a_run(self):
        self.write(self.baseline, f"<w:p><w:r><w:t>核算调节量</w:t></w:r>{FORMULA}</w:p>")
        self.write(self.revised, f'<w:p><w:r><w:t>核算</w:t></w:r><w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr>'
                                 f'<w:t>调节量</w:t></w:r>{FORMULA}</w:p>')
        report = audit(self.baseline, self.revised, highlight_color="yellow")
        self.assertEqual(report["structural_status"], "pass")
        self.assertEqual(report["ordinary_highlight_chars"], 3)
        self.assertFalse(report["visual_reviewed"])

    def test_highlighting_rejects_changed_wording_or_a_mark_inside_a_field(self):
        self.write(self.baseline, f"<w:p><w:r><w:t>核算功率</w:t></w:r>{SEQ}</w:p>")
        field_highlight = SEQ.replace("<w:r>", '<w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr>')
        for edit in (f"<w:p><w:r><w:t>核算电量</w:t></w:r>{SEQ}</w:p>",
                     f"<w:p><w:r><w:t>核算功率</w:t></w:r>{field_highlight}</w:p>"):
            with self.subTest(edit=edit):
                self.write(self.revised, edit)
                report = audit(self.baseline, self.revised, highlight_color="yellow")
                self.assertEqual(report["review_copy_unexpected_parts"], ["word/document.xml"])
                self.assertEqual(report["structural_status"], "fail")


if __name__ == "__main__":
    unittest.main()
