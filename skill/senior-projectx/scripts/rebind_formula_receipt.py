#!/usr/bin/env python3
"""Bind a layout-only final DOCX after checking native objects and previews."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from mathtype_authenticity import objects


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rebind(converted, final, receipt_path, output):
    if output.exists():
        raise FileExistsError(output)
    record = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    if record.get('final_docx_sha256') != sha(converted):
        raise ValueError('The original conversion receipt does not bind the converted DOCX.')
    a, b = objects(converted), objects(final)
    if len(a) != len(b) or not a:
        raise ValueError('Native object count changed during layout or roundtrip.')
    for old, new in zip(a, b):
        if old['errors'] or new['errors'] or old['key'] != new['key'] or old['mtef'] != new['mtef'] or old['preview'] != new['preview']:
            raise ValueError('Native content, order, identity or preview changed during layout or roundtrip.')
    old_base, new_base = receipt_path.resolve().parent, output.resolve().parent
    for key in ('source_manifest_path',):
        if record.get(key):
            record[key] = os.path.relpath((old_base / record[key]).resolve(), new_base).replace('\\', '/')
    record['converted_docx_sha256'] = sha(converted)
    record['final_docx_sha256'] = sha(final)
    record['layout_rebinding'] = {'native_and_preview_preserved': True, 'objects_checked': len(a)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'status': 'pass', 'objects_checked': len(a)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--converted-docx', type=Path, required=True)
    p.add_argument('--final-docx', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(rebind(a.converted_docx, a.final_docx, a.receipt, a.out)))
