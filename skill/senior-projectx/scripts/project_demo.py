#!/usr/bin/env python3
"""Prepare and run the small synthetic Project acceptance case."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from project_research import solve_allocation, validate_allocation, write_json


def prepare(root: Path) -> dict:
    for folder in ["data", "model", "review", "manuscript", "figure/final", "data/results"]:
        (root / folder).mkdir(parents=True, exist_ok=True)
    periods = pd.DataFrame({
        "period": list(range(8)),
        "timestamp": pd.date_range("2026-01-01 08:00", periods=8, freq="h").astype(str),
        "base_load_kw": [0.0, 18.0, 25.0, 31.0, 36.0, 33.0, 24.0, 16.0],
        "base_load_unit": ["kW"] * 8,
        "capacity_kw": [55.0] * 8,
        "capacity_unit": ["kW"] * 8,
        "duration_h": [1.0] * 8,
    })
    vehicles = pd.DataFrame({
        "vehicle_id": ["EV-01", "EV-02", "EV-03", "EV-04", "EV-05"],
        "arrival_period": [0, 1, 2, 3, 0],
        "departure_period": [4, 6, 8, 7, 8],
        "energy_kwh": [18.0, 22.0, 20.0, 16.0, 24.0],
        "energy_unit": ["kWh"] * 5,
        "max_charge_kw": [11.0, 11.0, 7.0, 7.0, 11.0],
        "power_unit": ["kW"] * 5,
    })
    periods.to_csv(root / "data/periods.csv", index=False, encoding="utf-8-sig")
    vehicles.to_csv(root / "data/vehicles.csv", index=False, encoding="utf-8-sig")
    write_json(root / "data/periods_schema.json", {"fields": [
        {"name": "period", "role": "record_id", "unit": "index", "min": 0},
        {"name": "timestamp", "role": "time", "unit": "datetime"},
        {"name": "base_load_kw", "role": "value", "unit": "kW", "unit_field": "base_load_unit", "allow_zero": True, "min": 0},
        {"name": "capacity_kw", "role": "value", "unit": "kW", "unit_field": "capacity_unit", "allow_zero": False, "min": 0},
        {"name": "duration_h", "role": "value", "unit": "h", "allow_zero": False, "min": 0.01},
    ]})
    write_json(root / "data/vehicles_schema.json", {"object_field": "vehicle_id", "expected_objects": vehicles.vehicle_id.tolist(), "fields": [
        {"name": "vehicle_id", "role": "object_id", "unit": "id"},
        {"name": "arrival_period", "role": "value", "unit": "index", "min": 0},
        {"name": "departure_period", "role": "value", "unit": "index", "min": 1},
        {"name": "energy_kwh", "role": "value", "unit": "kWh", "unit_field": "energy_unit", "allow_zero": False, "min": 0},
        {"name": "max_charge_kw", "role": "value", "unit": "kW", "unit_field": "power_unit", "allow_zero": False, "min": 0},
    ]})
    write_json(root / "model/allocation.json", {"period_cost": [0.55, 0.48, 0.42, 0.50, 0.82, 0.96, 0.72, 0.58],
                                                  "urgency_weight": [0.005, 0.004, 0.003, 0.006, 0.002],
                                                  "validation_tolerance": 1e-7})
    write_json(root / "task_contract.json", {
        "task_id": "T1", "question": "在基础负荷和变压器容量约束下，如何分配多辆电动汽车的充电功率并评价容量余量？",
        "deliverables": ["逐时段充电分配", "容量余量", "敏感性分析", "中文技术报告样章"],
        "data_objects": ["时段负荷与容量", "车辆时间窗与需求电量"],
        "upstream_objects": [{"name": "headroom", "unit": "kW", "definition": "capacity_kw-base_load_kw"}],
        "model": {"type": "continuous_linear_program", "decision": "vehicle-period charging power in kW",
                  "objective": "period cost plus urgency weighting", "constraints": ["vehicle energy", "period capacity", "availability", "power bounds"]}
    })
    return {"status": "ok", "identity": "synthetic_toolchain_example", "root": str(root)}


def sensitivity(root: Path) -> dict:
    base = pd.read_csv(root / "data/vehicles.csv")
    rows = []
    scenario_dir = root / "data/results/scenarios"; scenario_dir.mkdir(parents=True, exist_ok=True)
    for scale in [0.80, 0.95, 1.00, 1.05, 1.15, 1.25]:
        vehicles = base.copy(); vehicles["energy_kwh"] *= scale
        vehicles_path = scenario_dir / f"vehicles_{scale:.2f}.csv"; vehicles.to_csv(vehicles_path, index=False)
        allocation_path = scenario_dir / f"allocation_{scale:.2f}.csv"
        result_path = scenario_dir / f"result_{scale:.2f}.json"
        result = solve_allocation(root / "data/periods.csv", vehicles_path, root / "model/allocation.json", allocation_path)
        write_json(result_path, result)
        if result["status"] == "optimal":
            validation = validate_allocation(root / "data/periods.csv", vehicles_path, root / "model/allocation.json", allocation_path, result_path)
            objective = result["objective"]; margin = validation["minimum_capacity_margin_kw"]
            mean_margin = float(sum(result["capacity_margin_kw"]) / len(result["capacity_margin_kw"]))
        else:
            objective = float("nan"); margin = float("nan"); mean_margin = float("nan")
        rows.append({"demand_scale": scale, "status": result["status"], "objective": objective,
                     "minimum_margin_kw": margin, "mean_margin_kw": mean_margin})
    output = root / "data/results/sensitivity.csv"; pd.DataFrame(rows).to_csv(output, index=False, encoding="utf-8-sig")
    return {"status": "ok", "scenarios": len(rows), "output": str(output)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest="command", required=True)
    for name in ["prepare", "sensitivity"]: sub.add_parser(name).add_argument("workspace", type=Path)
    args = p.parse_args(argv); root = args.workspace.resolve()
    result = prepare(root) if args.command == "prepare" else sensitivity(root)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
