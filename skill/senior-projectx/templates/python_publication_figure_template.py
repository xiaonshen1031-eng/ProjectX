"""Publication figure skeleton using the project's existing Matplotlib stack.

Adapt the recipe and load saved evidence; never transcribe manuscript numbers.
CSV columns: method, estimate, lower, upper (same metric/unit and interval rule).
The CLI only generates illustrative data after explicit --demo, labels it DEMO,
and never claims scientific or manuscript QA has passed.
Choose encodings from the actual engineering relationship. Use real paired
effects, distributions, conditional or residual diagnostics when available;
continuous/time/trajectory curves must retain their true coordinates and units.
"""
from __future__ import annotations

import argparse
import csv
import math
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager


def configure_style(font: str = "Times New Roman", font_size: float = 9.5) -> str:
    try:
        font_manager.findfont(font, fallback_to_default=False)
        actual = font
    except ValueError:
        actual = "DejaVu Serif"
        warnings.warn(f"Requested font {font!r} unavailable; using {actual!r}. Record this in visual QA.", stacklevel=2)
    mpl.rcParams.update({
        "font.family": actual, "font.size": font_size,
        "axes.labelsize": font_size + 1, "axes.linewidth": 0.9,
        "xtick.labelsize": font_size, "ytick.labelsize": font_size,
        "legend.fontsize": font_size, "pdf.fonttype": 42,
        "ps.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 600,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })
    return actual


def scientific_colors(kind: str):
    """Match the palette semantics to the quantity; choose a data-defined pivot."""
    return mpl.colormaps[{"sequential": "viridis", "diverging": "RdBu_r", "categorical": "tab10"}[kind]]


def annotation_color(rgb) -> str:
    # Contrast against the rendered opaque cell, using linearized sRGB luminance.
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb[:3]]
    luminance = sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722)))
    return "black" if (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05) else "white"


def method_styles(methods):
    """Supply the same ordered method roster across a paper, or reuse its style map."""
    palette = scientific_colors("categorical")
    markers = ("o", "s", "D", "^", "v", "P", "X")
    return {name: {"color": palette(i % palette.N), "marker": markers[i % len(markers)]}
            for i, name in enumerate(methods)}


def insertion_scale(export_width_cm: float, export_height_cm: float,
                    final_width_cm: float, final_height_cm: float) -> float:
    """One uniform scale preserves geometry; displayed font = source pt * scale."""
    dimensions = (export_width_cm, export_height_cm, final_width_cm, final_height_cm)
    if any(isinstance(value, bool) or not math.isfinite(value) or value <= 0 for value in dimensions):
        raise ValueError("Export and insertion dimensions must be finite positive centimeters")
    scale = final_width_cm / export_width_cm
    if not math.isclose(scale, final_height_cm / export_height_cm, rel_tol=0.005):
        raise ValueError("Insertion would stretch the figure: preserve exported/post-crop aspect ratio")
    return scale


def load_effect_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Saved evidence CSV is empty")
    for row in rows:
        if not row.get("method", "").strip():
            raise ValueError("Each row requires a method identity")
        for key in ("estimate", "lower", "upper"):
            row[key] = float(row[key])
        if not all(math.isfinite(row[key]) for key in ("estimate", "lower", "upper")):
            raise ValueError("Unavailable/nonfinite evidence cannot be plotted as zero")
        if not row["lower"] <= row["estimate"] <= row["upper"]:
            raise ValueError("Interval endpoints must bracket the estimate")
    if len({row["method"] for row in rows}) != len(rows):
        raise ValueError("Use distinct method rows or facet by task before plotting")
    return rows


