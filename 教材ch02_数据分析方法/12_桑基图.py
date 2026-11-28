"""第 2 章 引申方法 6：桑基图（流量路径）。

教材的素材是网站页面的点击流向：首页 2,700 次点击分流到 4 个栏目，
再由栏目流向下一层页面。桑基图的“带宽 = 流量”，能一眼看出哪条路径粗、
哪条路径在中途断掉。
本脚本用 matplotlib 手绘桑基图（不额外依赖 plotly / pyecharts），
同时输出每个页面的“流入 / 流出 / 继续浏览率”，补上桑基图读不出的比例。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch, Rectangle

from src.config import COLORS, GREY, save_fig, save_table
from src.io_utils import read_excel


def build_depth(flows) -> dict[str, int]:
    nodes = list(dict.fromkeys(flows["来源"].tolist() + flows["目标"].tolist()))
    depth = {n: 0 for n in nodes}
    for _ in range(len(nodes)):
        changed = False
        for s, t in zip(flows["来源"], flows["目标"]):
            if depth[t] < depth[s] + 1:
                depth[t] = depth[s] + 1
                changed = True
        if not changed:
            break
    return depth


def draw_sankey(ax, flows, title: str) -> None:
    depth = build_depth(flows)
    inflow = flows.groupby("目标")["流量"].sum().to_dict()
    outflow = flows.groupby("来源")["流量"].sum().to_dict()
    nodes = [n for n in dict.fromkeys(flows["来源"].tolist() + flows["目标"].tolist())]
    value = {n: max(inflow.get(n, 0), outflow.get(n, 0)) for n in nodes}

    roots = {n: n for n in nodes if depth[n] <= 1}
    for _ in range(len(nodes)):
        for s, t in zip(flows["来源"], flows["目标"]):
            if s in roots and t not in roots:
                roots[t] = roots[s]
    color_of = {n: COLORS[i % len(COLORS)] for i, n in enumerate(
        [n for n in nodes if depth[n] == 1])}
    for n in nodes:
        if n not in color_of:
            color_of[n] = color_of.get(roots.get(n, n), COLORS[0])

    gap, node_w = 3.2, 0.22
    columns: dict[int, list[str]] = {}
    for n in nodes:
        columns.setdefault(depth[n], []).append(n)
    span = max(sum(value[n] for n in col) + gap * (len(col) - 1)
               for col in columns.values())
    scale = 100.0 / span
    x_of = {d: 0.35 + d * 3.3 for d in columns}

    pos, label_right = {}, {}
    for d, col in columns.items():
        col.sort(key=lambda n: -value[n])
        cursor = 100.0
        for n in col:
            h = value[n] * scale
            pos[n] = (x_of[d], cursor - h, cursor)
            cursor -= h + gap * scale
        label_right[d] = d != max(columns)

    out_cursor = {n: pos[n][2] for n in nodes}
    in_cursor = {n: pos[n][2] for n in nodes}
    order = flows.assign(层级=flows["来源"].map(depth),
                         _ty=flows["目标"].map(lambda n: pos[n][2]))
    order = order.sort_values(["层级", "来源", "_ty"], ascending=[True, True, False])
    for _, row in order.iterrows():
        s, t, w = row["来源"], row["目标"], row["流量"] * scale
        x0, _, _ = pos[s]
        x1, _, _ = pos[t]
        y0a, y0b = out_cursor[s], out_cursor[s] - w
        y1a, y1b = in_cursor[t], in_cursor[t] - w
        out_cursor[s] = y0b
        in_cursor[t] = y1b
        xm = (x0 + node_w + x1) / 2
        verts = [(x0 + node_w, y0a), (xm, y0a), (xm, y1a), (x1, y1a),
                 (x1, y1b), (xm, y1b), (xm, y0b), (x0 + node_w, y0b),
                 (x0 + node_w, y0a)]
        codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color_of[roots[t]],
                               alpha=0.5, edgecolor="none", zorder=1))

    for n in nodes:
        x, y0, y1 = pos[n]
        ax.add_patch(Rectangle((x, y0), node_w, y1 - y0, facecolor="#4A5260",
                               edgecolor="none", zorder=2))
        if label_right[depth[n]]:
            ax.text(x + node_w + 0.16, (y0 + y1) / 2, f"{n}  {value[n]:,}",
                    va="center", ha="left", fontsize=8.8,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85})
        else:
            ax.text(x - 0.16, (y0 + y1) / 2, f"{n}  {value[n]:,}",
                    va="center", ha="right", fontsize=8.8,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85})

    ax.set_xlim(-0.2, max(x_of.values()) + 2.6)
    ax.set_ylim(-2, 104)
    ax.axis("off")
    ax.set_title(title, pad=12)


def main() -> None:
    flows = read_excel("ch02/sankey.xlsx", sheet_name=0)
    flows = flows[["来源", "目标", "流量"]].dropna()
    flows["流量"] = flows["流量"].astype(int)
    total = int(flows.loc[flows["来源"] == "首页", "流量"].sum())

    depth = build_depth(flows)
    flows["层级"] = flows["来源"].map(depth)
    save_table(flows, "ch02_页面流量明细", index=False)

    inflow = flows.groupby("目标")["流量"].sum()
    outflow = flows.groupby("来源")["流量"].sum()
    stay = []
    for node in outflow.index:
        if node == "首页":
            continue
        inn = int(inflow.get(node, 0))
        out = int(outflow[node])
        rate = out / inn * 100 if inn else float("nan")
        stay.append({"页面": node, "流入": inn, "流出": out,
                     "继续浏览率%": round(rate, 1) if inn else None,
                     "未继续": inn - out})
    stay = pd.DataFrame(stay)
    print("各页面流量留存：")
    print(stay.to_string(index=False))
    save_table(stay, "ch02_页面流量留存")

    stuck = stay.sort_values("继续浏览率%").iloc[0]
    over = stay[stay["流出"] > stay["流入"]]
    if len(over):
        print(f"提示：{'、'.join(over['页面'])} 的流出大于流入，"
              "源表入口流量合计不足，按原值绘制桑基图。")
    strongest = flows[flows["来源"] == "首页"].sort_values("流量", ascending=False).iloc[0]
    print(f"\n首页共 {total:,} 次点击，最强分流是“首页 → {strongest['目标']}”"
          f"（{int(strongest['流量']):,} 次）")
    print(f"继续浏览率最低的是“{stuck['页面']}”（{stuck['继续浏览率%']}%），"
          f"有 {int(stuck['未继续'])} 次点击停在这一页")

    fig, ax = plt.subplots(figsize=(13.6, 7.2))
    draw_sankey(ax, flows, f"网站点击流向：首页 {total:,} 次点击，带宽即流量")
    save_fig(fig, "ch02_桑基图")

    top_branch = flows[flows["来源"] == "首页"].sort_values("流量", ascending=False)
    print("\n首页一级分流：")
    print(top_branch[["目标", "流量"]].assign(
        占比=(top_branch["流量"] / total * 100).round(1)).to_string(index=False))


if __name__ == "__main__":
    main()
