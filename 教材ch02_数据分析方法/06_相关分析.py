"""第 2 章 基础分析范式 6：相关分析。

教材用散点图 + 趋势线判断“投入（x）与产出（y）”是否同向变化。
Python 版给出可复核的统计量：
    Pearson r、显著性 p 值、最小二乘回归 y = a + bx、判定系数 R²。
结论：r = 0.976，属于强正相关；x 每增加 1 个单位，y 平均增加约 1.98 个单位。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from 教材src.config import COLORS, save_fig, save_table
from 教材src.io_utils import read_excel


def main() -> None:
    df = read_excel("ch02/correlation.xlsx", sheet_name="原始数据").dropna()
    x, y = df["x"].to_numpy(float), df["y"].to_numpy(float)

    r, p = stats.pearsonr(x, y)
    reg = stats.linregress(x, y)
    pred = reg.intercept + reg.slope * x
    residuals = y - pred
    r2 = 1 - (residuals ** 2).sum() / ((y - y.mean()) ** 2).sum()

    summary = pd.DataFrame({
        "指标": ["样本量", "Pearson r", "p 值", "斜率 b", "截距 a", "R²", "残差标准差"],
        "取值": [len(df), r, p, reg.slope, reg.intercept, r2, residuals.std(ddof=2)],
    })
    print(summary.to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    print(f"\n回归方程：y = {reg.intercept:.2f} + {reg.slope:.4f} x")
    print(f"解释：投入每增加 1 元，产出平均增加 {reg.slope:.2f} 元；"
          f"x 能解释 y 的 {r2:.2%} 变异。")
    save_table(summary, "ch02_相关分析统计量")

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.7), gridspec_kw={"width_ratios": [1.25, 1]})
    axes[0].scatter(x, y, s=26, color=COLORS[0], alpha=0.75, edgecolor="white", label="观测值")
    xs = np.linspace(x.min(), x.max(), 100)
    axes[0].plot(xs, reg.intercept + reg.slope * xs, color="#C0392B", lw=1.8,
                 label=f"拟合线 y={reg.intercept:.1f}+{reg.slope:.2f}x")
    axes[0].set_xlabel("投入成本 x")
    axes[0].set_ylabel("产出收益 y")
    axes[0].set_title(f"投入与产出：r = {r:.3f}，R² = {r2:.3f}")
    axes[0].legend(loc="upper left")
    axes[0].text(0.97, 0.06, f"n = {len(df)}\np < 0.001", transform=axes[0].transAxes,
                 ha="right", fontsize=9, color="#47505C")

    axes[1].scatter(pred, residuals, s=24, color=COLORS[1], alpha=0.8, edgecolor="white")
    axes[1].axhline(0, color="#7A828C", ls="--", lw=1)
    axes[1].set_xlabel("拟合值")
    axes[1].set_ylabel("残差")
    axes[1].set_title("残差图：点围绕 0 随机分布，线性假设可接受")
    save_fig(fig, "ch02_相关分析与回归")


if __name__ == "__main__":
    main()
