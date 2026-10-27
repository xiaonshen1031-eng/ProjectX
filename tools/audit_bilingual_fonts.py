"""Inspect rendered Python glyph fonts and native EMF font records."""
from pathlib import Path
import json,re,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'gallery'))
from chart_language import configure,CJK
from matplotlib.mathtext import MathTextParser
from prepare_gallery import inspect_emf

def main():
    configure();parser=MathTextParser('path')
    audit=json.loads((ROOT/'work/bilingual-python-labels.json').read_text(encoding='utf-8'))
    assert len(audit['charts'])==28,'Rebuild all Python language variants before auditing'
    cjk=latin=labels=0
    for chart in audit['charts']:
        for label in chart['labels']:
            for font,size,codepoint,x,y in parser.parse(label['rendered'],dpi=72).glyphs:
                glyph=chr(codepoint)
                if CJK.fullmatch(glyph):
                    assert font.family_name=='Microsoft YaHei' and 'Bold' in font.style_name,'Incorrect CJK glyph font'
                    cjk+=1
                elif glyph.isascii() and glyph.isalnum():
                    assert font.family_name=='Times New Roman' and font.style_name=='Regular','Incorrect Latin / numeric glyph font'
                    latin+=1
            labels+=1
    manifest=json.loads((ROOT/'docs/gallery.json').read_text(encoding='utf-8'))
    files=0
    for chart in manifest['charts']:
        for lang in ['zh','en']:
            png=ROOT/'docs'/chart['languages'][lang]['python']['path']
            with Image.open(png) as image:assert image.size==(2400,1440),'Unexpected PNG canvas'
            meta=inspect_emf(ROOT/'docs'/chart['languages'][lang]['matlab']['path'])
            assert not meta['embeddedRasterRecords'],'Raster payload in native EMF'
            assert any(f['family']=='Times New Roman' and f['weight']==400 for f in meta['fonts'])
            if lang=='zh':assert any(f['family'] in ['Microsoft YaHei','微软雅黑'] and f['weight']==700 for f in meta['fonts'])
            else:assert all(f['family']=='Times New Roman' and f['weight']==400 for f in meta['fonts'])
            files+=2
    result={'status':'pass','nativeFiles':files,'pythonLabelsInspected':labels,'cjkGlyphs':cjk,'latinNumericGlyphs':latin,'fontPolicy':audit['fontPolicy']}
    (ROOT/'work/bilingual-font-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':main()
