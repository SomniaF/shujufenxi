"""第 2 章 引申方法 5：关系分析。

教材按“变量类型配对”给了三组素材：
  1. 分类 × 分类：5 个营销活动的下单 / 未下单人数；3 档忠诚度 × 满意 / 不满意；
  2. 分类 × 连续：同一批 100 位用户在 3 个活动中的销售金额；
  3. 连续 × 连续：58 笔业务的投入成本与产出收益。
方法对应：列联表 + 卡方检验、分组比较 + 方差分析、散点图 + 相关系数 + 回归。
关系分析只说明“共同变化”，是否因果要另找证据。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from 教材src.config import ACCENT, COLORS, GREY, save_fig, save_table
from 教材src.io_utils import read_excel


def cramers_v(table: np.ndarray) -> float:
    chi2 = stats.chi2_contingency(table)[0]
    n = table.sum()
    return float(np.sqrt(chi2 / (n * (min(table.shape) - 1))))


def stacked_share(ax, table: pd.DataFrame, colors: list[str], title: str) -> None:
    share = table.div(table.sum(axis=1), axis=0) * 100
    bottom = np.zeros(len(share))
    for i, col in enumerate(share.columns):
        ax.bar(share.index, share[col], bottom=bottom, color=colors[i], width=0.6, label=col)
        for x, y0, v in zip(range(len(share)), bottom, share[col]):
            ax.text(x, y0 + v / 2, f"{v:.1f}%", ha="center", va="center",
                    fontsize=8.5, color="white")
        bottom += share[col].to_numpy()
    ax.set_ylim(0, 100)
    ax.set_ylabel("构成占比（%）")
    ax.set_title(title)
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.08))
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)


def main() -> None:
    raw = read_excel("ch02/relationship.xlsx", sheet_name=0, header=None)

    camp = raw.iloc[3:8, 1:4].copy()
    camp.columns = ["营销活动", "下单用户", "未下单用户"]
    camp[["下单用户", "未下单用户"]] = camp[["下单用户", "未下单用户"]].apply(pd.to_numeric)
    camp["参与人数"] = camp["下单用户"] + camp["未下单用户"]
    camp["下单率"] = camp["下单用户"] / camp["参与人数"] * 100
    print("营销活动下单情况：")
    print(camp.assign(下单率=camp["下单率"].round(2)).to_string(index=False))
    save_table(camp.round(2), "ch02_营销活动下单")

    chi2_c, p_c, dof_c, _ = stats.chi2_contingency(camp[["下单用户", "未下单用户"]].to_numpy())
    v_c = cramers_v(camp[["下单用户", "未下单用户"]].to_numpy())
    best = camp.loc[camp["下单率"].idxmax()]
    worst = camp.loc[camp["下单率"].idxmin()]
    print(f"卡方检验：χ² = {chi2_c:.2f}，df = {dof_c}，p = {p_c:.3e}，Cramér's V = {v_c:.3f}")
    print(f"下单率最高 {best['营销活动']}（{best['下单率']:.1f}%），"
          f"最低 {worst['营销活动']}（{worst['下单率']:.1f}%），"
          f"相差 {best['下单率'] - worst['下单率']:.1f} 个百分点")

    loyalty = raw.iloc[15:18, 1:4].copy()
    loyalty.columns = ["忠诚度", "满意", "不满意"]
    loyalty[["满意", "不满意"]] = loyalty[["满意", "不满意"]].apply(pd.to_numeric)
    loyalty["合计"] = loyalty["满意"] + loyalty["不满意"]
    loyalty["满意率"] = loyalty["满意"] / loyalty["合计"] * 100
    print("\n忠诚度与满意度：")
    print(loyalty.assign(满意率=loyalty["满意率"].round(2)).to_string(index=False))
    save_table(loyalty.round(2), "ch02_忠诚度满意度")

    chi2_l, p_l, dof_l, _ = stats.chi2_contingency(loyalty[["满意", "不满意"]].to_numpy())
    v_l = cramers_v(loyalty[["满意", "不满意"]].to_numpy())
    print(f"卡方检验：χ² = {chi2_l:.2f}，df = {dof_l}，p = {p_l:.3e}，Cramér's V = {v_l:.3f}")

    users = raw.iloc[1:101, 12:15].copy()
    users.columns = ["活动1", "活动2", "活动3"]
    users = users.apply(pd.to_numeric)
    groups = [users[c].to_numpy() for c in users.columns]
    f_stat, p_a = stats.f_oneway(*groups)
    means = users.mean()
    print("\n三次活动的销售金额：")
    print(users.describe().round(1).to_string())
    print(f"单因素方差分析：F = {f_stat:.2f}，p = {p_a:.3e}；"
          f"均值最高 {means.idxmax()}（{means.max():.1f} 元）")
    save_table(users.describe().round(2), "ch02_活动销售金额统计", index=True)

    inv = raw.iloc[1:59, 24:26].copy()
    inv.columns = ["产出收益", "投入成本"]
    inv = inv.apply(pd.to_numeric)
    lr = stats.linregress(inv["投入成本"], inv["产出收益"])
    r = inv["投入成本"].corr(inv["产出收益"])
    print(f"\n投入与收益：n = {len(inv)}，r = {r:.6f}，R² = {r ** 2:.4f}，"
          f"p = {lr.pvalue:.3e}")
    print(f"回归方程：收益 = {lr.intercept:.2f} + {lr.slope:.4f} × 成本"
          f"（成本每增加 1 元，收益平均增加 {lr.slope:.2f} 元）")
    save_table(inv.round(2), "ch02_投入产出数据")

    checks = pd.DataFrame([
        {"关系": "营销活动 → 是否下单", "变量类型": "分类 × 分类", "方法": "卡方检验",
         "统计量": f"χ²={chi2_c:.2f}", "p值": p_c, "强度": f"Cramér's V={v_c:.3f}"},
        {"关系": "忠诚度 → 是否满意", "变量类型": "分类 × 分类", "方法": "卡方检验",
         "统计量": f"χ²={chi2_l:.2f}", "p值": p_l, "强度": f"Cramér's V={v_l:.3f}"},
        {"关系": "活动类型 → 销售金额", "变量类型": "分类 × 连续", "方法": "单因素方差分析",
         "统计量": f"F={f_stat:.2f}", "p值": p_a, "强度": "组均值差异"},
        {"关系": "投入成本 → 产出收益", "变量类型": "连续 × 连续", "方法": "Pearson 相关与回归",
         "统计量": f"r={r:.4f}", "p值": lr.pvalue, "强度": f"R²={r ** 2:.4f}"},
    ])
    save_table(checks, "ch02_关系分析检验结果", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.9), gridspec_kw={"width_ratios": [1.35, 1]})
    stacked_share(axes[0], camp.set_index("营销活动")[["下单用户", "未下单用户"]],
                  [COLORS[0], "#C9CDD3"],
                  f"营销活动与下单：χ²={chi2_c:.1f}，p<0.001")
    stacked_share(axes[1], loyalty.set_index("忠诚度")[["满意", "不满意"]],
                  [COLORS[2], "#C9CDD3"],
                  f"忠诚度与满意度：χ²={chi2_l:.1f}，p<0.001")
    save_fig(fig, "ch02_关系分析_列联表")

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9))
    bp = axes[0].boxplot(groups, orientation="vertical", widths=0.5, patch_artist=True,
                         tick_labels=list(users.columns),
                         boxprops={"facecolor": "#D6E2EE", "edgecolor": COLORS[0]},
                         medianprops={"color": ACCENT, "lw": 1.8},
                         whiskerprops={"color": COLORS[0]},
                         capprops={"color": COLORS[0]},
                         flierprops={"marker": "o", "markersize": 4,
                                     "markerfacecolor": ACCENT, "markeredgecolor": ACCENT,
                                     "alpha": 0.7})
    axes[0].plot(range(1, 4), means.to_numpy(), "D", color=COLORS[1], ms=7, label="组均值")
    for i, m in enumerate(means, start=1):
        axes[0].annotate(f"{m:.0f}", (i, m), textcoords="offset points", xytext=(0, 8),
                         ha="center", fontsize=8.5, color=COLORS[1])
    axes[0].set_xlabel("营销活动")
    axes[0].set_ylabel("销售金额（元）")
    axes[0].set_title(f"分类 × 连续：三次活动金额分布，F={f_stat:.1f}，p<0.001")
    axes[0].legend(loc="upper right")
    axes[0].grid(axis="y")
    axes[0].grid(axis="x", visible=False)

    axes[1].scatter(inv["投入成本"], inv["产出收益"], s=26, color=COLORS[0],
                    alpha=0.75, edgecolor="white", linewidth=0.6)
    xs = np.linspace(inv["投入成本"].min(), inv["投入成本"].max(), 100)
    axes[1].plot(xs, lr.intercept + lr.slope * xs, color=ACCENT, lw=1.8,
                 label=f"y = {lr.intercept:.1f} + {lr.slope:.2f}x，r = {r:.3f}")
    axes[1].set_xlabel("投入成本（元）")
    axes[1].set_ylabel("产出收益（元）")
    axes[1].set_title(f"连续 × 连续：强正相关，R² = {r ** 2:.3f}")
    axes[1].legend(loc="upper left")
    axes[1].grid(axis="y")
    axes[1].grid(axis="x")
    save_fig(fig, "ch02_关系分析_散点与分组")


if __name__ == "__main__":
    main()
