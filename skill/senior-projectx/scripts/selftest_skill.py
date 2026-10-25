#!/usr/bin/env python3
"""Check portable resources, syntax, and the Project maintenance workflow."""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent


def inspect_docx_properties(path: Path) -> list[str]:
    issues = []
    with ZipFile(path) as package:
        properties = etree.fromstring(package.read('docProps/core.xml'))
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        for node in properties.xpath('//*[@xsi:type]', namespaces={'xsi': xsi}):
            kind = node.get('{' + xsi + '}type')
            if ':' in kind and kind.split(':', 1)[0] not in node.nsmap:
                issues.append('Unbound metadata QName: ' + kind)
    return issues


def inspect() -> dict:
    failures, checks = [], []
    for path in ROOT.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        if path.suffix == '.py':
            try:
                ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            except SyntaxError as exc:
                failures.append(f'{path.relative_to(ROOT)}: {exc}')
        if path.suffix == '.json':
            try:
                json.loads(path.read_text(encoding='utf-8-sig'))
            except ValueError as exc:
                failures.append(f'{path.relative_to(ROOT)}: {exc}')
        if path.suffix == '.docx':
            try:
                failures.extend(f'{path.relative_to(ROOT)}: {issue}' for issue in inspect_docx_properties(path))
            except (ValueError, KeyError, OSError, etree.XMLSyntaxError) as exc:
                failures.append(f'{path.relative_to(ROOT)}: {exc}')
        if path.suffix == '.md':
            text = path.read_text(encoding='utf-8')
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
                if re.match(r'https?://|#', target):
                    continue
                if not (path.parent / target.split('#')[0]).is_file():
                    failures.append(f'Broken link: {path.relative_to(ROOT)}: {target}')
    checks.append('Packaged Python/JSON syntax and Markdown resources')
    with tempfile.TemporaryDirectory(prefix='projectx-selftest-') as temporary:
        harness = Path(temporary) / 'harness'
        command = [sys.executable, '-B', str(ROOT / 'scripts/update_harness_state.py'), '--harness-root', str(harness)]
        ran = subprocess.run(command + ['preference', '--preference-id', 'temporary_project_rule', '--statement', 'Retain the declared units.', '--scope', 'project', '--confidence', '1'], capture_output=True, text=True, encoding='utf-8')
        if ran.returncode:
            failures.append(ran.stderr)
        else:
            stored = json.loads((harness / 'state/skill_state.json').read_text(encoding='utf-8'))
            if stored['preferences']['temporary_project_rule']['scope'] != 'project':
                failures.append('Preference scope was not preserved.')
        checks.append('Maintenance writes only to the explicitly selected temporary harness')
    return {'status': 'pass' if not failures else 'fail', 'checks': checks, 'issues': failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = inspect()
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + '\n', encoding='utf-8')
    print(text)
    return 0 if result['status'] == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())
