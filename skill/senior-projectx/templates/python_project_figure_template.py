"""Senior-ProjectX figure starter: bind real results before plotting."""
import json
from pathlib import Path
import re
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager


def pick_font(names):
    available = {f.name.lower(): f.name for f in font_manager.fontManager.ttflist}
    return next((available[n.lower()] for n in names if n.lower() in available), None)


CHINESE = pick_font(["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"])
LATIN = pick_font(["Times New Roman", "Liberation Serif", "DejaVu Serif"])
if not CHINESE or not LATIN:
    raise RuntimeError("Required Chinese/Latin figure font or an approved fallback is unavailable")

COLORS = json.loads(Path(__file__).with_name("research_figure_palette.json").read_text(encoding="utf-8"))["colors"]


def new_figure(width_in=6.55, height_in=3.4):
    fig, ax = plt.subplots(figsize=(width_in, height_in), constrained_layout=True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, axis="y", color=COLORS["grid"], linewidth=0.6)
    return fig, ax


def style_text(label, size):
    has_chinese = bool(re.search(r"[\u3400-\u9fff]", label.get_text()))
    label.set_fontfamily([LATIN, CHINESE] if has_chinese else [LATIN])
    label.set_fontweight(("normal" if CHINESE == "SimHei" else "bold") if has_chinese else "normal")
    label.set_fontsize(size)


def finish(ax, xlabel, ylabel, output: Path):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    # Include secondary axes/colorbars, category ticks and legend text.
    for current in ax.figure.axes:
        for label in [current.xaxis.label, current.yaxis.label]:
            style_text(label, 10)
        for label in current.get_xticklabels() + current.get_yticklabels() + [current.xaxis.get_offset_text(), current.yaxis.get_offset_text()]:
            style_text(label, 9)
        if current.get_legend() is not None:
            for label in current.get_legend().get_texts():
                style_text(label, 8.5)
    output.parent.mkdir(parents=True, exist_ok=True)
    with matplotlib.rc_context({"savefig.bbox": None, "pdf.fonttype": 42, "svg.fonttype": "none"}):
        ax.figure.savefig(output, dpi=320, facecolor="white")
    plt.close(ax.figure)


# Do not add a default title/suptitle. State the question, result paths, units,
# final width, caption, and manuscript location in the figure manifest.


def constraint_diagnostic(time, base, scheduled, capacity, output: Path, *,
                          power_unit="MW", width_in=6.55, height_in=4.1):
    """Use synchronized measured/model arrays; never fill absent observations."""
    import numpy as np
    time, base, scheduled, capacity = map(np.asarray, (time, base, scheduled, capacity))
    if time.ndim != 1 or not time.size or any(v.ndim != 1 or len(v) != len(time) for v in (base, scheduled, capacity)):
        raise ValueError("Synchronized one-dimensional arrays required")
    if not all(np.isfinite(v).all() for v in (time, base, scheduled, capacity)):
        raise ValueError("Missing values require explicit handling before plotting")
    if not np.all(np.diff(time) > 0):
        raise ValueError("Time must be strictly increasing")
    fig, (ax, residual) = plt.subplots(2, 1, sharex=True, figsize=(width_in, height_in),
                                    gridspec_kw={"height_ratios": [2.2, 1]}, constrained_layout=True)
    ax.step(time, base, where="mid", label="基础负荷", color=COLORS["cobalt"], linestyle=":")
    ax.step(time, base+scheduled, where="mid", label="分配后负荷", color=COLORS["iris"])
    ax.step(time, capacity, where="mid", linestyle="--", label="容量边界", color=COLORS["ink"])
    ax.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(.5, 1.01))
    ax.set_ylabel(f"功率（{power_unit}）")
    margin = capacity-base-scheduled
    residual.fill_between(time, 0, np.maximum(margin, 0), step="mid", color=COLORS["jade_wash"])
    residual.fill_between(time, 0, np.minimum(margin, 0), step="mid", color=COLORS["raspberry_wash"])
    residual.step(time, margin, where="mid", color=COLORS["ink"])
    residual.axhline(0, color=COLORS["ink"], linestyle="--", linewidth=.7)
    finish(residual, "时段", f"容量余量（{power_unit}）", output)
    return {"plot_type": "temporal_diagnostic", "capacity_margin": margin.tolist()}
