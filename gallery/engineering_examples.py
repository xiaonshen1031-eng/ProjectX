"""Regenerate illustrative engineering evidence and the shared drawing geometry."""

import argparse
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
DT = 0.25


def panel(position, xlim, ylim, *, xlabel="", ylabel="", xtick=None, ytick=None,
          xticklabels=None, yticklabels=None, grid="", axis=True):
    return {
        "position": position, "xlim": xlim, "ylim": ylim, "xlabel": xlabel, "ylabel": ylabel,
        "xtick": xtick, "ytick": ytick, "xticklabels": xticklabels, "yticklabels": yticklabels,
        "grid": grid, "axis": axis, "layers": [],
    }


def layer(a, kind, x, y, **attrs):
    a["layers"].append({"kind": kind, "x": x, "y": y, **attrs})


def line(a, x, y, color="ink", width=1.5, style="-"):
    layer(a, "line", x, y, color=color, width=width, style=style)


def polygon(a, x, y, face, edge="none", width=0.7):
    layer(a, "polygon", x, y, face=face, edge=edge, width=width)


def rect(a, left, right, bottom, top, face, edge="none", width=0.7):
    polygon(a, [left, right, right, left], [bottom, bottom, top, top], face, edge, width)


def points(a, x, y, *, marker="o", face="white", edge="ink", size=7, width=1.05):
    layer(a, "points", np.atleast_1d(x), np.atleast_1d(y), marker=marker, face=face,
          edge=edge, size=size, width=width)


def text(a, x, y, label, *, size=15, align="left", color="ink"):
    layer(a, "text", x, y, label=label, size=size, align=align, color=color)


def band(a, x, low, high, color):
    polygon(a, np.r_[x, x[::-1]], np.r_[low, high[::-1]], color)


def steps(values, step=1):
    edges = np.arange(len(values) + 1) * step
    return np.repeat(edges, 2)[1:-1], np.repeat(values, 2)


def key(position):
    return panel(position, [0, 1], [0, 1], axis=False)


def shift_examples():
    hours = np.arange(24)
    days = np.arange(14)
    ambient = 2.8 * np.sin(days * 0.62) + 1.3 * np.cos(days * 0.27)
    day_shape = (36 + 14 * np.exp(-((hours - 8) / 2.7)**2)
                 + 26 * np.exp(-((hours - 18) / 4.3)**2)
                 + 14 * np.exp(-((hours - 21) / 3.0)**2))
    baseline = day_shape + ambient[:, None] + 3.7 * np.sin(days[:, None] * .48 + hours *.39)
    cap = 70
    shifted = baseline.copy()
    release = np.minimum(np.maximum(baseline - cap, 0), 3.2)
    movable_hours = hours < 6
    for i, row in enumerate(shifted):
        row -= release[i]
        headroom = np.maximum(cap - row[movable_hours], 0)
        row[movable_hours] += release[i].sum() * headroom / headroom.sum()
    np.testing.assert_allclose(baseline.sum(axis=1), shifted.sum(axis=1))
    return baseline, shifted, cap


