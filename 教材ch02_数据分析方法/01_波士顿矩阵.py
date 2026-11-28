"""第 2 章 基础分析范式 1：波士顿矩阵（BCG Matrix）。

教材在 Excel 里用“销售额占比 + 销售额环比”两个指标，把 14 个品牌
按“品牌平均市场占有率 / 总市场环比增长率”两条阈值线分成四类。
Python 迁移的关键点：
  - 订单金额是计算列：单价 × 销量（原练习表刻意没有这一列）；
  - 阈值不是拍脑袋，而是“总体增长率”和“各品牌占有率均值”；
  - 矩阵图用气泡大小表达销售额，避免只看位置忽略体量。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from 教材src.config import COLORS, save_fig, save_table
from 教材src.io_utils import read_excel


def classify(row, avg_share, total_growth):
    if row["市场占有率"] >= avg_share and row["销售增长率"] >= total_growth:
        return "明星品牌"
    if row["市场占有率"] >= avg_share and row["销售增长率"] < total_growth:
        return "金牛品牌"
    if row["市场占有率"] < avg_share and row["销售增长率"] >= total_growth:
        return "问题品牌"
    return "瘦狗品牌"


def main() -> None:
    df = read_excel("ch02/boston.xlsx", sheet_name="销售表")
    df["订单金额"] = df["单价"] * df["销量"]
    df["销售日期"] = pd.to_datetime(df["销售日期"])
    df["月"] = df["销售日期"].dt.month

    monthly = df.pivot_table(index="品牌", columns="月", values="订单金额", aggfunc="sum").fillna(0)
    monthly.columns = ["7月", "8月"]
    monthly["销售额"] = monthly.sum(axis=1)
    monthly["市场占有率"] = monthly["销售额"] / monthly["销售额"].sum()
    monthly["销售增长率"] = monthly["8月"] / monthly["7月"] - 1

    total_growth = monthly["8月"].sum() / monthly["7月"].sum() - 1
    avg_share = monthly["市场占有率"].mean()
    monthly["品牌类型"] = monthly.apply(classify, axis=1, avg_share=avg_share, total_growth=total_growth)
    monthly = monthly.sort_values("销售额", ascending=False)

    print(f"总市场环比增长率 = {total_growth:.4%}（阈值线）")
    print(f"品牌平均市场占有率 = {avg_share:.4%}（阈值线，14 个品牌即 1/14）")
    print(monthly[["销售额", "市场占有率", "销售增长率", "品牌类型"]]
          .to_string(float_format=lambda v: f"{v:,.4f}"))
    print("\n四象限品牌数：")
    print(monthly["品牌类型"].value_counts().to_string())
    save_table(monthly.reset_index(), "ch02_波士顿矩阵")

    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    type_colors = {"明星品牌": COLORS[0], "金牛品牌": COLORS[2], "问题品牌": COLORS[1], "瘦狗品牌": COLORS[3]}
    for kind, group in monthly.groupby("品牌类型"):
        ax.scatter(group["市场占有率"], group["销售增长率"],
                   s=group["销售额"] / 1200, color=type_colors[kind],
                   alpha=0.82, edgecolor="white", linewidth=1.2, label=kind, zorder=3)
    for brand, row in monthly.iterrows():
        ax.annotate(brand, (row["市场占有率"], row["销售增长率"]),
                    textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8.5)

    ax.axvline(avg_share, color="#7A828C", ls="--", lw=1, zorder=1)
    ax.axhline(total_growth, color="#7A828C", ls="--", lw=1, zorder=1)
    ax.text(avg_share * 1.02, 0.155, "平均占有率 7.14%", fontsize=8.5, color="#5B6470")
    ax.text(0.005, total_growth + 0.004, "总市场增长 2.17%", fontsize=8.5, color="#5B6470")

    ax.set_xlim(0, 0.225)
    ax.set_ylim(-0.16, 0.185)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_xlabel("市场占有率（销售额占比）")
    ax.set_ylabel("销售增长率（8 月环比）")
    ax.set_title("品牌波士顿矩阵：气泡大小 = 销售额，虚线为教材阈值")
    ax.legend(loc="lower right", ncol=2)
    save_fig(fig, "ch02_波士顿矩阵")


if __name__ == "__main__":
    main()
