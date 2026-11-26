"""Prepare language-specific previews and native-file metadata."""
import argparse
import hashlib,json
from PIL import Image, ImageOps
from prepare_gallery import ROOT,CATALOG,inspect_emf


def save_preview(image, destination, size, quality):
    # Fit a single scale to the source, including the rounded EMF pixel bounds.
    fitted = ImageOps.pad(image.convert('RGB'), size, Image.Resampling.LANCZOS, color='white')
    fitted.save(destination, 'WEBP', quality=quality, method=6)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--charts',nargs='+',help='Regenerate only selected chart previews from their existing native files')
    args=parser.parse_args()
    selected=set(args.charts or [chart['id'] for chart in CATALOG])
    unknown=selected-{chart['id'] for chart in CATALOG}
    if unknown:
        parser.error(f"Unknown charts: {', '.join(sorted(unknown))}")
    manifest_path=ROOT/'docs/gallery.json'
    previous=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    old_charts={chart['id']:chart for chart in previous.get('charts',[])}
    manifest={'data':['gallery/demo-data.json','gallery/extra-data.json','gallery/engineering-data.json'],'source':'independent illustrative data','languages':['zh','en'],
      'fontPolicy':{'chinese':'Microsoft YaHei Bold','latinAndNumerals':'Times New Roman Regular'},'charts':[]}
    for chart in CATALOG:
        slug=chart['id'];item={**chart,'languages':{}}
        if slug not in selected:
            if slug not in old_charts:
                parser.error(f"Chart {slug!r} has no existing preview. Add it to --charts.")
            item.update({field:old_charts[slug][field] for field in ('languages','outputs')})
            manifest['charts'].append(item)
            continue
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
                    save_preview(image, preview_file, (1440, 864), 92)
                output={'path':source.relative_to(ROOT/'docs').as_posix(),'format':suffix.upper(),'bytes':source.stat().st_size,
                  'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'preview':preview_file.relative_to(ROOT/'docs').as_posix()}
                if backend=='matlab':
                    output.update(inspect_emf(source));detail_file=detail/('matlab-'+slug+'.webp')
                    with Image.open(source) as image:
                        image.load(dpi=240)
                        save_preview(image, detail_file, (2400, 1440), 95)
                    output['detailPreview']=detail_file.relative_to(ROOT/'docs').as_posix()
                outputs[backend]=output
            item['languages'][language]=outputs
        item['outputs']=item['languages']['en'];manifest['charts'].append(item)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'chartTypes':len(CATALOG),'languages':2,'nativeOutputs':len(CATALOG)*4}))

if __name__=='__main__':main()
