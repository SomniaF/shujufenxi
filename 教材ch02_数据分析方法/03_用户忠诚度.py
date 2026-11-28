"""第 2 章 基础分析范式 3：用户忠诚度模型（F-M 打分）。

教材分两步处理 990 名会员：
  1. 先按最近 13 周的行为圈出两类运营对象：
       潜在用户 = 13 周前消费 0 次，且 13 周内只消费 1 次；
       易流失用户 = 13 周内消费 0 次（此前消费过）；
  2. 对剩余 705 名活跃会员，用 F（消费次数）和 M（消费额）的
     25%/75% 分位数打 1~3 分，总分 2~3 低价值、4 普通、5 进阶、6 忠诚。
这样阈值（F=4/7，M=3198/5724）与教材参考表完全一致。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from src.config import COLORS, save_fig, save_table
from src.io_utils import read_excel

SNAPSHOT = pd.Timestamp("2021-01-01")
WEEKS = 13


def score_3(v: float, q1: float, q3: float) -> int:
    if v < q1:
        return 1
    return 2 if v <= q3 else 3


def tier(total: int) -> str:
    return {2: "低价值用户", 3: "低价值用户", 4: "普通用户",
            5: "进阶用户", 6: "忠诚用户"}[total]


def main() -> None:
    df = read_excel("ch02/loyalty.xlsx", sheet_name="销售流水表")
    df["消费日期"] = pd.to_datetime(df["消费日期"])
    cutoff = SNAPSHOT - pd.Timedelta(weeks=WEEKS)
    print(f"分析时点 {SNAPSHOT:%Y-%m-%d}，最近 {WEEKS} 周起点 {cutoff:%Y-%m-%d}")

    user = df.groupby("会员编号").agg(
        消费次数=("订单编号", "nunique"),
        消费额=("消费金额", "sum"),
        首次消费=("消费日期", "min"),
        最近消费=("消费日期", "max"),
    )
    before = df[df["消费日期"] < cutoff].groupby("会员编号")["订单编号"].nunique()
    after = df[df["消费日期"] >= cutoff].groupby("会员编号")["订单编号"].nunique()
    user["13周前消费次数"] = before.reindex(user.index).fillna(0).astype(int)
    user["13周内消费次数"] = after.reindex(user.index).fillna(0).astype(int)

    potential = (user["13周前消费次数"] == 0) & (user["13周内消费次数"] == 1)
    churn = (user["13周前消费次数"] > 0) & (user["13周内消费次数"] == 0)
    user["运营标签"] = ""
    user.loc[potential, "运营标签"] = "潜在用户"
    user.loc[churn, "运营标签"] = "易流失用户"
    target = user[user["运营标签"] != ""].copy()
    active = user[user["运营标签"] == ""].copy()
    print(f"会员总数 {len(user):,}：潜在 {potential.sum()} 人、易流失 {churn.sum()} 人，"
          f"待评分活跃会员 {len(active):,} 人")

    q1_f, q3_f = active["消费次数"].quantile([0.25, 0.75])
    q1_m, q3_m = active["消费额"].quantile([0.25, 0.75])
    print(f"活跃会员 F 的 Q1/Q3 = {q1_f:.0f}/{q3_f:.0f}；"
          f"M 的 Q1/Q3 = {q1_m:,.0f}/{q3_m:,.0f}")

    active["F评分"] = active["消费次数"].map(lambda v: score_3(v, q1_f, q3_f))
    active["M评分"] = active["消费额"].map(lambda v: score_3(v, q1_m, q3_m))
    active["总分"] = active["F评分"] + active["M评分"]
    active["用户类别"] = active["总分"].map(tier)
    user = user.join(active[["F评分", "M评分", "总分", "用户类别"]])
    save_table(user.reset_index(), "ch02_用户忠诚度_会员评分")
    save_table(target.reset_index(), "ch02_用户忠诚度_潜在与易流失")

    summary = active.groupby("用户类别").agg(会员数=("消费额", "size"), 消费额=("消费额", "sum"))
    summary = summary.reindex(["低价值用户", "普通用户", "进阶用户", "忠诚用户"])
    summary["人数占比"] = summary["会员数"] / summary["会员数"].sum()
    print("\n活跃会员分层：")
    print(summary.to_string(float_format=lambda v: f"{v:,.3f}"))
    save_table(summary.reset_index(), "ch02_用户忠诚度_分层汇总")

    print("\n待运营人群画像：")
    profile = target.groupby("运营标签").agg(
        人数=("消费额", "size"), 人均消费额=("消费额", "mean"), 人均消费次数=("消费次数", "mean")
    )
    print(profile.to_string(float_format=lambda v: f"{v:,.2f}"))
    save_table(profile.reset_index(), "ch02_用户忠诚度_待运营人群画像")

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), gridspec_kw={"width_ratios": [1.35, 1]})
    colors = {"低价值用户": COLORS[3], "普通用户": COLORS[1], "进阶用户": COLORS[2], "忠诚用户": COLORS[0]}
    for cat, color in colors.items():
        part = active[active["用户类别"] == cat]
        axes[0].scatter(part["消费额"], part["消费次数"], s=12, alpha=0.5, color=color, label=cat)
    axes[0].axhline(q3_f, color="#7A828C", ls="--", lw=0.9)
    axes[0].axvline(q3_m, color="#7A828C", ls="--", lw=0.9)
    axes[0].set_xlabel("消费额（元）")
    axes[0].set_ylabel("消费次数")
    axes[0].set_title("活跃会员 F-M 分层：右上角为忠诚用户")
    axes[0].set_xlim(0, active["消费额"].quantile(0.99))
    axes[0].set_ylim(0, active["消费次数"].quantile(0.99))
    axes[0].legend(markerscale=2)

    bars = axes[1].bar(profile.index, profile["人数"], color=[COLORS[1], COLORS[3]], width=0.5)
    for b, (n, money, freq) in zip(bars, profile[["人数", "人均消费额", "人均消费次数"]].to_numpy()):
        axes[1].text(b.get_x() + b.get_width() / 2, n + 4,
                     f"{n} 人\n人均 {money:,.0f} 元\n{freq:.1f} 次", ha="center", fontsize=9)
    axes[1].set_ylabel("人数")
    axes[1].set_ylim(0, profile["人数"].max() * 1.32)
    axes[1].set_title("待运营人群：易流失是潜在用户的 27 倍")
    save_fig(fig, "ch02_用户忠诚度")


if __name__ == "__main__":
    main()
