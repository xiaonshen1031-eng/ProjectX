"""Replay an explicitly schematic forecast issuance workflow at physical size.

The teaching example computes a convex weighted proposal and its Euclidean
projection onto a product of known intervals. Its shapes mark these operations,
not measured results. Adapt the topology and encodings to the actual method
and evidence before composing the manuscript figure.

Adapted from the NPS Research Paper v3.2.4 Project figure workflow by XiaoN.
"""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font
from matplotlib.patches import Rectangle
import numpy as np

from research_figure_composition import arrow, axes_mm, canvas_axes, new_figure, palette_catalog, save


@dataclass(frozen=True)
class Branch:
    width: float
    height: float
    font_pt: float
    language: str


BRANCHES = {
    "project": Branch(160., 79., 8.8, "zh"),
}
LABELS = {
    "en": {
        "context": "Worked example with illustrative inputs",
        "configured": "Operations on normalized traces",
        "stages": ("Delivered reports", "Weighted proposal (a)", "Admissible band (b)", "Issued forecast"),
        "lead": "Forecast lead",
        "weights": "(a) Weighted contributions",
        "constraint": "(b) Projection at the selected lead",
        "coordinate": "Lead {lead}",
        "band": "Admissible interval",
        "total": "Proposal ",
    },
    "zh": {
        "context": "示例数据与计算步骤",
        "configured": "归一化预测的计算步骤",
        "stages": ("收到的预测", "加权预测（a）", "可行区间（b）", "发布预测"),
        "lead": "预测步",
        "weights": "（a）加权贡献",
        "constraint": "（b）所选步的投影",
        "coordinate": "第 {lead} 步",
        "band": "可行区间",
        "total": "加权值 ",
    },
}


def calculation(spec, *, demo=False) -> dict:
    """Bind three normalized traces and calculate every plotted operation."""
    provenance = spec.get("provenance", {})
    if not provenance.get("kind") or not provenance.get("source"):
        raise ValueError("Give the input traces a source and an evidence kind")
    reports = np.asarray(spec["reports"], dtype=float)
    if reports.ndim != 2 or reports.shape[0] != 3 or not 3 <= reports.shape[1] <= 8:
        raise ValueError("This workflow shows three reports over three to eight leads")
    weights = np.asarray(spec["weights"], dtype=float)
    if weights.shape != (3,) or not np.isfinite(weights).all() or np.min(weights) < 0 or not np.isclose(weights.sum(), 1.):
        raise ValueError("Supply three finite nonnegative weights that sum to one")
    lower = np.broadcast_to(np.asarray(spec["lower"], dtype=float), (reports.shape[1],))
    upper = np.broadcast_to(np.asarray(spec["upper"], dtype=float), lower.shape)
    if not (np.isfinite(reports).all() and np.isfinite(lower).all() and np.isfinite(upper).all()
            and np.min(reports) >= 0 and np.max(reports) <= 1
            and np.all((0 <= lower) & (lower <= upper) & (upper <= 1))):
        raise ValueError("Reports and ordered constraint bounds must be on the declared normalized [0,1] scale")
    proposal = weights @ reports
    issued = np.clip(proposal, lower, upper)
    focus = spec.get("focus_index", int(np.argmax(np.abs(issued - proposal))))
    if type(focus) is not int or not 0 <= focus < reports.shape[1]:
        raise ValueError("The displayed zero-based focus index is outside the supplied lead roster")
    contributions = weights * reports[:, focus]
    return {
        "provenance": provenance,
        "illustrative": demo or provenance.get("kind") == "illustrative",
        "operation": "coordinatewise Euclidean projection onto a product of closed intervals",
        "reports": reports, "weights": weights, "lower": lower, "upper": upper,
        "proposal": proposal, "issued": issued, "contributions": contributions,
        "focus_index": focus,
    }


def teaching_calculation() -> dict:
    return calculation({
        "reports": [[.20, .48, .52, .72], [.48, .90, .44, .52], [.28, .60, .84, .76]],
        "weights": [.25, .50, .25], "lower": [.26, .34, .38, .40],
        "upper": [.64, .62, .67, .70], "focus_index": 1,
        "provenance": {"kind": "illustrative", "source": "Analytically specified teaching inputs"},
    }, demo=True)


def choose_font(labels: dict, language: str) -> list[str]:
    try:
        font_manager.findfont("Times New Roman", fallback_to_default=False)
        latin = "Times New Roman"
    except ValueError:
        latin = "DejaVu Serif"
    if language != "zh":
        return [latin]
    words = [word for value in labels.values() for word in
             (value if isinstance(value, tuple) else (value,))]
    required = {ord(char) for word in words for char in word if ord(char) > 127}
    for candidate in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC", "SimSun"):
        try:
            font_file = font_manager.findfont(candidate, fallback_to_default=False)
        except ValueError:
            continue
        if required <= set(FT2Font(font_file).get_charmap()):
            return [latin, candidate]
    raise ValueError("Project branch needs a CJK font with every Chinese figure glyph")


