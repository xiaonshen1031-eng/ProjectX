#!/usr/bin/env python3
"""Research, solve, validate, and lineage tools for the Senior-ProjectX.

The public CLI is intentionally small.  It accepts explicit task/data contracts,
solves only supported mathematical structures, and writes machine-readable
results that the figure and report builders consume.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import linprog


SCHEMA = "senior_projectx.project.v1"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def load_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported data format: {suffix}")


def semantic_fingerprint(path: Path) -> str:
    """Fingerprint an explicitly declared dependency, never a whole tree."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def infer_language(text: str) -> str:
    chinese = len([c for c in text if "\u3400" <= c <= "\u9fff"])
    latin = len([c for c in text if c.isascii() and c.isalpha()])
    return "chinese" if chinese >= max(2, latin // 3) else "english"


def define_task(manifest_path: Path, contract_path: Path, *, replace: bool = False) -> dict:
    manifest = read_json(manifest_path)
    contract = read_json(contract_path)
    required = ["task_id", "question", "deliverables", "data_objects", "model"]
    missing = [key for key in required if not contract.get(key)]
    if missing:
        raise ValueError("Task contract missing: " + ", ".join(missing))
    if not isinstance(contract["deliverables"], list) or not isinstance(contract["data_objects"], list):
        raise ValueError("deliverables and data_objects must be lists")
    tasks = manifest.setdefault("project", {}).setdefault("tasks", [])
    found = next((i for i, item in enumerate(tasks) if item.get("task_id") == contract["task_id"]), None)
    if found is not None and not replace:
        raise ValueError(f"Task {contract['task_id']} already exists; use --replace explicitly")
    if found is None:
        tasks.append(contract)
    else:
        tasks[found] = contract
    write_json(manifest_path, manifest)
    return {"status": "ok", "task_id": contract["task_id"], "language": infer_language(contract["question"])}


def audit_data(data_path: Path, schema_path: Path) -> dict:
    frame = load_table(data_path)
    schema = read_json(schema_path)
    fields = schema.get("fields", [])
    if not fields:
        raise ValueError("Schema requires a nonempty fields list")
    errors: list[dict] = []
    warnings: list[dict] = []
    profiles: dict[str, dict] = {}
    for spec in fields:
        name = spec.get("name")
        if not name:
            raise ValueError("Every field requires a name")
        if name not in frame.columns:
            if spec.get("required", True):
                errors.append({"type": "missing_required_field", "field": name})
            continue
        series = frame[name]
        missing = int(series.isna().sum())
        profile: dict[str, Any] = {
            "unit": spec.get("unit", ""),
            "role": spec.get("role", "value"),
            "dtype": str(series.dtype),
            "missing": missing,
            "unique": int(series.nunique(dropna=True)),
        }
        if missing and not spec.get("allow_missing", False):
            errors.append({"type": "unexpected_missing", "field": name, "count": missing})
        unit_field = spec.get("unit_field")
        if unit_field:
            if unit_field not in frame:
                errors.append({"type": "missing_unit_field", "field": name, "unit_field": unit_field})
            else:
                observed_units = sorted(set(frame[unit_field].dropna().astype(str)))
                expected_unit = str(spec.get("unit", ""))
                profile["observed_units"] = observed_units
                if expected_unit and observed_units != [expected_unit]:
                    errors.append({"type": "unit_conflict", "field": name, "expected": expected_unit,
                                   "observed": observed_units})
        if pd.api.types.is_numeric_dtype(series):
            finite = pd.to_numeric(series, errors="coerce")
            profile.update({
                "minimum": None if finite.dropna().empty else float(finite.min()),
                "maximum": None if finite.dropna().empty else float(finite.max()),
                "zero_count": int((finite == 0).sum()),
                "zero_status": "allowed" if spec.get("allow_zero", True) else "forbidden",
            })
            if not spec.get("allow_zero", True) and (finite == 0).any():
                errors.append({"type": "forbidden_zero", "field": name, "count": int((finite == 0).sum())})
            for bound, op in (("min", "below_minimum"), ("max", "above_maximum")):
                if bound in spec:
                    bad = finite < spec[bound] if bound == "min" else finite > spec[bound]
                    if bad.fillna(False).any():
                        errors.append({"type": op, "field": name, "count": int(bad.sum()), "bound": spec[bound]})
        profiles[name] = profile
    id_fields = [f["name"] for f in fields if f.get("role") in {"object_id", "record_id"} and f.get("name") in frame]
    duplicate_count = int(frame.duplicated(id_fields).sum()) if id_fields else int(frame.duplicated().sum())
    if duplicate_count:
        errors.append({"type": "duplicate_records", "fields": id_fields or ["all_columns"], "count": duplicate_count})
    time_fields = [f["name"] for f in fields if f.get("role") == "time" and f.get("name") in frame]
    for field in time_fields:
        parsed = pd.to_datetime(frame[field], errors="coerce")
        bad = int(parsed.isna().sum() - frame[field].isna().sum())
        if bad:
            errors.append({"type": "invalid_time", "field": field, "count": bad})
        profiles[field]["time_min"] = None if parsed.dropna().empty else parsed.min().isoformat()
        profiles[field]["time_max"] = None if parsed.dropna().empty else parsed.max().isoformat()
    expected = schema.get("expected_objects")
    object_field = schema.get("object_field")
    observed_objects = None
    if object_field and object_field in frame:
        observed_objects = sorted(str(v) for v in frame[object_field].dropna().unique())
        if expected is not None and set(map(str, expected)) != set(observed_objects):
            errors.append({"type": "object_population_mismatch", "field": object_field,
                           "expected": sorted(map(str, expected)), "observed": observed_objects})
    joins = []
    for join in schema.get("join_coverage", []):
        other = load_table(resolve(schema_path.parent, join["path"]))
        left_key, right_key = join["left_key"], join.get("right_key", join["left_key"])
        left = set(frame[left_key].dropna().astype(str))
        right = set(other[right_key].dropna().astype(str))
        coverage = len(left & right) / max(1, len(left))
        joins.append({"left_key": left_key, "right_key": right_key, "coverage": coverage,
                      "unmatched": sorted(left - right)[:20]})
        if coverage < float(join.get("minimum_coverage", 1.0)):
            errors.append({"type": "join_coverage_below_required", "left_key": left_key,
                           "coverage": coverage, "required": join.get("minimum_coverage", 1.0)})
    return {
        "schema": "senior_projectx.project.data_audit.v1",
        "status": "pass" if not errors else "fail",
        "data_path": str(data_path),
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "profiles": profiles,
        "object_population": observed_objects,
        "join_coverage": joins,
        "errors": errors,
        "warnings": warnings,
        "notes": ["零值按字段合同判定；允许的零值不计为缺失。"],
    }


def bounded_sum_linear(costs: list[float], lower: list[float], upper: list[float], total: float) -> dict:
    """Exact greedy solution for one continuous bounded-sum linear program."""
    c = np.asarray(costs, dtype=float)
    lo = np.asarray(lower, dtype=float)
    hi = np.asarray(upper, dtype=float)
    if not (c.ndim == lo.ndim == hi.ndim == 1 and len(c) == len(lo) == len(hi)):
        raise ValueError("costs/lower/upper must be equal-length vectors")
    if np.any(~np.isfinite(c)) or np.any(~np.isfinite(lo)) or np.any(~np.isfinite(hi)):
        raise ValueError("All inputs must be finite")
    if np.any(lo > hi):
        raise ValueError("lower cannot exceed upper")
    if total < lo.sum() - 1e-9 or total > hi.sum() + 1e-9:
        return {"status": "infeasible", "reason": "total outside bounded sum range"}
    x = lo.copy()
    remaining = float(total - x.sum())
    for i in np.argsort(c, kind="stable"):
        add = min(remaining, float(hi[i] - lo[i]))
        x[i] += add
        remaining -= add
        if remaining <= 1e-10:
            break
    return {"status": "optimal", "x": x.tolist(), "objective": float(c @ x),
            "sum_residual": float(x.sum() - total), "method": "continuous bounded-sum greedy exact"}


def dag_timing_replay(nodes: list[dict], order: list[str]) -> dict:
    """Replay a supplied order; this function does not optimize the schedule."""
    by_id = {str(n["id"]): n for n in nodes}
    if len(by_id) != len(nodes) or set(order) != set(by_id):
        raise ValueError("order must contain each unique node exactly once")
    finish: dict[str, float] = {}
    resource_ready: dict[str, float] = {}
    records = []
    seen = set()
    for node_id in order:
        node = by_id[node_id]
        deps = [str(v) for v in node.get("depends_on", [])]
        missing = [v for v in deps if v not in seen]
        if missing:
            raise ValueError(f"Order violates dependencies for {node_id}: {missing}")
        resource = str(node.get("resource", "default"))
        start = max([finish[d] for d in deps] + [resource_ready.get(resource, 0.0)])
        duration = float(node["duration"])
        if duration < 0 or not math.isfinite(duration):
            raise ValueError("duration must be finite and nonnegative")
        end = start + duration
        finish[node_id] = end
        resource_ready[resource] = end
        seen.add(node_id)
        records.append({"id": node_id, "resource": resource, "start": start, "finish": end})
    return {"status": "replayed", "scope": "given order only", "makespan": max(finish.values(), default=0.0), "records": records}


def _allocation_problem(periods: pd.DataFrame, vehicles: pd.DataFrame, config: dict) -> tuple:
    required_periods = {"period", "base_load_kw", "capacity_kw", "duration_h"}
    required_vehicles = {"vehicle_id", "arrival_period", "departure_period", "energy_kwh", "max_charge_kw"}
    if missing := sorted(required_periods - set(periods.columns)):
        raise ValueError("Periods missing fields: " + ", ".join(missing))
    if missing := sorted(required_vehicles - set(vehicles.columns)):
        raise ValueError("Vehicles missing fields: " + ", ".join(missing))
    if (periods["duration_h"] <= 0).any() or (vehicles[["energy_kwh", "max_charge_kw"]] < 0).any().any():
        raise ValueError("Durations must be positive; energy and power must be nonnegative")
    headroom = periods["capacity_kw"].to_numpy(float) - periods["base_load_kw"].to_numpy(float)
    if np.any(headroom < -1e-9):
        raise ValueError("Base load exceeds capacity before allocation")
    n_v, n_t = len(vehicles), len(periods)
    price = np.asarray(config.get("period_cost", [1.0] * n_t), dtype=float)
    if price.shape != (n_t,) or np.any(~np.isfinite(price)):
        raise ValueError("period_cost must contain one finite value per period")
    urgency = np.asarray(config.get("urgency_weight", [0.0] * n_v), dtype=float)
    if urgency.shape != (n_v,):
        raise ValueError("urgency_weight must contain one value per vehicle")
    c = np.zeros(n_v * n_t)
    bounds = []
    for vi, row in vehicles.reset_index(drop=True).iterrows():
        arrival, departure = int(row.arrival_period), int(row.departure_period)
        if not (0 <= arrival < departure <= n_t):
            raise ValueError(f"Invalid availability window for {row.vehicle_id}")
        for ti in range(n_t):
            c[vi * n_t + ti] = price[ti] + urgency[vi] * ti
            bounds.append((0.0, float(row.max_charge_kw) if arrival <= ti < departure else 0.0))
    A_ub = np.zeros((n_t, n_v * n_t))
    for ti in range(n_t):
        for vi in range(n_v):
            A_ub[ti, vi * n_t + ti] = 1.0
    A_eq = np.zeros((n_v, n_v * n_t))
    b_eq = vehicles["energy_kwh"].to_numpy(float)
    duration = periods["duration_h"].to_numpy(float)
    for vi in range(n_v):
        A_eq[vi, vi * n_t:(vi + 1) * n_t] = duration
    return c, A_ub, headroom, A_eq, b_eq, bounds


def solve_allocation(periods_path: Path, vehicles_path: Path, config_path: Path,
                     allocation_out: Path) -> dict:
    periods, vehicles, config = load_table(periods_path), load_table(vehicles_path), read_json(config_path)
    if config.get("integer_required"):
        raise ValueError("This interface solves continuous LPs only; integer_required cannot be silently relaxed")
    c, A_ub, b_ub, A_eq, b_eq, bounds = _allocation_problem(periods, vehicles, config)
    solved = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                     bounds=bounds, method="highs")
    result: dict[str, Any] = {
        "schema": "senior_projectx.project.allocation_result.v1",
        "solver": "scipy.optimize.linprog(method='highs')",
        "mathematical_scope": "continuous linear program",
        "status": "optimal" if solved.success else "infeasible_or_failed",
        "solver_status": int(solved.status),
        "solver_message": solved.message,
        "periods_path": str(periods_path),
        "vehicles_path": str(vehicles_path),
        "config_path": str(config_path),
    }
    if not solved.success:
        return result
    n_v, n_t = len(vehicles), len(periods)
    matrix = solved.x.reshape(n_v, n_t)
    rows = []
    for vi, vehicle in vehicles.reset_index(drop=True).iterrows():
        for ti, period in periods.reset_index(drop=True).iterrows():
            rows.append({"vehicle_id": vehicle.vehicle_id, "period": int(period.period),
                         "charge_kw": float(matrix[vi, ti])})
    allocation = pd.DataFrame(rows)
    allocation_out.parent.mkdir(parents=True, exist_ok=True)
    allocation.to_csv(allocation_out, index=False, encoding="utf-8-sig")
    total = matrix.sum(axis=0)
    headroom = periods["capacity_kw"].to_numpy(float) - periods["base_load_kw"].to_numpy(float)
    energy = (matrix * periods["duration_h"].to_numpy(float)).sum(axis=1)
    result.update({
        "objective": float(solved.fun),
        "allocation_path": str(allocation_out),
        "period_total_charge_kw": total.tolist(),
        "headroom_kw": headroom.tolist(),
        "capacity_margin_kw": (headroom - total).tolist(),
        "vehicle_delivered_energy_kwh": {str(v): float(e) for v, e in zip(vehicles.vehicle_id, energy)},
        "maximum_capacity_violation_kw": float(max(0.0, np.max(total - headroom))),
        "maximum_energy_residual_kwh": float(np.max(np.abs(energy - vehicles.energy_kwh.to_numpy(float)))),
    })
    return result


