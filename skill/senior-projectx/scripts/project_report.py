#!/usr/bin/env python3
"""Chinese figure and editable Word-report builder for the Senior-ProjectX."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from PIL import Image
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_font(candidates: Iterable[str]) -> tuple[str, str]:
    from matplotlib import font_manager
    available = {f.name.lower(): f.name for f in font_manager.fontManager.ttflist}
    for candidate in candidates:
        if candidate.lower() in available:
            return available[candidate.lower()], "requested"
    fallback = font_manager.FontProperties().get_name()
    return fallback, "fallback"


def font_contract() -> dict:
    chinese, status = resolve_font(["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"])
    latin, latin_status = resolve_font(["Times New Roman", "Liberation Serif", "DejaVu Serif"])
    return {"chinese": chinese, "chinese_status": status, "latin": latin, "latin_status": latin_status,
            "chinese_weight": "bold" if chinese != "SimHei" else "normal"}


def _style_figure_text(label, fonts: dict, size: float) -> None:
    has_chinese = bool(re.search(r"[\u3400-\u9fff]", label.get_text()))
    # Latin-first glyph fallback preserves TNR digits in mixed CJK/unit labels.
    label.set_fontfamily([fonts["latin"], fonts["chinese"]] if has_chinese else [fonts["latin"]])
    label.set_fontweight(fonts.get("chinese_weight", "bold") if has_chinese else "normal")
    label.set_fontsize(size)


def _mixed_axis(ax, fonts: dict, *, label_size: float = 10, tick_size: float = 9) -> None:
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        _style_figure_text(label, fonts, tick_size)
    for label in [ax.xaxis.label, ax.yaxis.label, ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()]:
        _style_figure_text(label, fonts, label_size if label in [ax.xaxis.label, ax.yaxis.label] else tick_size)
    ax.grid(True, axis="y", color="#DADAE2", linewidth=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    for spine in ax.spines.values():
        spine.set_color("#131419")
        spine.set_linewidth(.7)
    ax.tick_params(colors="#131419", width=.7)


def _figure_text_color(fill) -> str:
    """Choose the higher-contrast neutral text against an actual scalar fill."""
    rgb = np.asarray(fill[:3])
    linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    luminance = float(linear @ [.2126, .7152, .0722])
    return "#FFFFFF" if luminance < .179 else "#131419"


def _margin_label(value: float, decimals: int = 0) -> str:
    """A positive nonbinding margin must not acquire a printed zero."""
    if abs(value) <= 1e-7:
        value = 0.0
    if value != 0 and round(value, decimals) == 0:
        return f"{value:.2g}"
    return f"{value:.{decimals}f}"


def _check_figure_allocation(values, available, limits, duration, demand, source):
    """Check the quantities a window/energy graphic would otherwise misstate."""
    if (values < -1e-7).any() or (values > limits[:, None] + 1e-7).any():
        raise ValueError(f"{source}: allocation is outside vehicle power bounds")
    if (np.abs(values[~available]) > 1e-7).any():
        raise ValueError(f"{source}: allocation occurs outside an availability window")
    if not np.allclose(values @ duration, demand, atol=1e-6, rtol=1e-7):
        raise ValueError(f"{source}: allocation contradicts requested vehicle energy")


def _allocation_matrix(path: Path, roster: pd.MultiIndex, shape: tuple[int, int]) -> np.ndarray:
    table = pd.read_csv(path)
    required = {"vehicle_id", "period", "charge_kw"}
    if required - set(table.columns):
        raise ValueError(f"{path.name} is missing vehicle_id, period or charge_kw")
    rows = table.set_index(["vehicle_id", "period"]).charge_kw
    if not rows.index.is_unique or len(rows) != len(roster) or not roster.isin(rows.index).all():
        raise ValueError(f"{path.name} must include exactly one charge for every vehicle and period")
    values = pd.to_numeric(rows.reindex(roster), errors="coerce").to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError(f"{path.name} contains a missing or nonfinite charge")
    return values.reshape(shape)


def _single_vehicle_shift(allocation, available, limits, margin, duration, periods, vehicles, source):
    """Find the largest move to one slot for one vehicle, with all other charges fixed."""
    room = np.minimum(limits[:, None] - allocation, margin[None, :]).clip(min=0)
    receiving_energy = np.where(available, room * duration, 0.0)
    receiving_energy[:, source] = 0
    donated_energy = allocation[:, source] * duration[source]
    possible = np.minimum(donated_energy[:, None], receiving_energy)
    vehicle, destination = np.unravel_index(possible.argmax(), possible.shape)
    energy = possible[vehicle, destination]
    if energy <= 1e-7:
        return None
    return {
        "vehicle": str(vehicles[vehicle]), "origin": int(periods[source]), "destination": int(periods[destination]),
        "energy_kwh": float(energy), "destination_charge_increase_kw": float(energy / duration[destination]),
        "released_kw": float(energy / duration[source]),
        "departure_energy_kwh": float(allocation[vehicle] @ duration),
    }


def build_figures(periods_path: Path, allocation_path: Path, vehicles_path: Path,
                  sensitivity_path: Path, output_dir: Path) -> dict:
    """Render sourced constraint, response-window and scenario diagnostics."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.patches import Patch, Rectangle
    periods = pd.read_csv(periods_path)
    vehicles = pd.read_csv(vehicles_path)
    sensitivity = pd.read_csv(sensitivity_path)
    ids = periods.period.to_numpy()
    if (periods.empty or vehicles.empty or periods.period.isna().any() or vehicles.vehicle_id.isna().any()
            or not periods.period.is_unique or not vehicles.vehicle_id.is_unique):
        raise ValueError("Periods and vehicles must have unique, nonempty IDs")
    roster = pd.MultiIndex.from_product((vehicles.vehicle_id, ids))
    shape = (len(vehicles), len(ids))
    allocation = _allocation_matrix(allocation_path, roster, shape)
    x = np.arange(len(ids))
    base = periods.base_load_kw.to_numpy(float)
    capacity = periods.capacity_kw.to_numpy(float)
    total = allocation.sum(axis=0)
    duration = periods.duration_h.to_numpy(float)
    limits = vehicles.max_charge_kw.to_numpy(float)
    demand = vehicles.energy_kwh.to_numpy(float)
    numeric = [base, capacity, duration, limits, demand]
    if not all(np.isfinite(values).all() for values in numeric):
        raise ValueError("Figure inputs contain missing or nonfinite physical quantities")
    if (duration <= 0).any() or any((values < 0).any() for values in (base, capacity, limits, demand)):
        raise ValueError("Figure inputs require positive durations and nonnegative loads, capacities and demands")
    available = np.zeros(shape, dtype=bool)
    uniform = np.zeros(len(ids))
    for i, v in enumerate(vehicles.itertuples()):
        if not (int(v.arrival_period) == v.arrival_period and int(v.departure_period) == v.departure_period
                and 0 <= v.arrival_period < v.departure_period <= len(ids)):
            raise ValueError(f"Invalid availability window for {v.vehicle_id}")
        mask = (x >= v.arrival_period) & (x < v.departure_period)
        available[i] = mask
        uniform[mask] += v.energy_kwh / duration[mask].sum()
    _check_figure_allocation(allocation, available, limits, duration, demand, allocation_path.name)
    margin = capacity-base-total
    if (margin < -1e-6).any():
        raise ValueError("Saved allocation exceeds period capacity")
    uniform_margin = capacity-base-uniform
    shift_example = _single_vehicle_shift(allocation, available, limits, margin, duration, ids,
                                         vehicles.vehicle_id.to_numpy(), int(np.argmin(margin)))

    # Validate the full scenario set before producing any output files.
    if sensitivity.empty or sensitivity.status.isna().any():
        raise ValueError("Scenario status is required for every scenario")
    sensitivity = sensitivity.sort_values("demand_scale").reset_index(drop=True)
    all_scales = sensitivity.demand_scale.to_numpy(float)
    if (not np.isfinite(all_scales).all() or (all_scales < 0).any()
            or len(set(f"{scale:.2f}" for scale in all_scales)) != len(all_scales)):
        raise ValueError("Demand scales must map to distinct nonnegative scenario filenames")
    feasible = sensitivity[sensitivity.status == "optimal"].sort_values("demand_scale")
    if feasible.empty:
        raise ValueError("No feasible scenario traces available for a scenario atlas")
    scales = feasible.demand_scale.to_numpy(float)
    if not np.isfinite(scales).all() or len(set(f"{scale:.2f}" for scale in scales)) != len(scales):
        raise ValueError("Feasible demand scales must map to distinct scenario filenames")
    margins, scenario_sources, added_load = [], [], {}
    baseline_matches = False
    for row in feasible.itertuples():
        path = sensitivity_path.parent / "scenarios" / f"allocation_{row.demand_scale:.2f}.csv"
        if not path.is_file():
            raise FileNotFoundError("Scenario atlas requires saved allocation: " + str(path))
        values = _allocation_matrix(path, roster, shape)
        if row.demand_scale == 1.0:
            baseline_matches = np.allclose(values, allocation, atol=1e-7, rtol=0)
        charge = values.sum(axis=0)
        scenario_margin = capacity-base-charge
        if not np.isclose(row.mean_margin_kw, scenario_margin.mean(), atol=1e-6, rtol=1e-7):
            raise ValueError(f"{path.name} contradicts its reported mean capacity margin")
        if not np.isclose(row.minimum_margin_kw, scenario_margin.min(), atol=1e-6, rtol=1e-7):
            raise ValueError(f"{path.name} contradicts its reported minimum capacity margin")
        _check_figure_allocation(values, available, limits, duration, demand*row.demand_scale, path.name)
        if (scenario_margin < -1e-6).any():
            raise ValueError(f"{path.name} exceeds period capacity")
        newly_full = np.flatnonzero((margin > 1e-7) & (scenario_margin <= 1e-7))
        if newly_full.size:
            col = newly_full[0]
            changes = values[:, col] - allocation[:, col]
            growing = np.flatnonzero(changes > 1e-7)
            if 0 < growing.size <= 2 and np.all(changes >= -1e-7):
                added_load[row.demand_scale] = {"period": int(ids[col]), "baseline_margin_kw": float(margin[col]),
                    "increases_kw": {str(vehicles.vehicle_id.iloc[index]): float(changes[index]) for index in growing}}
        margins.append(scenario_margin)
        scenario_sources.append(path)
    margins = np.asarray(margins)
    shortfalls = {}
    for row in sensitivity.itertuples():
        if row.status != "infeasible":
            continue
        shortfall = _scenario_energy_shortfall(sensitivity_path, row.demand_scale)
        if shortfall is not None:
            shortfalls[row.demand_scale] = shortfall
            result_path = sensitivity_path.parent / "scenarios" / f"result_{row.demand_scale:.2f}.json"
            original = read_json(result_path)
            scenario_sources.extend([result_path, Path(original["periods_path"]), Path(original["vehicles_path"])])

    palette_path = Path(__file__).resolve().parents[1] / "templates" / "research_figure_palette.json"
    catalog = read_json(palette_path)
    colors = catalog["colors"]
    role_names = {"structure": "ink", "baseline": "cobalt", "allocation": "jade",
                  "comparison": "iris", "nonnegative_margin": "jade", "violation": "raspberry"}
    role_meanings = {"structure": "坐标、文字与物理限值", "baseline": "基础状态",
                     "allocation": "实际分配", "comparison": "同窗均分参考",
                     "nonnegative_margin": "容量减总负荷后的非负余量", "violation": "负余量或不可行状态"}
    roles = {role: {"catalog_key": key, "color": colors[key], "meaning": role_meanings[role]}
             for role, key in role_names.items()}
    jade_map = LinearSegmentedColormap.from_list("project_jade", [colors[key] for key in catalog["project_sequential"]])
    ink, jade, cobalt, iris = (colors[key] for key in ("ink", "jade", "cobalt", "iris"))

    output_dir.mkdir(parents=True, exist_ok=True)
    fonts = font_contract()
    if fonts["chinese_status"] != "requested" or fonts["latin_status"] != "requested":
        raise RuntimeError("Required Chinese and Latin figure fonts or approved fallbacks are unavailable")
    plt.rcParams.update({"font.size": 9, "axes.unicode_minus": False, "pdf.fonttype": 42,
                         "ps.fonttype": 42, "text.color": ink, "axes.labelcolor": ink})
    artifacts = []

    def layer(role, encoding, source, definition):
        return {"role": role, "encoding": encoding, "evidence_source": str(source), "evidence_definition": definition}

    def save(fig, name, identity, role, question, caption, sources, layers, kind, *, scales=(), evidence=None):
        for ax in fig.axes:
            _mixed_axis(ax, fonts)
            if ax.images or ax.patches: ax.grid(False)
            for label in ax.texts: _style_figure_text(label, fonts, label.get_fontsize())
            if ax.get_legend():
                for label in ax.get_legend().get_texts(): _style_figure_text(label, fonts, 8)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        clipped = []
        labels = list(fig.texts)
        for ax in fig.axes:
            labels.extend(ax.texts)
            if ax.axison:
                labels.extend(ax.get_xticklabels() + ax.get_yticklabels())
                labels.extend([ax.xaxis.label, ax.yaxis.label, ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()])
            if ax.get_legend():
                labels.extend(ax.get_legend().get_texts())
        for label in labels:
            if not label.get_visible() or not label.get_text().strip():
                continue
            box = label.get_window_extent(renderer)
            if box.x0 < -.5 or box.y0 < -.5 or box.x1 > fig.bbox.width+.5 or box.y1 > fig.bbox.height+.5:
                clipped.append(label.get_text())
        if clipped:
            plt.close(fig)
            raise ValueError("Rendered text exceeds figure canvas: " + ", ".join(clipped))
        path = output_dir / name
        exports = {}
        for extension in ("png", "pdf"):
            target = path.with_suffix("." + extension)
            with matplotlib.rc_context({"savefig.bbox": None}):
                fig.savefig(target, dpi=600, facecolor=colors["paper"])
            exports[extension] = {"path": str(target), "sha256": file_hash(target)}
        height_cm = fig.get_size_inches()[1] * 2.54
        plt.close(fig)
        sources = list(dict.fromkeys(map(str, sources)))
        artifacts.append({"id": identity, "path": str(path), "role": role, "question": question,
                          "width_cm": 15.6, "caption": caption, "plot_type": kind, "source": sources,
                           "source_sha256": {s: file_hash(Path(s)) for s in sources}, "plot_layers": layers,
                           "exports": exports, "numerical_evidence": evidence or {},
                           "generator_script": str(Path(__file__).resolve()),
                           "render_contract": {"schema": "senior_projectx.figure.render.v1",
                                               "palette_source": str(palette_path), "palette_sha256": file_hash(palette_path),
                                               "roles": roles, "scales": list(scales), "height_cm": height_cm,
                                               "raster_dpi": 600, "clipped_text": clipped}})

    width_in = 15.6 / 2.54
    fig, (ax, residual) = plt.subplots(2, 1, figsize=(width_in, 4.05), sharex=True,
                                    gridspec_kw={"height_ratios": [2.2, 1]}, constrained_layout=True)
    ax.step(x, base, where="mid", color=cobalt, linestyle="-.", label="基础负荷")
    ax.step(x, base+total, where="mid", color=jade, linewidth=1.6, label="分配后负荷")
    ax.step(x, base+uniform, where="mid", color=iris, linestyle=":", marker="s", markersize=3,
            markerfacecolor="white", label="均分参考")
    ax.step(x, capacity, where="mid", color=ink, linestyle="--", label="容量边界")
    ax.fill_between(x, base+total, capacity, step="mid", color=colors["jade_wash"])
    ax.set_ylabel("功率（kW）")
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=4, frameon=False)
    residual.fill_between(x, 0, np.maximum(margin, 0), step="mid", color=colors["jade_wash"])
    residual.fill_between(x, 0, np.minimum(margin, 0), step="mid", color=colors["raspberry_wash"])
    residual.step(x, margin, where="mid", color=jade)
    residual.step(x, uniform_margin, where="mid", color=iris, linestyle=":", marker="s", markersize=3,
                  markerfacecolor="white")
    residual.axhline(0, color=ink, linewidth=.7)
    tightest = np.flatnonzero(np.isclose(margin, margin.min(), atol=1e-7, rtol=0))
    residual.scatter(x[tightest], margin[tightest], color=colors["sun"], edgecolor=ink, zorder=5)
    residual.annotate(f"最小余量 {margin.min():.1f} kW", (x[tightest[0]], margin[tightest[0]]),
                      xytext=(8, 8), textcoords="offset points", fontsize=8)
    residual.set_ylabel("余量（kW）"); residual.set_xlabel("时段")
    residual.set_xticks(x, ids); residual.set_xlim(-.3, len(ids)-.7)
    save(fig, "figure_constraint_diagnostic.png", "figure_process", "过程与约束",
         "时间分配如何改变各时段容量占用和剩余容量？", "图1 充电时序、容量边界与逐时段余量",
         [periods_path, allocation_path, vehicles_path],
         [layer("observed_time_series", "line", periods_path, "基础负荷、容量和逐车辆均分参考使用原始时段与窗口"),
          layer("constraint_margin", "step_area", allocation_path, "余量等于容量减基础负荷再减实际分配功率，圆点标出最紧时段")],
         "temporal_diagnostic", evidence={"margin_kw": margin.tolist(),
             "tightest_periods": ids[tightest].tolist(), "uniform_margin_kw": uniform_margin.tolist(),
             "uniform_minimum_margin_kw": float(uniform_margin.min()),
             "uniform_capacity_breach_periods": ids[uniform_margin < -1e-7].tolist()})

    fig, ax = plt.subplots(figsize=(width_in, 3.45), constrained_layout=True)
    upper = float(vehicles.max_charge_kw.max())
    power_norm = Normalize(vmin=0, vmax=upper if upper > 0 else 1)
    for row, v in enumerate(vehicles.itertuples()):
        mask = available[row]
        for j in np.flatnonzero(mask):
            ax.add_patch(Rectangle((j-.46, row-.33), .92, .66, facecolor=colors["cobalt_wash"],
                                   edgecolor=ink, linewidth=.45))
            if allocation[row, j] <= 1e-9:
                ax.text(j, row, "0", ha="center", va="center", fontsize=8, color=ink)
        values = allocation[row]
        for j in np.flatnonzero(values > 1e-9):
            value = values[j]
            fill = jade_map(power_norm(value))
            ax.add_patch(Rectangle((j-.46, row-.33), .92, .66, facecolor=fill, edgecolor=ink, linewidth=.45))
            ax.text(j, row, f"{value:.1f}", ha="center", va="center", fontsize=8,
                    color=_figure_text_color(fill))
        delivered = float(np.dot(values, duration))
        ax.text(len(ids)-.15, row, f"{delivered:.1f}/{v.energy_kwh:.1f}", va="center", fontsize=8)
    ax.text(len(ids)-.15, -.75, "交付/需求（kWh）", fontsize=8, va="center")
    ax.set_xlim(-.65, len(ids)+1.65); ax.set_ylim(len(vehicles)-.4, -1.03)
    ax.set_xticks(x, ids); ax.set_yticks(np.arange(len(vehicles)), vehicles.vehicle_id)
    ax.set_xlabel("时段"); ax.set_ylabel("车辆")
    ax.legend(handles=[Patch(facecolor=colors["cobalt_wash"], edgecolor=ink, label="可用且未充电")],
              loc="upper left", bbox_to_anchor=(0, 1.12), frameon=False)
    if upper > 0:
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=power_norm, cmap=jade_map), ax=ax,
                          orientation="horizontal", pad=.16, fraction=.07, aspect=35)
        cb.set_label("实际充电功率（kW）")
        cb.set_ticks([0, upper/2, upper])
    save(fig, "figure_window_allocation.png", "figure_balance", "对象守恒与时间窗",
         "各对象如何在自身窗口和功率边界内满足需求电量？", "图2 车辆接入窗口、功率分配与电量满足关系",
         [periods_path, allocation_path, vehicles_path],
         [layer("coverage", "gantt", vehicles_path, "浅蓝零值格表示可用且未充电；空白为窗口外，不计作缺测或零功率格"),
          layer("conditional_response", "annotated_tiles", allocation_path, "着色格及数值给出真实功率，右列比较累计交付与需求电量")],
         "response_diagnostic", scales=[{"quantity": "charge_kw", "unit": "kW", "normalization": "sequential",
             "vmin": 0, "vmax": upper, "data_min": float(allocation.min()), "data_max": float(allocation.max()),
             "zero_meaning": "已知充电功率为零", "catalog_stops": catalog["project_sequential"]}],
         evidence={"delivered_energy_kwh": (allocation @ duration).tolist(), "requested_energy_kwh": demand.tolist(),
                   "single_vehicle_shift": shift_example})

    fig, (ax, summary) = plt.subplots(1, 2, figsize=(width_in, 3.9), sharey=True,
                                    gridspec_kw={"width_ratios": [3.9, 1.9]}, constrained_layout=True)
    display_margin = np.maximum(margins, 0)
    matrix = np.full((len(sensitivity), len(ids)), np.nan)
    optimal_rows = np.flatnonzero(sensitivity.status.to_numpy() == "optimal")
    matrix[optimal_rows] = display_margin
    max_margin = float(display_margin.max())
    mesh = ax.imshow(np.ma.masked_invalid(matrix), cmap=jade_map, aspect="auto", interpolation="nearest",
                     vmin=0, vmax=max_margin if max_margin > 0 else 1)
    for i in optimal_rows:
        for j in range(len(ids)):
            value = 0.0 if abs(matrix[i,j]) < 1e-7 else matrix[i,j]
            fill = jade_map(mesh.norm(value))
            ax.text(j, i, _margin_label(value), ha="center", va="center", fontsize=8,
                    color=_figure_text_color(fill))
            if abs(value) < 1e-7:
                ax.add_patch(Rectangle((j-.47, i-.47), .94, .94, fill=False, edgecolor=ink, linewidth=.8))
    ax.set_xticks(x, ids); ax.set_yticks(np.arange(len(sensitivity)), [f"{v:.2f}" for v in sensitivity.demand_scale])
    ax.set_xlabel("时段"); ax.set_ylabel("需求倍率")
    if max_margin > 0:
        cb = fig.colorbar(mesh, ax=[ax, summary], orientation="horizontal", pad=.18, fraction=.08, aspect=35)
        cb.set_label("容量余量（kW），黑框为满载时段")
        cb.set_ticks([0, max_margin/2, max_margin])
    summary.set_xlim(0, 1); summary.set_ylim(len(sensitivity)-.5, -1.2)
    for pos, label in ((.16, "最小\n(kW)"), (.50, "平均\n(kW)"), (.85, "满载\n时段数")):
        summary.text(pos, -.8, label, fontsize=8.5, ha="center", va="center")
    scenario_summary = []
    headroom_energy = float(np.maximum(capacity-base, 0) @ duration)
    for i, row in enumerate(sensitivity.itertuples()):
        record = {"demand_scale": float(row.demand_scale), "status": str(row.status)}
        if row.status == "optimal":
            values = matrix[i]
            full = values <= 1e-7
            record.update(minimum_margin_kw=float(values.min()), mean_margin_kw=float(values.mean()),
                          binding_period_count=int(full.sum()), binding_periods=ids[full].tolist())
            if baseline_matches and row.demand_scale in added_load:
                record["newly_full_example"] = added_load[row.demand_scale]
            summary.text(.16, i, _margin_label(record['minimum_margin_kw'], 1), fontsize=8.5, va="center", ha="center")
            summary.text(.50, i, f"{record['mean_margin_kw']:.2f}", fontsize=8.5, va="center", ha="center")
            summary.text(.85, i, str(record["binding_period_count"]), fontsize=8.5, va="center", ha="center")
        else:
            label = "不可行" if row.status == "infeasible" else str(row.status)
            if row.demand_scale in shortfalls:
                requested_energy, available_energy = shortfalls[row.demand_scale]
                shortfall = requested_energy-available_energy
                label += f"，电量缺口至少 {shortfall:g} kWh"
                record.update(energy_shortfall_lower_bound_kwh=shortfall, requested_energy_kwh=requested_energy,
                              available_energy_bound_kwh=available_energy)
            ax.text((len(ids)-1)/2, i, label, color=colors["raspberry"], fontsize=8, ha="center", va="center")
            for pos in (.16, .50, .85):
                summary.text(pos, i, "—", fontsize=8.5, ha="center", va="center")
        scenario_summary.append(record)
    summary.set_axis_off()
    save(fig, "figure_scenario_constraint_atlas.png", "figure_sensitivity", "情景与容量压力",
         "需求增长后哪些时段达到容量上限，平均余量能否代表局部约束？", "图3 需求增长下的逐时段容量余量、满载时段与不可行情景",
         [periods_path, vehicles_path, sensitivity_path, *scenario_sources],
         [layer("constraint_margin", "conditional_matrix", scenario_sources[0], "逐情景读取实际分配序列，逐时段计算容量余量；每一情景源文件均列于source"),
          layer("conditional_response", "aligned_numeric_profile", sensitivity_path, "按同一情景行对齐最小和平均余量、满载时段数；不可行保留状态，容量总额给出缺口下界")],
         "composite_diagnostic", scales=[{"quantity": "capacity_margin_kw", "unit": "kW", "normalization": "sequential",
             "vmin": 0, "vmax": max_margin, "data_min": float(display_margin.min()), "data_max": max_margin,
             "zero_meaning": "容量恰好占满，黑框标识", "catalog_stops": catalog["project_sequential"]}],
         evidence={"scenario_summary": scenario_summary, "headroom_energy_kwh": headroom_energy,
                   "baseline_requested_energy_kwh": float(demand.sum()), "zero_tolerance_kw": 1e-7})

    for item in artifacts:
        item["sha256"] = file_hash(Path(item["path"]))
        with Image.open(item["path"]) as rendered:
            item["pixel_size"] = [rendered.width, rendered.height]
            item["aspect_ratio"] = round(rendered.width / rendered.height, 6)
        item["font_contract"] = fonts
        item["final_size_typography"] = {"axis_label_pt": 10, "tick_pt": 9, "legend_pt": 8}
    return {"schema": "senior_projectx.project.figure_manifest.v1", "language": "chinese",
            "no_default_suptitle": True, "artifacts": artifacts, "font_contract": fonts}


