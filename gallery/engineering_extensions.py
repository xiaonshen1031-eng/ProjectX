"""Additional linked Project figures with recomputable synthetic measurements."""

import numpy as np

from engineering_geometry import key, line, panel, points, rect, text


def contingency():
    base = np.array([35, 18, 20, 0])
    after = np.array([35, 0, 20, 15])
    rating = np.array([42, 26, 32, 15])
    in_service = np.array([True, False, True, True])
    demand = np.array([35, 18, 20])
    delivered = np.array([after[0], after[1] + after[3], after[2]])
    locations = {"S1": (.9, 4.65), "S2": (.9, 1.3), "L1": (7.45, 5.05),
                 "L2": (7.45, 3.0), "L3": (7.45, .87)}
    endpoints = [("S1", "L1"), ("S1", "L2"), ("S2", "L3"), ("S2", "L2")]

    a = panel([.07, .16, .54, .69], [0, 9], [0, 6], axis=False)
    headings = key([.07, .872, .86, .08])
    text(headings, 0, .5, "After the branch outage", size=24)
    text(headings, .62, .5, "Spare branch capacity", size=24)

    for i, (start, end) in enumerate(endpoints):
        x1, y1 = locations[start]
        x2, y2 = locations[end]
        role = "exceedance" if i == 1 else "observation" if i == 3 else "ink"
        weight = 4.5 if i == 3 else 2.3
        slope = (y2 - y1) / (x2 - x1)
        # Terminate at the node boundaries so shafts leave every ID readable.
        inset = .34
        line(a, [x1+inset, x2-inset], [y1+slope*inset, y2-slope*inset],
             role, weight, "--" if i == 1 else "-")
        tx = 4.8 if i == 3 else 3.9
        ty = y1 + (y2 - y1) * (tx-x1) / (x2-x1)
        if i == 1:
            points(a, tx, ty, marker="x", edge=role, width=2.4, size=15)
            text(a, tx + .12, ty + .38, "Branch out", color=role, size=19)
        else:
            points(a, tx, ty, marker=">", face=role, edge=role, size=10)
            text(a, tx, ty + .35, f"{after[i]} / {rating[i]} kW", color=role, size=20, align="center")

    for name, (x, y) in locations.items():
        color = "observation" if name in ("S2", "L2") else "ink"
        rect(a, x - .34, x + .34, y - .24, y + .24, "white", color, 1.6)
        text(a, x, y, name, size=19, align="center")
    text(a, 7.85, 3.0, "3 kW short", size=22, color="exceedance")
    text(a, 4.7, 1.76, "Transfer route", size=21, color="observation", align="center")

    b = panel([.702, .16, .23, .62], [-.6, 17], [.4, 3.65], xlabel="Headroom / kW",
              xtick=[0, 4, 8, 12, 16], ytick=[1, 2, 3],
              yticklabels=["S2-L2", "S2-L3", "S1-L1"], grid="x")
    active = [0, 2, 3]
    for row, i in zip([3, 2, 1], active, strict=True):
        start_margin = rating[i] - base[i]
        end_margin = rating[i] - after[i]
        line(b, [start_margin, end_margin], [row, row], "ink", 1.6)
        points(b, start_margin, row, edge="ink", size=10)
        points(b, end_margin, row, marker="s", face="observation", edge="ink", size=10)
    text(b, .7, 1.27, "Tie has no spare", size=20, color="observation")
    labels = key([.70, .797, .26, .050])
    points(labels, .06, .5, edge="ink", size=9)
    text(labels, .13, .5, "Before", size=18)
    points(labels, .53, .5, marker="s", face="observation", edge="ink", size=9)
    text(labels, .60, .5, "After", size=18)

    return {"data": {"branchRatingKW": rating, "baselineFlowKW": base, "outageFlowKW": after,
                     "inService": in_service, "demandKW": demand, "deliveredKW": delivered,
                     "unservedKW": demand - delivered},
            "panels": [a, b, headings, labels]}


