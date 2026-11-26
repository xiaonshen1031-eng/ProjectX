"""Independently check the synthetic inputs and recompute annotated values."""
from pathlib import Path
import json

import numpy as np
from scipy.optimize import nnls


def load(filename):
    return json.loads((Path(__file__).parent / filename).read_text(encoding="utf-8"))


def flow_balance(data):
    nodes = np.asarray(data["nodes"])
    expected = float(data["total"])
    totals = np.asarray([nodes[nodes[:, 0] == stage, 4].sum() for stage in range(3)])
    np.testing.assert_allclose(totals, expected, atol=1e-10)
    outgoing = np.zeros(len(nodes))
    incoming = np.zeros(len(nodes))
    for link in data["links"]:
        x, y = np.asarray(link["x"]), np.asarray(link["y"])
        half = len(y) // 2
        stage = int(round((x[0] - .108) / .43))
        assert stage in (0, 1)
        for low, high, side, recorded in (
                (y[0], y[-1], stage, outgoing),
                (y[half - 1], y[half], stage + 1, incoming)):
            np.testing.assert_allclose(high - low, .76 * link["value"] / expected, atol=1e-12)
            matches = np.flatnonzero((nodes[:, 0] == side) & (nodes[:, 2] <= low + 1e-12)
                                     & (nodes[:, 2] + nodes[:, 3] >= high - 1e-12))
            assert len(matches) == 1
            recorded[matches[0]] += link["value"]
    np.testing.assert_allclose(outgoing[nodes[:, 0] != 2], nodes[nodes[:, 0] != 2, 4])
    np.testing.assert_allclose(incoming[nodes[:, 0] != 0], nodes[nodes[:, 0] != 0, 4])
    return expected


def project_constraints(data):
    active = []
    for p, q in zip(np.asarray(data["origin"]), np.asarray(data["projected"]), strict=True):
        x, y = q
        residual = np.array([((x - 54)/34)**2 + ((y - 49)/27)**2 - 1,
                             x + .65*y - 95, 19-y])
        assert np.all(residual <= 1e-6), (q, residual)
        binding = np.abs(residual) < 1e-5
        assert np.any(binding), q
        # Convex feasibility and nonnegative multipliers certify the nearest point.
        normals = np.array([[2*(x-54)/34**2, 2*(y-49)/27**2], [1, .65], [0, -1]])
        _, stationarity_error = nnls(normals[binding].T, p-q)
        assert stationarity_error < 1e-4, (p, q, stationarity_error)
        active.append(np.array(["E", "L", "F"])[binding].tolist())
    return active


def scheduled_energy(data):
    power = np.asarray(data["power"])
    hour = np.arange(power.shape[1])
    window = ((hour >= np.asarray(data["arrival"])[:, None])
              & (hour < np.asarray(data["departure"])[:, None]))
    assert np.all(power >= 0) and np.all(power[~window] == 0)
    groups = power.reshape(4, 4, -1).sum(axis=1)
    np.testing.assert_allclose(groups, data["groups"])
    headroom = data["capacity"] - groups.sum(axis=0)
    return {"hour": int(headroom.argmin()), "headroom_kw": float(headroom.min()),
            "delivered_kwh": power.sum(axis=1).tolist()}



