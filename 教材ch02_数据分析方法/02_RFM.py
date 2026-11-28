"""第 2 章 基础分析范式 2：RFM 用户价值模型。

教材在 Power BI 中先建三个度量：
    R = 分析时点 - max(销售日期)
    F = distinctcount(流水号)
    M = sum(销售金额)
再以均值为界把 R/F/M 各分成高/低，组合成 8 类用户，并用累计消费额
找到贡献 80% 的核心客群。脚本完全复现同一口径（对账结果一致）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from src.config import COLORS, save_fig, save_table
from src.io_utils import read_excel

SNAPSHOT = pd.Timestamp("2019-08-03")

CATEGORY_MAP = {
    "高高高": "重要价值用户", "高低高": "重要发展用户",
    "低高高": "重要保持用户", "低低高": "重要挽留用户",
    "高高低": "一般价值用户", "高低低": "一般发展用户",
    "低高低": "一般保持用户", "低低低": "一般挽留用户",
}


def main() -> None:
    df = read_excel("ch02/rfm.xlsx", sheet_name="原始数据")
    df["销售日期"] = pd.to_datetime(df["销售日期"])

    user = df.groupby("用户编号").agg(
        最近一次消费日期=("销售日期", "max"),
        消费频次=("流水号", "nunique"),
        消费金额=("销售金额", "sum"),
    )
    user["消费时间间隔"] = (SNAPSHOT - user["最近一次消费日期"]).dt.days

    r_mean = user["消费时间间隔"].mean()
    f_mean = user["消费频次"].mean()
    m_mean = user["消费金额"].mean()
    print(f"分析时点 {SNAPSHOT:%Y-%m-%d}，客户数 {len(user):,}")
    print(f"R 均值 {r_mean:.4f} 天，F 均值 {f_mean:.4f} 次，M 均值 {m_mean:.4f} 元")

    user["R程度"] = (user["消费时间间隔"] <= r_mean).map({True: "高", False: "低"})
    user["F程度"] = (user["消费频次"] >= f_mean).map({True: "高", False: "低"})
    user["M程度"] = (user["消费金额"] >= m_mean).map({True: "高", False: "低"})
    user["用户类别"] = (user["R程度"] + user["F程度"] + user["M程度"]).map(CATEGORY_MAP)
    save_table(user.reset_index(), "ch02_RFM_用户明细")

    order = list(CATEGORY_MAP.values())
    summary = (
        user.groupby("用户类别")
        .agg(用户数=("消费金额", "size"), 消费金额=("消费金额", "sum"))
        .reindex(order)
        .assign(用户占比=lambda x: x["用户数"] / x["用户数"].sum(),
                金额占比=lambda x: x["消费金额"] / x["消费金额"].sum())
    )
    summary["累计金额占比"] = summary["金额占比"].cumsum()
    print("\n八类用户（按教材顺序）：")
    print(summary.to_string(float_format=lambda v: f"{v:,.4f}"))
    save_table(summary.reset_index(), "ch02_RFM_用户分类汇总")

    top4 = summary.head(4)["金额占比"].sum()
    print(f"\n前 4 类（重要价值/发展/保持/挽留）贡献 {top4:.2%} 的消费额，"
          f"其中重要价值用户 {summary.iloc[0]['金额占比']:.2%}。")

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), gridspec_kw={"width_ratios": [1.15, 1]})
    y = range(len(summary))
    axes[0].barh(y, summary["用户数"], color=[COLORS[i % len(COLORS)] for i in range(len(summary))])
    axes[0].set_yticks(list(y), summary.index)
    axes[0].invert_yaxis()
    for i, (n, share) in enumerate(zip(summary["用户数"], summary["用户占比"])):
        axes[0].text(n + 25, i, f"{n:,} 人 / {share:.1%}", va="center", fontsize=8.5)
    axes[0].set_xlabel("用户数")
    axes[0].set_title("八类用户的规模")
    axes[0].set_xlim(0, summary["用户数"].max() * 1.32)
    axes[0].grid(axis="x")
    axes[0].grid(axis="y", visible=False)

    axes[1].bar(y, summary["金额占比"], color=[COLORS[i % len(COLORS)] for i in range(len(summary))])
    axes[1].plot(y, summary["累计金额占比"], color=COLORS[3], marker="o", ms=4, label="累计占比")
    axes[1].axhline(0.8, color="#7A828C", ls="--", lw=1)
    axes[1].text(len(summary) - 0.4, 0.815, "80% 参考线", ha="right", fontsize=8.5, color="#5B6470")
    axes[1].set_xticks(list(y), [c.replace("用户", "") for c in summary.index], rotation=40, ha="right")
    axes[1].yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    axes[1].set_title("消费额贡献与累计曲线")
    axes[1].legend(loc="center right")
    save_fig(fig, "ch02_RFM_用户分类")

    # R-F 分布：看“最近买”和“买得勤”是否一致
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    color_map = {c: COLORS[i % len(COLORS)] for i, c in enumerate(order)}
    for cat in order[:4]:
        part = user[user["用户类别"] == cat]
        ax.scatter(part["消费时间间隔"], part["消费频次"], s=8, alpha=0.55,
                   color=color_map[cat], label=cat)
    ax.axvline(r_mean, color="#7A828C", ls="--", lw=1)
    ax.axhline(f_mean, color="#7A828C", ls="--", lw=1)
    ax.set_xlabel("R：最近一次消费距今天数（越小越近）")
    ax.set_ylabel("F：消费频次")
    ax.set_title("R-F 分布：仅看“重要”四类，点越靠左上价值越高")
    ax.legend(markerscale=2.2, ncol=2)
    save_fig(fig, "ch02_RFM_RF分布")


if __name__ == "__main__":
    main()