def marginal_cost():
    capacity = np.array([10, 14, 12, 8])
    price = np.array([4, 10, 20, 42])
    end = capacity.cumsum()
    start = np.r_[0, end[:-1]]
    required = 29
    assigned = np.clip(required - start, 0, capacity)
    active = (start <= required) & (required < end)
    cost = assigned @ price
    colors = ["state", "observation", "alternative", "exceedance"]

    a = panel([.086, .18, .55, .64], [0, 46], [0, 47],
              xlabel="Reserve requirement / MW", ylabel="Marginal cost / USD/(MW·h)",
              xtick=[0, 10, 24, 29, 36, 44], ytick=[0, 10, 20, 30, 40], grid="y")
    rect(a, start[active][0], end[active][0], 0, 47, "alternative_wash")
    for i, (lo, hi, marginal) in enumerate(zip(start, end, price, strict=True)):
        line(a, [lo, hi], [marginal, marginal], colors[i], 4.5)
        if i:
            line(a, [lo, lo], [price[i-1], marginal], "ink", 1.3, ":")
        text(a, (lo+hi)/2, marginal+3.1, f"B{i+1}", size=20, align="center")
    line(a, [required, required], [0, price[active][0]], "ink", 1.3, "--")
    points(a, required, price[active][0], marker="d", face="attention", edge="ink", size=13)

    side = key([.677, .19, .27, .65])
    text(side, 0, .96, "Reserve allocated at 29 MW", size=24)
    for i, (maximum, used, color) in enumerate(zip(capacity, assigned, colors, strict=True)):
        y = .77 - i*.125
        span = .35
        text(side, .0, y, f"B{i+1}", size=20)
        rect(side, .17, .17+maximum/14*span, y-.024, y+.024, "white", color, 1.4)
        if used:
            rect(side, .17, .17+used/14*span, y-.024, y+.024, color)
        text(side, .58, y, f"{used} / {maximum} MW", size=20)
    line(side, [0, .98], [.29, .29], "grid", 1.4)
    text(side, 0, .21, f"{cost} USD/h", size=24)
    text(side, .0, .12, "Total procurement cost", size=20)
    text(side, 0, .015, "Next 1 MW adds 20 USD/h", color="alternative", size=22)

    return {"data": {"blockCapacityMW": capacity, "unitCostUSDPerMWh": price, "requirementMW": required,
                     "allocationMW": assigned, "procurementCostUSDPerHour": cost,
                     "nextMWCostUSDPerHour": price[active][0]},
            "panels": [a, side]}


def error_horizon():
    rng = np.random.default_rng(1026)
    horizon = np.array([1, 2, 3, 4, 6, 8])
    regimes = ("Stable", "Ramp", "High variability")
    counts = np.array([[48, 48, 46, 45, 40, 38], [48, 45, 42, 38, 28, 22], [42, 42, 33, 26, 15, 0]])
    shifts = np.array([[-.4, -.62, -.54, -.5, -.4, -.2], [-1.2, -1.15, -1.02, -.84, -.2, .15],
                       [-.5, -.1, .15, .28, .63, 0]])
    sample_pairs = []
    summaries = []
    roles = ("state", "observation", "exceedance")
    main = panel([.095, .39, .84, .434], [.52, len(horizon)+.5], [-2.5, 2.3],
                 ylabel="Paired error difference / kW", xtick=[], ytick=[-2, -1, 0, 1, 2], grid="y")
    coverage = panel([.095, .15, .84, .19], [.52, len(horizon)+.5], [.5, 3.5], xlabel="Forecast lead time / h",
                     xtick=np.arange(1, len(horizon)+1), xticklabels=[str(h) for h in horizon],
                     ytick=[1, 2, 3], yticklabels=["C", "B", "A"])
    legend = key([.095, .859, .84, .075])
    rect(main, .52, len(horizon)+.5, -2.5, 0, "state_wash")
    line(main, [.52, len(horizon)+.5], [0, 0], "ink", 1.5)
    for i, (regime, color, symbol) in enumerate(zip(regimes, roles, ("o", "s", "^"), strict=True)):
        x = .02 + .22*i
        y = 3-i
        points(legend, x, .55, marker=symbol, edge=color, face=color, size=11)
        text(legend, x+.035, .55, f"{chr(65+i)}", size=20)
        text(legend, x+.063, .55, regime, size=19)
        condition_cases = []
        condition_quantiles = []
        for j, sample_count in enumerate(counts[i]):
            xpos = j+1
            if not sample_count:
                condition_cases.append([])
                condition_quantiles.append([])
                rect(coverage, xpos-.39, xpos+.39, y-.38, y+.38, "white", "ink", 1.2)
                text(coverage, xpos, y, "Missing", size=19, align="center")
                continue
            baseline = 2.3 + .27*j + .4*i + rng.gamma(2.5, .8, sample_count)
            revised = np.maximum(0, baseline + shifts[i,j] + rng.normal(0, .48+.12*i, sample_count))
            pair = revised - baseline
            low, median, high = np.quantile(pair, [.25, .5, .75])
            condition_cases.append(np.column_stack([baseline, revised]))
            condition_quantiles.append([low, median, high])
            dose = xpos + (i-1)*.19
            line(main, [dose, dose], [low, high], color, 3)
            for bound in [low, high]:
                line(main, [dose-.052, dose+.052], [bound, bound], color, 1.6)
            points(main, dose, median, marker=symbol, face="white", edge=color, size=10, width=1.9)
            rect(coverage, xpos-.39, xpos+.39, y-.38, y+.38,
                 ("state_wash", "observation_wash", "exceedance_wash")[i])
            text(coverage, xpos, y, f"{sample_count}", size=19, align="center")
        sample_pairs.append(condition_cases)
        summaries.append(condition_quantiles)
    text(main, .77, -2.13, "Lower error", size=20, color="state")
    text(legend, .69, .55, "Median and middle 50%", size=19)
    return {"data": {"leadHours": horizon, "regimes": regimes, "pairCounts": counts,
                     "baselineAndRevisedAbsoluteErrorKW": sample_pairs, "quartilesKW": summaries,
                     "difference": "revised absolute error minus baseline absolute error"},
            "panels": [main, coverage, legend]}


