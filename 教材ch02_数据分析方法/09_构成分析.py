"""第 2 章 引申方法 3：构成分析。

构成（结构）分析回答“整体的各部分占多少”，教材给了三块素材：
  1. 4 个产品的销售量 —— 看单期占比，同时保留绝对量；
  2. 近 5 年 3 个产品的销量表 A —— 100% 堆叠柱看结构变化；
  3. 另一组同结构表 B —— 与表 A 对照，验证结构变化方向是否一致。
要点：占比结论必须与绝对量一起读；结构变化用 100% 堆叠或占比折线，
类别多的时候不要用饼图。Power BI 里的“100% 堆积柱形图”等价于按列归一化后画堆叠柱。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from src.config import COLORS, save_fig, save_table
from src.io_utils import read_excel


def to_share(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    total = df[cols].sum(axis=1)
    share = df[cols].div(total, axis=0) * 100
    share.insert(0, "年份", df["年份"].astype(int).astype(str))
    return share.reset_index(drop=True)


def main() -> None:
    raw = read_excel("ch02/composition.xlsx", sheet_name=0, header=None)

    single = raw.iloc[4:8, 1:3].copy()
    single.columns = ["产品", "销售量"]
    single["销售量"] = pd.to_numeric(single["销售量"])
    single["占比"] = single["销售量"] / single["销售量"].sum() * 100
    total = int(single["销售量"].sum())
    print(f"单期总销量 {total}：")
    print(single.assign(占比=single["占比"].round(2)).to_string(index=False))
    print(f"最大占比产品：{single.loc[single['占比'].idxmax(), '产品']}"
          f"（{single['占比'].max():.1f}%），最小：{single.loc[single['占比'].idxmin(), '产品']}"
          f"（{single['占比'].min():.1f}%），两者相差 {single['占比'].max() - single['占比'].min():.1f} 个百分点")
    save_table(single.round(2), "ch02_产品销量占比")

    cols = ["产品 1", "产品 2", "产品 3"]
    year_a = raw.iloc[17:22, 1:5].copy()
    year_a.columns = ["年份"] + cols
    year_a[["年份"] + cols] = year_a[["年份"] + cols].apply(pd.to_numeric)
    year_b = raw.iloc[29:34, 1:5].copy()
    year_b.columns = ["年份"] + cols
    year_b[["年份"] + cols] = year_b[["年份"] + cols].apply(pd.to_numeric)

    share_a, share_b = to_share(year_a, cols), to_share(year_b, cols)
    save_table(share_a.round(2), "ch02_年度产品结构A")
    save_table(share_b.round(2), "ch02_年度产品结构B")

    print("\n表 A 结构（%）：")
    print(share_a.round(2).to_string(index=False))
    print("\n表 B 结构（%）：")
    print(share_b.round(2).to_string(index=False))

    change = pd.DataFrame({
        "产品": cols,
        "表A_2020占比": share_a.loc[0, cols].to_numpy(),
        "表A_2024占比": share_a.loc[4, cols].to_numpy(),
        "表B_2020占比": share_b.loc[0, cols].to_numpy(),
        "表B_2024占比": share_b.loc[4, cols].to_numpy(),
    })
    change["表A变化_pp"] = change["表A_2024占比"] - change["表A_2020占比"]
    change["表B变化_pp"] = change["表B_2024占比"] - change["表B_2020占比"]
    save_table(change.round(2), "ch02_结构变化对比", index=False)
    print("\n2020→2024 结构变化（百分点）：")
    print(change.round(2).to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), gridspec_kw={"width_ratios": [1, 1.25]})
    single_sorted = single.sort_values("销售量", ascending=True)
    bars = axes[0].barh(single_sorted["产品"], single_sorted["销售量"],
                        color=COLORS[:4][::-1], height=0.6)
    for bar, v, p in zip(bars, single_sorted["销售量"], single_sorted["占比"]):
        axes[0].text(v + 8, bar.get_y() + bar.get_height() / 2, f"{v}（{p:.1f}%）",
                     va="center", fontsize=9)
    axes[0].set_xlim(0, single["销售量"].max() * 1.32)
    axes[0].set_xlabel("销售量（件）")
    axes[0].set_title(f"单期构成：总量 {total} 件，产品 4 占 {single['占比'].max():.1f}%")
    axes[0].grid(axis="x")
    axes[0].grid(axis="y", visible=False)

    years = share_a["年份"].tolist()
    bottom = [0.0] * len(years)
    for i, c in enumerate(cols):
        vals = share_a[c].tolist()
        axes[1].bar(years, vals, bottom=bottom, color=COLORS[i], width=0.62, label=c)
        for x, y0, v in zip(years, bottom, vals):
            if v >= 12:
                axes[1].text(x, y0 + v / 2, f"{v:.1f}%", ha="center", va="center",
                             fontsize=8, color="white")
        bottom = [b + v for b, v in zip(bottom, vals)]
    axes[1].set_ylim(0, 100)
    axes[1].set_ylabel("结构占比（%）")
    top_change = change.loc[change["表A变化_pp"].abs().idxmax()]
    axes[1].set_title(
        f"5 年结构变化：{top_change['产品']} 份额由 {top_change['表A_2020占比']:.1f}% "
        f"变为 {top_change['表A_2024占比']:.1f}%" if top_change["表A变化_pp"] < 0
        else f"5 年结构变化：{top_change['产品']} 份额由 {top_change['表A_2020占比']:.1f}% "
             f"升至 {top_change['表A_2024占比']:.1f}%"
    )
    axes[1].legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1), frameon=False)
    axes[1].grid(axis="y")
    axes[1].grid(axis="x", visible=False)
    save_fig(fig, "ch02_构成分析")

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.5), sharey=True)
    for ax, share, name, chg in [
        (axes[0], share_a, "表 A", change["表A变化_pp"]),
        (axes[1], share_b, "表 B", change["表B变化_pp"]),
    ]:
        for i, c in enumerate(cols):
            ax.plot(years, share[c], marker="o", ms=4.5, lw=1.8, color=COLORS[i], label=c)
        i = int(chg.abs().idxmax())
        direction = "下滑" if chg[i] < 0 else "上升"
        ax.set_title(f"{name}：{cols[i]} 份额{direction} {abs(chg[i]):.1f} 个百分点")
        ax.set_ylim(0, 60)
        ax.set_ylabel("结构占比（%）")
        ax.set_xlabel("年份")
        ax.legend(frameon=False, fontsize=8.5)
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
    save_fig(fig, "ch02_结构占比变化")


if __name__ == "__main__":
    main()
