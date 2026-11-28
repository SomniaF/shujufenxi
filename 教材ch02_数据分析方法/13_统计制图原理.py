"""第 2 章：统计制图原理（图表选择与常见误区）。

教材用同一份“4 个市场 × 3 年”的销售数据，演示三类制图问题：
  1. 双轴图：销售额（万元级）与毛利率（个位数百分比）共用一个画面，
     两条轴的刻度可以任意缩放，视觉上的“交叉”“靠拢”都是人为的；
  2. 饼图：2012 年 4 个市场销售额几乎四等分，饼图读不出高低；
  3. 分面小图：把 4 个市场拆成 4 个小图、共用同一纵轴，趋势差异才看得清。
结论：一张图只讲一件事；比较大小用条形，看趋势用折线，看构成要先确认差异够大。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import ACCENT, COLORS, GREY, save_fig, save_table
from src.io_utils import read_csv


def main() -> None:
    df = read_csv("ch02/sale.csv")
    df["毛利率%"] = df["profit"] / df["sale"] * 100
    wide = df.pivot(index="year", columns="market", values="毛利率%")
    markets = ["东", "南", "西", "北"]
    wide = wide[markets]
    print("各市场毛利率（%）：")
    print(wide.round(2).to_string())
    save_table(df.round(2), "ch02_市场销售额与毛利率", index=False)

    y2012 = df[df["year"] == 2012].set_index("market").loc[markets]
    y2012["占比%"] = y2012["sale"] / y2012["sale"].sum() * 100
    print("\n2012 年市场构成：")
    print(y2012[["sale", "占比%", "毛利率%"]].round(2).to_string())
    save_table(y2012[["sale", "占比%", "毛利率%"]].round(2),
               "ch02_市场构成", index=True)

    east = wide.loc[2010, "东"], wide.loc[2012, "东"]
    south = wide.loc[2010, "南"], wide.loc[2012, "南"]
    print(f"\n东：{east[0]:.2f}% → {east[1]:.2f}%（{east[1] - east[0]:+.2f} 个百分点）")
    print(f"南：{south[0]:.2f}% → {south[1]:.2f}%（{south[1] - south[0]:+.2f} 个百分点）")
    print(f"2012 年四市场销售额极差仅 {y2012['sale'].max() - y2012['sale'].min():,} 元，"
          f"最高与最低相差 {(y2012['sale'].max() / y2012['sale'].min() - 1) * 100:.1f}%")

    fig = plt.figure(figsize=(13.0, 5.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], hspace=0.55, wspace=0.28)
    bad = fig.add_subplot(gs[:, 0])
    xpos = np.arange(len(df))
    bad.bar(xpos, df["sale"], color="#B9C6D4", width=0.7)
    bad.set_ylabel("销售额（元）", color=GREY)
    bad.set_xticks([])
    bad.set_ylim(0, 42000)
    twin = bad.twinx()
    for i, m in enumerate(markets):
        mask = (df["market"] == m).to_numpy()
        twin.plot(xpos[mask], df.loc[mask, "毛利率%"],
                  color=COLORS[i], marker="o", ms=3.5, lw=1.6, label=m)
    twin.set_ylim(0, 20)
    twin.set_ylabel("毛利率（%）", color=GREY)
    twin.legend(loc="upper center", ncol=4, fontsize=8.5,
                bbox_to_anchor=(0.5, 1.02))
    bad.set_title("反面示例：双轴图把两种量纲硬塞进一张图\n"
                  "左轴 0–42,000 元、右轴 0–20%，两条曲线的高低由刻度决定")
    bad.grid(axis="y", visible=False)

    ax1 = fig.add_subplot(gs[0, 1])
    for i, m in enumerate(markets):
        ax1.plot(wide.index, wide[m], marker="o", color=COLORS[i], lw=1.8, label=m)
    ax1.set_ylim(6, 10)
    ax1.set_xticks([2010, 2011, 2012])
    ax1.set_ylabel("毛利率（%）")
    ax1.set_title("正确做法 1：只画一个量纲（毛利率），四个市场分线", fontsize=11)
    ax1.legend(ncol=4, fontsize=8.5, loc="upper left")
    ax1.grid(axis="y")

    ax2 = fig.add_subplot(gs[1, 1])
    x = np.arange(len(wide.index))
    w = 0.2
    for i, m in enumerate(markets):
        sub = df[df["market"] == m].sort_values("year")
        ax2.bar(x + (i - 1.5) * w, sub["sale"] / 1e4, width=w,
                color=COLORS[i], label=m)
    ax2.set_xticks(x, wide.index)
    ax2.set_ylim(0, 4.6)
    ax2.set_ylabel("销售额（万元）")
    ax2.set_title("正确做法 2：销售额单独看，四市场量级接近", fontsize=11)
    ax2.legend(ncol=4, fontsize=8, loc="upper center")
    ax2.grid(axis="y")
    fig.subplots_adjust(left=0.07, right=0.92, top=0.86, bottom=0.08)
    save_fig(fig, "ch02_统计制图_双轴图误区", tight=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9), gridspec_kw={"width_ratios": [1, 1.25]})
    values = y2012["sale"].to_numpy()
    axes[0].pie(values, labels=markets,
                colors=["#D6E2EE", "#E9D9C6", "#D3E3D9", "#E6D2D5"],
                autopct="%1.1f%%", startangle=90,
                textprops={"fontsize": 9},
                wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    axes[0].set_title("饼图：四块几乎等分（24.7%–25.3%）\n读不出谁高谁低，还占了大面积")

    order = y2012["毛利率%"].sort_values()
    bars = axes[1].bar(order.index, order.to_numpy(), color=COLORS[3], width=0.55)
    for bar, v in zip(bars, order.to_numpy()):
        axes[1].text(bar.get_x() + bar.get_width() / 2, v + 0.12, f"{v:.2f}%",
                     ha="center", fontsize=9)
    axes[1].set_ylim(0, 11.5)
    axes[1].set_ylabel("毛利率（%）")
    axes[1].set_xlabel("市场（按毛利率排序）")
    axes[1].set_title("同样 4 个市场，换成排序柱形：东最低 6.66%，南最高 9.63%")
    axes[1].grid(axis="y")
    axes[1].grid(axis="x", visible=False)
    save_fig(fig, "ch02_统计制图_饼图与排序")

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 6.6), sharex=True, sharey=True)
    for ax, m in zip(axes.ravel(), markets):
        ax.plot(wide.index, wide[m], marker="o", color=COLORS[markets.index(m)], lw=1.9)
        ax.set_ylim(6, 10.2)
        ax.set_title(f"{m}市场：{wide.loc[2010, m]:.2f}% → {wide.loc[2012, m]:.2f}%",
                     fontsize=11)
        ax.grid(axis="y")
        for yr in wide.index:
            ax.annotate(f"{wide.loc[yr, m]:.1f}", (yr, wide.loc[yr, m]),
                        textcoords="offset points", xytext=(0, 7),
                        ha="center", fontsize=8, color=GREY)
    for ax in axes[1]:
        ax.set_xlabel("年份")
    axes[0, 0].set_xticks([2010, 2011, 2012])
    for ax in axes[:, 0]:
        ax.set_ylabel("毛利率（%）")
    fig.suptitle("分面小图：共用纵轴 6%–10%，四个市场的走势差异一眼可见", y=1.0)
    save_fig(fig, "ch02_统计制图_分面小图")


if __name__ == "__main__":
    main()
