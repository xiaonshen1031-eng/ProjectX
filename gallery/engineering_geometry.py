"""Shared primitive data for the two native engineering gallery renderers."""

import numpy as np


def panel(position, xlim, ylim, *, xlabel="", ylabel="", xtick=None, ytick=None,
          xticklabels=None, yticklabels=None, grid="", axis=True):
    return {
        "position": position, "xlim": xlim, "ylim": ylim, "xlabel": xlabel, "ylabel": ylabel,
        "xtick": xtick, "ytick": ytick, "xticklabels": xticklabels, "yticklabels": yticklabels,
        "grid": grid, "axis": axis, "layers": [],
    }


def layer(a, kind, x, y, **attrs):
    a["layers"].append({"kind": kind, "x": x, "y": y, **attrs})


def line(a, x, y, color="ink", width=1.5, style="-"):
    layer(a, "line", x, y, color=color, width=width, style=style)


def polygon(a, x, y, face, edge="none", width=0.7):
    layer(a, "polygon", x, y, face=face, edge=edge, width=width)


def rect(a, left, right, bottom, top, face, edge="none", width=0.7):
    polygon(a, [left, right, right, left], [bottom, bottom, top, top], face, edge, width)


def points(a, x, y, *, marker="o", face="white", edge="ink", size=7, width=1.05):
    layer(a, "points", np.atleast_1d(x), np.atleast_1d(y), marker=marker, face=face,
          edge=edge, size=size, width=width)


def text(a, x, y, label, *, size=18, align="left", color="ink"):
    layer(a, "text", x, y, label=label, size=size, align=align, color=color)


def band(a, x, low, high, color):
    polygon(a, np.r_[x, x[::-1]], np.r_[low, high[::-1]], color)


def steps(values, step=1):
    edges = np.arange(len(values) + 1) * step
    return np.repeat(edges, 2)[1:-1], np.repeat(values, 2)


def key(position):
    return panel(position, [0, 1], [0, 1], axis=False)
