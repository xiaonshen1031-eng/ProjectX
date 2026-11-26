"""Render the static, browsable atlas from its bilingual chart catalog."""

import argparse
from html import escape
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'docs/index.html'
START = '<!-- atlas cards -->'
END = '<!-- end atlas cards -->'
FAMILIES = {
    'time': '时序与调度', 'distribution': '分布比较',
    'relation': '关联与构成', 'space': '空间与约束', 'evaluation': '评估对比',
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def render_card(chart, english):
    chart_id = chart['id']
    family = chart['family']
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', chart_id):
        raise ValueError(f'Invalid chart ID: {chart_id}')
    if chart.get('source') == 'engineering':
        matlab = 'build_matlab_engineering.m'
        python = 'build_python_engineering.py'
    else:
        matlab = 'build_matlab_extra.m' if chart.get('extra') else 'build_matlab.m'
        python = 'build_bilingual.py'
    fields = {'family': family, 'python-source': python, 'matlab-source': matlab}
    for language, copy in [('zh', chart), ('en', english)]:
        for field in ('title', 'description', 'tags'):
            fields[f'{field}-{language}'] = copy[field]
    attributes = ' '.join(f'data-{name}="{escape(value)}"' for name, value in fields.items())
    title = escape(chart['title'])
    png = f'downloads/figures/python/zh/{chart_id}.png'
    return f'''          <figure class="chart-card" id="chart-{chart_id}" data-chart="{chart_id}" {attributes}>
            <a class="chart-image" data-open href="{png}" aria-label="查看{title}大图">
              <img src="assets/charts/zh/python-{chart_id}.webp" alt="" width="1440" height="864" loading="lazy" decoding="async">
              <span class="expand-mark" aria-hidden="true">↗</span>
            </a>
            <figcaption>
              <p class="chart-family">{FAMILIES[family]}</p>
              <h3>{title}</h3>
              <a class="chart-download" href="{png}" download="{chart_id}-zh.png" aria-label="下载{title}的中文 PNG 原图">PNG <span aria-hidden="true">↓</span></a>
            </figcaption>
          </figure>'''


def render_page(page):
    catalog = read_json(ROOT / 'gallery/catalog.json')['charts']
    english = read_json(ROOT / 'gallery/figure-language.json')['charts']
    if len(catalog) != len({chart['id'] for chart in catalog}) or set(english) != {chart['id'] for chart in catalog}:
        raise ValueError('Chart IDs must be unique and have bilingual metadata')
    before, remainder = page.split(START)
    _, after = remainder.split(END)
    browse_order = sorted(catalog, key=lambda chart: chart.get('source') != 'engineering')
    cards = '\n'.join(render_card(chart, english[chart['id']]) for chart in browse_order)
    page = f'{before}{START}\n{cards}\n          {END}{after}'
    for name, value in [('atlas-count', len(catalog)), ('atlas-files', 4 * len(catalog))]:
        page, used = re.subn(rf'(<span data-{name}>)[0-9]+(</span>)', rf'\g<1>{value}\2', page)
        if not used:
            raise ValueError(f'Missing {name} in the page')
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    page = INDEX.read_text(encoding='utf-8')
    rendered = render_page(page)
    if args.check and rendered != page:
        parser.exit(1, 'Site atlas is stale. Run python tools/render_gallery.py.\n')
    if not args.check and rendered != page:
        INDEX.write_text(rendered, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
