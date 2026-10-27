"""Prepare browser previews from native illustrative PNG / EMF chart files."""
from pathlib import Path
import hashlib
import json
import struct
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
CATALOG=json.loads((ROOT/'gallery/catalog.json').read_text(encoding='utf-8'))['charts']
SLUGS=[chart['id'] for chart in CATALOG]


def inspect_emf(file):
    payload=file.read_bytes()
    if payload[40:44]!=b' EMF':raise ValueError('Invalid EMF signature: '+file.name)
    offset=0;records=0;embedded_raster=0
    while offset+8<=len(payload):
        kind,size=struct.unpack_from('<II',payload,offset)
        if size<8 or offset+size>len(payload):raise ValueError('Invalid EMF record')
        # BITBLT can clear a vector drawing without carrying a source bitmap.
        if kind==76 and size>=100:
            embedded_raster+=int(struct.unpack_from('<I',payload,offset+96)[0]>0)
        elif kind in {77,78,79,80,81,114,116}:
            embedded_raster+=1
        offset+=size;records+=1
    if offset!=len(payload):raise ValueError('Incomplete EMF record sequence')
    return {'records':records,'embeddedRasterRecords':embedded_raster}


def main():
    previews=ROOT/'docs/assets/charts';previews.mkdir(parents=True,exist_ok=True)
    detail=previews/'detail';detail.mkdir(parents=True,exist_ok=True)
    manifest={'data':['gallery/demo-data.json','gallery/extra-data.json'],'source':'independent illustrative data','charts':[]}
    for chart in CATALOG:
        slug=chart['id']
        item={**chart,'outputs':{}}
        for backend,suffix in [('python','png'),('matlab','emf')]:
            file=ROOT/f'docs/downloads/figures/{backend}/{slug}.{suffix}'
            with Image.open(file) as image:
                if backend=='matlab':image.load(dpi=150)
                image.convert('RGB').resize((1440,864),Image.Resampling.LANCZOS).save(previews/f'{backend}-{slug}.webp','WEBP',quality=92,method=6)
            output={'path':file.relative_to(ROOT/'docs').as_posix(),'format':suffix.upper(),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'preview':f'assets/charts/{backend}-{slug}.webp'}
            if backend=='matlab':output.update(inspect_emf(file))
            if backend=='matlab':
                with Image.open(file) as image:
                    image.load(dpi=240)
                    image.convert('RGB').resize((2400,1440),Image.Resampling.LANCZOS).save(detail/f'matlab-{slug}.webp','WEBP',quality=95,method=6)
                output['detailPreview']=f'assets/charts/detail/matlab-{slug}.webp'
            item['outputs'][backend]=output
        manifest['charts'].append(item)
    (ROOT/'docs/gallery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'chartTypes':len(SLUGS),'nativeOutputs':len(SLUGS)*2,'status':'pass'}))


if __name__=='__main__':main()
