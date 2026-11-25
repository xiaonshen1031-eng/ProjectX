"""Reusable physical-size composition primitives, with explicit evidence boundaries.

This is an editable Python/vector template, not a native PPTX/Visio replacement.
Use a requested native editor when that is the deliverable. The blank-slot mode produces empty layouts awaiting results.

Adapted from the NPS Research Paper v3.2.4 Project figure workflow by XiaoN.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence
import warnings

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.text import Text
import numpy as np

MM_PER_INCH = 25.4
PROJECT_FONTS = ("Times New Roman", "Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
                 "Source Han Sans SC", "SimSun", "DejaVu Serif")


def palette_catalog() -> dict:
    source = Path(__file__).with_name("research_figure_palette.json")
    return json.loads(source.read_text(encoding="utf-8"))


def palette(profile: str | None = None) -> dict:
    catalog = palette_catalog()
    selected = profile or catalog["default_profile"]
    return catalog["profiles"][selected]


def new_figure(width_mm: float, height_mm: float, font_pt: float = 8.5,
               font: str | Sequence[str] = PROJECT_FONTS):
    """Fix the final physical canvas; save without bbox_inches='tight'."""
    if not all(np.isfinite(x) and x > 0 for x in (width_mm, height_mm, font_pt)):
        raise ValueError("Physical dimensions and font size must be finite and positive")
    available = {f.name for f in font_manager.fontManager.ttflist}
    requested_fonts = [font] if isinstance(font, str) else list(font)
    actual_fonts = [name for name in requested_fonts if name in available]
    if not actual_fonts:
        actual_fonts = ["DejaVu Serif"]
    actual_font = actual_fonts[0] if len(actual_fonts) == 1 else actual_fonts
    fig = Figure(figsize=(width_mm / MM_PER_INCH, height_mm / MM_PER_INCH), layout="none")
    FigureCanvasAgg(fig)
    fig._nps_physical = {"width_mm": width_mm, "height_mm": height_mm,
                         "font_pt": font_pt, "requested_font": font,
                         "actual_font": actual_font,
                         "missing_fonts": [name for name in requested_fonts if name not in available]}
    return fig


def _style_text(obj, meta):
    obj.set_fontfamily(meta["actual_font"])
    obj.set_fontsize(meta["font_pt"])
    obj.set_math_fontfamily("stix")
    if "Microsoft YaHei" in meta["actual_font"] and any(
            "\u3400" <= char <= "\u9fff" for char in obj.get_text()):
        obj.set_fontweight("bold")


def _style_figure(fig):
    for ax in fig.axes:
        ax.tick_params(axis="both", width=.7, labelsize=fig._nps_physical["font_pt"])
        for spine in ax.spines.values():
            spine.set_linewidth(.8)
    for obj in fig.findobj(Text):
        _style_text(obj, fig._nps_physical)


def _text_width_mm(fig, label, *, weight="normal"):
    obj = Text(text=label, fontweight=weight)
    obj.set_figure(fig)
    _style_text(obj, fig._nps_physical)
    width_px = obj.get_window_extent(fig.canvas.get_renderer()).width
    return width_px * MM_PER_INCH / fig.dpi


def canvas_axes(fig):
    """Millimetre-coordinate vector canvas, with screen-oriented y positions."""
    meta = fig._nps_physical
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, meta["width_mm"])
    ax.set_ylim(meta["height_mm"], 0)
    ax.axis("off")
    return ax


def axes_mm(fig, left, top, width, height):
    meta = fig._nps_physical
    return fig.add_axes([left / meta["width_mm"],
                         1 - (top + height) / meta["height_mm"],
                         width / meta["width_mm"], height / meta["height_mm"]])


def arrow(ax, start, end, *, color="#111111", width=1.0, head=7,
          dashed=False, zorder=5):
    """One shaft/head object; endpoints are explicit ports, not hidden centres."""
    if np.linalg.norm(np.asarray(end) - start) < 1e-6:
        raise ValueError("A connector needs a visible shaft")
    obj = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=head,
                          linewidth=width, color=color,
                          linestyle=(0, (3, 2)) if dashed else "-",
                          shrinkA=0, shrinkB=0, zorder=zorder)
    ax.add_patch(obj)
    return obj


def exact_crop(array: np.ndarray, roi: Sequence[int]) -> np.ndarray:
    """ROI is [x0,y0,x1,y1], with half-open native pixel bounds."""
    if array.ndim not in (2, 3):
        raise ValueError("Expected a scalar image or an RGB(A) image")
    if len(roi) != 4 or any(int(v) != v for v in roi):
        raise ValueError("ROI requires four integer native pixel coordinates")
    x0, y0, x1, y1 = map(int, roi)
    if not (0 <= x0 < x1 <= array.shape[1] and 0 <= y0 < y1 <= array.shape[0]):
        raise ValueError("ROI is empty or outside the source image")
    return array[y0:y1, x0:x1].copy()


def _image(ax, array, *, cmap=None, vmin=None, vmax=None):
    if array.ndim not in (2, 3) or (array.ndim == 3 and array.shape[-1] not in (3, 4)):
        raise ValueError("Expected a scalar image or an RGB(A) image")
    if array.ndim == 3 and any(x is not None for x in (cmap, vmin, vmax)):
        raise ValueError("Do not recolor or scalar-normalize observed RGB pixels")
    if array.ndim == 2:
        if cmap is None or vmin is None or vmax is None:
            raise ValueError("Scalar images need an explicit physical display range and colormap")
        if not np.isfinite([vmin, vmax]).all() or vmin >= vmax:
            raise ValueError("Scalar display limits must be finite and strictly increasing")
    kwargs = {} if array.ndim == 3 else {"cmap": cmap, "vmin": vmin, "vmax": vmax}
    artist = ax.imshow(array, origin="upper", interpolation="nearest", aspect="equal", **kwargs)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("black"); spine.set_linewidth(.8)
    return artist


def _tile_size(shape, max_side):
    h, w = shape[:2]
    factor = max_side / max(h, w)
    return w * factor, h * factor


def image_crop_plate(images: Sequence[dict], *, width_mm=166, font_pt=8.5,
                     tile_mm=36, gap_mm=3, roi=None, font="Times New Roman"):
    """Source row above exact ROI row; each item retains its own data/display.

    Item fields: array, label, source_id, optional cmap/vmin/vmax/scale_label,
    and individual roi_xyxy (otherwise the explicitly supplied common roi).
    Same-variable comparisons must supply the same explicit display limits.
    This function never interpolates, enhances, reconstructs or rescales data.
    """
    if not images:
        raise ValueError("No source images supplied")
    if not np.isfinite(tile_mm) or tile_mm <= 0 or not np.isfinite(gap_mm) or gap_mm < 0:
        raise ValueError("Tile side must be positive and gap must be nonnegative")
    required_width = len(images) * tile_mm + (len(images) - 1) * gap_mm + 8
    if required_width > width_mm:
        raise ValueError("Images do not fit: split the plate or change its canvas, not its font")
    crops = []
    sources = []
    for item in images:
        if not item.get("source_id"):
            raise ValueError("Every displayed image needs an actual source identity")
        array = np.asanyarray(item["array"])
        image_roi = item.get("roi_xyxy", roi)
        if image_roi is None:
            raise ValueError("Supply each image's native ROI or an explicit common pixel ROI")
        crop = exact_crop(array, image_roi)
        crops.append(crop)
        sources.append((array, image_roi))
    source_sizes = [_tile_size(array.shape, tile_mm) for array, _ in sources]
    crop_sizes = [_tile_size(crop.shape, tile_mm) for crop in crops]
    source_row_height = max(height for _, height in source_sizes)
    image_rows_height = source_row_height + max(height for _, height in crop_sizes)
    has_scalar = any(array.ndim == 2 for array, _ in sources)
    height_mm = image_rows_height + (30 if has_scalar else 21)
    fig = new_figure(width_mm, height_mm, font_pt, font)
    ax = canvas_axes(fig)
    left = (width_mm - (required_width - 8)) / 2
    color_groups = {}
    crop_records = []
    for index, (item, (array, image_roi), crop) in enumerate(zip(images, sources, crops)):
        x = left + index * (tile_mm + gap_mm)
        label = item["label"]
        if _text_width_mm(fig, label) > tile_mm + gap_mm - 1:
            raise ValueError(f"Image label {label!r} exceeds its slot at the chosen font and width")
        ax.text(x + tile_mm / 2, 4.5, label, ha="center", va="center")
        source_w, source_h = source_sizes[index]
        crop_w, crop_h = crop_sizes[index]
        top = axes_mm(fig, x + (tile_mm - source_w) / 2, 9, source_w, source_h)
        bottom = axes_mm(fig, x + (tile_mm - crop_w) / 2, 13 + source_row_height, crop_w, crop_h)
        settings = {k: item.get(k) for k in ("cmap", "vmin", "vmax")}
        scalar_artist = _image(top, array, **settings); _image(bottom, crop, **settings)
        x0, y0, x1, y1 = image_roi
        # White under-stroke keeps the exact same ROI visible on dark pixels.
        for color, weight in [("white", 2.0), ("black", .8)]:
            top.add_patch(Rectangle((x0 - .5, y0 - .5), x1 - x0, y1 - y0,
                                    fill=False, edgecolor=color, linewidth=weight))
        if array.ndim == 2:
            group = (item["cmap"], item["vmin"], item["vmax"], item.get("scale_label", ""))
            color_groups.setdefault(group, []).append((index, x, scalar_artist))
        crop_records.append({"source_id": item["source_id"], "roi_xyxy": list(image_roi),
                             "source_shape": list(array.shape), "crop_shape": list(crop.shape),
                             "interpolation": "nearest",
                             "geographic_correspondence": item.get("geographic_correspondence", "not asserted by pixel ROI")})
    for group, members in color_groups.items():
        indices = [m[0] for m in members]
        if indices != list(range(min(indices), max(indices) + 1)):
            raise ValueError("Keep shared-scale image groups adjacent or split the plate")
        x0, x1 = members[0][1], members[-1][1] + tile_mm
        inset = min(6, (x1 - x0) * .12)
        if _text_width_mm(fig, group[3]) > x1 - x0 + gap_mm - 1:
            raise ValueError(f"Display scale label {group[3]!r} exceeds its slot at the chosen font and width")
        cax = axes_mm(fig, x0 + inset, image_rows_height + 17, x1 - x0 - 2 * inset, 1.6)
        colorbar = fig.colorbar(members[0][2], cax=cax, orientation="horizontal",
                                ticks=[group[1], (group[1] + group[2]) / 2, group[2]])
        colorbar.ax.tick_params(length=2, pad=1)
        ax.text((x0 + x1) / 2, image_rows_height + 26, group[3], ha="center", va="center")
    fig._nps_crop_records = crop_records
    _style_figure(fig)
    return fig, crops


def paired_effects(rows: Sequence[dict], comparators: Sequence[str], metrics: Sequence[str],
                   *, width_mm=166, font_pt=8.5, xlabel="Difference", interval_label="95% interval",
                   font="Times New Roman", metric_xlabels=None, comparator_labels=None,
                   share_x=False):
    """Complete-roster paired estimates; values and intervals arrive already computed.

    Required row fields: comparator, metric, mean, lower95, upper95.
    The caller supplies the estimator, resampling unit, sign and metric units in
    the caption. This renderer does not bootstrap or silently pool saved data.
    Use metric_xlabels for separate axis titles/units. share_x is appropriate
    only for metrics whose values have interchangeable units and definitions.
    comparator_labels optionally maps input names to distinct short display names.
    """
    if (not comparators or not metrics or len(set(comparators)) != len(comparators)
            or len(set(metrics)) != len(metrics)):
        raise ValueError("Need distinct comparator names and metric names")
    lookup = {}
    for row in rows:
        key = row["comparator"], row["metric"]
        if key in lookup:
            raise ValueError("Duplicate effect row: " + str(key))
        mean, lo, hi = map(float, [row["mean"], row["lower95"], row["upper95"]])
        if not np.isfinite([mean, lo, hi]).all() or lo > hi:
            raise ValueError("Effect interval is missing, nonfinite or inconsistent")
        lookup[key] = mean, lo, hi
    expected = {(c, m) for c in comparators for m in metrics}
    if set(lookup) != expected:
        raise ValueError("Effect rows must match the complete declared comparator/metric roster")
    comparator_labels = comparator_labels or {}
    if set(comparator_labels) - set(comparators):
        raise ValueError("Display labels must refer to declared comparators")
    display_names = [comparator_labels.get(c, c) for c in comparators]
    if (any(not isinstance(label, str) or not label.strip() for label in display_names)
            or len(set(display_names)) != len(display_names)):
        raise ValueError("Provide distinct nonempty comparator display labels")
    if metric_xlabels is not None:
        if (set(metric_xlabels) != set(metrics)
                or any(not isinstance(label, str) or not label.strip() for label in metric_xlabels.values())):
            raise ValueError("Supply a nonempty axis title for each plotted metric")
    height_mm = max(40, 6 * len(comparators) + 24)
    fig = new_figure(width_mm, height_mm, font_pt, font)
    ax_canvas = canvas_axes(fig)
    left = max(32, 5 + max(_text_width_mm(fig, label) for label in display_names))
    right, gap = 5, 5
    panel_width = (width_mm - left - right - gap * (len(metrics) - 1)) / len(metrics)
    if panel_width < 25:
        raise ValueError("Labels and metrics do not fit at the chosen font; shorten display names, widen, or split the figure")
    if metric_xlabels is None and _text_width_mm(fig, xlabel) > width_mm - left - right:
        raise ValueError("Common axis title does not fit at the chosen font; use a shorter title or a wider figure")
    if share_x:
        shared_limits = _effect_limits(np.array(list(lookup.values())))
    y = np.arange(len(comparators))
    axes = []
    for j, metric in enumerate(metrics):
        x = left + j * (panel_width + gap)
        axis_title = metric_xlabels[metric] if metric_xlabels is not None else ""
        if (_text_width_mm(fig, metric, weight="bold") > panel_width + gap - 1
                or _text_width_mm(fig, axis_title) > panel_width + gap - 1):
            raise ValueError(f"Metric title or units for {metric!r} do not fit at the chosen font and width")
        ax = axes_mm(fig, x, 10, panel_width, height_mm - 23)
        coordinates = np.array([lookup[(c, metric)] for c in comparators])
        means, lows, highs = coordinates.T
        # Draw intervals independently: a valid bias-corrected/percentile
        # interval need not contain its separately supplied point estimate.
        ax.hlines(y, lows, highs, color="black", linewidth=1.0)
        ax.vlines(lows, y - .11, y + .11, color="black", linewidth=1.0)
        ax.vlines(highs, y - .11, y + .11, color="black", linewidth=1.0)
        ax.plot(means, y, "o", color="black", markersize=3.8,
                markerfacecolor=palette()["observation"], markeredgewidth=.7)
        ax.axvline(0, color="black", linestyle=(0, (3, 2)), linewidth=.9)
        ax.set_xlim(shared_limits if share_x else _effect_limits(coordinates))
        ax.set_ylim(len(comparators) - .5, -.5)
        ax.set_yticks(y, display_names if j == 0 else [""] * len(comparators))
        ax.tick_params(axis="y", length=0, pad=5)
        ax.tick_params(axis="x", pad=2, length=3)
        ax_canvas.text(x + panel_width / 2, 5, metric, ha="center", va="center", fontweight="bold")
        if axis_title:
            ax_canvas.text(x + panel_width / 2, height_mm - 4, axis_title, ha="center", va="center")
        axes.append(ax)
    if metric_xlabels is None:
        ax_canvas.text((left + width_mm - right) / 2, height_mm - 4,
                       xlabel, ha="center", va="center")
    fig._nps_effect_records = {"comparators": list(comparators), "metrics": list(metrics),
                                "values": lookup, "result_markers": len(expected),
                                "interval_label": interval_label, "xlabel": xlabel if metric_xlabels is None else None,
                                "metric_xlabels": metric_xlabels, "comparator_labels": comparator_labels,
                                "share_x": share_x}
    _style_figure(fig)
    return fig, axes


def _effect_limits(coordinates):
    low, high = min(float(coordinates.min()), 0), max(float(coordinates.max()), 0)
    padding = .07 * (high - low) if high > low else .1
    return low - padding, high + padding


def blank_result_slots(*, labels=("Metric 1", "Metric 2"), width_mm=166,
                       height_mm=54, font_pt=8.5, font="Times New Roman"):
    """Authorized layout preview: no invented values, ticks, bands or zero cells."""
    fig = new_figure(width_mm, height_mm, font_pt, font)
    ax = canvas_axes(fig)
    gap = 5
    w = (width_mm - 12 - gap * (len(labels) - 1)) / len(labels)
    for i, label in enumerate(labels):
        x = 6 + i * (w + gap)
        ax.text(x + w / 2, 7, label, ha="center", va="center", fontweight="bold")
        ax.add_patch(Rectangle((x, 13), w, height_mm - 20,
                              fill=False, edgecolor="black", linewidth=.8))
    fig._nps_pending = {"result_artist_count": 0, "draft_status": "layout-only"}
    _style_figure(fig)
    return fig


def renderer_report(fig) -> dict:
    """Measure exported-canvas typography, not nominal module rectangles."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width_px, height_px = fig.canvas.get_width_height()
    meta = fig._nps_physical
    text = []
    candidates = list(fig.texts)
    for ax in fig.axes:
        candidates.extend(ax.texts)
        if ax.axison:
            candidates.extend([ax.title, ax.xaxis.label, ax.yaxis.label,
                               ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()])
            # Locators may create visible=True labels outside the view interval;
            # Matplotlib does not actually paint those ticks. Do not report them
            # as clipped text in an otherwise correctly rendered canvas.
            xlow, xhigh = sorted(ax.get_xlim()); ylow, yhigh = sorted(ax.get_ylim())
            candidates.extend(label for location, label in zip(ax.get_xticks(), ax.get_xticklabels())
                              if xlow <= location <= xhigh)
            candidates.extend(label for location, label in zip(ax.get_yticks(), ax.get_yticklabels())
                              if ylow <= location <= yhigh)
            if ax.get_legend(): candidates.extend(ax.get_legend().get_texts())
    for n, obj in enumerate(candidates):
        if not obj.get_visible() or not obj.get_text():
            continue
        bbox = obj.get_window_extent(renderer)
        text.append({"id": f"text_{n}", "text": obj.get_text(),
                     "font_pt": float(obj.get_fontsize()),
                     "bbox_mm": [bbox.x0 / width_px * meta["width_mm"],
                                 (height_px - bbox.y1) / height_px * meta["height_mm"],
                                 bbox.x1 / width_px * meta["width_mm"],
                                 (height_px - bbox.y0) / height_px * meta["height_mm"]]})
    effect = getattr(fig, "_nps_effect_records", None)
    if effect:
        effect = {key: value for key, value in effect.items() if key != "values"}
    def outline(identifier, bbox):
        return {"id": identifier, "bbox_mm": [
            bbox.x0 / width_px * meta["width_mm"], (height_px - bbox.y1) / height_px * meta["height_mm"],
            bbox.x1 / width_px * meta["width_mm"], (height_px - bbox.y0) / height_px * meta["height_mm"],
        ]}

    panels = [outline(f"panel_{index}", axis.get_window_extent(renderer))
              for index, axis in enumerate(fig.axes) if axis.axison]
    pending = []
    if getattr(fig, "_nps_pending", None):
        for index, patch in enumerate(fig.axes[0].patches):
            entry = outline(f"pending_{index}", patch.get_window_extent(renderer))
            panels.append(entry)
            pending.append({"id": entry["id"], "result_artist_count": 0})
    return {"canvas_mm": [meta["width_mm"], meta["height_mm"]],
            "typography": meta, "text": text, "panels": panels,
            "schematic": bool(getattr(fig, "_nps_schematic", False)),
            "image_sources": getattr(fig, "_nps_crop_records", []),
            "effect_summary": effect,
            "pending_results": pending,
            "visual_review_required": True}


