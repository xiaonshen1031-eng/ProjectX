"""Senior-ProjectX figure starter: bind real results before plotting."""
from pathlib import Path
import re
import matplotlib.pyplot as plt
from matplotlib import font_manager


def pick_font(names):
    available = {f.name.lower(): f.name for f in font_manager.fontManager.ttflist}
    return next((available[n.lower()] for n in names if n.lower() in available), None)


CHINESE = pick_font(["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"])
LATIN = pick_font(["Times New Roman", "Liberation Serif", "DejaVu Serif"])
if not CHINESE or not LATIN:
    raise RuntimeError("Required Chinese/Latin figure font or an approved fallback is unavailable")


def new_figure(width_in=6.55, height_in=3.4):
    fig, ax = plt.subplots(figsize=(width_in, height_in), constrained_layout=True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, axis="y", color="#D9D9D9", linewidth=0.6)
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
    ax.figure.savefig(output, dpi=320, bbox_inches="tight", pad_inches=0.04)
    plt.close(ax.figure)


# Do not add a default title/suptitle. State the question, result paths, units,
# final width, caption, and manuscript location in the figure manifest.


def constraint_diagnostic(time, base, scheduled, capacity, output: Path):
    """Use synchronized measured/model arrays; never fill absent observations."""
    import numpy as np
    time, base, scheduled, capacity = map(np.asarray, (time, base, scheduled, capacity))
    if any(v.ndim != 1 or len(v) != len(time) for v in (base, scheduled, capacity)):
        raise ValueError("Synchronized one-dimensional arrays required")
    if not all(np.isfinite(v).all() for v in (time, base, scheduled, capacity)):
        raise ValueError("Missing values require explicit handling before plotting")
    fig, (ax, residual) = plt.subplots(2, 1, sharex=True, figsize=(6.55, 4.1),
                                    gridspec_kw={"height_ratios": [2.2, 1]}, constrained_layout=True)
    ax.step(time, base, where="mid", label="基础负荷")
    ax.step(time, base+scheduled, where="mid", label="分配后负荷")
    ax.step(time, capacity, where="mid", linestyle="--", label="容量边界")
    ax.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(.5, 1.01))
    ax.set_ylabel("功率（MW）")
    margin = capacity-base-scheduled
    residual.fill_between(time, 0, margin, step="mid", color="#008580", alpha=.35)
    residual.step(time, margin, where="mid", color="#008580")
    residual.axhline(0, color="black", linewidth=.7)
    finish(residual, "时段", "容量余量（MW）", output)
    return {"plot_type": "temporal_diagnostic", "capacity_margin": margin.tolist()}
