"""第 10 章 效应分解与预测 2：节日效应识别、剔除与短期预测。

教材素材是 2013 年 3 月 1—31 日的信用卡日消费额：
  3 月 8 日（妇女节）当天消费额明显高于前后日，需要判断这是“节日效应”，
  还是趋势 / 星期效应造成的，剔除后再做预测。
做法：
  1. 回归 amount = a + b·t + Σ 星期虚拟变量 + c·节日虚拟变量；
  2. c 就是剔除趋势与星期效应后的节日净效应，3 月 8 日的调整值 = 实际值 − c；
  3. 用调整前后 z 分数验证异常是否被消除；
  4. 用趋势 + 星期效应预测 4 月 1—7 日，并给出 95% 预测区间。
教材同时给了“调整后”参考序列（credit_card_adjusted.xlsx）。该文件单位为万元、
且保留了周末周期，与原始日粒度序列口径不同，因此只做定性核对，不逐日对数值。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from 教材src.config import ACCENT, COLORS, GREY, save_fig, save_table
from 教材src.io_utils import read_excel

WD_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def main() -> None:
    df = read_excel("ch10/credit_card_holiday.xlsx", sheet_name="pos")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["amount"] = df["amount"].astype(float)
    df["t"] = np.arange(len(df))
    df["wd"] = df["date"].dt.day_of_week
    df["节日"] = (df["date"] == pd.Timestamp("2013-03-08")).astype(int)
    df["万元"] = df["amount"] / 1e4

    holiday = df.loc[df["节日"] == 1].iloc[0]
    normal = df[df["节日"] == 0]
    print(f"3 月 8 日消费额 {holiday['amount']:,.0f} 元，"
          f"其余日平均 {normal['amount'].mean():,.0f} 元，"
          f"高出 {(holiday['amount'] / normal['amount'].mean() - 1) * 100:.1f}%")

    model = smf.ols("amount ~ t + C(wd, Treatment(0)) + 节日", data=df).fit()
    effect = float(model.params["节日"])
    coef_tab = pd.DataFrame({
        "变量": model.params.index,
        "系数": model.params.round(1),
        "标准误": model.bse.round(1),
        "t值": model.tvalues.round(2),
        "p值": model.pvalues,
    })
    coef_tab["变量"] = coef_tab["变量"].replace({
        "Intercept": "截距", "t": "线性趋势 t",
        "C(wd, Treatment(0))[T.1]": "周二", "C(wd, Treatment(0))[T.2]": "周三",
        "C(wd, Treatment(0))[T.3]": "周四", "C(wd, Treatment(0))[T.4]": "周五",
        "C(wd, Treatment(0))[T.5]": "周六", "C(wd, Treatment(0))[T.6]": "周日",
        "节日": "节日（3 月 8 日）",
    })
    print(f"\n回归 R² = {model.rsquared:.3f}，调整后 R² = {model.rsquared_adj:.3f}")
    print(coef_tab.to_string(index=False))
    save_table(coef_tab, "ch10_回归系数")

    df["调整后"] = df["amount"] - effect * df["节日"]
    z_raw = (df["amount"] - df["amount"].mean()) / df["amount"].std()
    z_adj = (df["调整后"] - df["调整后"].mean()) / df["调整后"].std()
    print(f"\n节日净效应 c = {effect:,.1f} 元（p = {model.pvalues['节日']:.2e}）")
    print(f"3 月 8 日 z 分数：调整前 {z_raw.iloc[7]:.2f} → 调整后 {z_adj.iloc[7]:.2f}")
    print(f"调整后 3 月 8 日为 {df['调整后'].iloc[7]:,.0f} 元，"
          f"其余日平均 {df.loc[df['节日'] == 0, '调整后'].mean():,.0f} 元")
    save_table(pd.DataFrame({
        "日期": df["date"].dt.strftime("%Y-%m-%d"),
        "星期": df["wd"].map(dict(enumerate(WD_NAMES))),
        "消费额": df["amount"].round(0),
        "节日": df["节日"],
        "调整后": df["调整后"].round(0),
    }), "ch10_信用卡日消费")

    # 与教材调整序列做定性核对
    ref = read_excel("ch10/credit_card_adjusted.xlsx", header=0)
    ref.columns = ["date", "教材调整值"]
    ref["date"] = pd.to_datetime(ref["date"])
    merged = df[["date", "万元"]].merge(ref, on="date")
    r_ref = merged["万元"].corr(merged["教材调整值"])
    ref_38 = float(ref.loc[ref["date"] == "2013-03-08", "教材调整值"].iloc[0])
    ref_z = (ref_38 - ref["教材调整值"].mean()) / ref["教材调整值"].std()
    save_table(ref, "ch10_教材调整序列")
    print(f"\n教材调整序列：3 月 8 日 z 分数 {ref_z:.2f}（已无节日尖峰）")
    print(f"与本文调整序列的相关 r = {r_ref:.2f}：教材文件单位为万元且保留了周末周期，"
          "两者只做定性核对")

    # 预测 4 月 1—7 日
    future = pd.DataFrame({
        "date": pd.date_range("2013-04-01", periods=7, freq="D"),
    })
    future["t"] = np.arange(len(df), len(df) + 7)
    future["wd"] = future["date"].dt.day_of_week
    future["节日"] = 0
    sf = model.get_prediction(future).summary_frame(alpha=0.05)
    forecast = pd.DataFrame({
        "日期": future["date"].dt.strftime("%Y-%m-%d"),
        "星期": future["wd"].map(dict(enumerate(WD_NAMES))),
        "预测消费额": sf["mean"].round(0),
        "下限95%": sf["obs_ci_lower"].round(0),
        "上限95%": sf["obs_ci_upper"].round(0),
    })
    print("\n4 月 1—7 日预测：")
    print(forecast.to_string(index=False))
    save_table(forecast, "ch10_七日预测")

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.9), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    ax.plot(df["date"], df["万元"], color=GREY, lw=1.5, marker="o", ms=3.5,
            label="原始日消费额")
    ax.plot(df["date"], df["调整后"] / 1e4, color=COLORS[0], lw=1.8,
            marker="o", ms=3.5, label="剔除节日效应后")
    ax.scatter([holiday["date"]], [holiday["万元"]], s=90, color=ACCENT, zorder=4)
    ax.annotate(f"3 月 8 日 {holiday['万元']:.1f} 万元\n节日效应 +{effect / 1e4:.1f} 万元",
                (holiday["date"], holiday["万元"]), textcoords="offset points",
                xytext=(16, 6), ha="left", fontsize=8.5, color=ACCENT,
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8.5)
    ax.set_xlabel("日期")
    ax.set_ylabel("消费额（万元）")
    ax.set_ylim(df["万元"].min() * 0.985, holiday["万元"] * 1.10)
    ax.set_title(f"节日效应的识别与剔除：R² = {model.rsquared:.2f}")
    ax.legend(loc="upper left", fontsize=8.5, frameon=True, framealpha=0.9,
              edgecolor="none")
    ax.grid(axis="y")

    ax = axes[1]
    wd_effect = [0.0] + [float(model.params[f"C(wd, Treatment(0))[T.{i}]"]) / 1e4
                         for i in range(1, 7)]
    wd_se = [0.0] + [float(model.bse[f"C(wd, Treatment(0))[T.{i}]"]) / 1e4
                     for i in range(1, 7)]
    colors = [COLORS[0] if v >= 0 else COLORS[3] for v in wd_effect]
    ax.bar(WD_NAMES, wd_effect, yerr=np.array(wd_se) * 1.96, color=colors,
           width=0.62, error_kw={"ecolor": GREY, "capsize": 3, "lw": 1})
    ax.axhline(0, color=GREY, lw=1)
    ax.set_ylabel("相对周一的平均差异（万元）")
    ax.set_title("星期效应：各日均值差（误差线为 95% 置信区间）")
    p_wd = max(float(model.pvalues[f"C(wd, Treatment(0))[T.{i}]"]) for i in range(1, 7))
    ax.text(0.02, 0.95, f"各星期 p ≥ {p_wd:.2f}，均不显著",
            transform=ax.transAxes, fontsize=8.5, color=GREY, va="top")
    ax.tick_params(axis="x", labelsize=8.5)
    ax.grid(axis="y")
    save_fig(fig, "ch10_节日效应与调整")

    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.plot(df["date"], df["万元"], color=GREY, lw=1.5, label="3 月实际值")
    ax.plot(future["date"], sf["mean"] / 1e4, color=ACCENT, marker="o", lw=2,
            label="4 月 1—7 日预测")
    ax.fill_between(future["date"], sf["obs_ci_lower"] / 1e4, sf["obs_ci_upper"] / 1e4,
                    color=ACCENT, alpha=0.15, label="95% 预测区间")
    ax.axvline(pd.Timestamp("2013-04-01"), color=GREY, lw=1, ls="--")
    ax.set_xlim(pd.Timestamp("2013-03-10"), pd.Timestamp("2013-04-10"))
    ax.set_xlabel("日期")
    ax.set_ylabel("消费额（万元）")
    ax.set_title("趋势 + 星期效应外推：4 月首周 7 天预测")
    ax.legend(loc="upper left", fontsize=8.5)
    ax.grid(axis="y")
    save_fig(fig, "ch10_七日预测")


if __name__ == "__main__":
    main()