def route_plot(fig, left, width, top, height, style, leads, *, show_leads):
    axis = axes_mm(fig, left, top, width, height)
    axis.set(xlim=(.72, leads[-1]+.28), ylim=(-.05, 1.05), yticks=[],
             xticks=leads if show_leads else [])
    axis.spines[["left", "top", "right"]].set_visible(False)
    axis.spines["bottom"].set(color=style["ink"], linewidth=.68)
    axis.tick_params(axis="x", colors=style["ink"], length=2.1, pad=1.7)
    return axis


def plot_trace(axis, leads, values, color, ink, *, marker):
    axis.plot(leads, values, color=color, lw=1.12, marker=marker, ms=3.55,
              mec=ink, mew=.55, mfc=color, zorder=3)


def operations(canvas, branch, labels, style, put, data, left, right, top):
    ink = style["ink"]
    divider = (left + right) / 2
    lower_width = divider - left
    panel_left, panel_right = left + 2.5, divider + 5.
    canvas.plot([left, right], [top, top], color=ink, lw=.75)
    canvas.plot([divider, divider], [top+4, branch.height-3], color=style["grid"], lw=.58)
    put(canvas, panel_left, top+4.5, labels["weights"], bold=True)
    put(canvas, panel_right, top+4.5, labels["constraint"], bold=True)
    focus = data["focus_index"]
    p, q = data["proposal"][focus], data["issued"][focus]
    put(canvas, divider - 3.5, top+4.5, labels["coordinate"].format(lead=focus+1), align="right")

    def labelled_math(x, y, label, expression):
        # Keep CJK outside the mathtext artist so it uses the actual CJK font.
        text = put(canvas, x, y, label.strip())
        renderer = canvas.figure.canvas.get_renderer()
        label_width = text.get_window_extent(renderer).width * branch.width / renderer.width
        put(canvas, x+label_width+1.25, y, expression)

    # Same-length coordinate system for all actual weighted terms.
    bar_x = panel_left + .6
    bar_width = lower_width - 14.
    contribution_colors = [style["iris"], style["cobalt"], style["sun"]]
    starts = np.r_[0, np.cumsum(data["contributions"])]
    for j, solid in enumerate(contribution_colors):
        x0, x1 = bar_x + bar_width*starts[j:j+2]
        canvas.add_patch(Rectangle((x0, top+16.2), x1-x0, 4.15, fc=solid,
                                   ec=ink, lw=.64, zorder=4))
        mid = bar_x + bar_width * (j+.5)/3
        canvas.add_patch(Rectangle((mid-2., top+21.4), 1.55, 1.55, fc=solid, ec=ink, lw=.58))
        put(canvas, mid+.5, top+22.3, f"{data['contributions'][j]:.4g}")
        lead = focus+1
        put(canvas, mid, top+9.15, rf"$w_{{{j+1}}} f_{{{j+1},{lead}}}$", align="center")
        weight = data["weights"][j]
        value = data["reports"][j, focus]
        put(canvas, mid, top+13.0, "$" + rf"{weight:.4g}\times {value:.4g}$", align="center")
    labelled_math(bar_x, top+27, labels["total"], rf"$p_{{{focus+1}}}={p:.4g}$")

    # Move along the value coordinate from proposal to the active bound.
    axis_left, axis_span = panel_right, lower_width - 11.

    def at(value):
        return axis_left + axis_span * value

    y = top+18.3
    lo, hi = data["lower"][focus], data["upper"][focus]
    canvas.plot([at(0), at(1)], [y, y], color=ink, lw=.74, zorder=3)
    canvas.add_patch(Rectangle((at(lo), y-1.55), at(hi)-at(lo), 3.1,
                               fc=style["jade_wash"], ec=ink, lw=.69, zorder=4))
    canvas.plot(at(p), y, marker="D", ls="none", ms=4.35, mfc=style["raspberry"],
                mec=ink, mew=.65, zorder=6)
    canvas.plot(at(q), y, marker="o", ls="none", ms=4.45, mfc=style["jade"],
                mec=ink, mew=.65, zorder=6)
    if p != q:
        for value in (p, q):
            canvas.plot([at(value), at(value)], [y-1.8, y-3.95], color=ink, lw=.62)
        if abs(at(p)-at(q)) >= 3:
            arrow(canvas, (at(p), y-3.95), (at(q), y-3.95), color=ink, width=.77, head=6)
    put(canvas, axis_left, y-8.7, rf"$p_{{{focus+1}}}={p:.4g},\quad a_{{{focus+1}}}={q:.4g}$")
    labelled_math(axis_left, y+7.5, labels["band"], rf"$[{lo:.4g},\,{hi:.4g}]$")