def _set_cell_margin(cell, top=80, start=90, bottom=80, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar"); tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}"); tc_mar.append(node)
        node.set(qn("w:w"), str(value)); node.set(qn("w:type"), "dxa")


def _set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    element = OxmlElement("w:tblHeader"); element.set(qn("w:val"), "true"); tr_pr.append(element)


def _set_run_font(run, chinese="SimSun", latin="Times New Roman", size=12, bold=False):
    run.font.name = latin; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = RGBColor(0, 0, 0)
    fonts = run._element.get_or_add_rPr().rFonts
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn(f"w:{attr}"), None)
    fonts.set(qn("w:eastAsia"), chinese)


def _paragraph_role(paragraph, role: str) -> None:
    """Apply the explicit default-profile role; prose prefixes never infer captions."""
    if role not in {"body", "heading", "caption", "table", "display", "figure", "reference"}:
        raise ValueError(f"Unknown Project paragraph role: {role}")
    pf = paragraph.paragraph_format
    pf.widow_control = True
    pf.left_indent = Pt(0); pf.right_indent = Pt(0)
    pf.first_line_indent = Pt(24 if role == "body" else 0)
    ind = paragraph._element.get_or_add_pPr().get_or_add_ind()
    for attr in ("hanging", "hangingChars", "leftChars", "rightChars"):
        ind.attrib.pop(qn(f"w:{attr}"), None)
    ind.set(qn("w:firstLineChars"), "200" if role == "body" else "0")
    pf.line_spacing = 1.0 if role in {"table", "caption", "display", "figure"} else 1.5
    pf.space_before = Pt(0); pf.space_after = Pt(0)
    pf.alignment = (WD_ALIGN_PARAGRAPH.JUSTIFY if role == "body" else
                    WD_ALIGN_PARAGRAPH.CENTER if role in {"caption", "display", "figure", "table"} else
                    WD_ALIGN_PARAGRAPH.LEFT)
    if role in {"display", "caption", "figure", "table"}:
        pf.tab_stops.clear_all()


