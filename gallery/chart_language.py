"""Mixed figure typography: bold Microsoft YaHei CJK and regular Times New Roman."""
from pathlib import Path
import json,re
import matplotlib as mpl
from matplotlib import font_manager
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=json.loads((ROOT/'gallery/figure-language.json').read_text(encoding='utf-8'))
LABELS=dict(REGISTRY['labels'])
CJK=re.compile(r'[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]+')

def configure():
    font_manager.findfont(font_manager.FontProperties(family='Microsoft YaHei',weight='bold'),fallback_to_default=False)
    font_manager.findfont(font_manager.FontProperties(family='Times New Roman',weight='normal'),fallback_to_default=False)
    mpl.rcParams.update({'font.family':'Times New Roman','font.weight':'normal','font.size':12,'axes.unicode_minus':False,
        'mathtext.fontset':'custom','mathtext.rm':'Times New Roman','mathtext.it':'Times New Roman:style=italic',
        'mathtext.bf':'Microsoft YaHei:weight=bold','mathtext.default':'rm','mathtext.fallback':None})

def translate(text,language):
    if language=='en':return text
    value=LABELS.get(text,text)
    if value==text:
        for pattern,replacement in REGISTRY['patterns']:
            value=re.sub(pattern,re.sub(r'\$(\d)',r'\\g<\1>',replacement),value)
    return value

def rich_text(text,language):
    value=translate(text,language)
    return CJK.sub(lambda m:r'$\mathbf{'+m.group()+'}$',value)

def localize_figure(figure,language):
    figure.canvas.draw()
    for axis in figure.axes:
        for coordinate in (axis.xaxis,axis.yaxis):
            for kind in ('major','minor'):
                formatter=getattr(coordinate,'get_'+kind+'_formatter')()
                wrapped=FuncFormatter(lambda value,pos,original=formatter:rich_text(original(value,pos),language))
                getattr(coordinate,'set_'+kind+'_formatter')(wrapped)
    records=[]
    for artist in figure.findobj(match=Text):
        text=artist.get_text()
        artist.set_fontfamily('Times New Roman');artist.set_fontweight('normal');artist.set_fontstyle('normal')
        if text:
            localized=rich_text(text,language);artist.set_text(localized)
            records.append({'source':text,'localized':translate(text,language),'rendered':localized})
    figure.canvas.draw()
    return records