def response_delay():
    rng = np.random.default_rng(3117)
    actuate = rng.uniform(7.5, 13, 36)
    older_ack = rng.uniform(6.5, 21, 36)
    newer_ack = older_ack * .54 + 1.8
    deadline = 22
    latency = np.array([older_ack+actuate, newer_ack+actuate])
    late = (latency > deadline).sum(axis=1)
    means = np.column_stack(([older_ack.mean(), newer_ack.mean()], [actuate.mean(), actuate.mean()]))
    colors = ("exceedance", "observation")
    names = ("Queued confirmation", "Priority confirmation")

    main = panel([.092, .182, .55, .65], [0, 36], [-4, 103], xlabel="End-to-end latency / s",
                 ylabel="Commands still waiting / %", xtick=[0, 8, 16, 22, 28, 36],
                 ytick=[0, 25, 50, 75, 100], grid="y")
    rect(main, deadline, 36, 0, 100, "exceedance_wash")
    line(main, [deadline, deadline], [0, 100], "ink", 1.3, "--")
    text(main, deadline+.75, 94, "22 s deadline", size=20)
    for i, (sample, color) in enumerate(zip(latency, colors, strict=True)):
        ordered = np.sort(sample)
        after = np.arange(len(sample), -1, -1) * 100 / len(sample)
        x = np.repeat(np.r_[0, ordered, 36], 2)[1:-1]
        y = np.repeat(after, 2)
        line(main, x, y, color, 2.9, "--" if i == 0 else "-")
        miss = late[i]*100/len(sample)
        points(main, deadline, miss, marker="s" if i == 0 else "o", face="white", edge=color, size=10, width=1.8)
        text(main, deadline+.72, miss+4.5, f"{late[i]} / {len(sample)}", color=color, size=20)
    legend = key([.092, .861, .55, .074])
    line(legend, [.0,.075], [.54,.54], colors[0], 2.9, "--")
    text(legend, .09, .54, names[0], size=19)
    line(legend, [.5,.575], [.54,.54], colors[1], 2.9)
    text(legend, .59, .54, names[1], size=19)

    side = panel([.72, .235, .226, .52], [0, 28], [.5, 2.5], xlabel="Mean phase time / s",
                 xtick=[0, 7, 14, 21, 28], ytick=[], grid="x")
    heading = key([.72, .785, .226, .12])
    text(heading, 0, .58, "Where time is spent", size=24)
    for row, i in zip([2, 1], range(2), strict=True):
        before, after = means[i]
        rect(side, 0, before, row-.19, row+.19, colors[i])
        rect(side, before, before+after, row-.19, row+.19, "alternative_wash", "alternative")
        text(side, 0, row+.36, names[i], size=19)
        text(side, before/2, row, f"{before:.1f}", color="white", size=18, align="center")
        text(side, before+after/2, row, f"{after:.1f}", color="alternative", size=18, align="center")
    foot = key([.72, .086, .24, .067])
    text(foot, 0, .55, "Confirm then actuate", size=20)
    return {"data": {"commandCount": len(actuate), "confirmationS": [older_ack, newer_ack],
                     "actuationS": actuate, "latencyS": latency, "deadlineS": deadline,
                     "lateCounts": late, "meanPhaseS": means},
            "panels": [main, legend, side, heading, foot]}
