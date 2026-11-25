import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_pptx_evidence as audit


def fixture(path, *, slide_name="slide17", value=21, workbook=b"embedded values", width=9144000, x=0):
    office = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    ns = f'xmlns:p="{audit.P[1:-1]}" xmlns:a="{audit.A[1:-1]}" xmlns:c="{audit.C[1:-1]}" xmlns:r="{office}"'

    def relationship(rid, role, target):
        return (f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'<Relationship Id="{rid}" Type="{office}/{role}" Target="{target}"/></Relationships>')

    with ZipFile(path, "w") as package:
        package.writestr("ppt/presentation.xml",
                         f'<p:presentation {ns}><p:sldIdLst><p:sldId r:id="s"/></p:sldIdLst>'
                         f'<p:sldSz cx="{width}" cy="6858000"/></p:presentation>')
        package.writestr("ppt/_rels/presentation.xml.rels", relationship("s", "slide", f"slides/{slide_name}.xml"))
        package.writestr(f"ppt/slides/{slide_name}.xml",
                         f'<p:sld {ns}><a:off x="{x}" y="0"/><c:chart r:id="ch"/>'
                         '<a:tbl><a:tr><a:tc><a:t>限值</a:t></a:tc></a:tr></a:tbl></p:sld>')
        package.writestr(f"ppt/slides/_rels/{slide_name}.xml.rels", relationship("ch", "chart", "../charts/chart5.xml"))
        package.writestr("ppt/charts/chart5.xml",
                         f'<c:chartSpace {ns}><c:ser><c:val><c:numRef><c:f>Data!B2</c:f><c:numCache>'
                         f'<c:pt idx="0"><c:v>{value}</c:v></c:pt></c:numCache></c:numRef></c:val></c:ser>'
                         '<c:externalData r:id="w"/></c:chartSpace>')
        package.writestr("ppt/charts/_rels/chart5.xml.rels", relationship("w", "package", "../embeddings/data.xlsx"))
        package.writestr("ppt/embeddings/data.xlsx", workbook)


class PresentationEvidenceTests(unittest.TestCase):
    def test_reordered_part_names_and_layout_preserve_data(self):
        with tempfile.TemporaryDirectory() as temp:
            base, changed = [Path(temp) / name for name in ("base.pptx", "changed.pptx")]
            fixture(base)
            fixture(changed, slide_name="slide2", x=2100)
            result = audit.compare(base, changed)
            self.assertEqual(result["status"], "protected_evidence_matches")
            self.assertNotEqual(result["source_sha256"], result["revised_sha256"])

    def test_changed_cached_data_and_workbook_detected_separately(self):
        with tempfile.TemporaryDirectory() as temp:
            base, changed = [Path(temp) / name for name in ("base.pptx", "changed.pptx")]
            fixture(base)
            fixture(changed, value=19, width=11100000)
            result = audit.compare(base, changed)
            self.assertEqual(result["differences"], [
                {"kind": "page_size"}, {"slide": 1, "kind": "protected_content", "fields": ["chart_series"]}])
            fixture(changed, workbook=b"different workbook")
            result = audit.compare(base, changed)
            self.assertEqual(result["differences"][0]["fields"], ["chart_workbooks"])


if __name__ == "__main__":
    unittest.main()