def workflow(branch_name: str, data: dict, *, width_mm=None, height_mm=None, font_pt=None, language=None):
    branch = BRANCHES[branch_name]
    branch = replace(branch, width=branch.width if width_mm is None else width_mm,
                     height=branch.height if height_mm is None else height_mm,
                     font_pt=branch.font_pt if font_pt is None else font_pt,
                     language=branch.language if language is None else language)
    labels = LABELS[branch.language]
    font = choose_font(labels, branch.language)
    style = palette_catalog()["colors"]
    ink = style["ink"]
    fig = new_figure(branch.width, branch.height, branch.font_pt, font)
    canvas = canvas_axes(fig)

    def put(ax, x, y, label, *, align="left", bold=False):
        chinese_bold = font[-1] == "Microsoft YaHei" and any("\u3400" <= char <= "\u9fff" for char in label)
        return ax.text(x, y, label, ha=align, va="center", color=ink,
                       fontfamily=font, fontsize=branch.font_pt, math_fontfamily="stix",
                       fontweight="bold" if bold or chinese_bold else "normal", zorder=8)

    pad = 5.
    spacing = 9. if branch.language == "en" else 8.
    route_width = (branch.width - 2*pad - 3*spacing) / 4
    offset = 2.
    top = 14.
    height = 18. + offset
    lefts = np.arange(4) * (route_width + spacing) + pad
    labels_x = lefts + route_width/2
    context = "context" if data["illustrative"] else "configured"
    put(canvas, pad, 3.5, labels[context])
    for x, title in zip(labels_x, labels["stages"], strict=True):
        put(canvas, x, 9.1, title, align="center", bold=True)

    leads = np.arange(1, data["reports"].shape[1]+1)
    charts = [route_plot(fig, x, route_width, top, height, style, leads, show_leads=j == 0)
              for j, x in enumerate(lefts)]
    for tick in charts[0].get_xticklabels():
        tick.set(fontfamily=font, fontsize=branch.font_pt)
    put(canvas, labels_x[0], top+height+6.9, labels["lead"], align="center")

    focus = data["focus_index"]
    for trajectory, color, marker in zip(data["reports"],
            (style["iris"], style["cobalt"], style["sun"]), ("o", "^", "s"), strict=True):
        plot_trace(charts[0], leads, trajectory, color, ink, marker=marker)
    plot_trace(charts[1], leads, data["proposal"], style["cobalt"], ink, marker="o")
    for chart in charts[2:]:
        chart.fill_between(leads, data["lower"], data["upper"], color=style["jade_wash"], zorder=1)
        for boundary in ("lower", "upper"):
            chart.plot(leads, data[boundary], color=ink, lw=.61, ls=(0, (2, 2)), zorder=2)
    plot_trace(charts[2], leads, data["proposal"], style["cobalt"], ink, marker="o")
    charts[2].plot(leads[focus], data["proposal"][focus], "D", ms=4.3,
                   mfc=style["raspberry"], mec=ink, mew=.61, zorder=5)
    plot_trace(charts[3], leads, data["issued"], style["jade"], ink, marker="o")
    charts[3].plot(leads[focus], data["issued"][focus], "D", ms=4.2,
                   mfc=style["jade"], mec=ink, mew=.69, zorder=5)
    for x in lefts[1:]:
        y = top+height/2
        arrow(canvas, (x-spacing+1.45, y), (x-1.35, y), color=ink, width=.88, head=6.9)

    operations(canvas, branch, labels, style, put, data, pad, branch.width-pad, branch.height-30.5)
    fig._nps_schematic = True
    return fig


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true", help="Run the illustrated three-report example")
    mode.add_argument("--config", type=Path, help="Analytically replay the supported operation on supplied normalized traces")
    parser.add_argument("--branch", choices=tuple(BRANCHES), default="project")
    parser.add_argument("--language", choices=tuple(LABELS), default="zh")
    parser.add_argument("--width-mm", type=float)
    parser.add_argument("--height-mm", type=float)
    parser.add_argument("--font-pt", type=float)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--formats", nargs="+", choices=("pdf", "svg", "png", "tiff"), default=("pdf", "svg", "png"))
    parser.add_argument("--dpi", type=float, default=240)
    args = parser.parse_args()
    case = teaching_calculation() if args.demo else calculation(json.loads(args.config.read_text(encoding="utf-8-sig")))
    stem = args.output_dir / ("research_workflow_" + args.branch + ("_illustrative" if case["illustrative"] else ""))
    figure = workflow(args.branch, case, width_mm=args.width_mm, height_mm=args.height_mm,
                      font_pt=args.font_pt, language=args.language)
    layout = save(figure, stem, formats=args.formats, dpi=args.dpi)
    recorded = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in case.items()}
    calculation_file = stem.with_suffix(".calculation.json")
    calculation_file.write_text(json.dumps(recorded, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    layout["source"] = case["provenance"]
    layout["calculation"] = {"file": calculation_file.name, "sha256": sha256(calculation_file.read_bytes()).hexdigest()}
    stem.with_suffix(".layout.json").write_text(json.dumps(layout, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
