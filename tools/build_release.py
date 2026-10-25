"""Package the skill source and update the website's release metadata."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {'.md', '.py', '.ps1', '.m', '.json', '.jsonl', '.yaml', '.yml', '.txt'}


def source_bytes(file):
    data = file.read_bytes()
    return data.replace(b'\r\n', b'\n') if file.suffix in TEXT_SUFFIXES or file.name == 'LICENSE' else data


def main():
    manifest_path = ROOT / 'docs/release.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    source = ROOT / 'skill/senior-projectx'
    target = ROOT / 'docs' / manifest['download']
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(source.rglob('*')):
            if not file.is_file() or '__pycache__' in file.parts or file.suffix == '.pyc':
                continue
            item = ZipInfo('senior-projectx/' + file.relative_to(source).as_posix(), (2026, 10, 25, 0, 0, 0))
            item.compress_type = ZIP_DEFLATED
            item.external_attr = 0o644 << 16
            archive.writestr(item, source_bytes(file))
    manifest['bytes'] = target.stat().st_size
    manifest['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('version', 'bytes', 'sha256')}))


if __name__ == '__main__':
    main()