def duration():
    base, shifted, cap = shift_examples()
    position = np.arange(base.size + 1) / base.size * 100
    chains = [np.sort(series.ravel())[::-1] for series in [base, shifted]]
    count = [(series > cap + 1e-9).sum() for series in chains]
    excess = [np.r_[0, np.cumsum(np.maximum(series - cap, 0))] for series in chains]

    a = panel([.085, .15, .54, .70], [0, 100], [28, 84], xlabel="Share of hours / %",
              ylabel="Load / kW", xtick=[0, 20, 40, 60, 80, 100], grid="y")
    x, peak = steps(chains[0], 100 / base.size)
    band(a, x, np.full_like(x, cap), np.maximum(peak, cap), "exceedance_wash")
    line(a, [0, 100], [cap, cap], style="--")
    text(a, 55, cap + 2.2, "70 kW capacity", size=13)
    for series, color, style in zip(chains, ["observation", "state"], [":", "-"]):
        xx, yy = steps(series, 100 / base.size)
        line(a, xx, yy, color, 2.25, style)

    xmax = max(20, int(np.ceil(max(count) / base.size * 10) * 10))
    ymax = int(np.ceil(excess[0][-1] / 50) * 50)
    b = panel([.71, .15, .25, .70], [0, xmax], [0, ymax * 1.15],
              xlabel="Share of highest-load hours / %", ylabel="Above-cap energy / kWh",
              xtick=np.arange(0, xmax + 1, 5), grid="y")
    for seq, n, color, style in zip(excess, count, ["observation", "state"], [":", "-"]):
        line(b, position, seq, color, 2.25, style)
        points(b, position[n], seq[n], marker="s" if color == "observation" else "o",
               face="white", edge=color)
        text(b, xmax * .94, seq[n] + ymax * .065, f"{seq[n]:.1f} kWh", align="right", size=13)
        text(b, xmax * .94, seq[n] - ymax * .075, f"{n} h", align="right", size=13)

    legend = key([.09, .873, .86, .075])
    line(legend, [.01, .064], [.5, .5], "observation", 2.25, ":")
    text(legend, .077, .5, "Baseline load")
    line(legend, [.29, .344], [.5, .5], "state", 2.25)
    text(legend, .357, .5, "Shifted load")
    rect(legend, .56, .614, .35, .65, "exceedance_wash", "exceedance")
    text(legend, .627, .5, "Baseline overload")
    return {"data": {"baselineKW": base, "shiftedKW": shifted, "capacityKW": cap, "hoursPerBin": 1,
                     "exceedanceHours": count, "aboveCapKWh": [seq[-1] for seq in excess]},
            "panels": [a, b, legend]}


def saturation():
    base, shifted, capacity = shift_examples()
    margin = capacity - shifted
    near_kw = 4
    overload = margin < -1e-9
    near = (margin < near_kw) & ~overload
    stable = ~overload & ~near
    count = np.stack([overload.sum(axis=1), near.sum(axis=1)], axis=1)

    day = len(margin) - np.arange(len(margin))
    a = panel([.10, .145, .60, .725], [-.5, 23.5], [.5, len(day) + .5], xlabel="Hour of day",
              ylabel="Study day", xtick=np.arange(0, 24, 2), ytick=day[::-1],
              yticklabels=[f"D{i:02d}" for i in day])
    for row, y in enumerate(day):
        for hr in range(24):
            color = "exceedance_wash" if overload[row, hr] else "alternative_wash" if near[row, hr] else "state_wash"
            rect(a, hr - .5, hr + .5, y - .5, y + .5, color, "white")
        for mask, marker, role, size in [(near, "o", "alternative", 4.6),
                                          (overload, "s", "exceedance", 6.6)]:
            hours = np.flatnonzero(mask[row])
            if len(hours):
                points(a, hours, np.full(len(hours), y), marker=marker,
                       face="white" if mask is near else role, edge=role, size=size)

    maximum = int(count.sum(axis=1).max())
    b = panel([.75, .145, .20, .725], [0, maximum + 1], [.5, len(day) + .5], xlabel="Hours per day",
              xtick=np.arange(0, maximum + 1, 2), ytick=[], grid="x")
    for y, (one, two) in zip(day, count):
        if one:
            rect(b, 0, one, y - .28, y + .28, "exceedance")
        if two:
            rect(b, one, one + two, y - .28, y + .28, "alternative")

    legend = key([.10, .895, .84, .060])
    for x, face, edge, marker, label_text in [
        (.02, "exceedance", "exceedance", "s", "Above capacity"),
        (.33, "white", "alternative", "o", "Headroom below 4 kW"),
        (.68, "state_wash", "state", "s", "Headroom at least 4 kW"),
    ]:
        points(legend, x, .5, marker=marker, face=face, edge=edge, size=8.5)
        text(legend, x + .03, .5, label_text)
    return {"data": {"scheduledKW": shifted, "capacityKW": capacity, "headroomKW": margin,
                     "nearThresholdKW": near_kw, "aboveCapacity": overload, "nearCapacity": near,
                     "adequate": stable, "dailyHours": count},
            "panels": [a, b, legend]}


