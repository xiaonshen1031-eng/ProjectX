"""Observable Word-citation behavior; fixtures never invoke Office or conversion."""
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile
import contextlib
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_word_citations import audit_docx, main

NS='http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def run(text, sup=True, style=None):
    rp=(f'<w:rStyle w:val="{style}"/>' if style else '<w:vertAlign w:val="superscript"/>' if sup else '')
    return f'<w:r><w:rPr>{rp}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'

def field(number=1, target=None, *, simple=False, code_super=True, locked=False, switch='', style=None):
    target=target or f'b_{number}'
    code=f'REF {target} \\h \\* CHARFORMAT {switch}'
    if simple:return f'<w:fldSimple w:instr="{escape(code)}">{run(str(number),style=style)}</w:fldSimple>'
    rp=f'<w:rStyle w:val="{style}"/>' if style else '<w:vertAlign w:val="superscript"/>' if code_super else ''
    lock=' w:fldLock="1"' if locked else ''
    return (f'<w:r><w:fldChar w:fldCharType="begin"{lock}/></w:r>'
        f'<w:r><w:rPr>{rp}</w:rPr><w:instrText xml:space="preserve"> {escape(code)} </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'+run(str(number),style=style)+
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>')

def citation(number=1, **kw):return '<w:p>'+run('[')+field(number,**kw)+run(']')+'</w:p>'

def bibliography(numbers=(1,), heading='参考文献'):
    out='<w:p>'+run(heading,False)+'</w:p>'
    for n in numbers:
        out+=('<w:p>'+run('[',False)+f'<w:bookmarkStart w:id="{n}" w:name="b_{n}"/>'+run(str(n),False)+
            f'<w:bookmarkEnd w:id="{n}"/>'+run('] Author. Verified source.',False)+'</w:p>')
    return out


class WordCitationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'source.docx'

    def document(self, body, *, styles=None, footnotes=None):
        with ZipFile(self.path,'w') as z:
            z.writestr('word/document.xml',f'<w:document xmlns:w="{NS}"><w:body>{body}</w:body></w:document>')
            if styles:z.writestr('word/styles.xml',f'<w:styles xmlns:w="{NS}">{styles}</w:styles>')
            if footnotes:z.writestr('word/footnotes.xml',f'<w:footnotes xmlns:w="{NS}"><w:footnote w:id="1">{footnotes}</w:footnote></w:footnotes>')

    def audit(self, **kw):
        return audit_docx(self.path,require_superscript=True,**kw)

    def codes(self, result):return [x['code'] for x in result['errors']]

    def test_range_endpoints_cover_middle_references_without_equal_counts(self):
        group='<w:p>'+run('[')+field(1)+run('–')+field(3)+run(']')+'</w:p>'
        self.document(group+bibliography((1,2,3)))
        result=self.audit(require_all_cited=True)
        self.assertEqual(result['structural_status'],'pass')
        self.assertEqual((result['citation_groups'],result['citation_REF_fields'],result['bibliography_entries']),(1,2,3))
        self.assertEqual(result['covered_reference_numbers'],[1,2,3])
        self.assertFalse(result['word_update_verified'])

    def test_hand_typed_superscript_number_cannot_pass_as_cross_reference(self):
        self.document('<w:p>'+run('[1]')+'</w:p>'+bibliography())
        self.assertIn('unlinked_superscript_citation',self.codes(self.audit()))

    def test_baseline_brackets_or_dash_are_rejected(self):
        for punctuation in ['bracket','dash']:
            with self.subTest(punctuation=punctuation):
                self.document('<w:p>'+run('[',punctuation!='bracket')+field(1)+run('–',punctuation!='dash')+field(2)+run(']')+'</w:p>'+bibliography((1,2)))
                self.assertIn('citation_not_fully_superscript',self.codes(self.audit()))

    def test_simple_and_hyperlink_wrapped_fields_remain_live(self):
        linked='<w:p>'+run('[')+'<w:hyperlink>'+field(1,simple=True)+'</w:hyperlink>'+run(']')+'</w:p>'
        self.document(linked+bibliography())
        self.assertEqual(self.audit()['structural_status'],'pass')

    def test_nested_complex_field_keeps_the_inner_REF_identity(self):
        outer=('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText>HYPERLINK target</w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'+field(1)+'<w:r><w:fldChar w:fldCharType="end"/></w:r>')
        self.document('<w:p>'+run('[')+outer+run(']')+'</w:p>'+bibliography())
        self.assertEqual(self.audit()['structural_status'],'pass')

    def test_inherited_character_style_is_resolved(self):
        styles=('<w:style w:type="character" w:styleId="Base"><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="Cite"><w:basedOn w:val="Base"/></w:style>')
        body='<w:p>'+run('[',style='Cite')+field(1,style='Cite')+run(']',style='Cite')+'</w:p>'
        self.document(body+bibliography(),styles=styles)
        self.assertEqual(self.audit()['structural_status'],'pass')

    def test_missing_target_and_stale_cache_are_distinct_failures(self):
        self.document(citation(1,target='absent')+bibliography())
        self.assertIn('missing_or_duplicate_target_bookmark',self.codes(self.audit()))
        self.document(citation(2,target='b_1')+bibliography((1,2)))
        self.assertIn('stale_REF_cache',self.codes(self.audit()))

    def test_full_entry_bookmark_does_not_validate_a_numeric_only_cache(self):
        entry=('<w:p><w:bookmarkStart w:id="1" w:name="b_1"/>'+run('[1] Full reference',False)+'<w:bookmarkEnd w:id="1"/></w:p>')
        self.document(citation()+'<w:p>'+run('参考文献',False)+'</w:p>'+entry)
        self.assertIn('stale_REF_cache',self.codes(self.audit()))

    def test_CHARFORMAT_and_field_lock_cannot_hide_behind_a_good_cache(self):
        self.document(citation(code_super=False)+bibliography())
        self.assertIn('CHARFORMAT_instruction_not_superscript',self.codes(self.audit()))
        self.document(citation(locked=True)+bibliography())
        self.assertIn('locked_citation_field',self.codes(self.audit()))

    def test_EMBED_field_is_counted_separately_and_never_updated(self):
        embed='<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText>EMBED Equation.DSMT4</w:instrText></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        self.document(embed+citation()+bibliography());before=self.path.read_bytes()
        result=self.audit()
        self.assertEqual(result['field_counts'],{'EMBED':1,'REF':1})
        self.assertEqual(result['citation_REF_fields'],1)
        self.assertEqual(self.path.read_bytes(),before)

    def test_tables_and_footnotes_are_checked(self):
        self.document('<w:tbl><w:tr><w:tc>'+citation()+'</w:tc></w:tr></w:tbl>'+bibliography(),footnotes=citation())
        result=self.audit()
        self.assertEqual(result['structural_status'],'pass');self.assertEqual(result['citation_groups'],2)
        self.assertIn('word/footnotes.xml',result['checked_parts'])

    def test_deleted_citation_is_not_part_of_the_final_visible_view(self):
        self.document('<w:p><w:del>'+run('[99]')+'</w:del></w:p>'+citation()+bibliography())
        self.assertEqual(self.audit()['citation_groups'],1)

    def test_numbered_body_opening_is_not_a_bibliography_entry(self):
        self.document('<w:p>'+run('[1] is discussed here.',False)+'</w:p>'+bibliography())
        result=self.audit();self.assertEqual(result['citation_groups'],0)
        self.assertEqual(result['numeric_bracket_candidates'],1)
        self.assertTrue(result['needs_review'])

    def test_without_bibliography_checks_a_clean_report_and_preserves_equation_fields(self):
        eq='<w:p><w:fldSimple w:instr="SEQ Equation"><w:r><w:t>1</w:t></w:r></w:fldSimple></w:p>'
        self.document(eq)
        result=audit_docx(self.path,without_bibliography=True)
        self.assertEqual(result['structural_status'],'pass')
        self.assertEqual(result['field_counts'],{'SEQ':1})
        self.assertFalse(result['word_update_verified'])
        self.document(eq+citation()+bibliography())
        self.assertIn('numeric_citation_remains',self.codes(audit_docx(self.path,without_bibliography=True)))
        self.assertIn('unexpected_bibliography_heading',self.codes(audit_docx(self.path,without_bibliography=True)))

    def test_plain_mathematical_interval_is_pending_not_silently_accepted(self):
        self.document('<w:p>'+run('The feasible interval is [0,1].',False)+'</w:p>'+bibliography())
        result=audit_docx(self.path)
        self.assertEqual(result['structural_status'],'needs_review')
        self.assertEqual(result['covered_reference_numbers'],[])
        self.assertNotIn('citation_not_fully_superscript',self.codes(self.audit()))

    def test_baseline_literal_number_cannot_complete_a_live_citation_range(self):
        self.document('<w:p>'+run('[',False)+field(1)+run('–3]',False)+'</w:p>'+bibliography((1,2,3)))
        self.assertIn('unlinked_citation_token',self.codes(audit_docx(self.path)))

    def test_missing_middle_of_range_and_uncited_entry_are_reported(self):
        self.document('<w:p>'+run('[')+field(1)+run('-')+field(3)+run(']')+'</w:p>'+bibliography((1,3)))
        self.assertIn('cited_numbers_missing_from_bibliography',self.codes(self.audit()))
        self.document(citation()+bibliography((1,2)))
        self.assertIn('uncited_bibliography_entries',self.codes(self.audit(require_all_cited=True)))

    def test_numbering_switch_requires_Word_instead_of_a_false_pass(self):
        for switch in ['\\n','\\N']:
            with self.subTest(switch=switch):
                self.document(citation(switch=switch)+bibliography())
                result=self.audit();self.assertEqual(result['structural_status'],'needs_review')
                self.assertTrue(any(x['code']=='paragraph_number_REF_needs_Word_evaluation' for x in result['needs_review']))

    def test_resume_heading_returns_to_main_content_after_references(self):
        self.document(citation()+bibliography()+'<w:p>'+run('Appendix',False)+'</w:p>'+citation())
        result=self.audit(resume_headings=['Appendix'])
        self.assertEqual(result['citation_groups'],2)

    def test_malformed_fields_and_unknown_bibliography_boundary_fail(self):
        self.document('<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r></w:p>'+bibliography())
        self.assertIn('malformed_story',self.codes(self.audit()))
        self.document(citation())
        self.assertIn('bibliography_boundary_unresolved',self.codes(self.audit()))

    def test_cli_cannot_overwrite_its_source_or_a_non_JSON_path(self):
        self.document(citation()+bibliography());before=self.path.read_bytes()
        with patch.object(sys,'argv',['audit_word_citations.py',str(self.path),'--json-out',str(self.path)]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:main()
        self.assertEqual(exc.exception.code,2);self.assertEqual(self.path.read_bytes(),before)

    def test_cli_creates_only_the_requested_report_and_preserves_input(self):
        self.document(citation()+bibliography());before=self.path.read_bytes();out=Path(self.tmp.name)/'review'/'citations.json'
        with patch.object(sys,'argv',['audit_word_citations.py',str(self.path),'--require-superscript','--json-out',str(out)]):
            with contextlib.redirect_stdout(io.StringIO()):status=main()
        self.assertEqual(status,0);self.assertEqual(self.path.read_bytes(),before)
        report=json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(report['structural_status'],'pass');self.assertFalse(report['word_update_verified'])

    def test_paragraph_style_inheritance_and_non_superscript_profiles(self):
        styles=('<w:style w:type="paragraph" w:styleId="Base"><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="CitePara"><w:basedOn w:val="Base"/></w:style>')
        body='<w:p><w:pPr><w:pStyle w:val="CitePara"/></w:pPr>'+run('[',False)+field(1)+run(']',False)+'</w:p>'
        self.document(body+bibliography(),styles=styles)
        self.assertEqual(self.audit()['structural_status'],'pass')
        self.document('<w:p>'+run('[',False)+field(1,code_super=False)+run(']',False)+'</w:p>'+bibliography())
        self.assertEqual(audit_docx(self.path)['structural_status'],'pass')

    def test_multi_hyphen_range_is_not_accepted_as_just_its_first_endpoint(self):
        self.document('<w:p>'+run('[')+field(1)+run('-')+field(2)+run('-')+field(3)+run(']')+'</w:p>'+bibliography((1,2,3)))
        self.assertIn('invalid_citation_range',self.codes(self.audit()))

    def test_invalid_package_has_a_bounded_cli_error_and_preserves_source(self):
        self.path.write_bytes(b'legacy or invalid Word content');before=self.path.read_bytes()
        with patch.object(sys,'argv',['audit_word_citations.py',str(self.path)]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:main()
        self.assertEqual(exc.exception.code,2);self.assertEqual(self.path.read_bytes(),before)


if __name__=='__main__':unittest.main()
