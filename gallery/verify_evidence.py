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
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
