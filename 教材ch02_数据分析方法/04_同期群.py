"""第 2 章 基础分析范式 4：同期群分析（Cohort Analysis）。

教材按“注册日期”分组，计算每个同期群在第 N 日仍有登录的用户占比。
Python 版把“第几日”还原为日期差，再透视成留存矩阵：
    留存率(N) = 该群在第 N 日登录的去重用户数 / 该群注册用户数
首日固定为 100%（注册当天即计入），总计行按全体用户加权。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from 教材src.config import save_fig, save_table
from 教材src.io_utils import read_excel


def main() -> None:
    df = read_excel("ch02/cohort.xlsx", sheet_name="用户登录明细")
    df["注册日期"] = pd.to_datetime(df["注册日期"]).dt.normalize()
    df["登录日期"] = pd.to_datetime(df["登录时点"]).dt.normalize()
    df["日差"] = (df["登录日期"] - df["注册日期"]).dt.days
    df = df[df["日差"] >= 0]

    cohort_size = df.drop_duplicates("用户编号").groupby("注册日期")["用户编号"].nunique()
    active = df.groupby(["注册日期", "日差"])["用户编号"].nunique().unstack(fill_value=0)
    retention = active.div(cohort_size, axis=0)
    retention[0] = 1.0
    max_day = 30
    retention = retention.reindex(columns=range(max_day + 1))

    print(f"用户数 {df['用户编号'].nunique():,}，注册同期群 {len(cohort_size)} 个")
    print("各群规模：")
    print(cohort_size.to_string())
    print(f"\n次日留存率（全体加权）= {active[1].sum() / cohort_size.sum():.2%}")
    print(f"第 7 日留存率（全体加权）= {active[7].sum() / cohort_size.sum():.2%}")
    print(f"第 30 日留存率（全体加权）= {active[30].sum() / cohort_size.sum():.2%}")

    out = retention.copy()
    out.index = out.index.strftime("%Y-%m-%d")
    out.columns = ["首日"] + [f"第{d}日" for d in range(1, max_day + 1)]
    out["群规模"] = cohort_size.values
    total_row = (active.sum() / cohort_size.sum()).reindex(range(max_day + 1)).fillna(0)
    total_row.iloc[0] = 1.0
    out.loc["总计（加权）"] = list(total_row.values) + [cohort_size.sum()]
    save_table(out, "ch02_同期群留存矩阵", index=True)

    plot = retention.iloc[:, :22]
    fig, ax = plt.subplots(figsize=(12.4, 5.0))
    data = plot.to_numpy(dtype=float)
    im = ax.imshow(np.ma.masked_invalid(data), cmap="YlGnBu", aspect="auto", vmin=0, vmax=0.8)
    ax.set_xticks(range(plot.shape[1]), ["首日"] + [f"D{d}" for d in range(1, plot.shape[1])])
    ax.set_yticks(range(len(plot)), [d.strftime("%m-%d") for d in plot.index])
    ax.set_xlabel("注册后第 N 日")
    ax.set_ylabel("注册同期群")
    ax.set_title("同期群留存热力图：越靠右颜色越浅，说明用户逐日流失")
    ax.grid(False)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if not np.isnan(data[i, j]):
                ax.text(j, i, f"{data[i, j]:.0%}", ha="center", va="center", fontsize=6.4,
                        color="white" if data[i, j] > 0.45 else "#1F2A37")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.015, format=lambda v, _: f"{v:.0%}")
    save_fig(fig, "ch02_同期群留存热力图")

    # 注册量与登录量对照，解释留存分母
    daily_reg = df.drop_duplicates("用户编号").groupby("注册日期")["用户编号"].nunique()
    daily_login = df.groupby("登录日期")["用户编号"].nunique()
    comp = pd.DataFrame({"注册用户数": daily_reg, "登录用户数": daily_login}).fillna(0)
    save_table(comp.rename_axis(index="日期"), "ch02_注册与登录日活", index=True)

    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.bar(comp.index.strftime("%m-%d"), comp["注册用户数"], color="#9DB4C8", label="注册用户数", width=0.6)
    ax.plot(comp.index.strftime("%m-%d"), comp["登录用户数"], color="#C0392B", marker="o", ms=4, label="登录用户数")
    ax.set_xlabel("日期（2020 年）")
    ax.set_ylabel("用户数")
    ax.set_title("注册与登录：7 月上旬为拉新高峰，登录量随存量累积上升")
    ax.legend()
    save_fig(fig, "ch02_注册与登录")


if __name__ == "__main__":
    main()
