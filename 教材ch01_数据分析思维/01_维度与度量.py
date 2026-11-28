"""第 1 章 数据分析思维：维度、度量与聚合规则。

教材用 Excel 数据透视表演示“维度切分 + 度量汇总”。
Python 迁移后仍保留同一套思维：
  - 维度（dimension）：年份、市场，用来分组和筛选；
  - 度量（measure）：销售额、利润，必须连同汇总规则（sum/avg）一起定义；
  - 聚合陷阱：利润率的平均值不等于总利润/总销售额，必须加权。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from 教材src.config import ACCENT, COLORS, yuan, save_fig, save_table
from 教材src.io_utils import read_csv


def main() -> None:
    df = read_csv("ch01/sale.csv")
    df["利润率"] = df["profit"] / df["sale"]

    sale_pivot = df.pivot_table(index="year", columns="market", values="sale", aggfunc="sum")
    profit_pivot = df.pivot_table(index="year", columns="market", values="profit", aggfunc="sum")
    rate_pivot = profit_pivot / sale_pivot

    total_sale, total_profit = df["sale"].sum(), df["profit"].sum()
    weighted_rate = total_profit / total_sale
    naive_rate = df["利润率"].mean()
    print(f"总销售额 {yuan(total_sale)}，总利润 {yuan(total_profit)}")
    print(f"加权毛利率（总利润/总销售额）= {weighted_rate:.2%}")
    print(f"简单平均毛利率（12 行利润率取平均）= {naive_rate:.2%}")
    print(f"两者相差 {abs(weighted_rate - naive_rate) * 100:.2f} 个百分点\n")

    market_summary = (
        df.groupby("market")
        .agg(销售额=("sale", "sum"), 利润=("profit", "sum"))
        .assign(毛利率=lambda x: x["利润"] / x["销售额"])
        .sort_values("销售额", ascending=False)
    )
    print(market_summary.to_string(float_format=lambda v: f"{v:,.4f}"))
    save_table(market_summary.reset_index(), "ch01_分市场汇总")
    save_table(sale_pivot.rename_axis(index="年份"), "ch01_销售额透视", index=True)

    # 图 1：各市场销售额趋势（维度=年份/市场，度量=销售额 sum）
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for i, market in enumerate(sale_pivot.columns):
        ax.plot(sale_pivot.index, sale_pivot[market] / 1e4, marker="o", ms=4.5,
                color=COLORS[i], label=f"{market}市场")
        ax.annotate(f"{sale_pivot[market].iloc[-1] / 1e4:.1f}",
                    (sale_pivot.index[-1], sale_pivot[market].iloc[-1] / 1e4),
                    textcoords="offset points", xytext=(6, 0), fontsize=8.5,
                    color=COLORS[i], va="center")
    ax.set_xticks(sale_pivot.index)
    ax.set_xlabel("年份")
    ax.set_ylabel("销售额（万元）")
    ax.set_title("四个市场的销售额趋势：体量接近，增长都偏弱")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.13))
    save_fig(fig, "ch01_分市场销售额趋势")

    # 图 2：毛利率热力图，同时标出加权总体毛利率
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    data = rate_pivot.to_numpy()
    im = ax.imshow(data, cmap="Blues", aspect="auto", vmin=data.min() * 0.97, vmax=data.max() * 1.02)
    ax.set_xticks(np.arange(len(rate_pivot.columns)), rate_pivot.columns)
    ax.set_yticks(np.arange(len(rate_pivot.index)), rate_pivot.index)
    ax.set_xlabel("市场")
    ax.set_ylabel("年份")
    ax.set_title(f"毛利率热力图（总体加权毛利率 {weighted_rate:.2%}）")
    ax.grid(False)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:.2%}", ha="center", va="center", fontsize=9,
                    color="white" if data[i, j] > np.median(data) else "#1F2A37")
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, format=lambda v, _: f"{v:.0%}")
    save_fig(fig, "ch01_毛利率热力图")

    # 图 3：把“年份”下钻到“市场”，看每年销售额由哪些市场构成
    share = sale_pivot.div(sale_pivot.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    bottom = np.zeros(len(share))
    for i, market in enumerate(share.columns):
        ax.bar(share.index.astype(str), share[market], bottom=bottom, width=0.55,
               color=COLORS[i], label=f"{market}市场")
        for x, (v, b) in enumerate(zip(share[market], bottom)):
            if v > 0.12:
                ax.text(x, b + v / 2, f"{v:.0%}", ha="center", va="center",
                        color="white", fontsize=9)
        bottom += share[market].to_numpy()
    ax.set_ylim(0, 1)
    ax.set_ylabel("销售额占比")
    ax.set_xlabel("年份")
    ax.set_title("按年份下钻：四个市场规模相当，各占约四分之一")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.13))
    save_fig(fig, "ch01_市场构成下钻")


if __name__ == "__main__":
    main()
