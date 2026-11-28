"""第 2 章 引申方法 2：对比分析。

教材给了三组对比素材：
  1. 11 个产品的订单量排名；
  2. 12 个“名字很长”的产品——用来练习标签不重叠的排序条形图；
  3. 某顾客在 I/E/S/N/T/P 六个因素上的得分——雷达图。
对比分析的要点：先排序、再看差距，类别多时用横向条形而非饼图。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import COLORS, save_fig, save_table
from src.io_utils import read_excel


def main() -> None:
    raw = read_excel("ch02/compare.xlsx", sheet_name="对比分析", header=None)

    products = raw.iloc[2:13, 1:3].copy()
    products.columns = ["产品", "订单量"]
    products["订单量"] = pd.to_numeric(products["订单量"])
    products = products.sort_values("订单量", ascending=False).reset_index(drop=True)
    print("11 个产品订单量：")
    print(products.to_string(index=False))
    print(f"最高 {products['订单量'].max()}，最低 {products['订单量'].min()}，"
          f"极差 {products['订单量'].max() - products['订单量'].min()}，"
          f"均值 {products['订单量'].mean():.1f}")
    save_table(products, "ch02_产品订单对比")

    long_names = raw.iloc[18:29, 1:3].copy()
    long_names.columns = ["产品", "订单量"]
    long_names["订单量"] = pd.to_numeric(long_names["订单量"])
    long_names = long_names.sort_values("订单量")
    save_table(long_names, "ch02_长名称产品排序")

    factors = raw.iloc[38:44, 1:3].copy()
    factors.columns = ["因素", "得分"]
    factors["得分"] = pd.to_numeric(factors["得分"])
    save_table(factors, "ch02_顾客画像因素")

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9), gridspec_kw={"width_ratios": [1.35, 1]})
    colors = [COLORS[0] if v >= products["订单量"].median() else "#9DB4C8" for v in products["订单量"]]
    axes[0].barh(products["产品"], products["订单量"], color=colors, height=0.62)
    axes[0].invert_yaxis()
    for i, v in enumerate(products["订单量"]):
        axes[0].text(v + 5, i, str(v), va="center", fontsize=8.8)
    axes[0].set_xlabel("订单量（个）")
    axes[0].set_title("排序后的对比：一眼看出头部与尾部")
    axes[0].set_xlim(0, products["订单量"].max() * 1.12)
    axes[0].grid(axis="x")
    axes[0].grid(axis="y", visible=False)

    names = long_names["产品"].tolist()
    axes[1].barh(names, long_names["订单量"], color=COLORS[1], height=0.62)
    for i, v in enumerate(long_names["订单量"]):
        axes[1].text(v + 3, i, str(v), va="center", fontsize=8.5)
    axes[1].set_xlabel("订单量（个）")
    axes[1].set_title("类别名很长时：横向条形 + 排序，标签不旋转不重叠")
    axes[1].set_xlim(0, long_names["订单量"].max() * 1.12)
    axes[1].grid(axis="x")
    axes[1].grid(axis="y", visible=False)
    save_fig(fig, "ch02_对比分析")

    radar_labels = factors["因素"].tolist()
    radar_values = factors["得分"].tolist()
    angles = np.linspace(0, 2 * np.pi, len(radar_labels), endpoint=False).tolist()
    values = radar_values + radar_values[:1]
    angles += angles[:1]
    fig = plt.figure(figsize=(5.6, 5.0))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, values, color=COLORS[0], lw=1.8)
    ax.fill(angles, values, color=COLORS[0], alpha=0.22)
    ax.set_xticks(angles[:-1], radar_labels)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], fontsize=7.5)
    ax.set_title("顾客画像：六因素雷达图（I 外向性得分最高）", pad=20)
    save_fig(fig, "ch02_顾客画像雷达图")


if __name__ == "__main__":
    main()
