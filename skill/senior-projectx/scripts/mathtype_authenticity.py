#!/usr/bin/env python3
"""Native MathType gate. Structural presence alone never certifies meaning/rendering.

olefile is needed only for this gate. If absent, report unverified, never pass.
"""
from __future__ import annotations
import io
import json
import posixpath
import struct
from pathlib import Path
from zipfile import ZipFile
from lxml import etree

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'o':'urn:schemas-microsoft-com:office:office',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'v':'urn:schemas-microsoft-com:vml'}


def read_native(blob: bytes) -> bytes:
    """Read genuine compound storage; reject renamed images and empty native streams."""
    import olefile
    with olefile.OleFileIO(io.BytesIO(blob)) as ole:
        if not ole.exists('Equation Native'):
            raise ValueError('Missing Equation Native stream')
        return ole.openstream('Equation Native').read()


def mtef_bytes(native: bytes) -> bytes:
    if len(native)<33:
        raise ValueError('Truncated Equation Native header/payload')
    header=struct.unpack_from('<I',native,0)[0]
    length=struct.unpack_from('<I',native,8)[0]
    if header<28 or header>len(native)-5 or length!=len(native)-header:
        raise ValueError('Invalid Equation Native payload bounds')
    data=native[header:]
    if data[0] not in {3,4,5}:
        raise ValueError('Unrecognized MTEF version')
    if len(data)<12:
        raise ValueError('Empty/truncated MTEF equation')
    return data


def objects(path: Path) -> list[dict]:
    out=[]
    with ZipFile(path) as z:
        for part in z.namelist():
            if not part.startswith('word/') or not part.endswith('.xml') or '/_rels/' in part:
                continue
            root=etree.fromstring(z.read(part))
            nodes=root.xpath('.//o:OLEObject',namespaces=NS)
            if not nodes:continue
            relname=posixpath.join(posixpath.dirname(part),'_rels',posixpath.basename(part)+'.rels')
            rels={r.get('Id'):r for r in etree.fromstring(z.read(relname))} if relname in z.namelist() else {}
            for index,node in enumerate(nodes,1):
                progid=node.get('ProgID','')
                if not progid.lower().startswith('equation.'):continue
                rid=node.get('{'+NS['r']+'}id','')
                target=rels.get(rid)
                item={'key':part+'#'+rid,'progid':progid,'errors':[],'native':None,'mtef':None,'preview':None}
                try:
                    if progid!='Equation.DSMT4':raise ValueError('Object is not Equation.DSMT4')
                    if target is None or target.get('TargetMode')=='External':raise ValueError('Missing or external OLE target')
                    name=posixpath.normpath(posixpath.join(posixpath.dirname(part),target.get('Target','')))
                    item['native']=read_native(z.read(name));item['mtef']=mtef_bytes(item['native'])
                    parent=node.getparent()
                    images=parent.xpath('.//v:imagedata',namespaces=NS)
                    if not images:raise ValueError('Missing visible equation preview')
                    preview=rels.get(images[0].get('{'+NS['r']+'}id'))
                    if preview is None or preview.get('TargetMode')=='External':raise ValueError('Missing/internal preview target required')
                    preview_name=posixpath.normpath(posixpath.join(posixpath.dirname(part),preview.get('Target','')))
                    item['preview']=z.read(preview_name)
                    if not item['preview']:raise ValueError('Empty preview')
                except (ValueError,KeyError,OSError,ImportError,struct.error) as exc:
                    item['errors'].append(str(exc))
                out.append(item)
    return out


def audit_mathtype(path: Path, evidence_path: Path | None = None) -> dict:
    """Consume an independent expected native export and recorded visual/reopen QA.

    No checksum or sidecar is generated. Evidence paths are relative to the JSON.
    Expected native files must come from the intended equation's genuine MathType
    conversion, not from extracting the object currently under test.
    """
    items=objects(path)
    evidence={};base=path.parent
    if evidence_path:
        base=evidence_path.resolve().parent
        evidence=json.loads(evidence_path.read_text(encoding='utf-8-sig'))
    records=evidence.get('equations',{})
    reopened={}
    reopened_path=evidence.get('reopened_docx')
    errors=[]
    if reopened_path:
        try:reopened={i['key']:i for i in objects(base/reopened_path)}
        except (OSError,ValueError,KeyError) as exc:errors.append('Cannot inspect reopened DOCX: '+str(exc))
    if not items:errors.append('No native MathType equation objects found')
    results=[]
    for item in items:
        fail=list(item['errors']);record=records.get(item['key'],{})
        expected=None
        try:
            expected_file=record.get('expected_native_file')
            if not expected_file:raise ValueError('Missing independently converted expected Equation Native export')
            expected=mtef_bytes((base/expected_file).read_bytes())
            if item['mtef']!=expected:raise ValueError('Native MTEF does not match intended independently converted equation')
        except (OSError,ValueError,struct.error) as exc:fail.append(str(exc))
        if not record.get('expected_tex','').strip():fail.append('Missing intended mathematical expression')
        if record.get('expected_source')!='independent_mathtype_conversion':fail.append('Expected native export provenance not established')
        render=record.get('render_artifact','')
        if not render or not (base/render).is_file():fail.append('Missing Word-rendered visual evidence')
        for gate in ['native_meaning_checked','preview_matches_native','word_render_checked']:
            if record.get(gate) is not True:fail.append('Unverified inspection: '+gate)
        other=reopened.get(item['key'])
        if not other or other['errors'] or other['mtef']!=item['mtef'] or other['preview']!=item['preview']:
            fail.append('Reopen persistence not verified from the saved/reopened document')
        results.append({'key':item['key'],'progid':item['progid'],
                        'native_structure_valid':item['mtef'] is not None and not item['errors'],
                        'status':'pass' if not fail else 'unverified_or_failed','issues':fail})
    status='pass' if items and not errors and all(r['status']=='pass' for r in results) else 'unverified_or_failed'
    return {'status':status,'object_count':len(items),'equations':results,'issues':errors,
            'scope':'Native bytes and reopen persistence are checked automatically. Meaning and preview/render agreement require the recorded inspection; ProgID/count never suffices.'}