def engineering_checks(charts):
    duration = charts["duration"]["data"]
    baseline = np.asarray(duration["baselineKW"])
    shifted = np.asarray(duration["shiftedKW"])
    capacity = duration["capacityKW"]
    interval = duration["hoursPerBin"]
    np.testing.assert_allclose(baseline.sum(axis=1), shifted.sum(axis=1))
    exceeded = [np.asarray(case) - capacity for case in (baseline, shifted)]
    np.testing.assert_array_equal([np.count_nonzero(series > 1e-9) for series in exceeded],
                                  duration["exceedanceHours"])
    totals = [series[series > 0].sum() * interval for series in exceeded]
    np.testing.assert_allclose(totals, duration["aboveCapKWh"])

    saturation = charts["saturation"]["data"]
    np.testing.assert_array_equal(saturation["scheduledKW"], shifted)
    headroom = capacity - shifted
    above = headroom < -1e-9
    near = (headroom >= -1e-9) & (headroom < saturation["nearThresholdKW"])
    np.testing.assert_allclose(headroom, saturation["headroomKW"])
    np.testing.assert_array_equal(above, saturation["aboveCapacity"])
    np.testing.assert_array_equal(near, saturation["nearCapacity"])
    np.testing.assert_array_equal(~(above | near), saturation["adequate"])
    counts = np.column_stack((above.sum(axis=1), near.sum(axis=1)))
    np.testing.assert_array_equal(counts, saturation["dailyHours"])

    bridge = charts["energy-bridge"]["data"]
    values = np.asarray(bridge["incrementsKWh"])
    np.testing.assert_array_equal(np.r_[0, values.cumsum()], bridge["cumulativeChangeKWh"])
    assert values[:2].sum() == bridge["shiftBalanceKWh"] == 0
    assert values[2:4].sum() == bridge["storageLossKWh"]
    assert bridge["baselineKWh"] + values.sum() == bridge["gridKWh"]

    rebound = charts["rebound"]["data"]
    delta = np.array(rebound["controlledKW"]) - np.array(rebound["baselineKW"])
    event = np.asarray(rebound["controlMask"])
    recovery = np.asarray(rebound["recoveryMask"])
    assert not np.any(event & recovery)
    np.testing.assert_allclose(delta, rebound["deltaKW"])
    np.testing.assert_allclose(-delta[:, event].sum(axis=1) * rebound["intervalH"],
                               rebound["eventReductionKWh"])
    np.testing.assert_allclose(delta[:, recovery].sum(axis=1) * rebound["intervalH"],
                               rebound["returnKWh"])

    thermal = charts["hysteresis"]["data"]
    indoor = np.asarray(thermal["indoorC"])
    power = np.asarray(thermal["loadKW"])
    switches = np.diff(power)
    np.testing.assert_array_equal(np.flatnonzero(switches > 0) + 1, thermal["onIndex"])
    np.testing.assert_array_equal(np.flatnonzero(switches < 0) + 1, thermal["offIndex"])
    assert np.all(indoor[thermal["onIndex"]] >= thermal["startThresholdC"])
    assert np.all(indoor[thermal["offIndex"]] <= thermal["stopThresholdC"])

    pareto = charts["pareto"]["data"]
    cost = np.asarray(pareto["dailyCostUSD"])
    energy = np.asarray(pareto["unservedKWhPerDay"])
    deficit = np.asarray(pareto["scenarioDeficitKW"])
    for observed, reserve, storage in zip(energy, pareto["firmReserveKW"],
                                          pareto["usableStorageKWh"], strict=True):
        hourly = np.maximum(deficit - reserve, 0)
        np.testing.assert_allclose(np.maximum(hourly.sum(axis=1) - storage, 0).mean(), observed)
    expected_frontier = set()
    for i in range(len(cost)):
        better_cost = (cost < cost[i]) & (energy <= energy[i])
        better_robustness = (energy < energy[i]) & (cost <= cost[i])
        if not (better_cost | better_robustness).any():
            expected_frontier.add(i)
    assert set(pareto["frontierIndices"]) == expected_frontier
    chosen = pareto["chosenIndex"]
    viable = (cost <= pareto["costCapUSD"]) & (energy <= pareto["unservedCapKWh"])
    assert viable[chosen] and chosen in expected_frontier and cost[chosen] == cost[viable].min()
    return {
        "duration_above_cap_kwh": totals,
        "saturation_above_cap_hours": int(above.sum()),
        "net_grid_change_kwh": int(values.sum()),
        "matched_rebound_pairs": len(delta),
        "thermal_switches": int(np.count_nonzero(switches)),
        "nondominated_policies": len(expected_frontier),
        "selected_daily_cost_usd": float(cost[chosen]),
        "selected_unserved_kwh_per_day": float(energy[chosen]),
    }


