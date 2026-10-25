"""Validate public chart assets, download integrity and the publication boundary."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from zipfile import ZipFile
import hashlib,json,re,struct
from build_release import source_bytes
from prepare_gallery import inspect_emf

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'


def require(condition,message):
    if not condition:raise ValueError(message)


class Links(HTMLParser):
    def __init__(self):super().__init__();self.paths=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):
            require(attrs['id'] not in self.ids,'Duplicate HTML id');self.ids.add(attrs['id'])
        self.paths.extend(attrs[k] for k in ('src','href') if attrs.get(k))
        if tag=='img':require('alt' in attrs,'Image without alt text')


def main():
    public_files=list(DOCS.rglob('*'))
    require(not any(p.suffix.lower() in {'.docx','.pptx','.pdf','.xlsx'} for p in public_files),'Document artifact in public website')
    require(not (DOCS/'examples').exists(),'Legacy document examples directory remains public')
    require(not (ROOT/'examples').exists(),'Legacy project data directory remains public')
    forbidden=('report-model','report-results','slide-model','ProjectX-demo.mp4','demo-poster.webp','demo-data.json','ProjectX-research-report','ProjectX-project-briefing')
    for p in public_files:
        if p.is_file():require(not any(v in p.name for v in forbidden),'Legacy asset in website: '+p.name)
    for p in [ROOT/'README.md',DOCS/'index.html',DOCS/'app.js',DOCS/'release.json']:
        text=p.read_text(encoding='utf-8')
        require(not any(v in text for v in forbidden),'Legacy link in public text')
        require(not re.search(r'[A-Z]:[\\/]Users[\\/]Admin',text,re.I),'Machine path in public website')
    assets=set()
    for page in DOCS.glob('*.html'):
        parser=Links();parser.feed(page.read_text(encoding='utf-8'))
        for link in parser.paths:
            url=urlsplit(link)
            if url.scheme or url.netloc:continue
            if not url.path:
                require(not url.fragment or unquote(url.fragment) in parser.ids,'Missing HTML anchor');continue
            target=(page.parent/unquote(url.path)).resolve()
            require(target.is_relative_to(DOCS),'Asset outside public site')
            if target.is_dir():target/='index.html'
            require(target.is_file(),'Missing public asset: '+link);assets.add(target)
    manifest=json.loads((DOCS/'release.json').read_text(encoding='utf-8'))
    package=DOCS/manifest['download']
    require(package.stat().st_size==manifest['bytes'],'Skill byte count mismatch')
    require(hashlib.sha256(package.read_bytes()).hexdigest()==manifest['sha256'],'Skill hash mismatch')
    with ZipFile(package) as archive:
        require(archive.testzip() is None,'Corrupt skill archive')
        for name in archive.namelist():
            require(name.startswith('senior-projectx/') and '..' not in Path(name).parts,'Invalid skill path')
            source=ROOT/'skill'/name
            require(source.is_file() and source_bytes(source)==archive.read(name),'Skill source mismatch')
    gallery=json.loads((DOCS/'gallery.json').read_text(encoding='utf-8'))
    catalog=json.loads((ROOT/'gallery/catalog.json').read_text(encoding='utf-8'))['charts']
    require(len(catalog)==14,'Expected fourteen chart types')
    require([c['id'] for c in gallery['charts']]==[c['id'] for c in catalog],'Chart catalog mismatch')
    for chart in gallery['charts']:
        for backend in ('python','matlab'):
            output=chart['outputs'][backend];p=DOCS/output['path']
            require(p.is_file() and (DOCS/output['preview']).is_file(),'Missing chart output')
            require(hashlib.sha256(p.read_bytes()).hexdigest()==output['sha256'],'Chart output hash mismatch')
            if backend=='python':require(p.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n','Invalid PNG signature')
            else:
                meta=inspect_emf(p);require(meta['records']>100,'Insufficient native EMF records')
                require(meta['embeddedRasterRecords']==0,'Embedded raster layer in EMF demonstration')
    video=manifest['video']
    for key in ('src','poster','captions'):require((DOCS/video[key]).is_file(),'Missing chart video resource')
    require(20<video['duration']<120,'Unexpected chart video duration')
    print(json.dumps({'status':'pass','chartFamilies':len(catalog),'nativeOutputs':len(catalog)*2,'siteAssets':len(assets),'documentArtifacts':0,'skillSha256':manifest['sha256']},indent=2))


if __name__=='__main__':main()
