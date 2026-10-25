#!/usr/bin/env python3
"""Check the scientific encodings and source bindings of Project artifacts."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from validate_figure_manifest import validate_publication_encoding, declared_layer_paths


def audit(data: dict, base_dir: Path | None = None) -> dict:
    errors = []
    artifacts = data.get('artifacts')
    if not isinstance(artifacts, list) or not artifacts:
        return {'status': 'fail', 'errors': ['artifacts must be a nonempty list']}
    def resolve(raw):
        path = Path(raw)
        return path if path.is_absolute() else (base_dir or Path.cwd()) / path
    for index, item in enumerate(artifacts, 1):
        where = f'Figure {index}'
        if not isinstance(item, dict):
            errors.append(where + ': artifact must be an object'); continue
        if not item.get('plot_type') or not item.get('question'):
            errors.append(where + ': plot_type and scientific question are required')
        validate_publication_encoding(item, where, errors)
        sources = item.get('source', [])
        if not isinstance(sources, list) or not sources:
            errors.append(where + ': saved data sources are required'); continue
        for raw in sources:
            path = resolve(raw)
            if not path.is_file():
                errors.append(where + ': source missing: ' + str(raw)); continue
            expected = item.get('source_sha256', {}).get(str(raw))
            if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append(where + ': source hash missing or stale: ' + str(raw))
        for location, raw in declared_layer_paths(item, where):
            if not isinstance(raw, str) or raw not in sources:
                errors.append(location + ': layer source must name a bound source file')
        path = resolve(item.get('path', ''))
        if not path.is_file() or item.get('sha256') != hashlib.sha256(path.read_bytes()).hexdigest():
            errors.append(where + ': rendered figure missing or hash stale')
    return {'status': 'pass' if not errors else 'fail', 'errors': errors, 'figure_count': len(artifacts)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.manifest.read_text(encoding='utf-8-sig')), args.manifest.parent)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out: args.out.write_text(payload + '\n', encoding='utf-8')
    print(payload)
    raise SystemExit(0 if result['status'] == 'pass' else 2)
