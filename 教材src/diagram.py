"""用 matplotlib 画维度模型 / ER 图，替代 Power BI 的模型视图。"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .config import save_fig


def _box_rect(node):
    x, y = node["xy"]
    w = node.get("w", 2.5)
    h = 0.60 + 0.21 * len(node["fields"])
    return x - w / 2, y - h / 2, w, h


def _edge_point(rect, toward):
    x, y, w, h = rect
    cx, cy = x + w / 2, y + h / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    scale = min(
        (w / 2) / abs(dx) if dx else float("inf"),
        (h / 2) / abs(dy) if dy else float("inf"),
    )
    return cx + dx * scale, cy + dy * scale


def draw_schema(nodes, edges, title, filename, figsize=(11.5, 6.6)):
    """nodes: {name: {xy, fields, color?, w?}}；edges: [(src, dst, label)]。"""
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    rects = {}
    for name, node in nodes.items():
        x, y, w, h = _box_rect(node)
        rects[name] = (x, y, w, h)
        color = node.get("color", "#2E5E8C")
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.2, edgecolor=color, facecolor=color + "12",
        ))
        ax.add_patch(FancyBboxPatch(
            (x, y + h - 0.34), w, 0.34, boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=0, facecolor=color, alpha=0.92,
        ))
        ax.text(x + w / 2, y + h - 0.17, name, ha="center", va="center",
                color="white", fontsize=9.5, fontweight="bold")
        for i, field in enumerate(node["fields"]):
            ax.text(x + 0.12, y + h - 0.56 - i * 0.21, field, ha="left", va="center",
                    fontsize=7.8, color="#26313D")

    left = min(r[0] for r in rects.values())
    right = max(r[0] + r[2] for r in rects.values())
    bottom = min(r[1] for r in rects.values())
    top = max(r[1] + r[3] for r in rects.values())
    ax.set_xlim(left - 0.55, right + 0.55)
    ax.set_ylim(bottom - 0.45, top + 0.45)

    for src, dst, label in edges:
        p1 = _edge_point(rects[src], _center(rects[dst]))
        p2 = _edge_point(rects[dst], _center(rects[src]))
        ax.add_patch(FancyArrowPatch(
            p1, p2, arrowstyle="-|>", mutation_scale=11,
            linewidth=1.1, color="#7A828C", shrinkA=0, shrinkB=0,
        ))
        if label:
            ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 0.08, label,
                    ha="center", va="bottom", fontsize=7, color="#5B6470",
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    fig.subplots_adjust(left=0.015, right=0.985, top=0.90, bottom=0.02)
    save_fig(fig, filename)


def _center(rect):
    x, y, w, h = rect
    return x + w / 2, y + h / 2
