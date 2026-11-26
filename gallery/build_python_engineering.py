"""Render saved engineering evidence as native Matplotlib plots."""

from matplotlib.patches import Polygon

from build_python import COLORS, base, style


def color(value):
    return COLORS.get(value, value)


def render(series):
    figure = base()
    for spec in series["panels"]:
        ax = figure.add_axes(spec["position"])
        style(ax)
        ax.set_xlim(spec["xlim"])
        ax.set_ylim(spec["ylim"])
        # The 406.4 mm canvas scales to a 166 mm report width: 9.4 pt axes, 8.2 pt ticks.
        ax.set_xlabel(spec["xlabel"], fontsize=23)
        ax.set_ylabel(spec["ylabel"], fontsize=23)
        ax.tick_params(labelsize=20, pad=4)
        if spec["xtick"] is not None:
            ax.set_xticks(spec["xtick"], labels=spec["xticklabels"])
        if spec["ytick"] is not None:
            ax.set_yticks(spec["ytick"], labels=spec["yticklabels"])
        if spec["grid"]:
            ax.set_axisbelow(True)
            ax.grid(axis=spec["grid"], color=COLORS["grid"], linewidth=.65)
        if not spec["axis"]:
            ax.set_axis_off()

        for mark in spec["layers"]:
            x, y = mark["x"], mark["y"]
            kind = mark["kind"]
            if kind == "line":
                ax.plot(x, y, color=color(mark["color"]), lw=mark["width"],
                        ls=mark["style"])
            elif kind == "polygon":
                vertices = list(zip(x, y))
                ax.add_patch(Polygon(vertices, facecolor=color(mark["face"]),
                                     edgecolor=color(mark["edge"]), linewidth=mark["width"]))
            elif kind == "points":
                ax.plot(x, y, linestyle="none", marker=mark["marker"], markerfacecolor=color(mark["face"]),
                        markeredgecolor=color(mark["edge"]), markersize=mark["size"],
                        markeredgewidth=mark["width"])
            elif kind == "text":
                ax.text(x, y, mark["label"], va="center", ha=mark["align"],
                        color=color(mark["color"]), fontsize=mark["size"])
            else:
                raise ValueError(f"Unknown mark {kind!r}")
    return figure
