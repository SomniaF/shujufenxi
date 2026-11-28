"""第 2 章 引申方法 4：分布分析。

教材给了三组分布素材：
  1. 门店一天的客流量（半小时粒度，48 个时点）—— 看时间上的双峰；
  2. 338 位顾客的年龄 —— 看集中趋势、离散程度与异常值；
  3. 338 位顾客的客单价 —— 与年龄对照，看右偏形态。
分析要点：分布先看形状（单峰/双峰、对称/偏斜），再看均值和中位数的差异，
用四分位距 IQR 判定异常值，而不是“凭感觉”划一条线。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import ACCENT, COLORS, GREY, save_fig, save_table
from src.io_utils import read_excel


def describe(s: pd.Series) -> pd.Series:
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return pd.Series({
        "样本量": len(s),
        "均值": s.mean(),
        "标准差": s.std(),
        "最小值": s.min(),
        "Q1": q1,
        "中位数": s.median(),
        "Q3": q3,
        "最大值": s.max(),
        "IQR": iqr,
        "下界": lower,
        "上界": upper,
        "异常值个数": int(((s < lower) | (s > upper)).sum()),
        "偏度": s.skew(),
    })


def main() -> None:
    raw = read_excel("ch02/distribution.xlsx", sheet_name=0, header=None)

    traffic = raw.iloc[2:50, 1:3].copy()
    traffic.columns = ["时点", "客流量"]
    traffic["时点"] = pd.to_datetime(traffic["时点"])
    traffic["客流量"] = pd.to_numeric(traffic["客流量"])
    traffic["时间"] = traffic["时点"].dt.strftime("%H:%M")
    traffic = traffic.reset_index(drop=True)
    peak = traffic.loc[traffic["客流量"].idxmax()]
    valley = traffic.loc[traffic["客流量"].idxmin()]
    print(f"门店客流量：{len(traffic)} 个半小时时点，全天合计 {traffic['客流量'].sum():,.0f} 人次")
    print(f"  高峰 {peak['时间']}（{peak['客流量']:.0f}），低谷 {valley['时间']}（{valley['客流量']:.0f}）")
    print(f"  均值 {traffic['客流量'].mean():.1f}，中位数 {traffic['客流量'].median():.1f}，"
          f"峰谷比 {peak['客流量'] / valley['客流量']:.2f}")
    save_table(traffic[["时间", "客流量"]].round(1), "ch02_客流量时段分布")

    age = pd.to_numeric(raw.iloc[2:340, 11], errors="coerce").dropna().astype(float)
    price = pd.to_numeric(raw.iloc[2:340, 20], errors="coerce").dropna().astype(float)

    pair = pd.DataFrame({
        "age": pd.to_numeric(raw.iloc[2:340, 11], errors="coerce"),
        "price_prev": pd.to_numeric(raw.iloc[2:340, 20], errors="coerce").shift(1),
    }).dropna()
    if (pair["age"] == pair["price_prev"]).mean() > 0.99:
        print("提示：源表“客单价”列错位存放了下一行的年龄值（price[i] = age[i+1]），"
              "属于源数据录入问题；两条分布因此同形，不能当作相互独立的证据。")
    stat_age, stat_price = describe(age), describe(price)
    print("\n年龄分布：")
    print(stat_age.round(2).to_string())
    print("\n客单价分布：")
    print(stat_price.round(2).to_string())
    save_table(stat_age.rename_axis("指标").to_frame("取值").round(3),
               "ch02_年龄分布统计", index=True)
    save_table(stat_price.rename_axis("指标").to_frame("取值").round(3),
               "ch02_客单价分布统计", index=True)

    age_out = age[(age < stat_age["下界"]) | (age > stat_age["上界"])]
    print(f"\n年龄异常值（IQR 上界 {stat_age['上界']:.2f}）：{sorted(age_out.tolist())}")
    print(f"均值比中位数高 {stat_age['均值'] - stat_age['中位数']:.2f} 岁，偏度 "
          f"{stat_age['偏度']:.3f}")
    print(f"客单价均值 {stat_price['均值']:.2f} 元，中位数 {stat_price['中位数']:.0f} 元，"
          f"偏度 {stat_price['偏度']:.3f}")

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.7), gridspec_kw={"width_ratios": [1.55, 1]})
    bins = np.arange(10, 100, 5)
    axes[0].hist(age, bins=bins, color=COLORS[0], edgecolor="white", alpha=0.9)
    axes[0].axvline(stat_age["均值"], color=ACCENT, lw=1.6, ls="--",
                    label=f"均值 {stat_age['均值']:.1f}")
    axes[0].axvline(stat_age["中位数"], color=COLORS[1], lw=1.6, ls="-.",
                    label=f"中位数 {stat_age['中位数']:.0f}")
    axes[0].set_xlabel("年龄（岁）")
    axes[0].set_ylabel("人数")
    axes[0].set_title(f"年龄分布：右偏（偏度 {stat_age['偏度']:.2f}），均值被高值拉高")
    axes[0].legend(loc="upper right")
    axes[0].set_xlim(10, 100)

    axes[1].boxplot([age], orientation="horizontal", widths=0.45, patch_artist=True,
                    tick_labels=["年龄"],
                    boxprops={"facecolor": "#D6E2EE", "edgecolor": COLORS[0]},
                    medianprops={"color": ACCENT, "lw": 1.8},
                    whiskerprops={"color": COLORS[0]},
                    capprops={"color": COLORS[0]},
                    flierprops={"marker": "o", "markersize": 4,
                                "markerfacecolor": ACCENT, "markeredgecolor": ACCENT,
                                "alpha": 0.7})
    axes[1].axvline(stat_age["上界"], color=GREY, lw=1.2, ls=":",
                    label=f"IQR 上界 {stat_age['上界']:.1f}")
    axes[1].axvline(stat_age["下界"], color=GREY, lw=1.2, ls=":")
    axes[1].set_title(f"箱线图：IQR = {stat_age['IQR']:.1f}，"
                      f"{int(stat_age['异常值个数'])} 人超出上界")
    axes[1].set_xlabel("年龄（岁）")
    axes[1].set_xlim(0, 105)
    axes[1].legend(loc="lower right")
    axes[1].grid(axis="x")
    axes[1].grid(axis="y", visible=False)
    save_fig(fig, "ch02_年龄分布")

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.7))
    axes[0].hist(price, bins=np.arange(0, 100, 5), color=COLORS[2],
                 edgecolor="white", alpha=0.9)
    axes[0].axvline(stat_price["均值"], color=ACCENT, lw=1.6, ls="--",
                    label=f"均值 {stat_price['均值']:.1f} 元")
    axes[0].axvline(stat_price["中位数"], color=COLORS[1], lw=1.6, ls="-.",
                    label=f"中位数 {stat_price['中位数']:.0f} 元")
    axes[0].set_xlabel("客单价（元）")
    axes[0].set_ylabel("人数")
    axes[0].set_title(f"客单价分布：偏度 {stat_price['偏度']:.2f}，"
                      f"{(price > 70).sum()} 人客单价超过 70 元")
    axes[0].legend(loc="upper right")

    axes[1].plot(range(len(traffic)), traffic["客流量"], color=COLORS[0], lw=1.7)
    axes[1].scatter([traffic["客流量"].idxmax() - traffic.index[0]],
                    [peak["客流量"]], color=ACCENT, zorder=3, s=38)
    axes[1].annotate(f"高峰 {peak['时间']}\n{peak['客流量']:.0f} 人次",
                     xy=(traffic["客流量"].idxmax(), peak["客流量"]),
                     xytext=(16, -6), textcoords="offset points",
                     fontsize=8.5, color=ACCENT, ha="left", va="top")
    axes[1].axhline(traffic["客流量"].mean(), color=GREY, lw=1, ls="--",
                    label=f"全天均值 {traffic['客流量'].mean():.0f}")
    tick_pos = list(range(0, len(traffic), 4))
    axes[1].set_xticks(tick_pos, [traffic["时间"].iloc[i] for i in tick_pos], rotation=45)
    axes[1].set_xlabel("时点")
    axes[1].set_ylabel("客流量（人次）")
    axes[1].set_title("门店客流量：48 个半小时点在均值附近随机波动")
    axes[1].legend(loc="lower right")
    axes[1].grid(axis="y")
    axes[1].grid(axis="x", visible=False)
    save_fig(fig, "ch02_分布分析")


if __name__ == "__main__":
    main()
