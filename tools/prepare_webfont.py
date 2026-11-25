"""Build a locally hosted CJK webfont from the public website's characters."""
from pathlib import Path
import json
import re

import requests
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf'
LICENSE = 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/OFL.txt'
TEXT_FORMATS = {'.html', '.js', '.css', '.vtt'}
CJK = re.compile(r'[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef]')


def public_characters(directory):
    files = sorted(file for file in directory.rglob('*') if file.suffix.lower() in TEXT_FORMATS and file.is_file())
    chars = set('←→↑↓↗↘×＋− ·—，。；：（）《》')
    for file in files:
        chars.update(CJK.findall(file.read_text(encoding='utf-8-sig')))
    return chars


def main():
    cache = ROOT / 'work/webfont'
    cache.mkdir(parents=True, exist_ok=True)
    original = cache / 'NotoSansSC-variable.ttf'
    if not original.exists():
        response = requests.get(SOURCE, timeout=60)
        response.raise_for_status()
        original.write_bytes(response.content)
    doc_root = ROOT / 'docs'
    out = doc_root / 'assets/fonts/ProjectX-SansSC.woff2'
    license_file = out.with_name('NotoSansSC-OFL.txt')
    if not license_file.is_file():
        response = requests.get(LICENSE, timeout=30)
        response.raise_for_status()
        license_file.write_text(response.text, encoding='utf-8')

    chars = public_characters(doc_root)
    options = subset.Options()
    options.flavor = 'woff2'
    options.name_IDs = ['*']
    options.name_languages = ['*']
    font = TTFont(original, recalcTimestamp=False)
    worker = subset.Subsetter(options=options)
    worker.populate(text=''.join(sorted(chars)))
    worker.subset(font)
    font.flavor = 'woff2'
    names = {
        1: 'ProjectX Sans SC',
        2: 'Regular',
        3: 'ProjectX Sans SC Website Subset',
        4: 'ProjectX Sans SC',
        6: 'ProjectXSansSC',
        16: 'ProjectX Sans SC',
        17: 'Regular',
    }
    for record in font['name'].names:
        replacement = names.get(record.nameID)
        if replacement:
            try:
                record.string = replacement.encode(record.getEncoding())
            except UnicodeEncodeError:
                pass
    mapped = font.getBestCmap()
    missing = [value for value in sorted(chars) if ord(value) not in mapped]
    if missing:
        raise ValueError('The selected CJK source font lacks: ' + ' '.join(missing))
    font.save(out)
    metadata = {
        'source': SOURCE,
        'license': 'SIL Open Font License 1.1',
        'licenseFile': license_file.name,
        'subset': 'Characters used in public HTML, JavaScript, CSS and video captions',
        'characters': len(chars),
        'bytes': out.stat().st_size,
    }
    out.with_name('CJK-font-source.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps({'webfont': 'ready', 'characters': len(chars), 'bytes': out.stat().st_size}))


if __name__ == '__main__':
    main()