def validate_allocation(periods_path: Path, vehicles_path: Path, config_path: Path,
                        allocation_path: Path, result_path: Path | None = None) -> dict:
    periods, vehicles, config = load_table(periods_path), load_table(vehicles_path), read_json(config_path)
    allocation = load_table(allocation_path)
    required = {"vehicle_id", "period", "charge_kw"}
    if required - set(allocation.columns):
        raise ValueError("Allocation missing required columns")
    expected_pairs = {(str(v), int(t)) for v in vehicles.vehicle_id for t in periods.period}
    observed_pairs = {(str(r.vehicle_id), int(r.period)) for r in allocation.itertuples()}
    errors = []
    if expected_pairs != observed_pairs:
        errors.append({"type": "allocation_population_mismatch", "missing": len(expected_pairs - observed_pairs),
                       "unexpected": len(observed_pairs - expected_pairs)})
    pivot = allocation.pivot(index="vehicle_id", columns="period", values="charge_kw").reindex(
        index=vehicles.vehicle_id, columns=periods.period).fillna(0.0)
    matrix = pivot.to_numpy(float)
    duration = periods.duration_h.to_numpy(float)
    delivered = matrix @ duration
    requested = vehicles.energy_kwh.to_numpy(float)
    energy_residual = delivered - requested
    total = matrix.sum(axis=0)
    headroom = periods.capacity_kw.to_numpy(float) - periods.base_load_kw.to_numpy(float)
    capacity_residual = total - headroom
    upper = np.zeros_like(matrix)
    availability_errors = 0
    for vi, row in vehicles.reset_index(drop=True).iterrows():
        upper[vi, int(row.arrival_period):int(row.departure_period)] = float(row.max_charge_kw)
        availability_errors += int(np.sum(np.abs(matrix[vi, :int(row.arrival_period)]) > 1e-8))
        availability_errors += int(np.sum(np.abs(matrix[vi, int(row.departure_period):]) > 1e-8))
    tolerance = float(config.get("validation_tolerance", 1e-7))
    checks = {
        "energy_balance": float(np.max(np.abs(energy_residual), initial=0.0)) <= tolerance,
        "capacity": float(np.max(capacity_residual, initial=0.0)) <= tolerance,
        "lower_bounds": float(np.min(matrix, initial=0.0)) >= -tolerance,
        "upper_bounds": float(np.max(matrix - upper, initial=0.0)) <= tolerance,
        "availability": availability_errors == 0,
    }
    c, _, _, _, _, _ = _allocation_problem(periods, vehicles, config)
    objective = float(c @ matrix.reshape(-1))
    if result_path:
        claimed = read_json(result_path)
        if claimed.get("status") != "optimal" or abs(float(claimed.get("objective", math.inf)) - objective) > tolerance:
            checks["reported_objective"] = False
            errors.append({"type": "reported_objective_mismatch", "recomputed": objective,
                           "reported": claimed.get("objective")})
        else:
            checks["reported_objective"] = True
    status = "pass" if all(checks.values()) and not errors else "fail"
    return {
        "schema": "senior_projectx.project.validation.v1", "status": status,
        "method": "independent reconstruction from delivered allocation CSV",
        "checks": checks, "errors": errors,
        "maximum_energy_residual_kwh": float(np.max(np.abs(energy_residual), initial=0.0)),
        "maximum_capacity_violation_kw": float(max(0.0, np.max(capacity_residual, initial=0.0))),
        "minimum_capacity_margin_kw": float(np.min(headroom - total, initial=0.0)),
        "recomputed_objective": objective,
    }