def extended_engineering_checks(charts):
    network = charts["contingency"]["data"]
    baseline, after = (np.asarray(network[field]) for field in ("baselineFlowKW", "outageFlowKW"))
    rating = np.asarray(network["branchRatingKW"])
    active = np.asarray(network["inService"])
    demand = np.asarray(network["demandKW"])
    np.testing.assert_array_equal(baseline[:3], demand)
    assert np.all(after[~active] == 0) and np.all(after <= rating)
    delivered = np.array([after[0], after[1] + after[3], after[2]])
    np.testing.assert_array_equal(delivered, network["deliveredKW"])
    np.testing.assert_array_equal(demand - delivered, network["unservedKW"])
    assert after[3] == rating[3] and demand[1] - delivered[1] == 3

    marginal = charts["marginal-cost"]["data"]
    unit_cost = np.asarray(marginal["unitCostUSDPerMWh"])
    block = np.asarray(marginal["blockCapacityMW"])
    required = marginal["requirementMW"]

    def procurement(requirement):
        left = requirement
        allocation = np.zeros_like(block)
        for index in np.argsort(unit_cost):
            allocation[index] = min(left, block[index])
            left -= allocation[index]
        assert left == 0
        return allocation, np.dot(allocation, unit_cost)

    allocation, cost = procurement(required)
    np.testing.assert_array_equal(allocation, marginal["allocationMW"])
    assert cost == marginal["procurementCostUSDPerHour"]
    assert procurement(required + 1)[1] - cost == marginal["nextMWCostUSDPerHour"]

    forecast = charts["error-horizon"]["data"]
    pair_counts = np.asarray(forecast["pairCounts"])
    for row, pairs in enumerate(forecast["baselineAndRevisedAbsoluteErrorKW"]):
        for col, pair in enumerate(pairs):
            assert len(pair) == pair_counts[row, col]
            summary = forecast["quartilesKW"][row][col]
            if len(pair) > 0:
                error = np.asarray(pair)
                assert np.all(error >= 0)
                np.testing.assert_allclose(np.quantile(error[:, 1] - error[:, 0], [.25, .5, .75]), summary)
            else:
                assert summary == []

    response = charts["response-delay"]["data"]
    ack = np.asarray(response["confirmationS"])
    apply = np.asarray(response["actuationS"])
    latency = ack + apply
    assert np.isfinite(latency).all() and latency.shape == (2, response["commandCount"])
    np.testing.assert_allclose(latency, response["latencyS"])
    np.testing.assert_array_equal(np.sum(latency > response["deadlineS"], axis=1), response["lateCounts"])
    np.testing.assert_allclose(np.column_stack((ack.mean(axis=1), np.repeat(apply.mean(), 2))), response["meanPhaseS"])
    return {"unserved_power_kw": int((demand-delivered).sum()), "reserve_cost_usd_per_hour": int(cost),
            "forecast_matched_pairs": int(pair_counts.sum()), "forecast_missing_cells": int(np.sum(pair_counts == 0)),
            "deadline_miss_counts": response["lateCounts"]}


def main():
    basic, extra = load("demo-data.json"), load("extra-data.json")
    trajectory = basic["trajectory"]
    margin = np.asarray(trajectory["capacity"]) - trajectory["high"]
    minimum = margin.argmin()
    polar = np.ptp(extra["polar"]["values"], axis=0)
    chord = np.asarray(basic["chord"]["matrix"])
    np.testing.assert_array_equal(chord, chord.T)
    assert np.all(np.diag(chord) == 0)
    spectrum = np.asarray(extra["spectrum"]["db"])
    assert spectrum.max() == 0 and spectrum.min() >= -45
    bins = np.asarray(extra["calibration"]["bins"])
    assert bins[:, 4].sum() == extra["calibration"]["n"]
    assert np.all(bins[:, 2] <= bins[:, 1]) and np.all(bins[:, 1] <= bins[:, 3])
    quantiles = np.quantile(extra["raincloud"]["samples"], [.1, .25, .5, .75, .9], axis=1).T
    np.testing.assert_allclose(quantiles, extra["raincloud"]["quantiles"])
    forest_ci = np.asarray(extra["forest"]["ci"])
    assert np.all(forest_ci[:, 0] <= forest_ci[:, 1])
    engineered = load("engineering-data.json")["charts"]
    print(json.dumps({
        "data_scope": "independent synthetic illustration",
        "sankey_conserved_total": flow_balance(extra["sankey"]),
        "gantt": scheduled_energy(extra["gantt"]),
        "binding_at_projection": project_constraints(basic["feasibility"]),
        "trajectory_lowest_p90_margin": {"hour": trajectory["time"][minimum], "margin": float(margin[minimum])},
        "polar_largest_condition_range": {"hour": int(polar.argmax()), "range": float(polar.max())},
        "chord_largest_pair_weight": float(chord.max()),
        "forest_intervals_crossing_zero": int(((forest_ci[:, 0] <= 0) & (forest_ci[:, 1] >= 0)).sum()),
        "calibration_n": int(bins[:, 4].sum()),
        "engineering": engineering_checks(engineered),
        "engineering_extensions": extended_engineering_checks(engineered),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
