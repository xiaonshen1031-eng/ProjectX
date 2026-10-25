#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def find_col(columns: list[str], candidates: list[str]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lowered:
            return lowered[cand.lower()]
    for col in columns:
        lcol = col.lower()
        for cand in candidates:
            if cand.lower() in lcol:
                return col
    return None


def assess(workbook: Path, proposed: str) -> dict:
    xl = pd.ExcelFile(workbook)
    summary = pd.read_excel(workbook, sheet_name="summary_metrics") if "summary_metrics" in xl.sheet_names else None
    ablation = pd.read_excel(workbook, sheet_name="ablation") if "ablation" in xl.sheet_names else None
    robustness = pd.read_excel(workbook, sheet_name="robustness") if "robustness" in xl.sheet_names else None

    findings: list[str] = []
    stats: dict = {}

    if summary is not None:
        algo_col = find_col(summary.columns.tolist(), ["algorithm"])
        dev_col = find_col(summary.columns.tolist(), ["mean_voltage_deviation", "voltage_deviation"])
        loss_col = find_col(summary.columns.tolist(), ["mean_p_loss_mw", "loss"])
        viol_col = find_col(summary.columns.tolist(), ["mean_voltage_violation", "violation"])
        pen_col = find_col(summary.columns.tolist(), ["penetration"])
        if algo_col and dev_col:
            target = summary[summary[algo_col].astype(str).str.lower() == proposed.lower()]
            baselines = summary[summary[algo_col].astype(str).str.lower() != proposed.lower()]
            if not target.empty and not baselines.empty:
                target_dev = float(target[dev_col].mean())
                best_baseline = baselines.groupby(algo_col)[dev_col].mean().sort_values().head(1)
                best_name = str(best_baseline.index[0])
                best_dev = float(best_baseline.iloc[0])
                stats["primary_metric"] = {
                    "proposed": proposed,
                    "proposed_deviation": target_dev,
                    "best_baseline": best_name,
                    "best_baseline_deviation": best_dev,
                    "improvement_percent": (best_dev - target_dev) / best_dev * 100 if best_dev else None,
                }
                if target_dev > best_dev:
                    findings.append("Proposed method is not best on the primary deviation metric.")
                else:
                    findings.append("Proposed method is best on the primary deviation metric.")
            if pen_col:
                per_pen = summary.groupby([algo_col, pen_col])[dev_col].mean().reset_index()
                stats["per_penetration"] = per_pen.to_dict(orient="records")
        if loss_col and dev_col and algo_col:
            grouped = summary.groupby(algo_col)[[dev_col, loss_col]].mean()
            if proposed in grouped.index:
                proposed_row = grouped.loc[proposed]
                lower_loss = grouped[grouped[loss_col] < proposed_row[loss_col]]
                if not lower_loss.empty:
                    better_dev = lower_loss[lower_loss[dev_col] > proposed_row[dev_col]]
                    if not better_dev.empty:
                        findings.append("Loss-vs-deviation trade-off is plausible: some baselines have lower loss but worse voltage quality.")
    else:
        findings.append("summary_metrics sheet not found.")

    if ablation is not None:
        var_col = find_col(ablation.columns.tolist(), ["variant"])
        dev_col = find_col(ablation.columns.tolist(), ["mean_voltage_deviation", "voltage_deviation"])
        if var_col and dev_col:
            grp = ablation.groupby(var_col)[dev_col].mean().sort_values()
            stats["ablation_ranking"] = grp.to_dict()
            if grp.index[0].lower() != "full":
                findings.append("Full model is not best in ablation on deviation; inspect the scientific claim carefully.")
            else:
                findings.append("Ablation ranking supports the full model on the primary metric.")

    if robustness is not None:
        algo_col = find_col(robustness.columns.tolist(), ["algorithm"])
        dev_col = find_col(robustness.columns.tolist(), ["mean_voltage_deviation", "voltage_deviation"])
        viol_col = find_col(robustness.columns.tolist(), ["mean_voltage_violation", "violation"])
        if algo_col and dev_col:
            grp = robustness.groupby(algo_col)[dev_col].mean().sort_values()
            stats["robustness_deviation_ranking"] = grp.to_dict()
            if grp.index[0].lower() != proposed.lower():
                findings.append("Proposed method is not best on average robustness deviation.")
            else:
                findings.append("Proposed method remains best on average robustness deviation.")
        if algo_col and viol_col:
            grp_viol = robustness.groupby(algo_col)[viol_col].mean().sort_values()
            stats["robustness_violation_ranking"] = grp_viol.to_dict()

    return {"findings": findings, "stats": stats}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether exported experiment results support the claimed method advantage.")
    parser.add_argument("workbook")
    parser.add_argument("--proposed", default="trc_masac")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    result = assess(Path(args.workbook).resolve(), proposed=args.proposed)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
