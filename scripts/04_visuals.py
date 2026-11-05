# -*- coding: utf-8 -*-
"""04_visuals.py —— 33 张静态图（Matplotlib / Seaborn，200 dpi）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (COLORS, DATA_CLEAN, OUT_TAB, PALETTE, WEEKDAY_CN,
                    borough_cn, save_fig, setup_matplotlib, usd_short)

plt = setup_matplotlib()
GEO = json.loads((OUT_TAB / "zone_boundaries.json").read_text(encoding="utf-8"))


ZONE_CN = {
    "Upper East Side South": "上东区南",
    "Upper East Side North": "上东区北",
    "Midtown Center": "中城核心",
    "Midtown East": "中城东",
    "Midtown West": "中城西",
    "Upper West Side South": "上西区南",
    "Upper West Side North": "上西区北",
    "Lincoln Square East": "林肯广场东",
    "Lincoln Square West": "林肯广场西",
    "JFK Airport": "JFK 机场",
    "LaGuardia Airport": "拉瓜迪亚机场",
    "Times Sq/Theatre District": "时代广场/剧院区",
    "Lenox Hill West": "莱诺克斯山西",
    "Lenox Hill East": "莱诺克斯山东",
    "Penn Station/Madison Sq West": "宾州车站/麦迪逊广场西",
    "Midtown North": "中城北",
    "Midtown South": "中城南",
    "East Chelsea": "切尔西东",
    "West Chelsea/Hudson Yards": "切尔西西/哈德逊广场",
    "Murray Hill": "默里山",
    "Union Sq": "联合广场",
    "Clinton East": "克林顿东",
    "West Village": "西村",
    "East Village": "东村",
    "Gramercy": "格拉梅西",
    "Yorkville West": "约克维尔西",
    "Sutton Place/Turtle Bay North": "萨顿广场/龟湾北",
    "Garment District": "服装区",
    "Central Park": "中央公园",
    "TriBeCa/Civic Center": "翠贝卡/市政中心",
    "Flatiron": "熨斗区",
    "Greenwich Village South": "格林威治村南",
}


def short(text, n=9):
    text = str(text)
    return text if len(text) <= n else text[:n] + "…"


def zone_cn(name, n=12):
    text = ZONE_CN.get(str(name), str(name))
    return text if len(text) <= n else text[:n] + "…"


def add_base_map(ax, labels=True):
    for feat in GEO["features"]:
        geom = feat["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            ax.add_patch(Polygon(poly[0], closed=True, facecolor="#F4F6F8",
                                 edgecolor="#D7DFE8", linewidth=0.35, zorder=1))
    if labels:
        for name, x, y in [("曼哈顿", -73.985, 40.775), ("布鲁克林", -73.95, 40.645),
                           ("皇后区", -73.82, 40.72), ("布朗克斯", -73.86, 40.855),
                           ("斯塔滕岛", -74.15, 40.585), ("纽瓦克机场", -74.175, 40.695)]:
            ax.text(x, y, name, fontsize=8, color="#8D99AE", ha="center", alpha=0.9)
    ax.set_xlim(-74.27, -73.68)
    ax.set_ylim(40.52, 40.93)
    ax.set_aspect("equal")
    ax.axis("off")


def finish(ax, title, xlabel=None, ylabel=None, grid_axis="y"):
    ax.set_title(title, loc="left", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if grid_axis:
        ax.grid(axis=grid_axis, color="#E4EAF1", linewidth=0.8)
    sns.despine(ax=ax)
    return ax


def main() -> int:
    daily = pd.read_csv(OUT_TAB / "daily.csv", parse_dates=["date"]).sort_values("date")
    monthly = pd.read_csv(OUT_TAB / "monthly.csv")
    havg = pd.read_csv(OUT_TAB / "hourly_avg.csv")
    sample = pd.read_parquet(DATA_CLEAN / "trips_sample.parquet")
    pay = pd.read_csv(OUT_TAB / "payment_stats.csv")
    tip_hour = pd.read_csv(OUT_TAB / "tip_hour.csv")

    # fig01 月度行程量
    fig, ax = plt.subplots(figsize=(9, 4.6))
    m = monthly.sort_values("month")
    bars = ax.bar(m["month"].astype(str) + "月", m["trips"] / 1e4, color=COLORS["primary"], width=0.68)
    for b, v in zip(bars, m["trips"] / 1e4):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.0f}", ha="center", fontsize=8, color="#486581")
    finish(ax, "2024 年逐月行程量", "月份", "行程量（万次）")
    save_fig(fig, "fig01_月度行程量.png")

    # fig02 日行程量与 7 日移动平均
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.plot(daily["date"], daily["trips"] / 1e4, color=COLORS["primary"], lw=0.9, alpha=0.75, label="日行程量")
    ma = daily["trips"].rolling(7, center=True).mean() / 1e4
    ax.plot(daily["date"], ma, color=COLORS["accent"], lw=2.2, label="7 日移动平均")
    peak = daily.loc[daily["trips"].idxmax()]
    ax.annotate(f"峰值 {peak['date']:%m-%d}\n{peak['trips']/1e4:.1f} 万次",
                xy=(peak["date"], peak["trips"] / 1e4), xytext=(12, -4),
                textcoords="offset points", fontsize=8, color=COLORS["danger"])
    ax.legend(loc="upper left", ncol=2)
    finish(ax, "日行程量波动与 7 日移动平均", None, "行程量（万次）")
    save_fig(fig, "fig02_日行程量趋势.png")

    # fig03 星期 × 小时热力图
    hv = havg.pivot(index="weekday", columns="hour", values="avg_trips").reindex(range(7)) / 1000
    fig, ax = plt.subplots(figsize=(10, 4.2))
    sns.heatmap(hv, cmap="YlGnBu", ax=ax, linewidths=0.4, linecolor="white",
                cbar_kws={"label": "千次/日"})
    ax.set_yticklabels([WEEKDAY_CN[i] for i in range(7)], rotation=0)
    ax.set_xlabel("小时")
    ax.set_ylabel("")
    ax.set_title("星期 × 小时的平均行程量", loc="left", pad=12)
    save_fig(fig, "fig03_时段星期热力图.png")

    # fig04 月度收入构成
    mm = daily.groupby("month").agg(revenue=("revenue", "sum"), fare=("fare", "sum"),
                                    tip=("tip", "sum"), tolls=("tolls", "sum"))
    mm["other"] = (mm["revenue"] - mm["fare"] - mm["tip"] - mm["tolls"]).clip(lower=0)
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.stackplot(mm.index, mm["fare"] / 1e6, mm["tip"] / 1e6, mm["tolls"] / 1e6,
                 mm["other"] / 1e6, labels=["车费", "小费", "过路费", "税费及附加"],
                 colors=[COLORS["primary"], COLORS["accent"], COLORS["secondary"], COLORS["gray"]],
                 alpha=0.9)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([f"{i}月" for i in range(1, 13)])
    ax.legend(loc="upper left", ncol=4, fontsize=9)
    finish(ax, "月度总收入构成（百万美元）", "月份", "金额（百万美元）")
    save_fig(fig, "fig04_月度收入构成.png")

    # fig05 行程时长分布
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    d = sample["duration_min"].clip(upper=90)
    ax.hist(d, bins=60, color=COLORS["secondary"], alpha=0.85, edgecolor="white")
    med = sample["duration_min"].median()
    ax.axvline(med, color=COLORS["danger"], lw=1.6, ls="--")
    ax.text(med + 2, ax.get_ylim()[1] * 0.85, f"中位数 {med:.1f} 分钟", color=COLORS["danger"], fontsize=9)
    finish(ax, "行程时长分布（截尾至 90 分钟）", "时长（分钟）", "行程数")
    save_fig(fig, "fig05_行程时长分布.png")

    # fig06 时长箱线图：工作日 vs 周末
    s = sample.loc[sample["duration_min"] <= 90].copy()
    s["日类型"] = s["is_weekend"].map({True: "周末", False: "工作日"})
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    sns.boxplot(data=s, x="日类型", y="duration_min", hue="日类型", ax=ax,
                palette=[COLORS["primary"], COLORS["accent"]], width=0.45,
                showfliers=False, legend=False)
    finish(ax, "工作日与周末的行程时长差异", None, "时长（分钟）")
    save_fig(fig, "fig06_时长箱线图.png")

    # fig07 行程距离分布
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    dist = sample["distance_mi"].clip(upper=20)
    ax.hist(dist, bins=60, color=COLORS["primary"], alpha=0.85, edgecolor="white")
    ax.axvline(sample["distance_mi"].median(), color=COLORS["danger"], lw=1.6, ls="--")
    finish(ax, "行程距离分布（截尾至 20 英里）", "距离（英里）", "行程数")
    save_fig(fig, "fig07_行程距离分布.png")

    # fig08 距离—时长六边形密度图
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    hb = ax.hexbin(sample["distance_mi"], sample["duration_min"], gridsize=55,
                   bins="log", cmap="YlGnBu", extent=(0, 25, 0, 90), mincnt=1)
    cb = fig.colorbar(hb, ax=ax, pad=0.02)
    cb.set_label("行程数（对数）")
    finish(ax, "距离与时长的联合分布", "距离（英里）", "时长（分钟）", grid_axis=None)
    save_fig(fig, "fig08_距离时长散点.png")

    # fig09 支付方式占比
    p = pay.sort_values("trips", ascending=False)
    p = p[p["share"] >= 0.002]
    p = p.sort_values("share")
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    ax.barh(p["name"], p["share"] * 100, color=PALETTE[:len(p)][::-1], height=0.62)
    for y, (s, t) in enumerate(zip(p["share"], p["trips"])):
        ax.text(s * 100 + 0.8, y, f"{s*100:.2f}%（{t/1e4:.0f} 万次）",
                va="center", fontsize=8.5, color=COLORS["dark"])
    ax.set_xlim(0, max(p["share"]) * 100 * 1.42)
    finish(ax, "支付方式结构（按行程量）", "占比（%）", grid_axis="x")
    save_fig(fig, "fig09_支付方式占比.png")

    # fig10 信用卡小费率分布
    tr = sample["tip_rate"].dropna()
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.hist(tr.clip(upper=0.5), bins=50, color=COLORS["secondary"], alpha=0.85, edgecolor="white")
    ax.axvline(tr.median(), color=COLORS["danger"], lw=1.6, ls="--")
    ax.text(tr.median() + 0.01, ax.get_ylim()[1] * 0.85,
            f"中位数 {tr.median()*100:.1f}%", color=COLORS["danger"], fontsize=9)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x*100:.0f}%")
    finish(ax, "信用卡行程小费率分布（现金小费不可观测）", "小费率", "行程数")
    save_fig(fig, "fig10_小费率分布.png")

    # fig11 小费率的时段曲线
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    ax.bar(tip_hour["hour"], tip_hour["mean_tip_rate"] * 100, color=COLORS["light"],
           edgecolor=COLORS["secondary"], label="平均小费率（左轴）")
    ax.set_ylim(0, max(tip_hour["mean_tip_rate"] * 100) * 1.35)
    ax.set_ylabel("平均小费率（%）", color=COLORS["secondary"])
    ax2 = ax.twinx()
    ax2.plot(tip_hour["hour"], tip_hour["generous_share"] * 100, color=COLORS["danger"],
             marker="o", ms=4, lw=2, label="慷慨小费（≥25%）占比（右轴）")
    ax2.set_ylabel("小费率≥25% 的占比（%）", color=COLORS["danger"])
    ax2.set_ylim(0, max(tip_hour["generous_share"] * 100) * 1.35)
    ax.set_xticks(range(0, 24, 2))
    ax.set_title("小费行为的时段差异", loc="left", pad=12)
    ax.grid(axis="y", color="#E4EAF1")
    sns.despine(ax=ax, right=False)
    ax2.spines["right"].set_visible(True)
    save_fig(fig, "fig11_小费率时段曲线.png")

    # fig12 区域收入帕累托
    zs = pd.read_csv(OUT_TAB / "zone_stats.csv").sort_values("revenue", ascending=False)
    z30 = zs.head(30).copy()
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(range(len(z30)), z30["revenue"] / 1e6, color=COLORS["primary"], width=0.7)
    ax.set_ylabel("收入（百万美元）")
    ax.set_xticks(range(len(z30)))
    ax.set_xticklabels([zone_cn(z, 10) for z in z30["Zone"]], rotation=55, ha="right", fontsize=7.4)
    ax2 = ax.twinx()
    ax2.plot(range(len(z30)), z30["cum_revenue_share"] * 100, color=COLORS["accent"],
             marker="o", ms=3.5, lw=2)
    ax2.axhline(70, color=COLORS["danger"], ls="--", lw=1)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("累计收入占比（%）")
    ax.set_title("Top 30 区域收入帕累托", loc="left", pad=12)
    ax.grid(axis="y", color="#E4EAF1")
    sns.despine(ax=ax, right=False)
    ax2.spines["right"].set_visible(True)
    save_fig(fig, "fig12_区域收入帕累托.png")

    # fig13 区域 ABC 分层
    abc = zs.groupby("abc_tier").agg(zones=("PULocationID", "size"),
                                     revenue=("revenue", "sum"), trips=("trips", "sum")).reindex(["A", "B", "C"])
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
    axes[0].bar(abc.index, abc["zones"], color=[COLORS["primary"], COLORS["secondary"], COLORS["gray"]])
    axes[0].set_title("区域数量（个）", loc="left")
    axes[1].bar(abc.index, abc["revenue"] / abc["revenue"].sum() * 100,
                color=[COLORS["primary"], COLORS["secondary"], COLORS["gray"]])
    axes[1].set_title("收入占比（%）", loc="left")
    for ax in axes:
        ax.grid(axis="y", color="#E4EAF1")
        sns.despine(ax=ax)
    fig.suptitle("区域收入 ABC 分层", x=0.01, y=1.0, ha="left", fontsize=14, fontweight="bold")
    fig.subplots_adjust(top=0.82, wspace=0.28)
    save_fig(fig, "fig13_区域ABC分层.png")

    # fig14 区域收入气泡地图
    zmap = zs.dropna(subset=["lat", "lng"]).copy()
    fig, ax = plt.subplots(figsize=(8.2, 7.2))
    add_base_map(ax)
    sizes = 18 + 420 * (zmap["revenue"] / zmap["revenue"].max()) ** 0.55
    sc = ax.scatter(zmap["lng"], zmap["lat"], s=sizes, c=zmap["avg_fare"], cmap="YlOrRd",
                    alpha=0.82, edgecolors="white", linewidth=0.45, zorder=3)
    cb = fig.colorbar(sc, ax=ax, shrink=0.62, pad=0.01)
    cb.set_label("平均车费（美元）")
    offsets = {"JFK Airport": (8, -3), "LaGuardia Airport": (8, 7),
               "Midtown Center": (-9, 8), "Upper East Side South": (-9, -10)}
    for _, r in zmap.nlargest(4, "revenue").iterrows():
        ax.annotate(zone_cn(r["Zone"], 7), (r["lng"], r["lat"]),
                    xytext=offsets.get(r["Zone"], (6, 4)), textcoords="offset points",
                    fontsize=8, color=COLORS["dark"], zorder=5,
                    arrowprops=dict(arrowstyle="-", color="#B7C2CF", lw=0.6),
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    ax.set_title("区域收入气泡地图（气泡=收入，颜色=平均车费）", loc="left", pad=10)
    save_fig(fig, "fig14_区域收入气泡地图.png")

    # fig15 区域聚类 PCA
    zc = pd.read_csv(OUT_TAB / "zone_clusters.csv")
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    for c, sub in zc.groupby("cluster"):
        ax.scatter(sub["pca1"], sub["pca2"], s=22 + 170 * (sub["trips"] / zc["trips"].max()),
                   color=PALETTE[int(c) % len(PALETTE)], alpha=0.78, edgecolors="white",
                   linewidth=0.4, label=sub["cluster_name"].iloc[0])
    ax.set_xlabel("主成分 1")
    ax.set_ylabel("主成分 2")
    ax.legend(fontsize=8, loc="best")
    finish(ax, "区域功能聚类的 PCA 投影", grid_axis=None)
    save_fig(fig, "fig15_区域聚类PCA.png")

    # fig16 聚类雷达图
    prof = pd.read_csv(OUT_TAB / "cluster_profiles.csv")
    bands = [(0, 3), (4, 7), (8, 11), (12, 15), (16, 19), (20, 23)]
    band_labels = ["0–3 时", "4–7 时", "8–11 时", "12–15 时", "16–19 时", "20–23 时"]
    vals = np.array([[prof.loc[i, [f"h{h}" for h in range(a, b + 1)]].mean() * 100
                      for a, b in bands] for i in range(len(prof))])
    angles = np.linspace(0, 2 * np.pi, len(bands), endpoint=False).tolist()
    angles += angles[:1]
    fig = plt.figure(figsize=(7.0, 6.6))
    ax = plt.subplot(111, polar=True)
    for i in range(len(prof)):
        v = vals[i].tolist() + [vals[i][0]]
        ax.plot(angles, v, color=PALETTE[i % len(PALETTE)], lw=2, label=prof.loc[i, "cluster_name"])
        ax.fill(angles, v, color=PALETTE[i % len(PALETTE)], alpha=0.08)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(band_labels, fontsize=9)
    ax.set_title("各区域类型的时段结构（出发量占比）", loc="left", pad=22)
    ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.12), fontsize=8)
    save_fig(fig, "fig16_聚类雷达图.png")

    # fig17 聚类 24 小时曲线
    fig, ax = plt.subplots(figsize=(9.4, 3.9))
    for i in range(len(prof)):
        y = prof.loc[i, [f"h{h}" for h in range(24)]].values.astype(float) * 100
        ax.plot(range(24), y, lw=2, color=PALETTE[i % len(PALETTE)], label=prof.loc[i, "cluster_name"])
    ax.set_xticks(range(0, 24, 2))
    ax.set_ylim(0, max(prof[[f"h{h}" for h in range(24)]].values.max() * 100 * 1.38, 11))
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    finish(ax, "各区域类型的 24 小时出发曲线", "小时", "出发量占比（%）")
    save_fig(fig, "fig17_聚类时段曲线.png")

    # fig18 聚类空间分布
    fig, ax = plt.subplots(figsize=(8.2, 7.2))
    add_base_map(ax)
    for c, sub in zc.groupby("cluster"):
        ax.scatter(sub["lng"], sub["lat"], s=20 + 150 * (sub["trips"] / zc["trips"].max()),
                   color=PALETTE[int(c) % len(PALETTE)], alpha=0.75, edgecolors="white",
                   linewidth=0.35, zorder=4, label=sub["cluster_name"].iloc[0])
    ax.legend(loc="lower right", fontsize=8, frameon=True)
    ax.set_title("区域功能类型的空间分布", loc="left", pad=10)
    save_fig(fig, "fig18_聚类空间分布.png")

    # fig19 Top 20 OD 走廊地图
    od20 = pd.read_csv(OUT_TAB / "od_top20.csv")
    zd = pd.read_csv(OUT_TAB / "zone_dim.csv")[["LocationID", "lat", "lng"]]
    o = od20.merge(zd.rename(columns={"LocationID": "PULocationID", "lat": "pu_lat", "lng": "pu_lng"}),
                   on="PULocationID", how="left")
    o = o.merge(zd.rename(columns={"LocationID": "DOLocationID", "lat": "do_lat", "lng": "do_lng"}),
                on="DOLocationID", how="left")
    fig, ax = plt.subplots(figsize=(8.2, 7.2))
    add_base_map(ax)
    for _, r in o.iterrows():
        if pd.isna(r["pu_lat"]) or pd.isna(r["do_lat"]):
            continue
        ax.plot([r["pu_lng"], r["do_lng"]], [r["pu_lat"], r["do_lat"]],
                color=COLORS["primary"], alpha=0.55,
                lw=0.5 + 4.0 * (r["trips"] / o["trips"].max()) ** 0.6, zorder=3,
                solid_capstyle="round")
    ax.set_title("Top 20 起讫（OD）走廊", loc="left", pad=10)
    save_fig(fig, "fig19_OD走廊地图.png")

    # fig20 OD 集中度
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    oo = o.sort_values("trips", ascending=True)
    ax.barh(range(len(oo)), oo["trips"] / 1e3, color=COLORS["secondary"], height=0.72)
    ax.set_yticks(range(len(oo)))
    ax.set_yticklabels([f"{zone_cn(a)} → {zone_cn(b)}" for a, b in zip(oo["pu_zone"], oo["do_zone"])], fontsize=7.8)
    ax.set_xlabel("行程量（千次）")
    finish(ax, "Top 20 OD 走廊的行程量", grid_axis="x")
    fig.subplots_adjust(left=0.30, right=0.98, top=0.90, bottom=0.13)
    save_fig(fig, "fig20_OD集中度.png")

    # fig21 机场 vs 非机场（统一取信用卡行程，保证车费与小费口径一致）
    card_sample = sample.loc[sample["is_card"] & sample["tip_rate"].notna()]
    ap = card_sample.groupby("airport").agg(fare=("fare", "mean"), dist=("distance_mi", "mean"),
                                            tip=("tip_rate", "mean"), n=("fare", "size")).reset_index()
    ap["label"] = ap["airport"].map({True: "机场相关", False: "非机场"})
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.8))
    for ax, col, title, fmt in zip(axes, ["fare", "dist", "tip"],
                                   ["平均车费（美元）", "平均距离（英里）", "平均小费率"],
                                   ["{:.1f}", "{:.1f}", "{:.1%}"]):
        bars = ax.bar(ap["label"], ap[col], color=[COLORS["gray"], COLORS["accent"]])
        for b, v in zip(bars, ap[col]):
            ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", fontsize=9)
        ax.set_title(title, loc="left", fontsize=11)
        ax.grid(axis="y", color="#E4EAF1")
        sns.despine(ax=ax)
    fig.suptitle("机场相关行程与非机场行程的结构差异", x=0.01, y=0.99, ha="left",
                 fontsize=14, fontweight="bold")
    fig.subplots_adjust(top=0.76, wspace=0.30)
    save_fig(fig, "fig21_机场与非机场对比.png")

    # fig22 工作日 vs 周末时段曲线
    hv2 = havg.pivot(index="weekday", columns="hour", values="avg_trips")
    wd = hv2.loc[0:4].mean(axis=0)
    we = hv2.loc[5:6].mean(axis=0)
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    ax.plot(wd.index, wd.values / 1e3, color=COLORS["primary"], lw=2.2, label="工作日")
    ax.plot(we.index, we.values / 1e3, color=COLORS["accent"], lw=2.2, label="周末")
    ax.set_xticks(range(0, 24, 2))
    ax.legend()
    finish(ax, "工作日与周末的小时需求曲线", "小时", "平均行程量（千次/日）")
    save_fig(fig, "fig22_工作日周末时段对比.png")

    # fig23 需求预测拟合与区间
    fdf = pd.read_csv(OUT_TAB / "demand_forecast.csv", parse_dates=["date"])
    fitdf = pd.read_csv(OUT_TAB / "demand_fit.csv", parse_dates=["date"])
    fmet = json.loads((OUT_TAB / "forecast_metrics.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(fitdf["date"], fitdf["actual"] / 1e4, color=COLORS["gray"], lw=1.4, label="训练期实际")
    ax.plot(fitdf["date"], fitdf["fitted"] / 1e4, color=COLORS["secondary"], lw=1.6, ls="--", label="训练期拟合")
    ax.plot(fdf["date"], fdf["actual"] / 1e4, color=COLORS["dark"], lw=1.8, label="12 月实际")
    ax.plot(fdf["date"], fdf["forecast"] / 1e4, color=COLORS["danger"], lw=2, label="12 月预测")
    ax.fill_between(fdf["date"], fdf["lower"] / 1e4, fdf["upper"] / 1e4,
                    color=COLORS["danger"], alpha=0.15, label="95% 置信区间")
    ax.axvline(pd.Timestamp("2024-12-01"), color=COLORS["gray"], ls=":", lw=1.2)
    xmas = fdf[fdf["date"] == pd.Timestamp("2024-12-25")]
    if len(xmas):
        ax.annotate("圣诞周需求塌陷：模型未预见", xy=(xmas["date"].iloc[0], xmas["actual"].iloc[0] / 1e4),
                    xytext=(-80, 26), textcoords="offset points", fontsize=8,
                    color=COLORS["danger"], arrowprops=dict(arrowstyle="->", color=COLORS["danger"], lw=0.9))
    ax.legend(loc="upper left", ncol=3, fontsize=8)
    finish(ax, f"SARIMAX 日需求预测（11 月验证 MAPE={fmet['val_mape']:.1f}%，"
               f"12 月测试 {fmet['mape']:.1f}%）", None, "行程量（万次）")
    save_fig(fig, "fig23_需求预测拟合.png")

    # fig24 预测误差
    fdf["ape"] = (fdf["actual"] - fdf["forecast"]).abs() / fdf["actual"] * 100
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.axvspan(21.5, 31.5, color=COLORS["danger"], alpha=0.08, lw=0)
    ax.text(26.5, fdf["ape"].max() * 0.92, "圣诞假期周", ha="center", fontsize=8,
            color=COLORS["danger"])
    ax.bar(fdf["date"].dt.day, fdf["ape"], color=COLORS["purple"], alpha=0.8, width=0.75)
    ax.axhline(fmet["mape"], color=COLORS["danger"], ls="--", lw=1.2,
               label=f"MAPE={fmet['mape']:.1f}%")
    ax.legend()
    finish(ax, "12 月逐日绝对百分比误差", "日期（12 月）", "绝对百分比误差（%）")
    save_fig(fig, "fig24_预测误差.png")

    # fig25 12 月实际 vs 预测散点
    fig, ax = plt.subplots(figsize=(7.6, 4.9))
    ax.scatter(fdf["actual"] / 1e4, fdf["forecast"] / 1e4, s=38, color=COLORS["primary"],
               alpha=0.75, edgecolors="white", linewidth=0.5)
    lim = max(fdf["actual"].max(), fdf["forecast"].max()) / 1e4 * 1.06
    ax.plot([0, lim], [0, lim], color=COLORS["danger"], ls="--", lw=1.2, label="理想预测线")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("实际行程量（万次）")
    ax.set_ylabel("预测行程量（万次）")
    ax.legend()
    finish(ax, f"12 月实际与预测对比（R²={fmet['r2']:.2f}）", grid_axis=None)
    save_fig(fig, "fig25_十二月实际与预测.png")

    # fig26 小费模型 ROC
    roc = pd.read_csv(OUT_TAB / "tip_roc.csv")
    tmet = json.loads((OUT_TAB / "tip_model.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    ax.plot(roc["fpr"], roc["tpr"], color=COLORS["primary"], lw=2.2,
            label=f"GBM（AUC={tmet['auc']:.3f}）")
    ax.plot([0, 1], [0, 1], color=COLORS["gray"], ls="--", lw=1)
    ax.set_xlabel("假阳性率")
    ax.set_ylabel("真阳性率")
    ax.legend(loc="lower right")
    finish(ax, "小费概率模型的 ROC 曲线", grid_axis=None)
    save_fig(fig, "fig26_小费模型ROC.png")

    # fig27 小费模型特征重要性
    imp = pd.read_csv(OUT_TAB / "tip_importance.csv").head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.barh(range(len(imp)), imp["importance"], color=COLORS["secondary"], height=0.7)
    ax.set_yticks(range(len(imp)))
    ax.set_yticklabels([short(f, 22) for f in imp["feature"]], fontsize=9)
    ax.set_xlabel("置换重要性（AUC 下降）")
    finish(ax, "小费模型的特征重要性", grid_axis="x")
    save_fig(fig, "fig27_小费特征重要性.png")

    # fig28 区域 × 时段小费率热力图
    tbh = pd.read_csv(OUT_TAB / "tip_borough_hour.csv")
    mat = tbh.pivot_table(index="borough_pu", columns="hour", values="mean_tip_rate", aggfunc="mean")
    mat.index = [borough_cn(x) for x in mat.index]
    fig, ax = plt.subplots(figsize=(10, 4.0))
    sns.heatmap(mat * 100, cmap="YlOrRd", ax=ax, linewidths=0.4, linecolor="white",
                cbar_kws={"label": "平均小费率（%）"})
    ax.set_xlabel("小时")
    ax.set_ylabel("")
    ax.set_title("区域 × 时段的小费率（信用卡）", loc="left", pad=12)
    save_fig(fig, "fig28_小费率热力图.png")

    # fig29 区域机会矩阵
    bcg = pd.read_csv(OUT_TAB / "bcg_matrix.csv")
    bsum = json.loads((OUT_TAB / "bcg_summary.json").read_text(encoding="utf-8"))
    qcolor = {"明星": COLORS["primary"], "现金牛": COLORS["secondary"],
              "问题": COLORS["accent"], "瘦狗": COLORS["gray"]}
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    for q, sub in bcg.groupby("quadrant"):
        ax.scatter(sub["growth"] * 100, sub["revenue_share"] * 100,
                   s=30 + 420 * (sub["revenue"] / bcg["revenue"].max()) ** 0.55,
                   color=qcolor[q], alpha=0.75, edgecolors="white", linewidth=0.5, label=q)
    ax.axvline(bsum["growth_median"] * 100, color=COLORS["gray"], ls="--", lw=1)
    ax.axhline(bsum["share_median"] * 100, color=COLORS["gray"], ls="--", lw=1)
    labels = {
        "JFK Airport": ("JFK 机场", (-72, 9)),
        "LaGuardia Airport": ("LaGuardia 机场", (12, 4)),
        "Midtown Center": ("中城核心", (12, 7)),
        "Upper East Side South": ("上东区南", (-86, -2)),
        "Times Sq/Theatre District": ("时代广场", (40, -26)),
    }
    for _, r in bcg.nlargest(5, "revenue").iterrows():
        text, offset = labels.get(r["Zone"], (short(r["Zone"], 9), (6, 4)))
        ax.annotate(text, (r["growth"] * 100, r["revenue_share"] * 100),
                    xytext=offset, textcoords="offset points", fontsize=8,
                    color=COLORS["dark"],
                    bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.75),
                    arrowprops=dict(arrowstyle="-", color=COLORS["gray"], lw=0.6))
    ax.set_xlim(-12, 54)
    ax.set_xlabel("下半年相对上半年的行程增速（%）")
    ax.set_ylabel("全年收入份额（%）")
    ax.legend(title="象限", fontsize=8, loc="upper right")
    finish(ax, "区域增长—份额机会矩阵", grid_axis=None)
    save_fig(fig, "fig29_区域机会矩阵.png")

    # fig30 STL 残差异常日
    ad = pd.read_csv(OUT_TAB / "anomaly_days.csv", parse_dates=["date"])
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1.2], "hspace": 0.12})
    axes[0].plot(ad["date"], ad["trips"] / 1e4, color=COLORS["primary"], lw=0.9, alpha=0.8)
    flag = ad[ad["flag"]]
    axes[0].scatter(flag["date"], flag["trips"] / 1e4, s=34, color=COLORS["danger"],
                    zorder=4, label=f"异常日（|z|≥2.5，共 {len(flag)} 天）")
    for _, r in flag.nlargest(4, "trips").iterrows():
        axes[0].annotate(f"{r['date']:%m-%d}", (r["date"], r["trips"] / 1e4),
                         xytext=(4, 4), textcoords="offset points", fontsize=8,
                         color=COLORS["danger"])
    axes[0].legend(loc="upper left", fontsize=8)
    finish(axes[0], "STL 残差法的需求异常日识别", None, "行程量（万次）")
    axes[1].bar(ad["date"], ad["z"], width=0.9,
                color=np.where(ad["flag"], COLORS["danger"], COLORS["gray"]), alpha=0.85)
    for y in (-2.5, 2.5):
        axes[1].axhline(y, color=COLORS["dark"], ls="--", lw=1)
    axes[1].set_ylabel("残差 z 值")
    axes[1].set_xlabel("日期")
    axes[1].grid(axis="y", color="#E4EAF1")
    sns.despine(ax=axes[1])
    save_fig(fig, "fig30_异常检测.png")

    # fig31 行程速度分布
    sp = sample["speed_mph"].replace([np.inf, -np.inf], np.nan).dropna()
    sp = sp[sp.between(0, 70)]
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    ax.hist(sp, bins=70, color=COLORS["purple"], alpha=0.85, edgecolor="white")
    med = sp.median()
    ax.axvline(med, color=COLORS["secondary"], lw=1.8, label=f"中位数 {med:.1f} 英里/小时")
    ax.axvline(60, color=COLORS["danger"], lw=1.4, ls="--", label="60 英里/小时质检阈值")
    ax.set_yscale("log")
    ax.legend(fontsize=8)
    finish(ax, "行程平均速度分布（对数纵轴）", "速度（英里/小时）", "行程数")
    save_fig(fig, "fig31_速度分布.png")

    # fig32 行政区收入构成
    bor = pd.read_csv(OUT_TAB / "borough_stats.csv")
    bor = bor[bor["trips"] >= 10000].copy()
    bor["other"] = (bor["revenue"] - bor["fare"] - bor["tip"]).clip(lower=0)
    for c in ["fare", "tip", "other"]:
        bor[c + "_pct"] = bor[c] / bor["revenue"] * 100
    bor["label"] = bor["borough_pu"].map(borough_cn)
    bor = bor.sort_values("revenue", ascending=True)
    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    left = np.zeros(len(bor))
    for col, name, color in [("fare_pct", "车费", COLORS["primary"]),
                             ("tip_pct", "小费", COLORS["accent"]),
                             ("other_pct", "税费及其他", COLORS["gray"])]:
        ax.barh(bor["label"], bor[col], left=left, color=color, label=name, height=0.62)
        left += bor[col].values
    ax.set_xlim(0, 100)
    ax.set_xlabel("占该区域总收入的比例（%）")
    ax.legend(ncol=3, loc="lower right", fontsize=8, bbox_to_anchor=(1.0, 1.0), frameon=False)
    finish(ax, "各行政区收入构成", grid_axis="x")
    save_fig(fig, "fig32_行政区收入构成.png")

    # fig33 行政区距离结构
    s2 = sample.dropna(subset=["borough_pu"]).copy()
    s2 = s2[s2["borough_pu"].isin(["Manhattan", "Queens", "Brooklyn", "Bronx"])]
    s2["距离段"] = pd.cut(s2["distance_mi"], [0, 2, 5, 10, 100],
                        labels=["0–2 英里", "2–5 英里", "5–10 英里", "10 英里以上"])
    tab = s2.groupby(["borough_pu", "距离段"], observed=True).size().unstack(fill_value=0)
    tab = tab.div(tab.sum(axis=1), axis=0) * 100
    tab.index = [borough_cn(x) for x in tab.index]
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    bottom = np.zeros(len(tab))
    for col, color in zip(tab.columns, [COLORS["primary"], COLORS["secondary"],
                                        COLORS["accent"], COLORS["danger"]]):
        ax.bar(tab.index, tab[col], bottom=bottom, color=color, label=str(col), width=0.6)
        for i, v in enumerate(tab[col]):
            if v >= 7:
                ax.text(i, bottom[i] + v / 2, f"{v:.0f}%", ha="center", va="center",
                        fontsize=8, color="white")
        bottom += tab[col].values
    ax.set_ylim(0, 100)
    ax.set_ylabel("行程占比（%）")
    ax.legend(ncol=4, fontsize=8, loc="lower left", bbox_to_anchor=(0.0, 1.0))
    finish(ax, "主要行政区的行程距离结构", grid_axis="y")
    save_fig(fig, "fig33_行政区距离结构.png")

    print("[完成] 33 张静态图已写入 outputs/figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