def effect_forest(rows, *, metric_label: str, reference: str, width_cm=16.5, height_cm=10.0, styles=None):
    """Use effects already computed from saved paired units; Full is the reference."""
    if not rows or not any(row["method"] == reference for row in rows):
        raise ValueError("Include the declared Full/reference row in saved evidence")
    insertion_scale(width_cm, height_cm, width_cm, height_cm)
    fig = plt.figure(figsize=(width_cm / 2.54, height_cm / 2.54))
    grid = fig.add_gridspec(1, 1, left=0.30, right=0.96, bottom=0.22, top=0.92)
    ax = fig.add_subplot(grid[0, 0])
    styles = styles or method_styles([row["method"] for row in rows])
    ax.axvline(0, color="0.4", linestyle="--", linewidth=0.9)
    for y, row in enumerate(rows):
        style = styles[row["method"]]
        ax.errorbar(row["estimate"], y,
                    xerr=[[row["estimate"] - row["lower"]], [row["upper"] - row["estimate"]]],
                    fmt=style["marker"], color=style["color"], capsize=3, markersize=6,
                    markerfacecolor="white" if row["lower"] <= 0 <= row["upper"] else style["color"])
    bounds = [0.0] + [row[key] for row in rows for key in ("lower", "upper")]
    padding = max((max(bounds) - min(bounds)) * 0.08, 1e-3)
    ax.set_xlim(min(bounds) - padding, max(bounds) + padding)
    ax.set_yticks(range(len(rows)), [row["method"] for row in rows])
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xlabel(metric_label)
    ax.grid(axis="x", alpha=0.16)
    # Add panel letters only if the caption/body uses them. No automatic title.
    # For correlation: explicit masks + one clustering order + separate metric keys.
    # For regression: shared limits, identical sample IDs, y=x, complete baselines.
    return fig


def export_figure(fig, stem: Path, formats=("pdf", "png")) -> list[Path]:
    formats = tuple(str(ext).lower().lstrip(".") for ext in formats)
    if not formats or any(ext not in {"pdf", "svg", "png"} for ext in formats):
        raise ValueError("This Python template exports only requested PDF/SVG/PNG")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.get_window_extent(renderer)
    # Matplotlib retains tick artists outside view limits; Axis.draw excludes
    # them. They are not clipped exported labels and must not cause false QA.
    unrendered_tick_labels = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                if not lo <= tick.get_loc() <= hi:
                    unrendered_tick_labels.update((id(tick.label1), id(tick.label2)))
    for text in fig.findobj(mpl.text.Text):
        if id(text) not in unrendered_tick_labels and text.get_visible() and text.get_text().strip():
            box = text.get_window_extent(renderer)
            if box.width > 0 and box.height > 0 and (box.x0 < canvas.x0 - 2 or box.y0 < canvas.y0 - 2 or box.x1 > canvas.x1 + 2 or box.y1 > canvas.y1 + 2):
                raise ValueError(f"Text outside physical canvas: {text.get_text()!r}; adjust margins, not approved fonts")
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in dict.fromkeys(formats):
        path = stem.with_suffix("." + ext)
        # No tight crop: retain the declared physical size. Rasterize only large
        # data layers when justified; keep axes, text, annotations and keys vector.
        fig.savefig(path, dpi=600 if ext == "png" else None)
        paths.append(path)
    # Bounds checks do not prove no overlaps or readable final manuscript pages.
    # Inspect requested vectors and actual manuscript render before declaring QA.
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data", type=Path)
    source.add_argument("--demo", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--formats", nargs="+", choices=["pdf", "svg", "png"], default=["pdf", "png"])
    parser.add_argument("--font", default="Times New Roman")
    parser.add_argument("--reference", default="Full")
    parser.add_argument("--metric-label", default="Paired effect (declare unit/direction)")
    parser.add_argument("--width-cm", type=float, default=16.5, help="Actual final physical insertion width")
    parser.add_argument("--height-cm", type=float, default=10.0, help="Actual final physical insertion height")
    parser.add_argument("--font-size", type=float, default=9.5, help="Source/final tick and legend size in points at this physical canvas")
    args = parser.parse_args()
    if not math.isfinite(args.font_size) or args.font_size <= 0:
        parser.error("--font-size must be finite and positive")
    configure_style(args.font, args.font_size)
    if args.demo:
        rows = [dict(method="Full", estimate=0, lower=0, upper=0),
                dict(method="Demo removal A", estimate=1.0, lower=-0.4, upper=2.2),
                dict(method="Demo removal B", estimate=-0.5, lower=-1.4, upper=0.4)]
    else:
        rows = load_effect_rows(args.data)
    fig = effect_forest(rows, metric_label=args.metric_label, reference=args.reference, width_cm=args.width_cm, height_cm=args.height_cm)
    if args.demo:
        fig.text(0.5, 0.98, "DEMO - illustrative layout, not research evidence", ha="center", va="top", fontsize=9)
    export_figure(fig, args.output, args.formats)
    plt.close(fig)


if __name__ == "__main__":
    main()
