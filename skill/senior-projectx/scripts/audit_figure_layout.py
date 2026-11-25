#!/usr/bin/env python3
"""Read-only checks of geometry measured from a final-size figure renderer.

This helper cannot establish that measurements came from the delivered revision,
or judge scientific meaning, arrows, color, crops, or visual quality. Inspect the
actual export as well. Coordinates are millimetres from the canvas top left;
font_pt is the final inserted size, after any document scaling.

Adapted from the NPS Research Paper v3.2.4 Project figure workflow by XiaoN.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def finite_value(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def finite_number(value: Any, *, positive: bool = False) -> bool:
    return finite_value(value) and (value > 0 if positive else value >= 0)


def audit_layout(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {
        'measurement_checks_passed': False,
        'visual_review_required': True,
        'scope': 'Supplied final-size bounding boxes and font measurements only; not visual or scientific approval.',
        'errors': errors,
        'measurements': {'gaps_mm': [], 'alignment_spans_mm': []},
    }
    if not isinstance(data, dict):
        errors.append('measurement document must be an object.')
        return result
    canvas = data.get('canvas_mm')
    if (not isinstance(canvas, list) or len(canvas) != 2
            or not all(finite_number(v, positive=True) for v in canvas)):
        errors.append('canvas_mm must contain two finite positive dimensions.')
        return result
    width, height = canvas
    thresholds: dict[str, float] = {}
    for name, positive in [('minimum_font_pt', True), ('minimum_margin_mm', False)]:
        if name in data:
            if not finite_number(data[name], positive=positive):
                errors.append(f'{name} must be a finite {"positive" if positive else "non-negative"} number.')
            else:
                thresholds[name] = float(data[name])

    objects: dict[str, dict[str, Any]] = {}
    texts: dict[str, dict[str, Any]] = {}
    panels: dict[str, dict[str, Any]] = {}
    for kind, target in [('text', texts), ('panels', panels)]:
        entries = data.get(kind, [])
        if not isinstance(entries, list):
            errors.append(f'{kind} must be a list.')
            continue
        for index, entry in enumerate(entries):
            where = f'{kind}[{index}]'
            if not isinstance(entry, dict):
                errors.append(f'{where} must be an object.')
                continue
            key = entry.get('id')
            if not isinstance(key, str) or not key.strip():
                errors.append(f'{where}.id must be a non-empty string.')
                continue
            if key in objects:
                errors.append(f'duplicate object id: {key}.')
                continue
            box = entry.get('bbox_mm')
            if (not isinstance(box, list) or len(box) != 4
                    or not all(finite_value(v) for v in box)
                    or box[2] <= box[0] or box[3] <= box[1]):
                errors.append(f'{where}.bbox_mm must be finite [left,top,right,bottom] with positive extent.')
                continue
            left, top, right, bottom = box
            # Exclude invalid geometry before deriving widths or gaps: finite
            # endpoints outside the canvas can still overflow on subtraction.
            if left < 0 or top < 0 or right > width or bottom > height:
                errors.append(f'{key}: bbox extends beyond the canvas.')
                continue
            objects[key] = entry
            target[key] = entry
            margin = min(left, top, width-right, height-bottom)
            if 'minimum_margin_mm' in thresholds and margin < thresholds['minimum_margin_mm']:
                errors.append(f'{key}: actual margin {margin:.6g} mm is below minimum_margin_mm.')
            if kind == 'text':
                font = entry.get('font_pt')
                if not finite_number(font, positive=True):
                    errors.append(f'{key}: font_pt must be finite and positive.')
                elif 'minimum_font_pt' in thresholds and font < thresholds['minimum_font_pt']:
                    errors.append(f'{key}: final font {font:.6g} pt is below minimum_font_pt.')
    if not objects:
        errors.append('no valid measured text or panel objects supplied.')

    permitted: set[frozenset[str]] = set()
    allowed = data.get('permitted_text_overlaps', [])
    if not isinstance(allowed, list):
        errors.append('permitted_text_overlaps must be a list of text-id pairs.')
    else:
        for pair in allowed:
            if (not isinstance(pair, list) or len(pair) != 2
                    or not all(isinstance(k, str) and k in texts for k in pair)
                    or pair[0] == pair[1]):
                errors.append('permitted_text_overlaps contains an invalid or unknown text-id pair.')
            else:
                permitted.add(frozenset(pair))
    items = list(texts.items())
    for index, (key, entry) in enumerate(items):
        a = entry['bbox_mm']
        for other, candidate in items[index+1:]:
            b = candidate['bbox_mm']
            if (min(a[2], b[2]) > max(a[0], b[0])
                    and min(a[3], b[3]) > max(a[1], b[1])
                    and frozenset([key, other]) not in permitted):
                errors.append(f'text overlap: {key} and {other}.')

    groups = data.get('alignment_groups', [])
    if not isinstance(groups, list):
        errors.append('alignment_groups must be a list.')
        groups = []
    for index, group in enumerate(groups):
        where = f'alignment_groups[{index}]'
        if not isinstance(group, dict):
            errors.append(f'{where} must be an object.')
            continue
        ids, edge, tolerance = group.get('ids'), group.get('edge'), group.get('tolerance_mm')
        if (not isinstance(ids, list) or len(ids) < 2
                or not all(isinstance(k, str) and k in panels for k in ids)
                or len(set(ids)) != len(ids)):
            errors.append(f'{where}.ids must name at least two distinct known panels.')
            continue
        if edge not in ['left', 'top', 'right', 'bottom', 'width', 'height']:
            errors.append(f'{where}.edge is invalid.')
            continue
        if not finite_number(tolerance):
            errors.append(f'{where}.tolerance_mm must be explicitly finite and non-negative.')
            continue
        def position(key: str) -> float:
            b = panels[key]['bbox_mm']
            if edge in ['left', 'top', 'right', 'bottom']:
                return b[['left', 'top', 'right', 'bottom'].index(edge)]
            return b[2]-b[0] if edge == 'width' else b[3]-b[1]
        positions = [position(k) for k in ids]
        span = max(positions)-min(positions)
        result['measurements']['alignment_spans_mm'].append(dict(ids=ids, edge=edge, span_mm=span))
        if span > tolerance:
            errors.append(f'{where}: {edge} span {span:.6g} mm exceeds tolerance {tolerance:.6g} mm.')

    gaps = data.get('gaps', [])
    if not isinstance(gaps, list):
        errors.append('gaps must be a list.')
        gaps = []
    for index, gap in enumerate(gaps):
        where = f'gaps[{index}]'
        if not isinstance(gap, dict):
            errors.append(f'{where} must be an object.')
            continue
        left, right, minimum = gap.get('left_id'), gap.get('right_id'), gap.get('minimum_mm')
        if (not isinstance(left, str) or left not in objects
                or not isinstance(right, str) or right not in objects or left == right):
            errors.append(f'{where} must name distinct known left_id and right_id objects.')
            continue
        if not finite_number(minimum):
            errors.append(f'{where}.minimum_mm must be explicitly finite and non-negative.')
            continue
        actual = objects[right]['bbox_mm'][0]-objects[left]['bbox_mm'][2]
        result['measurements']['gaps_mm'].append(dict(left_id=left, right_id=right, actual_mm=actual))
        if actual < minimum:
            errors.append(f'{where}: visible gap {actual:.6g} mm is below minimum {minimum:.6g} mm.')

    pending = data.get('pending_results', [])
    if not isinstance(pending, list):
        errors.append('pending_results must be a list.')
        pending = []
    for index, entry in enumerate(pending):
        where = f'pending_results[{index}]'
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or entry['id'] not in objects:
            errors.append(f'{where}.id must name a known measured object.')
            continue
        count = entry.get('result_artist_count')
        if not isinstance(count, int) or isinstance(count, bool) or count != 0:
            errors.append(f'{where}: a pending result must have result_artist_count=0; plotted zero values are results.')
    result['checked_objects'] = dict(text=len(texts), panels=len(panels), pending_results=len(pending))
    result['measurement_checks_passed'] = not errors
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('measurements', type=Path, help='Final-renderer measurements JSON; input is never modified.')
    parser.add_argument('--pretty', action='store_true')
    args = parser.parse_args()
    try:
        report = audit_layout(json.loads(args.measurements.read_text(encoding='utf-8-sig')))
    except (OSError, ValueError) as exc:
        report = {'measurement_checks_passed': False, 'visual_review_required': True,
                  'scope': 'Measurement-file parsing only.', 'errors': [str(exc)]}
    print(json.dumps(report, ensure_ascii=True, indent=2 if args.pretty else None, allow_nan=False))
    return 0 if report['measurement_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
