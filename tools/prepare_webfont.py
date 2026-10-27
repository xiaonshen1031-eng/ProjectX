"""Build a locally hosted CJK webfont from the public website's characters."""
from pathlib import Path
import json,re
import requests
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf'
LICENSE='https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/OFL.txt'

def main():
    cache=ROOT/'work/webfont';cache.mkdir(parents=True,exist_ok=True)
    original=cache/'NotoSansSC-variable.ttf'
    if not original.exists():
        response=requests.get(SOURCE,timeout=60);response.raise_for_status();original.write_bytes(response.content)
    license_response=requests.get(LICENSE,timeout=30);license_response.raise_for_status()
    public_text=''.join(p.read_text(encoding='utf-8') for p in [ROOT/'docs/index.html',ROOT/'docs/app.js',ROOT/'docs/assets/workflow-demo.zh.vtt'])
    chars=set(re.findall(r'[\u2e80-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef]',public_text))
    chars.update('←→↑↓↗↘×＋− ·—，。；：（）《》')
    opts=subset.Options();opts.flavor='woff2';opts.name_IDs=['*'];opts.name_languages=['*']
    font=TTFont(original);worker=subset.Subsetter(options=opts);worker.populate(text=''.join(sorted(chars)));worker.subset(font)
    font.flavor='woff2'
    for rec in font['name'].names:
        replacement={1:'ProjectX Sans SC',2:'Regular',3:'ProjectX Sans SC Website Subset',4:'ProjectX Sans SC',6:'ProjectXSansSC',16:'ProjectX Sans SC',17:'Regular'}.get(rec.nameID)
        if replacement:
            try:rec.string=replacement.encode(rec.getEncoding())
            except UnicodeEncodeError:pass
    out=ROOT/'docs/assets/fonts/ProjectX-SansSC.woff2';font.save(out)
    (out.parent/'NotoSansSC-OFL.txt').write_text(license_response.text,encoding='utf-8')
    (out.parent/'CJK-font-source.json').write_text(json.dumps({'source':SOURCE,'license':'SIL Open Font License 1.1','licenseFile':'NotoSansSC-OFL.txt','subset':'Characters used in the public index.html, app.js and video captions','characters':len(chars),'bytes':out.stat().st_size},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'webfont':'ready','characters':len(chars),'bytes':out.stat().st_size}))

if __name__=='__main__':main()
