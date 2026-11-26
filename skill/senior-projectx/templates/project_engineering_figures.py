"""Build six decision-specific Project figures from checked engineering evidence."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re

import numpy as np


HERE = Path(__file__).resolve().parent
PALETTE = json.loads((HERE / 'research_figure_palette.json').read_text(encoding='utf-8'))['colors']
AXIS_PT, TICK_PT = 10.0, 8.5
LATIN, CJK = 'Times New Roman', 'Microsoft YaHei'
CJK_RUN = re.compile(r'[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]+')
EPS = 1e-9


def choose(locale):
    return lambda zh, en: zh if locale == 'zh' else en


def numeric(value, name, *, minimum=None):
    raw = np.asarray(value, dtype=object)
    if not raw.size or not all(type(v) in (int, float) for v in raw.flat):
        raise ValueError(f'{name} requires finite numbers')
    output = np.asarray(value, dtype=float)
    if not np.isfinite(output).all() or (minimum is not None and (output < minimum).any()):
        raise ValueError(f'Invalid value or unit range in {name}')
    return float(output) if output.ndim == 0 else output


def scalar(value, name, *, minimum=None):
    number = numeric(value, name, minimum=minimum)
    if type(number) is not float:
        raise ValueError(f'{name} must be a scalar')
    return number


def rows(case, key):
    result = case[key]
    if not isinstance(result, list) or not result or any(not isinstance(row, dict) for row in result):
        raise ValueError(f'{key} must contain one or more records')
    return result


def identifier(value, name):
    if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
        raise ValueError(f'{name} requires a non-empty single-line string')
    return value


def unique_ids(records, key='id'):
    values = [identifier(row[key], key) for row in records]
    if len(values) != len(set(values)):
        raise ValueError(f'Duplicate {key}; resolve identities before comparison')
    return values


def padded(start, end, lower=.06, upper=.12):
    spread = max(end - start, abs(start) * .06, abs(end) * .06, .1)
    return [start - lower * spread, end + upper * spread]


def panel(position, xlim, ylim, *, xlabel='', ylabel='', xtick=None, ytick=None,
          xticklabels=None, yticklabels=None, grid='y', axis=True):
    return {'position': position, 'xlim': xlim, 'ylim': ylim, 'xlabel': xlabel, 'ylabel': ylabel,
            'xtick': xtick, 'ytick': ytick, 'xticklabels': xticklabels, 'yticklabels': yticklabels,
            'xtick_explicit': xtick is not None, 'ytick_explicit': ytick is not None,
            'grid': grid, 'axis': axis, 'layers': []}


def key(position):
    return panel(position, [0, 1], [0, 1], axis=False, grid='')


def add(a, kind, x, y, **attributes):
    a['layers'].append({'kind': kind, 'x': x, 'y': y, **attributes})


def line(a, x, y, color='ink', width=1.0, style='-'):
    add(a, 'line', x, y, color=color, width=width, style=style)


def rect(a, left, right, bottom, top, face, edge='none', width=.65):
    add(a, 'polygon', [left, right, right, left], [bottom, bottom, top, top],
        face=face, edge=edge, width=width)


def points(a, x, y, *, marker='o', face='paper', edge='ink', size=4.4, width=.8):
    add(a, 'points', np.atleast_1d(x), np.atleast_1d(y), marker=marker,
        face=face, edge=edge, size=size, width=width)


def label(a, x, y, value, *, align='left', size=TICK_PT, color='ink'):
    add(a, 'text', x, y, label=value, align=align, size=size, color=color)


def step_line(a, edges, values, color='ink', width=1.0, style='-'):
    line(a, np.repeat(edges, 2)[1:-1], np.repeat(values, 2), color, width, style)


def legend_strip(entries):
    a = key([.105, .877, .86, .075])
    for x, role, style, title in entries:
        line(a, [x, x + .047], [.42, .42], role, 1.45, style)
        label(a, x + .064, .42, title)
    return a


def duration(case, tr):
    intervals = rows(case, 'intervals')
    unique_ids(intervals)
    hours = numeric([row['hours'] for row in intervals], 'hours', minimum=0)
    if (hours <= 0).any():
        raise ValueError('All represented intervals must have positive hours')
    base = numeric([row['baseline_kw'] for row in intervals], 'baseline_kw')
    candidate = numeric([row['candidate_kw'] for row in intervals], 'candidate_kw')
    cap = scalar(case['capacity_kw'], 'capacity_kw')
    stages = []
    for series, role, style in [(base, 'cobalt', '-.'), (candidate, 'jade', '-')]:
        order = np.argsort(-series, kind='stable')
        lengths = hours[order]
        edges = np.r_[0, np.cumsum(lengths)]
        excess = np.maximum(series[order] - cap, 0)
        excess[excess <= EPS] = 0
        stages.append((series[order], edges, np.r_[0, np.cumsum(excess * lengths)],
                       float(lengths[excess > 0].sum()), role, style))

    horizon = float(hours.sum())
    above_hours = [stage[3] for stage in stages]
    energy = [float(stage[2][-1]) for stage in stages]
    limit = max(above_hours)
    view_end = min(horizon, max(horizon * .16, limit * 1.22))
    a = panel([.11, .183, .47, .65], [0, horizon], padded(min(base.min(), candidate.min(), cap), max(base.max(), candidate.max(), cap)),
              xlabel=tr('负荷持续时长 / h', 'Load duration / h'), ylabel=tr('负荷 / kW', 'Load / kW'))
    b = panel([.705, .183, .255, .65], [0, view_end], [0, max(.1, max(energy) * 1.12)],
              xlabel=tr('高负荷时长 / h', 'Highest-load hours / h'), ylabel=tr('超限电量 / kWh', 'Energy above limit / kWh'))
    line(a, [0, horizon], [cap, cap], style='--')
    for series, edges, excess_energy, excess_hours, role, style in stages:
        step_line(a, edges, series, role, 1.45, style)
        line(b, edges, excess_energy, role, 1.45, style)
        points(b, excess_hours, excess_energy[-1], edge=role, marker='s' if role == 'cobalt' else 'o')
    legend = legend_strip([(.0, 'cobalt', '-.', tr('基准负荷', 'Baseline')),
                           (.30, 'jade', '-', tr('调节后负荷', 'After dispatch')),
                           (.65, 'ink', '--', tr('容量上限', 'Capacity limit'))])
    return [a, b, legend], {'observed_hours': horizon, 'capacity_kw': cap,
                             'above_cap_hours': above_hours, 'above_cap_kwh': energy,
                             'order': ['baseline', 'candidate']}, .59


def saturation(case, tr):
    days = rows(case, 'days')
    dates = unique_ids(days, 'date')
    chronological = [date.fromisoformat(day) for day in dates]
    if chronological != sorted(chronological):
        raise ValueError('days must be in ascending calendar order')
    capacity = scalar(case['capacity_kw'], 'capacity_kw')
    near = scalar(case['near_kw'], 'near_kw', minimum=0)
    count = len(days)
    if not all(isinstance(row['load_kw'], list) and len(row['load_kw']) == 24 for row in days):
        raise ValueError('Each day requires 24 local hourly values; use null for an unavailable hour')
    if not any(v is not None for row in days for v in row['load_kw']):
        raise ValueError('Calendar cannot show saturation without an observed hour')
    y = np.arange(1, count + 1)
    labels = [value[5:] for value in dates[::-1]]
    if len({day[0:4] for day in dates}) > 1:
        labels = [value[2:] for value in dates[::-1]]
    stride = max(1, int(np.ceil(count / 17)))
    a = panel([.106, .152, .62, .675], [-.5, 23.5], [.5, count + .5], xlabel=tr('当地时刻 / h', 'Local hour / h'),
              xtick=np.arange(0, 24, 3), ytick=y[::stride], yticklabels=labels[::stride], grid='')
    b = panel([.762, .152, .195, .675], [0, 24], [.5, count + .5], ytick=[], xtick=[0, 8, 16, 24],
              xlabel=tr('时长 / h', 'Hours / h'), grid='x')
    category = [('raspberry', 'raspberry_wash', 's'), ('iris', 'iris_wash', 'o'),
                ('jade', 'jade_wash', ''), ('ink', 'grid', 'x')]
    daily = []
    for row, yy in zip(days, y[::-1]):
        counts = np.zeros(4, dtype=int)
        for hh, value in enumerate(row['load_kw']):
            kind = 3
            if value is not None:
                margin = capacity - scalar(value, 'load_kw')
                kind = 0 if margin < -EPS else 1 if margin < near else 2
            counts[kind] += 1
            role, wash, marker = category[kind]
            rect(a, hh - .5, hh + .5, yy - .5, yy + .5, wash, 'paper', .3)
            if marker:
                points(a, hh, yy, marker=marker, edge=role, size=3.35)
        running = 0
        for n, (role, _, _) in zip(counts, category):
            if n:
                rect(b, running, running + n, yy - .30, yy + .30, role, 'paper', .35)
            running += n
        daily.append(counts)
    legend = key([.105, .868, .855, .064])
    headings = [tr('超限', 'Over limit'), tr('低余量', 'Low headroom'), tr('余量充足', 'Adequate'), tr('缺测', 'Missing')]
    for x, (role, wash, marker), title in zip([0, .24, .52, .79], category, headings):
        if marker:
            points(legend, x + .012, .50, marker=marker, edge=role, size=5.1)
        else:
            rect(legend, x, x + .027, .20, .80, wash, role)
        label(legend, x + .038, .50, title)
    return [a, b, legend], {'dates': dates, 'capacity_kw': capacity, 'near_kw': near,
                             'daily_hours': daily, 'order': ['above_cap', 'near', 'adequate', 'missing']}, max(.60, .37 + count * .022)


def energy_bridge(case, tr):
    components = rows(case, 'components')
    names = unique_ids(components, 'label')
    opening = scalar(case['baseline_kwh'], 'baseline_kwh', minimum=0)
    closing = scalar(case['candidate_kwh'], 'candidate_kwh', minimum=0)
    tolerance = scalar(case.get('reconciliation_tolerance_kwh', 1e-6), 'reconciliation_tolerance_kwh', minimum=0)
    changes = numeric([row['delta_kwh'] for row in components], 'delta_kwh')
    shift = np.r_[0, np.cumsum(changes)]
    residual = closing - opening - shift[-1]
    if abs(residual) > tolerance:
        raise ValueError(f'Energy budget does not reconcile: residual {residual:.8g} kWh')
    lo, hi = padded(min(shift), max(shift), .24, .24)
    total = len(components) + 1
    a = panel([.11, .175, .515, .64], [.48, total + .52], [lo, hi], ylabel=tr('相对基准的变化 / kWh', 'Change vs baseline / kWh'),
              xtick=np.arange(1, total + 1), xticklabels=[str(i) for i in range(1, total)] + [tr('净变化', 'Net')])
    line(a, [.5, total + .5], [0, 0], style='--')
    for i, (before, after, delta) in enumerate(zip(shift, shift[1:], changes), 1):
        role, wash = ('jade', 'jade_wash') if delta < 0 else ('cobalt', 'cobalt_wash')
        rect(a, i - .30, i + .30, min(before, after), max(before, after), wash, role, 1.1)
        line(a, [i + .30, i + .70], [after, after], style=':')
        if delta == 0:
            points(a, i, before, edge=role, size=4.4)
    rect(a, total - .30, total + .30, min(0, shift[-1]), max(0, shift[-1]), 'iris_wash', 'ink', 1.0)
    if shift[-1] == 0:
        points(a, total, 0, marker='d', face='sun')
    side = key([.69, .176, .272, .64])
    label(side, 0, 1.015, tr('电网购电量 / kWh', 'Grid energy / kWh'), size=AXIS_PT)
    for ypos, wording, value in [(.87, tr('基准', 'Baseline'), opening), (.74, tr('调节后', 'After dispatch'), closing)]:
        label(side, 0, ypos, wording)
        label(side, .99, ypos, f'{value:.5g}', align='right')
    line(side, [0, .99], [.644, .644], 'grid', .75)
    for i, (wording, delta) in enumerate(zip(names, changes), 1):
        ypos = .61 - i * (.48 / max(5, len(names)))
        label(side, 0, ypos, f'{i:02d}  {wording}')
        label(side, .99, ypos, f'{delta:+.4g}', align='right')
    return [a, side], {'baseline_kwh': opening, 'candidate_kwh': closing,
                        'components_kwh': dict(zip(names, changes)), 'net_kwh': float(shift[-1]),
                        'residual_kwh': residual, 'tolerance_kwh': tolerance}, max(.59, .38 + len(names) * .033)


def rebound(case, tr):
    edges = numeric(case['bin_edges_h'], 'bin_edges_h')
    event_end = scalar(case['event_end_h'], 'event_end_h')
    recovery_end = scalar(case['recovery_end_h'], 'recovery_end_h')
    if edges.ndim != 1 or len(edges) < 3 or not np.all(np.diff(edges) > 0):
        raise ValueError('bin_edges_h must be strictly increasing')
    if not 0 < event_end < recovery_end or not all(np.isclose(edges, edge, atol=EPS, rtol=0).any() for edge in [0, event_end, recovery_end]):
        raise ValueError('Control and recovery boundaries must be exact input bin edges')
    pairs = rows(case, 'pairs')
    ids = unique_ids(pairs)
    original = numeric([row['reference_kw'] for row in pairs], 'reference_kw')
    control = numeric([row['controlled_kw'] for row in pairs], 'controlled_kw')
    if original.shape != (len(pairs), len(edges) - 1) or control.shape != original.shape:
        raise ValueError('Paired reference and controlled profiles must match the declared bins')
    widths = np.diff(edges)
    event = (edges[:-1] >= -EPS) & (edges[1:] <= event_end + EPS)
    recovery = (edges[:-1] >= event_end - EPS) & (edges[1:] <= recovery_end + EPS)
    delta = control - original
    reduced = -(delta[:, event] * widths[event]).sum(axis=1)
    returned = (delta[:, recovery] * widths[recovery]).sum(axis=1)
    yl = padded(min(0, delta.min()), max(0, delta.max()), .10, .18)
    limits = padded(min(0, reduced.min(), returned.min()), max(0, reduced.max(), returned.max()), .065, .13)
    a = panel([.11, .177, .475, .657], [edges[0], edges[-1]], yl,
              xlabel=tr('相对启动时刻 / h', 'Time since event start / h'), ylabel=tr('控制后减基准功率 / kW', 'Controlled minus baseline / kW'))
    b = panel([.714, .177, .245, .657], limits, limits,
              xlabel=tr('净削减电量 / kWh', 'Net reduction / kWh'), ylabel=tr('净回补电量 / kWh', 'Net return / kWh'))
    rect(a, 0, event_end, *yl, 'cobalt_wash')
    rect(a, event_end, recovery_end, *yl, 'raspberry_wash')
    line(a, [edges[0], edges[-1]], [0, 0], style='--')
    for row in delta:
        step_line(a, edges, row, 'grid', .60)
    step_line(a, edges, delta.mean(axis=0), 'ink', 1.6)
    line(b, limits, limits, 'ink', .85, '--')
    points(b, reduced, returned, edge='cobalt', size=4.5)
    points(b, reduced.mean(), returned.mean(), marker='d', face='sun', edge='ink', size=6.0)
    legend = key([.11, .876, .85, .063])
    for x, role, title in [(0, 'cobalt_wash', tr('控制窗口', 'Control')), (.20, 'raspberry_wash', tr('回补窗口', 'Recovery'))]:
        rect(legend, x, x + .043, .26, .74, role, 'grid')
        label(legend, x + .056, .5, title)
    line(legend, [.40, .445], [.5, .5], 'ink', 1.55)
    label(legend, .457, .5, tr('均值轨迹', 'Mean trace'))
    points(legend, .631, .5, marker='d', face='sun', edge='ink', size=5.8)
    label(legend, .655, .5, tr('均值坐标', 'Mean pair'))
    line(legend, [.81, .855], [.5, .5], style='--')
    label(legend, .867, .5, tr('等量回补线', 'Full return'))
    return [a, b, legend], {'pairs': ids, 'event_window_h': [0, event_end], 'recovery_window_h': [event_end, recovery_end],
                            'net_reduced_kwh': reduced, 'net_returned_kwh': returned}, .60


def hysteresis(case, tr):
    samples = rows(case, 'samples')
    t = numeric([row['time_h'] for row in samples], 'time_h')
    temp = numeric([row['temperature_c'] for row in samples], 'temperature_c')
    power = numeric([row['power_kw'] for row in samples], 'power_kw', minimum=0)
    active = [row['cooling'] for row in samples]
    if len(t) < 3 or not np.all(np.diff(t) > 0) or any(type(v) is not bool for v in active):
        raise ValueError('Provide at least three increasing time samples with measured boolean states')
    active = np.asarray(active)
    start = scalar(case['on_threshold_c'], 'on_threshold_c')
    stop = scalar(case['off_threshold_c'], 'off_threshold_c')
    if start <= stop:
        raise ValueError('Cooling start threshold must exceed the stop threshold')
    on = np.flatnonzero(active[1:] & ~active[:-1]) + 1
    off = np.flatnonzero(~active[1:] & active[:-1]) + 1
    first, last = (off[0], off[1]) if off.size >= 2 and np.any((on > off[0]) & (on < off[1])) else (0, len(t) - 1)
    view = slice(first, last + 1)
    xl = padded(min(temp.min(), stop), max(temp.max(), start))
    yl = padded(power.min(), power.max(), .15, .15)
    tl = [t[0], t[-1]]
    a = panel([.11, .157, .395, .696], xl, yl, xlabel=tr('室温 / °C', 'Indoor temperature / °C'),
              ylabel=tr('负荷 / kW', 'Power / kW'))
    b = panel([.639, .520, .313, .333], tl, xl, xtick=[], ylabel=tr('室温 / °C', 'Temperature / °C'))
    c = panel([.639, .157, .313, .271], tl, yl, xlabel=tr('采样时刻 / h', 'Sample time / h'), ylabel=tr('负荷 / kW', 'Power / kW'))
    rect(a, stop, start, *yl, 'iris_wash')
    rect(b, *tl, stop, start, 'iris_wash')
    for threshold in [stop, start]:
        line(a, [threshold, threshold], yl, 'iris', .8, ':')
        line(b, tl, [threshold, threshold], 'iris', .8, ':')
    for enabled, role, style in [(True, 'raspberry', '-'), (False, 'cobalt', '-.')]:
        indexes = np.flatnonzero(active[view] == enabled)
        for run in np.split(indexes, np.flatnonzero(np.diff(indexes) != 1) + 1):
            if not len(run):
                continue
            low = first + run[0]
            high = min(last, first + run[-1] + 1)
            line(a, temp[low:high + 1], power[low:high + 1], role, 1.4, style)
            if high > low:
                midpoint = (low + high) // 2
                if abs(temp[high] - temp[low]) > .04:
                    points(a, temp[midpoint], power[midpoint], marker='>' if temp[high] > temp[low] else '<',
                           face=role, edge=role, size=5.2)
    line(b, t, temp, 'ink', 1.25)
    step_line(c, t, power[:-1], 'ink', 1.15)
    for sequence, role, marker in [(on, 'raspberry', 's'), (off, 'cobalt', 'o')]:
        visible = sequence[(sequence >= first) & (sequence <= last)]
        points(a, temp[visible], power[visible], marker=marker, edge=role)
        points(b, t[sequence], temp[sequence], marker=marker, edge=role)
        points(c, t[sequence], power[sequence], marker=marker, edge=role, size=3.5)
    legend = legend_strip([(.0, 'cobalt', '-.', tr('停机段', 'Cooling off')),
                           (.31, 'raspberry', '-', tr('运行段', 'Cooling on')),
                           (.62, 'iris', ':', tr('配置阈值', 'Configured thresholds'))])
    return [a, b, c, legend], {'observed_on': [{'time_h': t[i], 'temperature_c': temp[i]} for i in on],
                              'observed_off': [{'time_h': t[i], 'temperature_c': temp[i]} for i in off],
                              'on_threshold_c': start, 'off_threshold_c': stop, 'left_trace_window_h': [t[first], t[last]]}, .60


def pareto(case, tr):
    records = rows(case, 'candidates')
    ids = unique_ids(records)
    cost = numeric([row['daily_cost'] for row in records], 'daily_cost', minimum=0)
    energy = numeric([row['unserved_kwh_per_day'] for row in records], 'unserved_kwh_per_day', minimum=0)
    groups = np.asarray([identifier(row['family'], 'family') for row in records])
    group_order = list(dict.fromkeys(groups))
    currency = identifier(case['currency'], 'currency')
    cap_cost = scalar(case['cost_cap'], 'cost_cap', minimum=0)
    cap_energy = scalar(case['unserved_cap_kwh_per_day'], 'unserved_cap_kwh_per_day', minimum=0)
    frontier = np.asarray([i for i, (x, y) in enumerate(zip(cost, energy))
                           if not np.any((cost <= x) & (energy <= y) & ((cost < x) | (energy < y)))])
    frontier = frontier[np.argsort(cost[frontier], kind='stable')]
    viable = np.flatnonzero((cost <= cap_cost) & (energy <= cap_energy))
    chosen = min(viable, key=lambda i: (cost[i], energy[i], ids[i])) if len(viable) else None
    xl = padded(min(cost.min(), cap_cost), max(cost.max(), cap_cost))
    yl = padded(min(energy.min(), cap_energy), max(energy.max(), cap_energy))
    a = panel([.113, .169, .574, .665], xl, yl, xlabel=tr(f'日成本 / {currency}', f'Daily cost / {currency}'),
              ylabel=tr('未供电量 / kWh/day', 'Unserved energy / kWh/day'))
    rect(a, max(0, xl[0]), cap_cost, max(0, yl[0]), cap_energy, 'jade_wash')
    line(a, [cap_cost, cap_cost], yl, style=':')
    line(a, xl, [cap_energy, cap_energy], style=':')
    side = key([.75, .152, .215, .70])
    label(side, 0, .99, tr('方案类别', 'Plan family'), size=AXIS_PT)
    roles = ['cobalt', 'iris', 'raspberry', 'jade', 'ink']
    markers = ['o', 's', '^', 'v', 'P']
    for index, group in enumerate(group_order):
        subset = groups == group
        role, marker = roles[index % len(roles)], markers[(index + index // len(roles)) % len(markers)]
        points(a, cost[subset], energy[subset], marker=marker, edge=role, size=4.2)
        ypos = .858 - index * (.54 / max(len(group_order), 4))
        points(side, .043, ypos, marker=marker, edge=role, size=4.9)
        label(side, .119, ypos, group)
    line(a, cost[frontier], energy[frontier], 'ink', 1.0, '--')
    line(side, [0, .095], [.286, .286], 'ink', 1.0, '--')
    label(side, .119, .286, tr('非支配边界', 'Nondominated'))
    if chosen is not None:
        points(a, cost[chosen], energy[chosen], marker='d', face='sun', edge='ink', size=6.6)
        points(side, .043, .167, marker='d', face='sun', edge='ink', size=5.8)
        label(side, .119, .167, tr('达标的最低成本', 'Least cost within limits'))
        label(side, .119, .031, ids[chosen])
    else:
        label(side, .0, .155, tr('无达标方案', 'No plan meets both limits'))
    return [a, side], {'nondominated_ids': [ids[i] for i in frontier], 'cost_cap': cap_cost,
                        'unserved_cap_kwh_per_day': cap_energy, 'feasible_ids': [ids[i] for i in viable],
                        'least_cost_feasible': ids[chosen] if chosen is not None else None,
                        'currency': currency}, max(.60, .39 + len(group_order) * .049)


BUILDERS = {'duration': duration, 'saturation': saturation, 'energy-bridge': energy_bridge,
            'rebound': rebound, 'hysteresis': hysteresis, 'pareto': pareto}


def serialize(value):
    if isinstance(value, (np.ndarray, np.generic)):
        return value.tolist()
    raise TypeError(type(value).__name__)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False, default=serialize) + '\n', encoding='utf-8')


def build_plan(kind, case, locale='zh', width_mm=166):
    if not isinstance(case, dict):
        raise ValueError('Input must be a JSON object')
    scope = identifier(case['scope'], 'scope')
    panels, evidence, aspect = BUILDERS[kind](case, choose(locale))
    return {'schema': 'projectx.engineering-figure.v1', 'type': kind, 'locale': locale,
            'canvas_mm': [width_mm, width_mm * aspect], 'scope': scope,
            'fonts': {'cjk': CJK, 'latin': LATIN, 'axis_pt': AXIS_PT, 'tick_pt': TICK_PT},
            'palette': PALETTE, 'panels': panels, 'evidence': evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('type', choices=BUILDERS)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path, help='JSON input with caller-supplied evidence')
    source.add_argument('--example', action='store_true', help='Render the explicitly synthetic teaching fixture')
    parser.add_argument('--output', type=Path, help='Matplotlib PNG or vector PDF')
    parser.add_argument('--plan', type=Path, help='Geometry and evidence JSON usable by the native MATLAB backend')
    parser.add_argument('--locale', default='zh', choices=['zh', 'en'])
    parser.add_argument('--width-mm', type=float, default=166)
    args = parser.parse_args()
    if not (args.output or args.plan):
        parser.error('Choose --output, --plan, or both')
    if not np.isfinite(args.width_mm) or args.width_mm <= 0:
        parser.error('--width-mm must be finite and positive')
    if args.output and args.output.suffix.lower() not in {'.png', '.pdf'}:
        parser.error('--output must end in .png or .pdf')
    try:
        if args.example:
            raw = (HERE / 'project-engineering-examples.json').read_bytes()
            case = json.loads(raw)[args.type][args.locale]
        else:
            raw = args.input.read_bytes()
            case = json.loads(raw)
        plan = build_plan(args.type, case, args.locale, args.width_mm)
        plan['input_sha256'] = hashlib.sha256(raw).hexdigest()
        plan['source_kind'] = 'synthetic_example' if args.example else 'caller_input'
        if args.output:
            from project_engineering_render import export as render
            render(plan, args.output)
        if args.plan:
            save_json(args.plan, plan)
    except (ValueError, TypeError, OSError, KeyError, RuntimeError) as error:
        parser.exit(2, f'Figure generation stopped: {error}\n')


if __name__ == '__main__':
    main()