def save(fig, stem: Path | str, formats=("pdf", "svg", "png"), dpi=240):
    formats = tuple(formats)
    if any(fmt not in {"pdf", "svg", "png", "tiff"} for fmt in formats):
        raise ValueError("Choose PDF/SVG/PNG/TIFF or the requested native backend")
    if not np.isfinite(dpi) or dpi <= 0:
        raise ValueError("Raster export resolution must be positive")
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error", message=r"Glyph .* missing from font")
            report = renderer_report(fig)
    except UserWarning as exc:
        raise ValueError(f"Resolve the figure font for every required glyph before export: {exc}") from exc
    report["artifacts"] = {}
    with matplotlib.rc_context({"savefig.bbox": None, "pdf.fonttype": 42, "svg.fonttype": "none"}):
        for fmt in formats:
            path = stem.with_suffix("." + fmt)
            fig.savefig(path, dpi=dpi, facecolor="white")
            report["artifacts"][fmt] = {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}
    stem.with_suffix(".layout.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def image_plate_from_config(path: Path):
    """Portable JSON input; paths are relative to the config, never this machine."""
    config = json.loads(path.read_text(encoding="utf-8"))
    images = []
    for specification in config["images"]:
        item = dict(specification)
        source = path.parent / item.pop("path")
        key = item.pop("key", None)
        mask_key = item.pop("mask_key", None)
        if source.suffix.lower() == ".npz":
            if not key:
                raise ValueError("NPZ images need an explicit array key")
            with np.load(source, allow_pickle=False) as archive:
                array = archive[key].copy()
                if mask_key:
                    mask = archive[mask_key].astype(bool)
                    if mask.shape != array.shape[:2]:
                        raise ValueError("Image and quality mask shapes differ")
                    invalid = ~mask
                    if array.ndim == 3:
                        invalid = np.broadcast_to(invalid[..., None], array.shape)
                    array = np.ma.array(array, mask=invalid)
        elif source.suffix.lower() == ".npy":
            array = np.load(source, allow_pickle=False)
        else:
            array = plt.imread(source)
        item["array"] = array
        images.append(item)
    return image_crop_plate(images, width_mm=config.get("width_mm", 166),
                            font_pt=config.get("font_pt", 8.5),
                            font=config.get("font", PROJECT_FONTS),
                            tile_mm=config.get("tile_mm", 36),
                            gap_mm=config.get("gap_mm", 3), roi=config.get("roi_xyxy"))[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--blank-slots", action="store_true", help="Render empty slots for a layout draft")
    mode.add_argument("--image-plate-config", type=Path)
    mode.add_argument("--effect-config", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.image_plate_config:
        fig = image_plate_from_config(args.image_plate_config)
        save(fig, args.output_dir / "source_and_exact_crops")
        return
    if args.effect_config:
        config = json.loads(args.effect_config.read_text(encoding="utf-8"))
        with (args.effect_config.parent / config["csv"]).open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        # A declared metric subset is a valid figure scope. Do not filter the
        # comparator roster: that would conceal a missing or unexpected method.
        rows = [row for row in rows if row["metric"] in config["metrics"]]
        fig, _ = paired_effects(rows, config["comparators"], config["metrics"],
                               width_mm=config.get("width_mm", 166),
                               font_pt=config.get("font_pt", 8.5),
                               font=config.get("font", PROJECT_FONTS),
                               xlabel=config.get("xlabel", "Difference"), interval_label=config["interval_label"],
                               metric_xlabels=config.get("metric_xlabels"),
                               comparator_labels=config.get("comparator_labels"),
                               share_x=config.get("share_x", False))
        save(fig, args.output_dir / "paired_effects")
        return

    save(blank_result_slots(width_mm=166, font_pt=9), args.output_dir / "blank_result_layout")


if __name__ == "__main__":
    main()
