#!/usr/bin/env python3
"""Check cached numeric citations or a requested no-bibliography Word profile."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
import json
import io
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
GROUP = re.compile(r'[\[［]\s*\d+(?:\s*[,，;；–—\-]\s*\d+)*\s*[\]］]')
LABEL = re.compile(r'^\s*[\[［]\s*(\d+)\s*[\]］]')
REF = re.compile(r'^\s*REF\s+(?:"([^"]+)"|(\S+))', re.I)
JOINERS = '\u2060\ufeff\u200b'


def heading(text):
    return re.sub(r'\s+', '', text).strip(':：').casefold()


def clean(text):
    return ''.join(c for c in text if c not in JOINERS)


def true(value):
    return str(value).lower() in {'1', 'true', 'on'}


class Formatting:
    def __init__(self, styles):
        self.styles = {} if styles is None else {s.get(W+'styleId'): s for s in styles.findall(W+'style')}
        default = None if styles is None else styles.find(f'{W}docDefaults/{W}rPrDefault/{W}rPr/{W}vertAlign')
        self.default = default.get(W+'val') if default is not None else 'baseline'
        self.par_default = next((k for k,s in self.styles.items() if s.get(W+'type')=='paragraph' and true(s.get(W+'default'))), 'Normal')

    def style_value(self, name):
        seen = set()
        while name and name not in seen:
            seen.add(name); style = self.styles.get(name)
            if style is None: break
            value = style.find(f'{W}rPr/{W}vertAlign')
            if value is not None: return value.get(W+'val')
            base = style.find(W+'basedOn'); name = base.get(W+'val') if base is not None else None
        return None

    def superscript(self, run, paragraph):
        if run is not None:
            direct = run.find(f'{W}rPr/{W}vertAlign')
            if direct is not None: return direct.get(W+'val') == 'superscript'
            style = run.find(f'{W}rPr/{W}rStyle')
            value = self.style_value(style.get(W+'val')) if style is not None else None
            if value is not None: return value == 'superscript'
        style = paragraph.find(f'{W}pPr/{W}pStyle') if paragraph is not None else None
        value = self.style_value(style.get(W+'val') if style is not None else self.par_default)
        return (value or self.default) == 'superscript'


@dataclass
class WordField:
    code: str = ''
    result: str = ''
    state: str = 'code'
    simple: bool = False
    locked: bool = False
    instruction_formats: list = field(default_factory=list)


class Story:
    def __init__(self, part, root, formatting):
        self.part, self.formatting = part, formatting
        self.paragraphs, self.glyphs, self.fields, self.bookmarks, self.errors = [], [], [], [], []
        self.stack, self.open_bookmarks = [], {}
        self.visit(root)
        if self.stack: self.errors.append('Unclosed complex field')
        if self.open_bookmarks: self.errors.append('Unclosed bookmark')

    def add_field(self, **kwargs):
        self.fields.append(WordField(**kwargs)); self.stack.append(len(self.fields)-1)
        return len(self.fields)-1

    def visit(self, node, paragraph=None, run=None):
        tag = node.tag
        if tag in {W+'del', W+'moveFrom'}: return
        if tag == W+'p':
            paragraph = len(self.paragraphs)
            self.paragraphs.append({'node':node, 'glyphs':[], 'text':''})
        if tag == W+'r': run = node
        pnode = self.paragraphs[paragraph]['node'] if paragraph is not None else None
        if tag == W+'bookmarkStart':
            key = node.get(W+'id')
            if key in self.open_bookmarks: self.errors.append('Duplicate open bookmark ID')
            self.open_bookmarks[key] = {'name':node.get(W+'name'), 'start':len(self.glyphs), 'paragraph':paragraph}
        elif tag == W+'bookmarkEnd':
            item = self.open_bookmarks.pop(node.get(W+'id'), None)
            if item is None: self.errors.append('Unmatched bookmark end')
            else: item['end']=len(self.glyphs); self.bookmarks.append(item)
        elif tag == W+'fldSimple':
            key = self.add_field(code=node.get(W+'instr',''), state='result', simple=True, locked=true(node.get(W+'fldLock')))
            for child in node: self.visit(child, paragraph, run)
            if not self.stack or self.stack[-1] != key: self.errors.append('Malformed nested simple field')
            else: self.stack.pop()
            return
        elif tag == W+'fldChar':
            kind = node.get(W+'fldCharType')
            if kind == 'begin': self.add_field(locked=true(node.get(W+'fldLock')))
            elif kind in {'separate','end'}:
                if not self.stack or self.fields[self.stack[-1]].simple: self.errors.append('Unmatched complex field marker')
                elif kind == 'separate': self.fields[self.stack[-1]].state='result'
                else: self.stack.pop()
        elif tag == W+'instrText' and self.stack:
            active = self.fields[self.stack[-1]]
            if active.state == 'code':
                active.code += node.text or ''
                active.instruction_formats.append((node.text or '', self.formatting.superscript(run,pnode)))
        elif tag in {W+'t',W+'tab',W+'br'}:
            value = (node.text or '') if tag==W+'t' else '\t' if tag==W+'tab' else '\n'
            for key in self.stack:
                if self.fields[key].state=='result': self.fields[key].result += value
            if paragraph is not None and all(self.fields[k].state=='result' for k in self.stack):
                for char in value:
                    glyph = {'char':char, 'paragraph':paragraph, 'fields':tuple(self.stack), 'superscript':self.formatting.superscript(run,pnode)}
                    self.paragraphs[paragraph]['glyphs'].append(len(self.glyphs)); self.glyphs.append(glyph)
                    self.paragraphs[paragraph]['text'] += char
        for child in node: self.visit(child, paragraph, run)


def audit_docx(path, *, bib_headings=None, resume_headings=None, require_superscript=False,
               require_all_cited=False, without_bibliography=False):
    path = Path(path).resolve(); data = path.read_bytes()
    with ZipFile(io.BytesIO(data)) as package:
        if 'word/document.xml' not in package.namelist():
            raise ValueError('The Word package lacks word/document.xml.')
        styles = ET.fromstring(package.read('word/styles.xml')) if 'word/styles.xml' in package.namelist() else None
        fmt = Formatting(styles)
        names = [p for p in ['word/document.xml','word/footnotes.xml','word/endnotes.xml'] if p in package.namelist()]
        stories = [Story(p,ET.fromstring(package.read(p)),fmt) for p in names]
    main = stories[0]; errors=[]; pending=[]; groups=[]; covered=set(); bracket_candidates=0
    def finding(bucket, code, **detail): bucket.append({'code':code, **detail})
    for story in stories:
        for message in story.errors: finding(errors,'malformed_story',part=story.part,message=message)
    starts = [i for i,p in enumerate(main.paragraphs) if heading(clean(p['text'])) in {heading(x) for x in (bib_headings or ['References','参考文献'])}]
    if without_bibliography:
        if starts:
            finding(errors,'unexpected_bibliography_heading',matches=starts)
        start,end=len(main.paragraphs),len(main.paragraphs)
    elif len(starts)!=1:
        finding(errors,'bibliography_boundary_unresolved',matches=starts)
        start,end=len(main.paragraphs),len(main.paragraphs)
    else:
        start=starts[0]+1
        end=next((i for i in range(start,len(main.paragraphs)) if heading(clean(main.paragraphs[i]['text'])) in {heading(x) for x in (resume_headings or [])}),len(main.paragraphs))
    entries={}; entry_by_paragraph={}; current=None
    for i in range(start,end):
        match=LABEL.match(clean(main.paragraphs[i]['text']))
        if match:
            current=int(match[1])
            if current in entries: finding(errors,'duplicate_bibliography_number',number=current)
            entries[current]=i
        if current is not None: entry_by_paragraph[i]=current
    if not entries and not without_bibliography:
        finding(pending,'bibliography_numbers_not_resolved',message='Literal or SEQ square-bracket labels were not found; automatic list numbering needs Word evaluation.')
    bookmarks={}
    for story in stories:
        for item in story.bookmarks: bookmarks.setdefault(item['name'],[]).append((story,item))
        for word_field in story.fields:
            if REF.match(word_field.code) and re.search(r'Error!|Reference source not found|错误[!！]|未找到引用',word_field.result,re.I):
                finding(errors,'broken_REF_result',part=story.part,instruction=word_field.code,result=word_field.result)
    used_fields=set()
    for story in stories:
        for pi,paragraph in enumerate(story.paragraphs):
            if story is main and len(starts)==1 and not without_bibliography and starts[0]<=pi<end: continue
            glyphs=[story.glyphs[i] for i in paragraph['glyphs'] if story.glyphs[i]['char'] not in JOINERS]
            text=''.join(g['char'] for g in glyphs)
            for match in GROUP.finditer(text):
                location={'part':story.part,'paragraph_index':pi,'citation':match[0]}
                bracket_candidates += 1
                segment=[g for g in glyphs[match.start():match.end()] if not g['char'].isspace()]
                linked=any(REF.match(story.fields[key].code) for g in segment for key in g['fields'])
                fully_superscript=all(g['superscript'] for g in segment)
                if not (linked or fully_superscript):
                    finding(pending,'literal_numeric_candidate',**location,
                            message='Confirm whether a literal interval, algorithm label or citation is intended.')
                    continue
                if (match[0][0],match[0][-1]) not in {('[',']'),('［','］')}:
                    finding(errors,'mismatched_citation_brackets',**location)
                if without_bibliography:
                    finding(errors,'numeric_citation_remains',**location)
                targets=[]
                if require_superscript and not fully_superscript:
                    finding(errors,'citation_not_fully_superscript',**location)
                for number_match in re.finditer(r'\d+',match[0]):
                    number=int(number_match[0])
                    token=glyphs[match.start()+number_match.start():match.start()+number_match.end()]
                    ids=[]
                    for glyph in token:
                        ids.append(next((key for key in reversed(glyph['fields']) if REF.match(story.fields[key].code)),None))
                    if None in ids:
                        finding(errors,'unlinked_superscript_citation' if fully_superscript else 'unlinked_citation_token',
                                **location,number=number)
                        continue
                    if len(set(ids))!=1:
                        finding(errors,'numeric_token_spans_multiple_REF_fields',**location,number=number); continue
                    key=ids[0]; used_fields.add((story.part,key)); word_field=story.fields[key]
                    ref=REF.match(word_field.code); target=ref[1] or ref[2]; targets.append(target)
                    if word_field.locked: finding(errors,'locked_citation_field',**location,target=target)
                    if require_superscript and re.search(r'\\\*\s+CHARFORMAT\b',word_field.code,re.I):
                        first=next((sup for raw,sup in word_field.instruction_formats if re.search('[A-Za-z]',raw)),None)
                        if first is False: finding(errors,'CHARFORMAT_instruction_not_superscript',**location,target=target)
                    normalized=clean(word_field.result).strip().strip('[]［］').strip()
                    if not normalized.isdigit() or int(normalized)!=number:
                        finding(errors,'REF_result_does_not_match_numeric_token',**location,target=target); continue
                    matches=bookmarks.get(target,[])
                    if len(matches)!=1:
                        finding(errors,'missing_or_duplicate_target_bookmark',**location,target=target); continue
                    owner,bookmark=matches[0]
                    in_entries={entry_by_paragraph[g['paragraph']] for g in owner.glyphs[bookmark['start']:bookmark['end']] if owner is main and g['paragraph'] in entry_by_paragraph}
                    if in_entries!={number}:
                        if entries: finding(errors,'target_not_matching_bibliography_entry',**location,target=target,entries=sorted(in_entries))
                        else: finding(pending,'target_number_needs_Word_evaluation',**location,target=target)
                    if re.search(r'(?<!\S)\\[nrw](?=\s|$)',word_field.code,re.I):
                        finding(pending,'paragraph_number_REF_needs_Word_evaluation',**location,target=target)
                    else:
                        target_text=''.join(g['char'] for g in owner.glyphs[bookmark['start']:bookmark['end']])
                        if word_field.result!=target_text: finding(errors,'stale_REF_cache',**location,target=target,cached=word_field.result,target_text=target_text)
                for item in re.split('[,，;；]',match[0][1:-1]):
                    bounds=re.split(r'[–—\-]',item.strip())
                    if len(bounds)==2:
                        lo,hi=map(int,bounds)
                        if hi<lo or hi-lo>10000: finding(errors,'invalid_citation_range',**location); continue
                        covered.update(range(lo,hi+1))
                    elif len(bounds)==1: covered.add(int(bounds[0]))
                    else: finding(errors,'invalid_citation_range',**location)
                groups.append({**location,'REF_targets':list(dict.fromkeys(targets))})
    missing=sorted(covered-set(entries)); uncited=sorted(set(entries)-covered)
    if missing and entries: finding(errors,'cited_numbers_missing_from_bibliography',numbers=missing)
    if require_all_cited and uncited: finding(errors,'uncited_bibliography_entries',numbers=uncited)
    if not groups and not without_bibliography: finding(pending,'no_numeric_citations_detected')
    status='fail' if errors else 'needs_review' if pending else 'pass'
    counts=Counter(re.split(r'\s+',f.code.strip(),maxsplit=1)[0].upper() for story in stories for f in story.fields if f.code.strip())
    return {'structural_status':status,'input':str(path),'input_sha256':sha256(data).hexdigest(),
        'modified_input':False,'word_update_verified':False,'superscript_required':require_superscript,
        'profile':'without_bibliography' if without_bibliography else 'live_numeric',
        'checked_parts':names,'bibliography_span':None if without_bibliography else {'start_paragraph':start,'end_paragraph_exclusive':end},
        'scope_note':'Main story, tables/captions, and available footnotes/endnotes; bibliography ends at the supplied resume heading or end of main story. Headers, footers, metadata and native equation text are not certified.',
        'field_counts':dict(counts),'field_count_scope':'Explicit OOXML fields in checked parts; not Word COM Fields.Count or a native OLE count.',
        'numeric_bracket_candidates':bracket_candidates,'citation_groups':len(groups),'citation_REF_fields':len(used_fields),
        'bibliography_entries':len(entries),'covered_reference_numbers':sorted(covered),'uncited_reference_numbers':uncited,
        'errors':errors,'needs_review':pending,'groups':groups}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx',type=Path)
    parser.add_argument('--bib-heading',action='append')
    parser.add_argument('--resume-heading',action='append',default=[])
    parser.add_argument('--require-superscript',action='store_true')
    parser.add_argument('--require-all-cited',action='store_true')
    parser.add_argument('--without-bibliography',action='store_true',
                        help='Check an explicitly citation-free delivery. Literal bracketed numbers still need contextual review.')
    parser.add_argument('--json-out',type=Path)
    args=parser.parse_args(); source=args.docx.resolve()
    if args.without_bibliography and (args.require_superscript or args.require_all_cited or args.resume_heading):
        parser.error('Citation style, citation coverage and bibliography-resume checks require a bibliography.')
    if args.json_out:
        output=args.json_out.resolve()
        if output==source or (output.exists() and source.exists() and output.samefile(source)) or output.suffix.lower()!='.json':
            parser.error('JSON output must be a .json report separate from the input DOCX.')
    try:
        result=audit_docx(source,bib_headings=args.bib_heading,resume_headings=args.resume_heading,
            require_superscript=args.require_superscript,require_all_cited=args.require_all_cited,
            without_bibliography=args.without_bibliography)
    except (OSError,ValueError,ET.ParseError,KeyError,BadZipFile) as exc: parser.error(str(exc))
    payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding='utf-8')
    print(payload,end='')
    return 0 if result['structural_status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main())
