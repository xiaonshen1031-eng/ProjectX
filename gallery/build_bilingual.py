"""Export the same independent chart data in Chinese and English."""
from pathlib import Path
import argparse,json
import matplotlib.pyplot as plt
from PIL import Image
import build_python as basic
import build_python_extra as extra
from chart_language import ROOT,configure,localize_figure,REGISTRY

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--language',choices=['zh','en','both'],default='both');parser.add_argument('--charts',nargs='*');args=parser.parse_args()
    configure()
    catalog=json.loads((ROOT/'gallery/catalog.json').read_text(encoding='utf-8'))['charts']
    data=json.loads((ROOT/'gallery/demo-data.json').read_text(encoding='utf-8'));additional=json.loads((ROOT/'gallery/extra-data.json').read_text(encoding='utf-8'))
    languages=['en','zh'] if args.language=='both' else [args.language]
    records=[]
    for language in languages:
        out=ROOT/'docs/downloads/figures/python';preview=ROOT/'docs/assets/charts'
        if language=='zh':out/='zh';preview/='zh'
        out.mkdir(parents=True,exist_ok=True);preview.mkdir(parents=True,exist_ok=True)
        for chart in catalog:
            slug=chart['id']
            if args.charts and slug not in args.charts:continue
            source=extra if chart['extra'] else basic
            fig=getattr(source,slug)((additional if chart['extra'] else data)[slug])
            labels=localize_figure(fig,language)
            path=out/(slug+'.png');fig.savefig(path,dpi=150,facecolor='white');plt.close(fig)
            with Image.open(path) as image:image.resize((1440,864),Image.Resampling.LANCZOS).save(preview/('python-'+slug+'.webp'),'WEBP',quality=92,method=6)
            records.append({'chart':slug,'language':language,'labels':labels})
            print('Python PNG:',language,slug,flush=True)
    audit=ROOT/'work/bilingual-python-labels.json';audit.write_text(json.dumps({'fontPolicy':REGISTRY['fontPolicy'],'charts':records},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
