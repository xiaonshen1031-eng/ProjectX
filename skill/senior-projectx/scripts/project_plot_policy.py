#!/usr/bin/env python3
"""Check the scientific encodings and source bindings of Project artifacts."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
from validate_figure_manifest import validate_publication_encoding, declared_layer_paths


def audit_render_contract(item: dict, resolve, where: str, errors: list[str]) -> None:
    """Check a declared renderer's actual palette/export bindings and scale bounds."""
    contract = item.get('render_contract')
    if contract is None:
        return
    if not isinstance(contract, dict):
        errors.append(where + ': render_contract must be an object')
        return
    palette_path = resolve(contract.get('palette_source', ''))
    catalog = {}
    if not palette_path.is_file() or contract.get('palette_sha256') != hashlib.sha256(palette_path.read_bytes()).hexdigest():
        errors.append(where + ': palette source missing or stale')
    else:
        catalog = json.loads(palette_path.read_text(encoding='utf-8-sig'))
    roles = contract.get('roles')
    if not isinstance(roles, dict) or not roles:
        errors.append(where + ': named color roles are required in render_contract')
    else:
        for role, binding in roles.items():
            if (not isinstance(binding, dict) or not binding.get('meaning')
                    or binding.get('catalog_key') not in catalog.get('colors', {})
                    or catalog.get('colors', {}).get(binding.get('catalog_key')) != binding.get('color')):
                errors.append(where + ': color role contradicts its catalog or lacks meaning: ' + role)
    scales = contract.get('scales', [])
    if not isinstance(scales, list):
        errors.append(where + ': scales must be a list')
        scales = []
    for scale in scales:
        if not isinstance(scale, dict):
            errors.append(where + ': scale must be an object')
            continue
        values = [scale.get(key) for key in ('vmin', 'vmax', 'data_min', 'data_max')]
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
            errors.append(where + ': finite scale and plotted-data bounds are required')
            continue
        lower, upper, data_lower, data_upper = values
        if not lower <= data_lower <= data_upper <= upper:
            errors.append(where + ': scalar normalization clips declared plotted values')
        if not scale.get('unit') or not scale.get('quantity') or not scale.get('zero_meaning'):
            errors.append(where + ': scale needs quantity, unit and the physical meaning of zero')
        if scale.get('normalization') == 'sequential':
            if scale.get('semantics') == 'signed_difference':
                errors.append(where + ': signed quantities need a diverging scale with an explicit pivot')
        elif scale.get('normalization') == 'diverging':
            pivot = scale.get('pivot')
            if not isinstance(pivot, (int, float)) or not math.isfinite(pivot) or not lower < pivot < upper:
                errors.append(where + ': diverging scale requires an interior physical pivot')
        else:
            errors.append(where + ': scalar normalization must be sequential or diverging')
    if contract.get('clipped_text'):
        errors.append(where + ': renderer found text outside the physical canvas')
    exports = item.get('exports')
    if not isinstance(exports, dict) or not exports:
        errors.append(where + ': rendered export bindings are required')
        return
    for extension, artifact in exports.items():
        if not isinstance(artifact, dict):
            errors.append(where + ': export must bind its path and hash: ' + extension)
            continue
        path = resolve(artifact.get('path', ''))
        if not path.is_file() or artifact.get('sha256') != hashlib.sha256(path.read_bytes()).hexdigest():
            errors.append(where + ': export missing or stale: ' + extension)
            continue
        if extension == 'png':
            dimensions = [item.get('width_cm'), contract.get('height_cm'), contract.get('raster_dpi')]
            if not all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in dimensions):
                errors.append(where + ': physical width, height and raster density are required')
                continue
            width, height, dpi = dimensions
            with Image.open(path) as rendered:
                if abs(rendered.width-width/2.54*dpi) > 1 or abs(rendered.height-height/2.54*dpi) > 1:
                    errors.append(where + ': raster dimensions contradict final physical size or density')


def audit(data: dict, base_dir: Path | None = None) -> dict:
    errors = []
    if not isinstance(data, dict):
        return {'status': 'fail', 'errors': ['manifest must be an object']}
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
        validate_publication_encoding(item, where, errors, allow_project_direct=True)
        audit_render_contract(item, resolve, where, errors)
        sources = item.get('source', [])
        if not isinstance(sources, list) or not sources or not all(isinstance(raw, str) and raw.strip() for raw in sources):
            errors.append(where + ': saved data sources are required'); continue
        hashes = item.get('source_sha256')
        if not isinstance(hashes, dict):
            errors.append(where + ': source_sha256 must map source paths to hashes')
            hashes = {}
        for raw in sources:
            path = resolve(raw)
            if not path.is_file():
                errors.append(where + ': source missing: ' + str(raw)); continue
            expected = hashes.get(raw)
            if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append(where + ': source hash missing or stale: ' + str(raw))
        for location, raw in declared_layer_paths(item, where):
            if not isinstance(raw, str) or raw not in sources:
                errors.append(location + ': layer source must name a bound source file')
        raw_path = item.get('path')
        if not isinstance(raw_path, str) or not raw_path.strip():
            errors.append(where + ': rendered figure path is required'); continue
        path = resolve(raw_path)
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
