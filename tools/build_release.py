"""Package the skill source and update the website's release metadata."""
from pathlib import Path
from datetime import date
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {'.md', '.py', '.ps1', '.m', '.json', '.jsonl', '.yaml', '.yml', '.txt'}


def source_bytes(file):
    data = file.read_bytes()
    return data.replace(b'\r\n', b'\n') if file.suffix in TEXT_SUFFIXES or file.name == 'LICENSE' else data


def source_files(source):
    for file in sorted(source.rglob('*')):
        if (file.is_file() and '__pycache__' not in file.parts
                and file.suffix != '.pyc' and file.name not in {'.DS_Store', 'Thumbs.db'}):
            yield file


def main():
    manifest_path = ROOT / 'docs/release.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    source = ROOT / 'skill/senior-projectx'
    target = ROOT / 'docs' / manifest['download']
    target.parent.mkdir(parents=True, exist_ok=True)
    release_day = date.fromisoformat(manifest['date'])
    zip_stamp = (release_day.year, release_day.month, release_day.day, 0, 0, 0)
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
        for file in source_files(source):
            item = ZipInfo('senior-projectx/' + file.relative_to(source).as_posix(), zip_stamp)
            item.compress_type = ZIP_DEFLATED
            item.external_attr = 0o644 << 16
            archive.writestr(item, source_bytes(file))
    manifest['bytes'] = target.stat().st_size
    manifest['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('version', 'bytes', 'sha256')}))


if __name__ == '__main__':
    main()