def energy_bridge():
    reference = 1184
    steps_kwh = np.array([-132, 132, -80, 92, -36])
    running = np.r_[0, np.cumsum(steps_kwh)]
    final = reference + running[-1]
    labels = ["Off-peak transfer out", "Off-peak transfer in", "Storage discharge",
              "Grid recharge", "Avoided consumption", "Net grid change"]
    a = panel([.086, .19, .59, .64], [.52, 6.6], [-165, 55], ylabel="Change vs baseline / kWh",
              xtick=range(1, 7), xticklabels=[f"{i:02d}" for i in range(1, 7)],
              ytick=[-150, -100, -50, 0, 50], grid="y")
    line(a, [.52, 6.6], [0, 0], style="--")
    for i, (before, after, current) in enumerate(zip(running, running[1:], steps_kwh), 1):
        role = "observation" if i <= 2 else "alternative" if i <= 4 else "state"
        fill = "observation_wash" if i <= 2 else "alternative_wash" if i <= 4 else "state_wash"
        rect(a, i - .31, i + .31, min(before, after), max(before, after), fill, role, 1.65)
        line(a, [i + .31, i + .69], [after, after], "ink", 1.1, ":")
        anchor = min(before, after) - 10 if current < 0 else max(before, after) + 10
        text(a, i, anchor, f"{current:+d}", align="center", size=15)
    rect(a, 5.69, 6.31, running[-1], 0, "state", "ink", 1.3)
    text(a, 6, running[-1] - 11, f"{running[-1]:+d}", align="center")

    right = key([.72, .18, .245, .7])
    text(right, .03, .92, "Grid electricity / kWh", size=18)
    text(right, .03, .78, "Baseline energy")
    text(right, .98, .78, f"{reference}", align="right", size=18)
    text(right, .03, .65, "Scheduled energy")
    text(right, .98, .65, f"{final}", align="right", size=18)
    line(right, [.03, .98], [.56, .56], "grid", 1.2)
    for i, label_text in enumerate(labels, 1):
        y = .47 - (i - 1) * .078
        text(right, .03, y, f"{i:02d}", size=13)
        text(right, .16, y, label_text, size=13)
    return {"data": {"baselineKWh": reference, "incrementsKWh": steps_kwh, "cumulativeChangeKWh": running,
                     "gridKWh": final, "shiftBalanceKWh": steps_kwh[:2].sum(),
                     "storageLossKWh": steps_kwh[2:4].sum(), "componentLabels": labels},
            "panels": [a, right]}


def rebound():
    rng = np.random.default_rng(627)
    t = np.arange(-2, 5, DT)
    event = (t >= 0) & (t < 1.5)
    recovery = (t >= 1.5) & (t < 4)
    sample_count = 20
    shaping = np.sin((t[event] - .05) * 2.2)**2
    bump = np.exp(-((t[recovery] - 2.17) / .82)**2)
    main = 52 + 4 * np.sin(t * .48)[None, :] + rng.normal(0, 1.25, (sample_count, 1))
    control = main + rng.normal(0, .30, (sample_count, len(t)))
    control[:, event] -= rng.uniform(9, 17, (sample_count, 1)) * (.70 + .30 * shaping)
    control[:, recovery] += rng.uniform(4.8, 11.0, (sample_count, 1)) * bump
    diff = control - main
    mean = diff.mean(axis=0)
    saved = -diff[:, event].sum(axis=1) * DT
    returned = diff[:, recovery].sum(axis=1) * DT

    a = panel([.086, .15, .515, .67], [-2, 5], [-17, 13], xlabel="Hours since event start",
              ylabel="Controlled minus baseline / kW", xtick=np.arange(-2, 6), grid="y")
    rect(a, 0, 1.5, -17, 13, "observation_wash")
    rect(a, 1.5, 4, -17, 13, "exceedance_wash")
    line(a, [-2, 5], [0, 0], style="--")
    step_x = steps(mean, DT)[0] + t[0]
    for row in diff:
        line(a, step_x, steps(row, DT)[1], "grid", .7)
    line(a, step_x, steps(mean, DT)[1], "ink", 2.65)
    text(a, .75, 10.8, "Control event", align="center", size=14)
    text(a, 2.75, 10.8, "Recovery window", align="center", size=14)

    width = 27
    b = panel([.70, .15, .26, .67], [0, width], [0, width], xlabel="Event reduction / kWh",
              ylabel="Returned energy / kWh", xtick=[0, 5, 10, 15, 20, 25],
              ytick=[0, 5, 10, 15, 20, 25], grid="y")
    line(b, [0, width], [0, width], style="--")
    points(b, saved, returned, edge="observation", size=7)
    points(b, saved.mean(), returned.mean(), marker="d", face="attention", edge="ink", size=10)
    text(b, 2.2, 24.0, "Full return")
    legend = key([.09, .87, .87, .071])
    line(legend, [.00, .06], [.5, .5], "grid", 1.5)
    text(legend, .073, .5, "20 paired days")
    line(legend, [.30, .36], [.5, .5], "ink", 2.65)
    text(legend, .373, .5, "Pair mean")
    points(legend, .66, .5, marker="d", face="attention", edge="ink", size=9)
    text(legend, .68, .5, "Mean event and return")
    return {"data": {"intervalH": DT, "timeH": t, "baselineKW": main, "controlledKW": control,
                     "deltaKW": diff, "controlMask": event, "recoveryMask": recovery,
                     "eventReductionKWh": saved, "returnKWh": returned},
            "panels": [a, b, legend]}


