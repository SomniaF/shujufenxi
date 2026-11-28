"""第 10 章 效应分解与预测 1：乘法模型分解（AirPassengers）。

教材用 1949—1960 年国际航空客运量（144 个月）演示时间序列的四个成分：
  实际值 = 趋势 × 季节 × 循环 × 不规则
步骤（与 Power BI / Excel 里的“预测”功能同一套思路）：
  1. 12 个月中心化移动平均提取趋势 T；
  2. 原值 / 趋势得到“去趋势比率”，按月求平均得到季节指数 S（12 个月均值为 1）；
  3. 比率 / 季节指数得到不规则成分 I；
  4. 用线性趋势外推 × 1961 年季节指数，得到 1961 年 12 个月预测；
  5. 用 1949—1959 建模、预测 1960 做回测，计算 MAPE 说明可信度。
乘法模型适用于“波动幅度随水平一起变大”的序列；若幅度基本不变，应改用加法模型。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import ACCENT, COLORS, GREY, save_fig, save_table
from src.io_utils import read_csv


def centered_ma12(y: pd.Series) -> pd.Series:
    w = np.r_[0.5, np.ones(11), 0.5] / 12
    out = pd.Series(np.nan, index=y.index)
    vals = y.to_numpy(dtype=float)
    for t in range(6, len(y) - 6):
        out.iloc[t] = float(np.dot(w, vals[t - 6:t + 7]))
    return out


def seasonal_index(ratio: pd.Series, months: pd.Series) -> pd.Series:
    idx = ratio.groupby(months).mean()
    return idx / idx.mean()


def fit_model(df: pd.DataFrame) -> dict:
    y = df["AIR"].astype(float)
    trend = centered_ma12(y)
    ratio = y / trend
    season = seasonal_index(ratio, df["date"].dt.month)
    resid = ratio / df["date"].dt.month.map(season)
    fitted = trend * df["date"].dt.month.map(season)
    return {"trend": trend, "ratio": ratio, "season": season,
            "resid": resid, "fitted": fitted}


def trend_fit(trend: pd.Series):
    """趋势在对数尺度上做线性拟合，等价于指数增长——乘法模型里波动随水平放大的常见形态。"""
    mask = trend.notna()
    t = np.arange(len(trend))[mask]
    coef = np.polyfit(t, np.log(trend[mask].to_numpy()), 1)
    return coef


def trend_predict(coef, t):
    return np.exp(np.polyval(coef, t))


def main() -> None:
    df = read_csv("ch10/AirPassengers.csv")
    df["date"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    df = df.sort_values("date").reset_index(drop=True)
    df["月份"] = df["date"].dt.month

    model = fit_model(df)
    season = model["season"]
    peak_m, low_m = season.idxmax(), season.idxmin()
    print(f"样本：{df['date'].min():%Y-%m} 至 {df['date'].max():%Y-%m}，共 {len(df)} 个月")
    print(f"季节指数最高 {peak_m} 月（{season.max():.3f}），"
          f"最低 {low_m} 月（{season.min():.3f}），振幅 {(season.max() - season.min()):.3f}")
    print("季节指数：")
    print(season.round(3).to_string())
    save_table(season.rename("季节指数").to_frame().T.round(3), "ch10_季节指数")

    detail = pd.DataFrame({
        "月份": df["date"].dt.strftime("%Y-%m"),
        "客运量": df["AIR"].astype(int),
        "趋势T": model["trend"].round(1),
        "去趋势比率": model["ratio"].round(3),
        "季节指数S": df["月份"].map(season).round(3),
        "不规则I": model["resid"].round(3),
        "拟合值": model["fitted"].round(1),
    })
    save_table(detail, "ch10_月度分解数据")

    # 回测：1949—1959 建模，预测 1960
    train, test = df.iloc[:132].copy(), df.iloc[132:].copy()
    tm = fit_model(train)
    coef_bt = trend_fit(tm["trend"])
    t_test = np.arange(132, 144)
    pred_test = trend_predict(coef_bt, t_test) * test["月份"].map(tm["season"]).to_numpy()
    mape = float(np.mean(np.abs((test["AIR"].to_numpy() - pred_test) / test["AIR"].to_numpy())) * 100)
    backtest = pd.DataFrame({
        "月份": test["date"].dt.strftime("%Y-%m"),
        "实际值": test["AIR"].to_numpy(),
        "预测值": pred_test.round(1),
        "绝对百分比误差%": (np.abs((test["AIR"].to_numpy() - pred_test)
                                / test["AIR"].to_numpy()) * 100).round(2),
    })
    save_table(backtest, "ch10_回测1960")
    print(f"\n回测 1960：MAPE = {mape:.2f}%")

    # 用全部 144 个月预测 1961
    coef = trend_fit(model["trend"])
    t_future = np.arange(144, 156)
    fc = trend_predict(coef, t_future) * season.reindex(range(1, 13)).to_numpy()
    forecast = pd.DataFrame({
        "月份": [f"1961-{m:02d}" for m in range(1, 13)],
        "预测客运量": fc.round(1),
    })
    forecast["环比%"] = (forecast["预测客运量"].pct_change() * 100).round(2)
    save_table(forecast, "ch10_1961预测")
    total_1961, total_1960 = fc.sum(), int(df.loc[132:, "AIR"].sum())
    print(f"1961 年预测合计 {total_1961:,.0f} 人次，较 1960 年实际 {total_1960:,} "
          f"增长 {(total_1961 / total_1960 - 1) * 100:.1f}%")
    print(f"趋势（对数线性）：月度复合增长 {(np.exp(coef[0]) - 1) * 100:.2f}%")
    print(forecast.to_string(index=False))

    fig, axes = plt.subplots(2, 2, figsize=(12.8, 7.2))
    ax = axes[0, 0]
    ax.plot(df["date"], df["AIR"], color=COLORS[0], lw=1.6, label="实际值")
    ax.plot(df["date"], model["trend"], color=ACCENT, lw=1.8, label="趋势 T（12 月中心化 MA）")
    ax.set_title("① 原始序列与趋势：波动幅度随水平放大 → 用乘法模型")
    ax.legend(fontsize=8.5)
    ax.grid(axis="y")

    ax = axes[0, 1]
    ax.bar(season.index, season.to_numpy(), color=[ACCENT if m in (peak_m, low_m) else COLORS[0]
                                                   for m in season.index], width=0.65)
    for m, v in season.items():
        ax.text(m, v + 0.012, f"{v:.2f}", ha="center", fontsize=7.5)
    ax.axhline(1.0, color=GREY, lw=1, ls="--")
    ax.set_xticks(range(1, 13), [f"{m}月" for m in range(1, 13)], fontsize=8)
    ax.set_ylim(0.8, 1.28)
    ax.set_title(f"② 季节指数：{peak_m} 月最高、{low_m} 月最低")
    ax.grid(axis="y")

    ax = axes[1, 0]
    ax.plot(df["date"], model["ratio"], color="#9DB4C8", lw=1.2, label="去趋势比率 实际/趋势")
    ax.plot(df["date"], df["月份"].map(season), color=ACCENT, lw=1.6, label="季节指数")
    ax.set_title("③ 去趋势比率围绕季节指数上下波动")
    ax.legend(fontsize=8.5)
    ax.grid(axis="y")

    ax = axes[1, 1]
    resid = model["resid"] - 1.0
    ax.plot(df["date"], resid, color=COLORS[2], lw=1.4, label="不规则成分 I−1")
    ax.axhline(0, color=GREY, lw=1)
    sd = resid.std()
    ax.axhline(2 * sd, color=ACCENT, lw=1, ls=":")
    ax.axhline(-2 * sd, color=ACCENT, lw=1, ls=":", label=f"±2σ（σ={sd:.3f}）")
    ax.set_title(f"④ 残差围绕 0：{int((resid.abs() > 2 * sd).sum())} 个月超出 ±2σ")
    ax.legend(fontsize=8.5)
    ax.grid(axis="y")
    fig.tight_layout()
    save_fig(fig, "ch10_乘法效应分解")

    fig, ax = plt.subplots(figsize=(11.6, 4.9))
    ax.plot(df["date"], df["AIR"], color=COLORS[0], lw=1.6, label="实际值（1949—1960）")
    ax.plot(test["date"], pred_test, color=COLORS[1], lw=1.8, ls="--",
            label=f"回测预测 1960（MAPE {mape:.1f}%）")
    future_dates = pd.date_range("1961-01-01", periods=12, freq="MS")
    ax.axvspan(future_dates[0], future_dates[-1], color=ACCENT, alpha=0.06)
    ax.axvline(future_dates[0], color=GREY, lw=1, ls="--")
    ax.annotate("预测区", xy=(future_dates[0], 0.97), xycoords=("data", "axes fraction"),
                xytext=(5, 0), textcoords="offset points", fontsize=8.5,
                color=GREY, va="top")
    ax.plot(future_dates, fc, color=ACCENT, lw=2.0, marker="o", ms=3.5,
            label=f"1961 年预测（合计 {total_1961:,.0f}）")
    ax.set_xlim(pd.Timestamp("1948-09-01"), pd.Timestamp("1962-03-01"))
    ax.set_xlabel("月份")
    ax.set_ylabel("客运量（千人）")
    ax.set_title("乘法分解外推：1960 年回测 + 1961 年 12 个月预测")
    ax.legend(loc="upper left")
    ax.grid(axis="y")
    save_fig(fig, "ch10_1961预测")


if __name__ == "__main__":
    main()
