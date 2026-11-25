"""Read-only EMF text diagnostics; never decode glyph indices as Unicode.

Adapted from the NPS Research Paper v3.2.4 Project figure workflow by XiaoN.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import struct


def inspect_emf(data: bytes) -> dict:
    if len(data) < 88:
        raise ValueError('Truncated EMF header')
    kind, header_size = struct.unpack_from('<II', data)
    if kind != 1 or header_size < 88 or header_size > len(data):
        raise ValueError('Invalid EMF header record')
    if struct.unpack_from('<I', data, 40)[0] != 0x464D4520:
        raise ValueError('Invalid EMF signature')
    declared_bytes, declared_records = struct.unpack_from('<II', data, 48)
    if declared_bytes != len(data):
        raise ValueError('EMF byte count does not match the input')
    frame = struct.unpack_from('<4i', data, 24)
    counts: Counter = Counter()
    fonts: Counter = Counter()
    glyph_records = unicode_records = glyph_count = 0
    offset = 0
    last_kind = None
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError(f'Truncated record header at {offset}')
        kind, size = struct.unpack_from('<II', data, offset)
        if size < 8 or size % 4 or offset + size > len(data):
            raise ValueError(f'Invalid record size at {offset}')
        counts[kind] += 1
        last_kind = kind
        if kind == 82:  # EMR_EXTCREATEFONTINDIRECTW, LOGFONTW face at byte 40.
            if size < 104:
                raise ValueError('Truncated font record')
            name = data[offset + 40:offset + 104].decode('utf-16-le').split('\0', 1)[0]
            fonts[name] += 1
        elif kind == 84:  # EMR_EXTTEXTOUTW with one EMRTEXT structure.
            if size < 76:
                raise ValueError('Truncated wide-text record')
            nchars, string_offset, options = struct.unpack_from('<III', data, offset + 44)
            if nchars and (string_offset < 76 or string_offset + 2 * nchars > size):
                raise ValueError('Wide-text string lies outside its record')
            if options & 0x10:
                glyph_records += 1
                glyph_count += nchars
            else:
                # Count only. Do not print potentially private text or guess glyph mappings.
                unicode_records += 1
        offset += size
    if sum(counts.values()) != declared_records or last_kind != 14:
        raise ValueError('EMF record count or EOF does not match its header')
    return {
        'frame_0_01_mm': list(frame),
        'frame_width_mm': (frame[2] - frame[0]) / 100,
        'frame_height_mm': (frame[3] - frame[1]) / 100,
        'record_counts': dict(sorted(counts.items())),
        'fonts': dict(fonts),
        'wide_text_records': counts[84],
        'glyph_index_text_records': glyph_records,
        'glyph_indices': glyph_count,
        'unicode_wide_text_records': unicode_records,
        'uninspected_text_records': sum(counts[k] for k in (83, 96, 97, 108)),
        'interpretation': 'Font/glyph-index coupling detected; visible corruption is not established.' if glyph_records else 'No glyph-index wide-text record detected; visible correctness is not established.',
        'limits': 'Only EMR_EXTTEXTOUTW text flags and LOGFONTW names are inspected. Other text forms and EMF+ comment payloads are not decoded. This is not a complete EMF or visual validator.',
        'modified_input': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('emf', type=Path)
    parser.add_argument('--json-out', type=Path)
    args = parser.parse_args()
    try:
        result = inspect_emf(args.emf.read_bytes())
    except (OSError, ValueError, struct.error, UnicodeError) as exc:
        parser.exit(1, f'EMF inspection failed: {exc}\n')
    payload = json.dumps(result, ensure_ascii=True, indent=2)
    if args.json_out:
        if args.json_out.resolve() == args.emf.resolve() or (args.json_out.exists() and args.json_out.samefile(args.emf)):
            parser.error('The JSON report must not replace the EMF input')
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload + '\n', encoding='utf-8')
    print(payload)


if __name__ == '__main__':
    main()
