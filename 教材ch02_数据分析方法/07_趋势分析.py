"""第 2 章 引申方法 1：趋势分析。

教材用折线图看“近 10 年订单量”，并配一条“平均处理时长 / 预警值”参考线。
Python 版补上可量化的趋势指标：
  同比增速、区间复合增长率（CAGR）、峰值与谷值；
处理时长则用“均值线 + 预警线”判断异常周。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from 教材src.config import COLORS, save_fig, save_table
from 教材src.io_utils import read_excel


def main() -> None:
    raw = read_excel("ch02/trend.xlsx", sheet_name="趋势图", header=None)
    yearly = raw.iloc[2:13, 1:3].copy()
    yearly.columns = ["年份", "订单量"]
    yearly["年份"] = yearly["年份"].astype(int)
    yearly["订单量"] = pd.to_numeric(yearly["订单量"])
    yearly["同比增速"] = yearly["订单量"].pct_change()
    cagr = (yearly["订单量"].iloc[-1] / yearly["订单量"].iloc[0]) ** (1 / (len(yearly) - 1)) - 1

    print(f"2014—2024 订单量：{yearly['订单量'].iloc[0]} → {yearly['订单量'].iloc[-1]}，"
          f"CAGR = {cagr:.2%}")
    print(f"峰值 {yearly['订单量'].max()}（{yearly.loc[yearly['订单量'].idxmax(), '年份']}），"
          f"谷值 {yearly['订单量'].min()}（{yearly.loc[yearly['订单量'].idxmin(), '年份']}）")
    print(yearly.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    save_table(yearly, "ch02_年度订单趋势")

    weekly = raw.iloc[18:29, 1:5].copy()
    weekly.columns = ["周", "平均处理时长", "均值", "预警值"]
    for c in ["平均处理时长", "均值", "预警值"]:
        weekly[c] = pd.to_numeric(weekly[c])
    save_table(weekly, "ch02_周处理时长")

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.6), gridspec_kw={"width_ratios": [1.25, 1]})
    axes[0].plot(yearly["年份"], yearly["订单量"], color=COLORS[0], marker="o", ms=5, lw=2)
    axes[0].fill_between(yearly["年份"], yearly["订单量"], yearly["订单量"].min() * 0.92,
                         color=COLORS[0], alpha=0.08)
    for _, row in yearly.iterrows():
        axes[0].annotate(f"{row['订单量']:.0f}", (row["年份"], row["订单量"]),
                         textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    min_row = yearly.loc[yearly["订单量"].idxmin()]
    axes[0].annotate(f"{min_row['年份']:.0f} 年跌至谷值\n同比 {min_row['同比增速']:.1%}",
                     (min_row["年份"], min_row["订单量"]),
                     textcoords="offset points", xytext=(-14, 18), fontsize=9, color="#C0392B",
                     ha="right", va="bottom",
                     arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1))
    axes[0].set_xticks(yearly["年份"].tolist())
    axes[0].tick_params(axis="x", labelsize=8.5)
    axes[0].set_ylim(yearly["订单量"].min() * 0.88, yearly["订单量"].max() * 1.15)
    axes[0].set_ylim(yearly["订单量"].min() * 0.88, yearly["订单量"].max() * 1.15)
    axes[0].set_xlabel("年份")
    axes[0].set_ylabel("订单量（个）")
    axes[0].set_title(f"近 11 年订单量：整体上行，CAGR {cagr:.1%}")

    axes[1].plot(range(len(weekly)), weekly["平均处理时长"], color=COLORS[1],
                 marker="o", ms=5, lw=1.8, label="平均处理时长")
    mean_v, warn_v = weekly["均值"].iloc[0], weekly["预警值"].iloc[0]
    axes[1].axhline(mean_v, color=COLORS[0], ls="--", lw=1.2, label=f"均值 {mean_v:.1f}h")
    axes[1].axhline(warn_v, color="#C0392B", ls=":", lw=1.4, label=f"预警值 {warn_v:.0f}h")
    over = weekly[weekly["平均处理时长"] > weekly["预警值"]]
    over_pos = [weekly.index.get_loc(i) for i in over.index]
    axes[1].scatter(over_pos, over["平均处理时长"], s=70, color="#C0392B", zorder=4)
    for pos, (_, row) in zip(over_pos, over.iterrows()):
        axes[1].annotate(f"{row['平均处理时长']:.0f}h 超预警", (pos, row["平均处理时长"]),
                         textcoords="offset points", xytext=(-14, 10), fontsize=8.5,
                         color="#C0392B", ha="right")
    axes[1].set_xticks(range(len(weekly)),
                       [str(i) for i in range(1, len(weekly) + 1)], fontsize=8.5)
    axes[1].set_ylim(0, 44)
    axes[1].set_xlabel("周次（第 1—11 周）")
    axes[1].set_ylabel("平均处理时长（小时）")
    axes[1].set_title(f"周处理时长：第 {over['周'].str.replace('week', '').iloc[0]} 周触发预警")
    axes[1].legend(loc="lower left")
    save_fig(fig, "ch02_趋势分析")


if __name__ == "__main__":
    main()
