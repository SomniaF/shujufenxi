"""第 2 章 基础分析范式 5：漏斗图。

教材用两种漏斗做练习：
  1. 销售漏斗：潜在 → 接触 → 意向 → 明确 → 谈判 → 成交；
  2. 用户行为 / AARRR 漏斗：浏览 → 收藏 → 加购 → 购买，获取 → 激活 → 留存 → 收益 → 推荐。
Python 版用居中的水平条形画出漏斗，并同时给出“环节转化率”和“总体转化率”。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from 教材src.config import COLORS, save_fig, save_table
from 教材src.io_utils import read_excel


def draw_funnel(ax, stages, users, title, colors):
    users = np.asarray(users, dtype=float)
    y = np.arange(len(users))[::-1]
    width = users / users.max()
    ax.barh(y, width, left=(1 - width) / 2, height=0.68, color=colors)
    overall = users / users[0]
    for i, (stage, u, w) in enumerate(zip(stages, users, width)):
        ax.text(0.5, y[i], f"{stage}\n{u:,.0f}", ha="center", va="center",
                color="white", fontsize=9, fontweight="bold")
        step = u / users[i - 1] if i else 1
        ax.text(1.03, y[i], f"环节 {step:.1%}\n总体 {overall[i]:.1%}",
                ha="left", va="center", fontsize=8.2, color="#47505C")
    ax.set_xlim(0, 1.36)
    ax.set_ylim(-0.7, len(users) - 0.3)
    ax.axis("off")
    ax.set_title(title, fontsize=11.5, pad=6)


def main() -> None:
    demo = read_excel("ch02/funnel.xlsx", sheet_name="演示", header=2).dropna(subset=["阶段"])
    demo["转化率"] = demo["用户数"] / demo["用户数"].shift(1)
    demo.loc[demo.index[0], "转化率"] = 1.0
    demo["总体转化率"] = demo["用户数"] / demo["用户数"].iloc[0]
    print("销售漏斗：")
    print(demo.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"总体转化率 {demo['总体转化率'].iloc[-1]:.2%}，"
          f"环节转化率最低的是“{demo.loc[demo['转化率'].idxmin(), '阶段']}”"
          f"（{demo['转化率'].min():.1%}）")
    save_table(demo, "ch02_销售漏斗")

    raw = read_excel("ch02/funnel.xlsx", sheet_name="练习", header=None)
    behavior = raw.iloc[2:6, 1:3].copy()
    behavior.columns = ["用户行为", "用户数"]
    behavior["用户数"] = pd.to_numeric(behavior["用户数"])
    aarrr = raw.iloc[10:15, 1:3].copy()
    aarrr.columns = ["运营阶段", "用户数"]
    aarrr["用户数"] = pd.to_numeric(aarrr["用户数"])
    save_table(behavior, "ch02_用户行为漏斗")
    save_table(aarrr, "ch02_AARRR漏斗")

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.9), gridspec_kw={"width_ratios": [1.18, 1]})
    draw_funnel(axes[0], demo["阶段"].tolist(), demo["用户数"].tolist(),
                "销售漏斗：100 个潜在客户最终成交 50 个", [COLORS[0]] * len(demo))
    draw_funnel(axes[1], aarrr["运营阶段"].tolist(), aarrr["用户数"].tolist(),
                "AARRR 运营漏斗：获取 100 → 推荐 30", [COLORS[2]] * len(aarrr))
    save_fig(fig, "ch02_漏斗图")


if __name__ == "__main__":
    main()
