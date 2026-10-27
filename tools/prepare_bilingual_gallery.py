"""Prepare language-specific previews and native-file metadata."""
from pathlib import Path
import hashlib,json
from PIL import Image
from prepare_gallery import ROOT,CATALOG,inspect_emf

def main():
    manifest={'data':['gallery/demo-data.json','gallery/extra-data.json'],'source':'independent illustrative data','languages':['zh','en'],
      'fontPolicy':{'chinese':'Microsoft YaHei Bold','latinAndNumerals':'Times New Roman Regular'},'charts':[]}
    for chart in CATALOG:
        slug=chart['id'];item={**chart,'languages':{}}
        for language in ['en','zh']:
            outputs={}
            for backend,suffix in [('python','png'),('matlab','emf')]:
                source=ROOT/f'docs/downloads/figures/{backend}'
                preview=ROOT/'docs/assets/charts';detail=preview/'detail'
                if language=='zh':source/='zh';preview/='zh';detail/='zh'
                source/=slug+'.'+suffix;preview.mkdir(parents=True,exist_ok=True);detail.mkdir(parents=True,exist_ok=True)
                preview_file=preview/(backend+'-'+slug+'.webp')
                with Image.open(source) as image:
                    if backend=='matlab':image.load(dpi=150)
                    image.convert('RGB').resize((1440,864),Image.Resampling.LANCZOS).save(preview_file,'WEBP',quality=92,method=6)
                output={'path':source.relative_to(ROOT/'docs').as_posix(),'format':suffix.upper(),'bytes':source.stat().st_size,
                  'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'preview':preview_file.relative_to(ROOT/'docs').as_posix()}
                if backend=='matlab':
                    output.update(inspect_emf(source));detail_file=detail/('matlab-'+slug+'.webp')
                    with Image.open(source) as image:
                        image.load(dpi=240);image.convert('RGB').resize((2400,1440),Image.Resampling.LANCZOS).save(detail_file,'WEBP',quality=95,method=6)
                    output['detailPreview']=detail_file.relative_to(ROOT/'docs').as_posix()
                outputs[backend]=output
            item['languages'][language]=outputs
        item['outputs']=item['languages']['en'];manifest['charts'].append(item)
    (ROOT/'docs/gallery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'chartTypes':len(CATALOG),'languages':2,'nativeOutputs':len(CATALOG)*4}))

if __name__=='__main__':main()
