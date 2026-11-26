"""Render ProjectX geometry at its physical size using separate glyph fonts."""

from pathlib import Path
import sys

import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, get_font, findfont
from matplotlib.patches import Polygon
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter, MaxNLocator

from project_engineering_figures import CJK_RUN


sys.path.append(str(Path(__file__).resolve().parent.parent / 'scripts'))
from audit_figure_layout import audit_layout


def mixed(text):
    return CJK_RUN.sub(lambda match: r'$\mathbf{' + match.group() + '}$', text.replace('$', r'\$'))


def verify_fonts(plan):
    fonts = plan['fonts']
    found = {}
    for family, weight in [(fonts['latin'], 'normal'), (fonts['cjk'], 'bold')]:
        try:
            path = findfont(FontProperties(family=family, weight=weight), fallback_to_default=False)
        except ValueError as error:
            raise ValueError(f'Figure requires installed {family} {weight}') from error
        face = get_font(path)
        if face.family_name != family or (weight == 'bold' and 'Bold' not in face.style_name) or (weight == 'normal' and face.style_name != 'Regular'):
            raise ValueError(f'Expected {family} {weight}, found {face.family_name} {face.style_name}')
        found[weight] = face
    labels = []
    for spec in plan['panels']:
        labels.extend([spec['xlabel'], spec['ylabel'], *(spec['xticklabels'] or []), *(spec['yticklabels'] or [])])
        labels.extend(mark['label'] for mark in spec['layers'] if mark['kind'] == 'text')
    for character in set(''.join(labels)):
        face = found['bold' if CJK_RUN.fullmatch(character) else 'normal']
        if not face.get_char_index(ord(character)):
            raise ValueError(f'{face.family_name} lacks a required glyph {character!r} (U+{ord(character):04X})')


def color(palette, role):
    return 'none' if role == 'none' else palette[role]


def draw_panel(fig, spec, fonts, colors):
    a = fig.add_axes(spec['position'])
    a.set_xlim(spec['xlim'])
    a.set_ylim(spec['ylim'])
    a.set_xlabel(mixed(spec['xlabel']), fontsize=fonts['axis_pt'], labelpad=4)
    a.set_ylabel(mixed(spec['ylabel']), fontsize=fonts['axis_pt'], labelpad=4)
    a.spines[['top', 'right']].set_visible(False)
    for spine in a.spines.values():
        spine.set_color(colors['ink'])
        spine.set_linewidth(.75)
    a.tick_params(labelsize=fonts['tick_pt'], colors=colors['ink'], length=2.5, width=.65, pad=3)
    for axis, key in ((a.xaxis, 'x'), (a.yaxis, 'y')):
        ticks, labels = spec[f'{key}tick'], spec[f'{key}ticklabels']
        if ticks is not None:
            axis.set_ticks(ticks, labels=None if labels is None else [mixed(label) for label in labels])
        else:
            axis.set_major_locator(MaxNLocator(nbins=5 if key == 'y' else 4))
        if labels is None:
            axis.set_major_formatter(FuncFormatter(lambda value, _index: f'{value:.5g}'))
    if spec['grid']:
        a.set_axisbelow(True)
        a.grid(axis=spec['grid'], color=colors['grid'], linewidth=.45)
    if not spec['axis']:
        a.set_axis_off()
    for mark in spec['layers']:
        x, y = mark['x'], mark['y']
        kind = mark['kind']
        if kind == 'line':
            a.plot(x, y, color=colors[mark['color']], lw=mark['width'], ls=mark['style'])
        elif kind == 'polygon':
            a.add_patch(Polygon(list(zip(x, y)), facecolor=color(colors, mark['face']),
                                edgecolor=color(colors, mark['edge']), lw=mark['width']))
        elif kind == 'points':
            a.plot(x, y, linestyle='none', marker='p' if mark['marker'] == 'P' else mark['marker'],
                   markerfacecolor=color(colors, mark['face']), markeredgecolor=colors[mark['edge']],
                   markersize=mark['size'], markeredgewidth=mark['width'])
        else:
            a.text(x, y, mixed(mark['label']), va='center', ha=mark['align'], color=colors[mark['color']],
                   fontsize=mark['size'])


def audit(fig, plan):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px_to_mm = 25.4 / fig.dpi
    height = fig.bbox.height
    objects = []
    names = {}
    for p, axes in enumerate(fig.axes, 1):
        artists = list(axes.texts)
        if axes.axison:
            for axis in [axes.xaxis, axes.yaxis]:
                artists.append(axis.label)
                lo, hi = sorted(axis.get_view_interval())
                artists.extend(tick.label1 for tick in axis.get_major_ticks() if lo <= tick.get_loc() <= hi)
        for text in artists:
            if not isinstance(text, Text) or not text.get_visible() or not text.get_text().strip():
                continue
            bounds = text.get_window_extent(renderer)
            x0, y0, x1, y1 = bounds.extents
            id_ = f'p{p}-t{len(objects) + 1}'
            names[id_] = text.get_text()
            objects.append({'id': id_, 'font_pt': text.get_fontsize(),
                            'bbox_mm': [x0 * px_to_mm, (height-y1) * px_to_mm,
                                        x1 * px_to_mm, (height-y0) * px_to_mm]})
    measures = {'canvas_mm': plan['canvas_mm'], 'minimum_font_pt': 8., 'text': objects}
    result = audit_layout(measures)
    if not result['measurement_checks_passed']:
        errors = '; '.join(result['errors'][:7])
        detail = ', '.join(f'{key}={value}' for key, value in names.items() if key in errors)
        raise ValueError(f'Reflow the figure at {plan["canvas_mm"][0]:g} mm. {errors} ({detail})')


def export(plan, output):
    fonts = plan['fonts']
    verify_fonts(plan)
    with mpl.rc_context({'font.family': fonts['latin'], 'font.weight': 'normal',
                         'mathtext.fontset': 'custom', 'mathtext.rm': fonts['latin'],
                         'mathtext.bf': fonts['cjk'] + ':weight=bold', 'mathtext.default': 'rm',
                         'mathtext.fallback': None, 'axes.unicode_minus': False,
                         'pdf.fonttype': 42, 'savefig.bbox': None}):
        fig = Figure(figsize=[x / 25.4 for x in plan['canvas_mm']], dpi=600, facecolor=plan['palette']['paper'])
        FigureCanvasAgg(fig)
        for spec in plan['panels']:
            draw_panel(fig, spec, fonts, plan['palette'])
        audit(fig, plan)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=600, facecolor=plan['palette']['paper'], bbox_inches=None)