def build_brief(manifest_path: Path, task_id: str, result_path: Path,
                validation_path: Path, table_path: Path, max_rows: int = 12) -> dict:
    manifest, result, validation = read_json(manifest_path), read_json(result_path), read_json(validation_path)
    tasks = manifest.get("project", {}).get("tasks", [])
    task = next((t for t in tasks if t.get("task_id") == task_id), None)
    if not task:
        raise ValueError(f"Unknown task_id: {task_id}")
    table = load_table(table_path)
    return {
        "schema": "senior_projectx.project.chapter_brief.v1",
        "task_id": task_id,
        "technical_question": task["question"],
        "upstream_objects": task.get("upstream_objects", task.get("data_objects", [])),
        "model": task["model"],
        "result_source": {"path": str(result_path), "pointers": ["/status", "/objective", "/capacity_margin_kw"]},
        "validation_source": {"path": str(validation_path), "pointers": ["/status", "/checks", "/maximum_energy_residual_kwh"]},
        "table_source": {"path": str(table_path), "slice": f"rows[0:{min(max_rows, len(table))}]",
                         "records": table.head(max_rows).to_dict(orient="records")},
        "facts": {
            "solver_status": result.get("status"),
            "objective": result.get("objective"),
            "minimum_capacity_margin_kw": validation.get("minimum_capacity_margin_kw"),
            "maximum_energy_residual_kwh": validation.get("maximum_energy_residual_kwh"),
        },
        "writing_instruction": "仅使用上述路径、JSON 指针和表格切片中的当前事实；区分计算结果、解释和建议。",
    }