def hysteresis():
    t = np.arange(0, 8 + 1/60, 1/30)
    ambient = 31 + 1.2 * np.sin((t - 2) * np.pi / 12)
    lower, upper = 23.7, 25.2
    idle, cooling = .6, 4.8
    indoor = np.zeros_like(t)
    indoor[0] = 24.25
    active = np.zeros(t.size, dtype=bool)
    for i in range(t.size):
        active[i] = (active[i - 1] if i else False)
        if indoor[i] >= upper:
            active[i] = True
        if indoor[i] <= lower:
            active[i] = False
        if i < len(t) - 1:
            indoor[i + 1] = indoor[i] + ((ambient[i] - indoor[i]) / 5.9 - 2.8 * active[i]) / 30
    power = np.where(active, cooling, idle)
    on = np.flatnonzero(active[1:] & ~active[:-1]) + 1
    off = np.flatnonzero(~active[1:] & active[:-1]) + 1
    first = off[0]
    end = off[1]
    cycle_temp = indoor[first:end + 1]
    cycle_power = power[first:end + 1]

    a = panel([.089, .18, .41, .63], [23.0, 26.0], [0, 6.1], xlabel="Indoor temperature / °C",
              ylabel="Cooling-unit load / kW", xtick=[23, 23.7, 24.5, 25.2, 26],
              ytick=[.6, 2, 3.4, 4.8], grid="y")
    rect(a, lower, upper, 0, 6.1, "alternative_wash")
    for threshold in [lower, upper]:
        line(a, [threshold, threshold], [0, 6.1], "alternative", 1.1, ":")
    x = np.r_[cycle_temp[0], np.repeat(cycle_temp[1:], 2)]
    y = np.repeat(cycle_power, 2)[:-1]
    line(a, x, y, "ink", 2.3)
    points(a, [24.45], [.6], marker=">", face="observation", edge="observation", size=10)
    points(a, [24.45], [4.8], marker="<", face="exceedance", edge="exceedance", size=10)
    text(a, 24.45, 1.25, "Warming while off", align="center")
    text(a, 24.45, 5.36, "Cooling while on", align="center")
    text(a, 23.62, 3.1, "Off", align="right", size=13)
    text(a, 25.27, 3.1, "On", size=13)

    b = panel([.60, .49, .35, .32], [0, 8], [23.2, 25.8], ylabel="Indoor temperature / °C",
              xtick=[], ytick=[23.7, 24.5, 25.2])
    rect(b, 0, 8, lower, upper, "alternative_wash")
    for threshold in [lower, upper]:
        line(b, [0, 8], [threshold, threshold], "alternative", 1.15, ":")
    line(b, t, indoor, "ink", 1.85)
    points(b, t[on], indoor[on], marker="s", edge="exceedance", size=6)
    points(b, t[off], indoor[off], marker="o", edge="observation", size=6)

    c = panel([.60, .18, .35, .23], [0, 8], [0, 5.8], xlabel="Elapsed time / h",
              ylabel="Unit load / kW", xtick=np.arange(0, 9, 2), ytick=[.6, 4.8])
    cooling_intervals = np.r_[off, len(t) - 1] if active[-1] else off
    for start, stop in zip(on, cooling_intervals, strict=True):
        rect(c, t[start], t[stop], .6, 4.8, "exceedance_wash")
    sx, sy = steps(power[:-1], 1/30)
    line(c, sx, sy, "ink", 1.8)
    return {"data": {"intervalH": 1/30, "timeH": t, "ambientC": ambient, "indoorC": indoor,
                     "loadKW": power, "startThresholdC": upper, "stopThresholdC": lower,
                     "onIndex": on, "offIndex": off, "cycleIndices": [first, end]},
            "panels": [a, b, c]}