def _configure_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    _set_run_font(normal)
    _paragraph_role(normal, "body")
    for name, size in (("Title", 22), ("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)):
        style = doc.styles[name]
        _set_run_font(style, size=size)
        _paragraph_role(style, "heading")
        style.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(6)
        ppr = style._element.get_or_add_pPr()
        border = ppr.find(qn("w:pBdr"))
        if border is not None: ppr.remove(border)
    subtitle = doc.styles["Subtitle"]
    _set_run_font(subtitle, size=14); subtitle.font.italic = False
    _paragraph_role(subtitle, "heading")
    subtitle_ppr = subtitle._element.get_or_add_pPr()
    subtitle_border = subtitle_ppr.find(qn("w:pBdr"))
    if subtitle_border is not None: subtitle_ppr.remove(subtitle_border)
    _set_run_font(doc.styles["Caption"], size=10.5)
    _paragraph_role(doc.styles["Caption"], "caption")


def _configure_page(doc: Document) -> None:
    for section in doc.sections:
        section.page_width = Cm(21.0); section.page_height = Cm(29.7)
        section.top_margin = Cm(2.5); section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.8); section.right_margin = Cm(2.6)


def create_default_template(path: Path) -> None:
    doc = Document(); _configure_styles(doc); _configure_page(doc)
    p = doc.add_paragraph("项目技术研究报告", style="Title"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("按任务书、技术问题与当前证据调整章节", style="Subtitle"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    for heading in ["项目概述与研究任务", "研究对象、资料与数据", "研究专题", "综合技术评价与工程建议", "结论及后续工作"]:
        doc.add_heading(heading, level=1)
        doc.add_paragraph("[按当前项目材料填写]")
    doc.core_properties.author = ""; doc.core_properties.last_modified_by = ""
    path.parent.mkdir(parents=True, exist_ok=True); doc.save(path)


def _clean_template(doc: Document) -> None:
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _append_text(paragraph, text: str, *, formulas: list[dict] | None = None,
                 context: str = "body", equation_backend: str = "mathtype_native", size: float = 12):
    """Explicit $TeX$ spans become inventoried inline math, never faux variables."""
    parts = re.split(r"(\$[^$\r\n]+\$)", text)
    if len(parts) > 1 and formulas is None:
        raise ValueError("Inline mathematics requires an ordered formula manifest")
    for part in parts:
        if not part:
            continue
        if part.startswith("$") and part.endswith("$") and len(part) > 2:
            tex = part[1:-1]
            if equation_backend == "office_math":
                paragraph._p.append(_tex_to_omml(tex, size=size))
            elif equation_backend in {"mathtype_native", "mathtype_toggle_tex"}:
                _set_run_font(paragraph.add_run(part), size=size)
            else:
                raise ValueError(f"Unsupported Project equation backend: {equation_backend}")
            formula_id = f"inline_{len(formulas) + 1:04d}"
            if any(f["formula_id"] == formula_id for f in formulas):
                raise ValueError(f"Duplicate formula ID: {formula_id}")
            formulas.append({"formula_id": formula_id, "tex": tex, "placement": "inline",
                             "context": context, "font_size_pt": size})
        else:
            _set_run_font(paragraph.add_run(part), size=size)


def _add_body(doc: Document, text: str, *, bold_lead: str | None = None,
              formulas: list[dict] | None = None, equation_backend: str = "mathtype_native"):
    p = doc.add_paragraph()
    _paragraph_role(p, "body")
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead); _set_run_font(r, bold=True)
        text = text[len(bold_lead):]
    _append_text(p, text, formulas=formulas, equation_backend=equation_backend)
    return p


def _office_math_xslt() -> Path:
    configured = os.environ.get("OFFICE_MML2OMML_XSL")
    candidates = [
        Path(configured) if configured else None,
        Path(r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL"),
        Path(r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL"),
        Path(r"C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise RuntimeError(
        "office_math requires Microsoft Office MML2OMML.XSL; set OFFICE_MML2OMML_XSL to its path"
    )


def _tex_to_omml(tex: str, *, size: float = 12):
    try:
        from latex2mathml.converter import convert
        from lxml import etree
    except ImportError as exc:
        raise RuntimeError("office_math requires the installed latex2mathml and lxml packages") from exc
    mathml = etree.fromstring(convert(tex).encode("utf-8"))
    transform = etree.XSLT(etree.parse(str(_office_math_xslt())))
    omml = transform(mathml).getroot()
    if omml is None or omml.tag != qn("m:oMath"):
        raise RuntimeError("Microsoft Office MathML transform did not produce one editable m:oMath object")
    for run in omml.xpath(".//m:r", namespaces={"m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}):
        word_properties = OxmlElement("w:rPr")
        fonts = OxmlElement("w:rFonts"); fonts.set(qn("w:ascii"), "Cambria Math"); fonts.set(qn("w:hAnsi"), "Cambria Math")
        font_size = OxmlElement("w:sz"); font_size.set(qn("w:val"), str(round(size * 2)))
        size_cs = OxmlElement("w:szCs"); size_cs.set(qn("w:val"), str(round(size * 2)))
        word_properties.extend([fonts, font_size, size_cs])
        first_text = next((i for i, child in enumerate(run) if child.tag == qn("m:t")), len(run))
        run.insert(first_text, word_properties)
    return omml


def _add_formula(doc: Document, tex: str, formula_id: str, formulas: list[dict], *,
                 context: str = "body", equation_backend: str = "mathtype_native"):
    if any(f["formula_id"] == formula_id for f in formulas):
        raise ValueError(f"Duplicate formula ID: {formula_id}")
    p = doc.add_paragraph(); _paragraph_role(p, "display")
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(6)
    if equation_backend == "office_math":
        p._p.append(_tex_to_omml(tex))
    elif equation_backend in {"mathtype_native", "mathtype_toggle_tex"}:
        literal = r"\[" + tex + r"\]"
        r = p.add_run(literal); _set_run_font(r, size=12)
    else:
        raise ValueError(f"Unsupported Project equation backend: {equation_backend}")
    formulas.append({"formula_id": formula_id, "tex": tex, "placement": "display", "context": context,
                     "font_size_pt": 12})
    return p


def _add_caption(doc: Document, text: str, *, formulas: list[dict] | None = None,
                 equation_backend: str = "mathtype_native"):
    p = doc.add_paragraph(style="Caption"); _paragraph_role(p, "caption")
    p.paragraph_format.keep_with_next = text.startswith("表")
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(6)
    _append_text(p, text, formulas=formulas, context="caption", equation_backend=equation_backend, size=10.5)
    return p


def _add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None,
               *, formulas: list[dict] | None = None, equation_backend: str = "mathtype_native"):
    if not headers or any(len(row) != len(headers) for row in rows):
        raise ValueError("Table rows must match the nonempty header")
    if widths and (len(widths) != len(headers) or any(w <= 0 for w in widths)):
        raise ValueError("Table widths must be positive and match the header")
    table = doc.add_table(rows=1, cols=len(headers)); table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Normal Table"; table.autofit = False
    section = doc.sections[-1]
    available = (section.page_width - section.left_margin - section.right_margin) / Cm(1)
    widths = widths or [available / len(headers)] * len(headers)
    scale = min(1.0, available / sum(widths))
    widths = [w * scale for w in widths]
    for column, width in zip(table.columns, widths): column.width = Cm(width)
    properties = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "left", "right", "insideH", "insideV"):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:val"), "single" if edge in {"top", "bottom"} else "nil")
        node.set(qn("w:color"), "000000"); node.set(qn("w:sz"), "12")
        borders.append(node)
    properties.append(borders)
    look = properties.find(qn("w:tblLook"))
    if look is not None: properties.remove(look)
    _set_repeat_header(table.rows[0])
    for row_index, row in enumerate([headers, *rows]):
        cells = table.rows[0].cells if row_index == 0 else table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]; cell.text = ""; cell.width = Cm(widths[i])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER; _set_cell_margin(cell)
            p = cell.paragraphs[0]; p.clear(); _paragraph_role(p, "table")
            _append_text(p, str(value), formulas=formulas, context="table",
                         equation_backend=equation_backend, size=10.5)
            tcpr = cell._tc.get_or_add_tcPr()
            shading = OxmlElement("w:shd"); shading.set(qn("w:val"), "clear")
            shading.set(qn("w:fill"), "auto"); tcpr.append(shading)
            if row_index == 0:
                cb = OxmlElement("w:tcBorders"); bottom = OxmlElement("w:bottom")
                bottom.set(qn("w:val"), "single"); bottom.set(qn("w:color"), "000000")
                bottom.set(qn("w:sz"), "6"); cb.append(bottom); tcpr.append(cb)
    return table


def _scenario_energy_shortfall(sensitivity_path: Path, scale: float) -> tuple[float, float] | None:
    """Return the actual demand and transformer energy bound for a saved infeasible case."""
    result_path = sensitivity_path.parent / "scenarios" / f"result_{scale:.2f}.json"
    if not result_path.is_file():
        return None
    result = read_json(result_path)
    if result.get("termination") != "infeasible":
        return None
    periods_path = Path(result.get("periods_path", ""))
    vehicles_path = Path(result.get("vehicles_path", ""))
    if not (periods_path.is_file() and vehicles_path.is_file()):
        return None
    periods = pd.read_csv(periods_path)
    vehicles = pd.read_csv(vehicles_path)
    headroom = periods.capacity_kw - periods.base_load_kw
    available = float(headroom.clip(lower=0) @ periods.duration_h)
    demand = float(vehicles.energy_kwh.sum())
    return (demand, available) if demand - available > 1e-7 else None


def _compare_scenario_capacity(low, high, summaries: list[dict]) -> str:
    """Connect the aggregate comparison to the periods where load can be added."""
    difference = high.mean_margin_kw - low.mean_margin_kw
    text = f"设备容量不变时，需求从基准的 {low.demand_scale:.2f} 倍增至 {high.demand_scale:.2f} 倍"
    if abs(difference) > 1e-7:
        signed_change = "减少" if difference < 0 else "增加"
        text += f"后，时段平均余量{signed_change} {_margin_label(abs(difference), 2)} kW（图3）。"
    else:
        text += "后，时段平均余量相同（图3）。"
    by_scale = {item["demand_scale"]: item for item in summaries if item["status"] == "optimal"}
    low_record, high_record = by_scale.get(low.demand_scale, {}), by_scale.get(high.demand_scale, {})
    before, after = low_record.get("binding_periods"), high_record.get("binding_periods")
    if before is None or after is None:
        return text + "要判断某辆车还能增充多少，须核对其接入窗内各时段的容量余量。"
    added = [period for period in after if period not in before]
    relieved = [period for period in before if period not in after]
    example = high_record.get("newly_full_example") if float(low.demand_scale) == 1.0 else None
    if example and example["period"] in added and not relieved:
        items = [f"{car} 多用 {_margin_label(power, 2)} kW" for car, power in example["increases_kw"].items()]
        room = _margin_label(example["baseline_margin_kw"], 2)
        text += f"时段 {example['period']} 原有 {room} kW 余量，" + "，".join(items) + "，正好把余量用完。"
    elif added and relieved:
        text += f"时段 {relieved[0]} 重现余量，时段 {added[0]} 达到容量上限。"
    elif added:
        text += f"在高需求情景中，时段 {added[0]} 也达到容量上限。" if before else f"高需求使时段 {added[0]} 达到容量上限。"
    elif relieved:
        text += f"重排后，原满载的时段 {relieved[0]} 出现余量。"
    elif after:
        text += "两种需求下仍是同一批时段满载。"
    else:
        text += "两种需求下的各时段都保有余量。"
    if after:
        tight = added[0] if added else after[0]
        return text + f"要在时段 {tight} 加充，得先看已经安排在那里充电的车能挪到哪个时段。"
    return text + "高需求下还能增充多少，取决于车辆可接入时段积累的电量。"


def build_report(template_path: Path, manifest_path: Path, audit_paths: list[Path], result_path: Path,
                 validation_path: Path, brief_path: Path, figure_manifest_path: Path,
                 sensitivity_path: Path, output_path: Path, formula_manifest_path: Path) -> dict:
    manifest, result, validation, brief = map(read_json, [manifest_path, result_path, validation_path, brief_path])
    equation_backend = manifest.get("equation_backend", "mathtype_native")
    if equation_backend not in {"mathtype_native", "mathtype_toggle_tex", "office_math"}:
        raise ValueError(f"Unsupported Project equation backend: {equation_backend}")
    figure_manifest = read_json(figure_manifest_path)
    audits = [read_json(path) for path in audit_paths]
    if result.get("status") != "optimal" or validation.get("status") != "pass" or any(a.get("status") != "pass" for a in audits):
        raise ValueError("Allocation example requires a verified feasible result; retain adverse cases in a task-specific report")
    sensitivity = pd.read_csv(sensitivity_path)
    doc = Document(template_path); _configure_styles(doc); _configure_page(doc); _clean_template(doc)
    formulas: list[dict] = []
    title = manifest.get("paper_title", "项目技术研究报告")
    p = doc.add_paragraph(title, style="Title"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("技术研究样章", style="Subtitle"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("摘要", level=1)
    minimum_margin = float(validation["minimum_capacity_margin_kw"])
    _add_body(doc, f"用连续线性规划为各车辆安排充电功率。基准计划满足全部离站电量要求，变压器最小容量余量为 {_margin_label(minimum_margin, 2)} kW。核定可增充电量时，按各车接入窗内的时段余量逐段计算。")
    _add_body(doc, "关键词　充电资源分配、连续线性规划、容量约束、敏感性分析")

    doc.add_heading("1 项目概述与研究任务", level=1)
    _add_body(doc, "充电站在车辆离站前交付规定电量。基础负荷先占用变压器容量，其余功率由同时接入的车辆分配。计划须落实到每辆车的接入时段，并据此核算设备余量。")

    doc.add_heading("2 研究对象、资料与数据", level=1)
    _add_body(doc, "表1列出了算例用到的两组数据。用变压器容量减去同一时段的基础负荷，得到还能用来充电的功率。车辆从到站起可接入，离站时段起不再安排充电。模型据此分配各车所需的电量，每个时段的分配都受车端功率上限约束。两组数据均为合成算例。")
    rows = []
    for audit in audits:
        is_period = "base_load_kw" in audit["profiles"]
        rows.append(["时段数据" if is_period else "车辆数据", str(audit["rows"]),
                     "基础负荷、容量（kW），时长（h）" if is_period else "需求电量（kWh），功率上限（kW），接入窗口"])
    _add_caption(doc, "表1 输入数据及单位")
    _add_table(doc, ["数据对象", "记录数", "主要变量及单位"], rows, [3.0, 2.0, 10.6])

    doc.add_heading("3 数学模型与求解", level=1)
    _add_body(doc, r"模型以时段 $t$ 和车辆 $v$ 为索引。从变压器容量 $C_t$ 扣除基础负荷 $L_t$，得到可分配功率 $H_t$。各车辆分配到的充电功率记为 $x_{v,t}$。", formulas=formulas, equation_backend=equation_backend)
    _add_formula(doc, r"H_t=C_t-L_t", "headroom", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"\min_{x}\ \sum_{v\in\mathcal{V}}\sum_{t\in\mathcal{T}} c_{v,t}x_{v,t}", "objective", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"\sum_{t\in\mathcal{T}_v}\Delta t_t x_{v,t}=E_v,\quad \forall v\in\mathcal{V}", "energy", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"\sum_{v\in\mathcal{V}}x_{v,t}\leq H_t,\quad \forall t\in\mathcal{T}", "capacity", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"0\leq x_{v,t}\leq \overline{x}_v\,\mathbf{1}\{t\in\mathcal{T}_v\}", "bounds", formulas, equation_backend=equation_backend)
    _add_body(doc, r"车辆集合记为 $\mathcal{V}$，时段集合记为 $\mathcal{T}$。车辆只在接入窗口 $\mathcal{T}_v$ 内充电。交付电量应等于需求 $E_v$，由各时段的功率乘时长 $\Delta t_t$ 后累计得到。窗内充电功率受单车上限 $\overline{x}_v$ 约束，所有车辆在同一时段的功率之和受变压器余量约束。目标系数 $c_{v,t}$ 由时段权重加上车端时间偏好项得到。线性规划在上述约束下最小化加权功率和。", formulas=formulas, equation_backend=equation_backend)

    doc.add_heading("4 分配结果与容量约束", level=1)
    process = next(a for a in figure_manifest["artifacts"] if a["id"] == "figure_process")
    p = doc.add_paragraph(); _paragraph_role(p, "figure"); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(process["path"], width=Cm(process["width_cm"]))
    _add_caption(doc, process["caption"]).paragraph_format.keep_with_next = True
    tight_index = int(np.argmin(result["capacity_margin_kw"]))
    tight = validation.get("tightest_period", result.get("tightest_period", tight_index))
    headroom, charge = result.get("headroom_kw", []), result.get("period_total_charge_kw", [])
    process_evidence = process.get("numerical_evidence", {})
    if not np.isclose(float(result["capacity_margin_kw"][tight_index]), minimum_margin, atol=1e-7, rtol=0):
        raise ValueError("Reported minimum margin differs from the independent capacity reconstruction")
    bottleneck = f"时段 {tight} 的容量余量最小（图1）。"
    if tight_index < min(len(headroom), len(charge)):
        bottleneck = f"时段 {tight} 可供充电 {headroom[tight_index]:.2f} kW，计划使用其中 {charge[tight_index]:.2f} kW（图1）。"
    if abs(minimum_margin) <= 1e-7:
        uniform_margin = process_evidence.get("uniform_margin_kw", [])
        if tight_index < min(len(headroom), len(uniform_margin)) and uniform_margin[tight_index] > 1e-7:
            extra = _margin_label(uniform_margin[tight_index], 2)
            power = _margin_label(headroom[tight_index], 2)
            bottleneck = (f"时段 {tight} 是基准计划最紧的时段。变压器还可供充电 {power} kW，加权计划用满了这部分容量（图1）。"
                          f"同一时段，如果各车把充电均匀排在自己的接入窗内，变压器还有 {extra} kW 余量。")
        else:
            bottleneck += "该时段的变压器容量已经用满。"
        bottleneck += "要给新的充电需求留出空间，先看原先排在这个时段的充电能挪走多少。"
    else:
        bottleneck += f"该时段在设备侧最多还能增加 {_margin_label(minimum_margin, 2)} kW。图2再核对这部分功率能分给哪些车辆。"
    _add_body(doc, bottleneck)
    balance = next(a for a in figure_manifest["artifacts"] if a["id"] == "figure_balance")
    p = doc.add_paragraph(); _paragraph_role(p, "figure"); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(balance["path"], width=Cm(balance["width_cm"]))
    _add_caption(doc, balance["caption"]).paragraph_format.keep_with_next = True
    window_evidence = balance.get("numerical_evidence", {})
    move = window_evidence.get("single_vehicle_shift")
    if move and abs(minimum_margin) <= 1e-7 and move["origin"] == tight:
        energy = f"{move['energy_kwh']:.6g}"
        added = f"{move['destination_charge_increase_kw']:.6g}"
        released = f"{move['released_kw']:.6g}"
        delivered = f"{move['departure_energy_kwh']:.6g}"
        delivery_text = (f"图2里，{move['vehicle']} 在时段 {move['destination']} 也可充电。"
                         f"这一时段能给它多分 {added} kW，变压器仍在容量内。把原排在时段 {tight} 的 {energy} kWh 挪过去，"
                         f"时段 {tight} 就能腾出 {released} kW，这辆车离站时仍能充到 {delivered} kWh。")
    elif "single_vehicle_shift" in window_evidence and not move and abs(minimum_margin) <= 1e-7:
        delivery_text = (f"时段 {tight} 已安排的车辆里，找不到一辆能把部分充电直接挪到另一个时段。"
                         "要腾出该时段的容量，还得检查多辆车能否一起重排。")
    else:
        delivery_text = "图2标出了各车能充电的时段。要换时段，先看车在新时段是否接入，再看车端和变压器还剩多少功率。调整完还要核对车辆离站时的电量。"
    _add_body(doc, delivery_text)
    doc.add_heading("5 工况变化与敏感性分析", level=1)
    sens = next(a for a in figure_manifest["artifacts"] if a["id"] == "figure_sensitivity")
    p = doc.add_paragraph(); _paragraph_role(p, "figure"); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(sens["path"], width=Cm(sens["width_cm"]))
    _add_caption(doc, sens["caption"])
    status_names = {"optimal": "可行", "infeasible": "不可行", "unresolved": "未判定", "infeasible_or_failed": "未判定"}
    sens_rows = [[f"{r.demand_scale:.2f}", status_names.get(r.status, r.status), f"{r.objective:.3f}" if np.isfinite(r.objective) else "—",
                  f"{r.mean_margin_kw:.2f}" if np.isfinite(r.mean_margin_kw) else "—"] for r in sensitivity.itertuples()]
    _add_caption(doc, "表2 需求倍率敏感性结果")
    _add_table(doc, ["需求倍率", "状态", "目标值", "平均容量余量（kW）"], sens_rows, [3.0, 3.0, 4.0, 6.0])
    feasible = sensitivity[sensitivity.status == "optimal"].sort_values("demand_scale")
    if feasible["demand_scale"].nunique() > 1:
        lo, hi = feasible.iloc[0], feasible.iloc[-1]
        summaries = sens.get("numerical_evidence", {}).get("scenario_summary", [])
        baseline = feasible[feasible.demand_scale == 1.0]
        base_record = next((item for item in summaries if item["demand_scale"] == 1.0), {})
        base_periods = base_record.get("binding_periods")
        if not baseline.empty and base_periods is not None:
            first_change = next((item["demand_scale"] for item in summaries
                                 if item["demand_scale"] > 1 and set(item.get("binding_periods") or []) - set(base_periods)), None)
            if first_change is not None and first_change in set(feasible.demand_scale):
                lo, hi = baseline.iloc[0], feasible[feasible.demand_scale == first_change].iloc[0]
        _add_body(doc, _compare_scenario_capacity(lo, hi, summaries))
    _add_body(doc, "其他车辆照原计划充电时，每个接入时段能多分给同一辆车的功率，取变压器余量和车端剩余功率中较小的一项。用这个功率乘上各自的时长，再把各段电量加起来，就能算出这辆车还可多充多少电。")
    infeasible = sensitivity[sensitivity.status == "infeasible"]
    if not infeasible.empty:
        scale = infeasible["demand_scale"].min()
        shortfall = _scenario_energy_shortfall(sensitivity_path, scale)
        if shortfall:
            demand, available = shortfall
            _add_body(doc, f"需求达到基准的 {scale:.2f} 倍后，仅靠改换充电时段已经不够。车辆共需 {demand:.3g} kWh，即使把各时段的变压器余量都用于充电，也只能供 {available:.3g} kWh，至少还差 {demand - available:.3g} kWh。增供前还要检查，各车的接入时间够不够用。")
        else:
            _add_body(doc, f"需求倍率 {scale:.2f} 时，在现有接入窗口、车端功率上限和变压器容量下，车辆的电量要求无法同时满足。")

    doc.add_heading("6 校核结果与工程结论", level=1)
    checks = [["最大电量差值", f"{validation['maximum_energy_residual_kwh']:.3g}", "kWh"],
              ["最大容量越界量", f"{validation['maximum_capacity_violation_kw']:.3g}", "kW"],
              ["最小容量余量", f"{minimum_margin:.2f}", "kW"]]
    _add_caption(doc, "表3 电量与容量指标")
    _add_table(doc, ["指标", "数值", "单位"], checks, [8.0, 4.0, 3.6])
    _add_body(doc, "按基准计划，各车能在离站前充到所需电量，变压器也能承担各时段的负荷（表3）。排入新的充电需求后，还要逐车核对离站电量，并重新校核各时段的容量。")
    doc.core_properties.author = ""; doc.core_properties.last_modified_by = ""
    output_path.parent.mkdir(parents=True, exist_ok=True); doc.save(output_path)
    is_office_math = equation_backend == "office_math"
    receipt = {
        "schema": "senior_projectx.project.equation_source.v1",
        "equation_backend": "office_math" if is_office_math else "mathtype_toggle_tex",
        "requested_final_backend": equation_backend,
        "status": "render_review_pending" if is_office_math else "conversion_pending", "publication_eligible": False,
        "source_docx_path": os.path.relpath(output_path, formula_manifest_path.parent).replace("\\", "/"),
        "source_docx_sha256": file_hash(output_path), "formula_count": len(formulas), "formulas": formulas,
        "note": (
            "This DOCX contains editable Office Math objects and requires Word render/page review before delivery."
            if is_office_math else
            "This source must be converted once through Word MathType and audited before it is called native MathType output."
        ),
    }
    write_json(formula_manifest_path, receipt)
    return {"status": "render_review_pending" if is_office_math else "conversion_pending",
            "equation_backend": receipt["equation_backend"], "docx": str(output_path),
            "formula_manifest": str(formula_manifest_path), "formula_count": len(formulas),
            "pages_are_not_self_certified": True}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build Chinese Project figures and a Word report from current result objects.")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("make-template", help="Create the default editable A4 Project DOCX template.")
    q.add_argument("output", type=Path)
    q = sub.add_parser("figures", help="Create role-distinct Chinese figures from current allocation and sensitivity results.")
    q.add_argument("--periods", required=True, type=Path); q.add_argument("--allocation", required=True, type=Path)
    q.add_argument("--vehicles", required=True, type=Path); q.add_argument("--sensitivity", required=True, type=Path)
    q.add_argument("--output-dir", required=True, type=Path); q.add_argument("--manifest-out", required=True, type=Path)
    q = sub.add_parser("build", help="Build the manifest-selected Project equation backend; MathType creates a conversion-pending source, Office Math creates editable OMML.")
    q.add_argument("--template", required=True, type=Path); q.add_argument("--manifest", required=True, type=Path)
    q.add_argument("--audit", action="append", required=True, type=Path); q.add_argument("--result", required=True, type=Path)
    q.add_argument("--validation", required=True, type=Path); q.add_argument("--brief", required=True, type=Path)
    q.add_argument("--figures", required=True, type=Path); q.add_argument("--sensitivity", required=True, type=Path)
    q.add_argument("--output", required=True, type=Path); q.add_argument("--formula-manifest", required=True, type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "make-template":
        if args.output.exists(): raise FileExistsError(args.output)
        create_default_template(args.output.resolve()); result = {"status": "ok", "template": str(args.output.resolve())}
    elif args.command == "figures":
        result = build_figures(args.periods.resolve(), args.allocation.resolve(), args.vehicles.resolve(), args.sensitivity.resolve(), args.output_dir.resolve())
        write_json(args.manifest_out.resolve(), result)
    elif args.command == "build":
        if args.output.exists() or args.formula_manifest.exists():
            raise FileExistsError("Refusing to overwrite report source or formula manifest")
        result = build_report(args.template.resolve(), args.manifest.resolve(), [p.resolve() for p in args.audit],
                              args.result.resolve(), args.validation.resolve(), args.brief.resolve(), args.figures.resolve(),
                              args.sensitivity.resolve(), args.output.resolve(), args.formula_manifest.resolve())
    else: raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