def lineage_record(manifest_path: Path, artifact: Path, dependencies: list[Path], *, role: str = "") -> dict:
    manifest = read_json(manifest_path)
    base = manifest_path.parent.resolve()
    def rel(path: Path) -> str:
        path = path.resolve()
        try:
            return os.path.relpath(path, base).replace("\\", "/")
        except ValueError:
            return str(path)
    record = {
        "artifact": rel(artifact), "role": role,
        "dependencies": [{"path": rel(path), "fingerprint": semantic_fingerprint(path.resolve())} for path in dependencies],
    }
    lineage = manifest.setdefault("project", {}).setdefault("lineage", [])
    lineage[:] = [r for r in lineage if r.get("artifact") != record["artifact"]]
    lineage.append(record)
    write_json(manifest_path, manifest)
    return record


def lineage_check(manifest_path: Path) -> dict:
    manifest = read_json(manifest_path)
    base = manifest_path.parent.resolve()
    records = []
    for record in manifest.get("project", {}).get("lineage", []):
        changed = []
        for dep in record.get("dependencies", []):
            path = resolve(base, dep["path"])
            if not path.is_file() or semantic_fingerprint(path) != dep.get("fingerprint"):
                changed.append(dep["path"])
        artifact = resolve(base, record["artifact"])
        status = "stale" if changed else ("current" if artifact.is_file() else "missing")
        records.append({"artifact": record["artifact"], "role": record.get("role", ""),
                        "status": status, "changed_dependencies": changed})
    return {"schema": "senior_projectx.project.lineage_check.v1",
            "status": "pass" if all(r["status"] == "current" for r in records) else "fail",
            "artifacts": records}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Senior-ProjectX research chain: contracts, data, solve, validation, briefs, and lineage.")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("define-task", help="Add or explicitly replace one task contract in project_manifest.json.")
    q.add_argument("manifest", type=Path); q.add_argument("contract", type=Path); q.add_argument("--replace", action="store_true")
    q = sub.add_parser("audit-data", help="Audit fields, units, identifiers, time, ranges, legal zeros, populations, and joins.")
    q.add_argument("data", type=Path); q.add_argument("--schema", required=True, type=Path); q.add_argument("--out", required=True, type=Path)
    q = sub.add_parser("solve-allocation", help="Solve a continuous multi-period charging allocation LP.")
    q.add_argument("--periods", required=True, type=Path); q.add_argument("--vehicles", required=True, type=Path)
    q.add_argument("--config", required=True, type=Path); q.add_argument("--allocation-out", required=True, type=Path); q.add_argument("--out", required=True, type=Path)
    q = sub.add_parser("validate-allocation", help="Independently rebuild allocation constraints and objective.")
    q.add_argument("--periods", required=True, type=Path); q.add_argument("--vehicles", required=True, type=Path)
    q.add_argument("--config", required=True, type=Path); q.add_argument("--allocation", required=True, type=Path)
    q.add_argument("--result", type=Path); q.add_argument("--out", required=True, type=Path)
    q = sub.add_parser("brief", help="Build a chapter brief from exact current JSON pointers and a bounded table slice.")
    q.add_argument("manifest", type=Path); q.add_argument("--task-id", required=True); q.add_argument("--result", required=True, type=Path)
    q.add_argument("--validation", required=True, type=Path); q.add_argument("--table", required=True, type=Path)
    q.add_argument("--max-rows", type=int, default=12); q.add_argument("--out", required=True, type=Path)
    q = sub.add_parser("bounded-sum", help="Solve a continuous bounded single-sum linear allocation.")
    q.add_argument("input", type=Path); q.add_argument("--out", required=True, type=Path)
    q = sub.add_parser("replay-dag", help="Replay a caller-supplied dependency/resource order; no schedule optimization.")
    q.add_argument("input", type=Path); q.add_argument("--out", required=True, type=Path)
    q = sub.add_parser("record-lineage", help="Bind one downstream artifact to only its declared upstream files.")
    q.add_argument("manifest", type=Path); q.add_argument("--artifact", required=True, type=Path)
    q.add_argument("--depends-on", action="append", required=True, type=Path); q.add_argument("--role", default="")
    q = sub.add_parser("check-lineage", help="Report missing or stale downstream artifacts after upstream changes.")
    q.add_argument("manifest", type=Path); q.add_argument("--out", type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "define-task":
        result = define_task(args.manifest.resolve(), args.contract.resolve(), replace=args.replace)
    elif args.command == "audit-data":
        result = audit_data(args.data.resolve(), args.schema.resolve()); write_json(args.out.resolve(), result)
    elif args.command == "solve-allocation":
        result = solve_allocation(args.periods.resolve(), args.vehicles.resolve(), args.config.resolve(), args.allocation_out.resolve()); write_json(args.out.resolve(), result)
    elif args.command == "validate-allocation":
        result = validate_allocation(args.periods.resolve(), args.vehicles.resolve(), args.config.resolve(), args.allocation.resolve(), args.result.resolve() if args.result else None); write_json(args.out.resolve(), result)
    elif args.command == "brief":
        result = build_brief(args.manifest.resolve(), args.task_id, args.result.resolve(), args.validation.resolve(), args.table.resolve(), args.max_rows); write_json(args.out.resolve(), result)
    elif args.command == "bounded-sum":
        data = read_json(args.input.resolve()); result = bounded_sum_linear(data["costs"], data["lower"], data["upper"], data["total"]); write_json(args.out.resolve(), result)
    elif args.command == "replay-dag":
        data = read_json(args.input.resolve()); result = dag_timing_replay(data["nodes"], data["order"]); write_json(args.out.resolve(), result)
    elif args.command == "record-lineage":
        result = lineage_record(args.manifest.resolve(), args.artifact.resolve(), [p.resolve() for p in args.depends_on], role=args.role)
    elif args.command == "check-lineage":
        result = lineage_check(args.manifest.resolve())
        if args.out: write_json(args.out.resolve(), result)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") not in {"fail", "infeasible_or_failed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