def pareto():
    scenario = np.arange(16)[:, None]
    hours = np.arange(6)
    deficit = (np.maximum(0, 16 + 1.1 * scenario + 4.5*np.sin(hours * .8 + scenario * .3)
                          - (hours - 2.5)**2))
    battery = np.repeat([0, 14, 28, 42], 14)
    firm = np.tile(np.arange(0, 28, 2), 4)
    cost = 58 + 2.7 * firm + 1.62 * battery + .0375 * firm**2
    residual = np.maximum(np.maximum(0, deficit[None, :, :] - firm[:, None, None]).sum(axis=2)
                          - battery[:, None], 0)
    unserved = residual.mean(axis=1)
    nondominated = np.array([not np.any((cost <= x) & (unserved <= y) & ((cost < x) | (unserved < y)))
                            for x, y in zip(cost, unserved)])
    frontier = np.flatnonzero(nondominated)
    frontier = frontier[np.argsort(cost[frontier])]
    cost_cap = 190
    energy_cap = 15
    feasible = (cost <= cost_cap) & (unserved <= energy_cap)
    viable = np.flatnonzero(feasible)
    chosen = viable[np.argmin(cost[viable])]
    assert nondominated[chosen]

    xlim, ylim = [45, 235], [0, 155]
    a = panel([.088, .155, .63, .70], xlim, ylim, xlabel="Daily cost / USD",
              ylabel="Expected unserved energy / kWh/day", xtick=np.arange(60, 231, 30), grid="y")
    rect(a, xlim[0], cost_cap, 0, energy_cap, "state_wash")
    line(a, xlim, [energy_cap, energy_cap], "ink", 1.1, ":")
    line(a, [cost_cap, cost_cap], ylim, "ink", 1.1, ":")
    text(a, 66, 5.5, "Within both limits", size=13)
    text(a, 192, 147, "Cost limit", size=12.5)
    markers = ["o", "s", "^", "v"]
    colors = ["observation", "alternative", "exceedance", "state"]
    for b, marker, role in zip(np.unique(battery), markers, colors):
        group = battery == b
        points(a, cost[group], unserved[group], marker=marker, face="white", edge=role, size=7.1)
    line(a, cost[frontier], unserved[frontier], "ink", 1.6, "--")
    points(a, cost[chosen], unserved[chosen], marker="d", face="attention", edge="ink", size=10)

    side = key([.755, .185, .205, .67])
    text(side, .03, .96, "Usable storage", size=17)
    for i, (b, marker, role) in enumerate(zip(np.unique(battery), markers, colors)):
        ypos = .83 - i * .108
        points(side, .07, ypos, marker=marker, face="white", edge=role, size=8)
        text(side, .19, ypos, f"{b} kWh", size=14)
    line(side, [.02, .12], [.38, .38], "ink", 1.6, "--")
    text(side, .19, .38, "Nondominated")
    points(side, .07, .265, marker="d", face="attention", edge="ink", size=9)
    text(side, .19, .265, "Least-cost feasible")
    text(side, .19, .155, f"{cost[chosen]:.1f} USD", size=14)
    text(side, .19, .080, f"{unserved[chosen]:.1f} kWh/day", size=14)
    return {"data": {"firmReserveKW": firm, "usableStorageKWh": battery, "scenarioDeficitKW": deficit,
                     "dailyCostUSD": cost, "unservedKWhPerDay": unserved, "frontierIndices": frontier,
                     "chosenIndex": chosen, "costCapUSD": cost_cap, "unservedCapKWh": energy_cap},
            "panels": [a, side]}


def serial(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, range):
        return list(obj)
    raise TypeError(type(obj).__name__)


def export():
    builders = [duration, saturation, energy_bridge, rebound, hysteresis, pareto]
    result = {"schema": "projectx.illustrative-engineering.v1",
              "source": "Analytic or seeded illustrative examples; no client observations",
              "charts": {builder.__name__.replace("_", "-"): builder() for builder in builders}}
    return json.dumps(result, ensure_ascii=False, default=serial, separators=(",", ":")) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the saved fixture is current")
    args = parser.parse_args()
    output = HERE / "engineering-data.json"
    generated = export()
    if args.check:
        if output.read_text(encoding="utf-8") != generated:
            parser.error(f"{output} is out of date")
    else:
        output.write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
