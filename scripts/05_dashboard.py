# -*- coding: utf-8 -*-
"""05_dashboard.py —— Streamlit + Plotly 联动运营大屏。

运行：py -m streamlit run scripts/05_dashboard.py
六个以上联动组件：筛选器、KPI 卡片、日趋势、时段热力、区域气泡地图、
Top 区域榜、功能类型分布、站点下钻与明细表（含 CSV 下载）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import COLORS, DATA_CLEAN, OUT_TAB

FONT = "Microsoft YaHei, Noto Sans CJK SC, sans-serif"
PAY_CN = {0: "未知/弹性计价", 1: "信用卡", 2: "现金", 3: "免收费", 4: "争议"}
BOR_CN = {"Manhattan": "曼哈顿", "Queens": "皇后区", "Brooklyn": "布鲁克林",
          "Bronx": "布朗克斯", "Staten Island": "斯塔滕岛", "EWR": "纽瓦克机场"}
CLUSTER_COLOR = {"机场枢纽型": COLORS["primary"], "早高峰通勤型": COLORS["secondary"],
                 "核心商业区型": COLORS["accent"], "通勤休闲混合型": COLORS["gold"],
                 "晚高峰通勤型": COLORS["danger"], "夜间活力型": COLORS["purple"],
                 "日间综合型": COLORS["gray"]}

st.set_page_config(page_title="纽约黄色出租车运营分析大屏", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.kpi {background:#fff; border:1px solid #E4EAF1; border-radius:12px; padding:12px 16px;
      box-shadow:0 1px 3px rgba(16,42,67,.06); height:100%;}
.kpi .t {font-size:.78rem; color:#627D98; letter-spacing:.02em;}
.kpi .v {font-size:1.55rem; font-weight:700; color:#102A43; line-height:1.5;}
.kpi .s {font-size:.72rem; color:#829AB1;}
h1 {font-size:1.55rem !important; color:#102A43; margin-bottom:.1rem;}
.sub {color:#627D98; font-size:.85rem; margin-bottom:.6rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="加载聚合数据…")
def load_tables():
    dzp = pd.read_parquet(DATA_CLEAN / "daily_zone_payment.parquet")
    dzp["date"] = pd.to_datetime(dzp["date"])
    dzp["支付方式"] = dzp["payment_type"].map(PAY_CN)
    dzp["行政区"] = dzp["borough_pu"].map(BOR_CN).fillna("其他")
    dzp["机场"] = dzp["airport"].map({True: "机场相关", False: "非机场"})
    dzp = dzp.drop(columns=["payment_type", "borough_pu", "airport", "card_trips"])
    daily = pd.read_csv(OUT_TAB / "daily.csv", parse_dates=["date"])
    dhb = pd.read_csv(OUT_TAB / "daily_hour_borough.csv", parse_dates=["date"])
    dhb["行政区"] = dhb["borough_pu"].map(BOR_CN).fillna("其他")
    zs = pd.read_csv(OUT_TAB / "zone_stats.csv")
    zd = pd.read_csv(OUT_TAB / "zone_dim.csv")
    zc = pd.read_csv(OUT_TAB / "zone_clusters.csv")
    zh = pd.read_csv(OUT_TAB / "zone_hour.csv")
    od = pd.read_csv(OUT_TAB / "od_pairs.csv")
    ad = pd.read_csv(OUT_TAB / "anomaly_days.csv", parse_dates=["date"])
    geo = json.loads((OUT_TAB / "zone_boundaries.json").read_text(encoding="utf-8"))
    return dzp, daily, dhb, zs, zd, zc, zh, od, ad, geo


def kpi_card(col, title, value, sub=""):
    col.markdown(f'<div class="kpi"><div class="t">{title}</div>'
                 f'<div class="v">{value}</div><div class="s">{sub}</div></div>',
                 unsafe_allow_html=True)


def style(fig, height=330, legend_top=True):
    fig.update_layout(template="plotly_white", height=height, font=dict(family=FONT, size=11),
                      margin=dict(l=10, r=10, t=54, b=10),
                      title=dict(font=dict(size=14, color="#102A43"), x=0.01, y=0.97, yanchor="top"),
                      legend=dict(orientation="h", yanchor="top", y=-0.16, x=0,
                                  font=dict(size=10)))
    fig.update_xaxes(gridcolor="#EEF2F6", zeroline=False)
    fig.update_yaxes(gridcolor="#EEF2F6", zeroline=False)
    return fig


dzp, daily, dhb, zs, zd, zc, zh, od, ad, GEO = load_tables()

with st.sidebar:
    st.markdown("## 筛选器")
    dmin, dmax = dzp["date"].min().date(), dzp["date"].max().date()
    d0, d1 = st.date_input("日期范围", value=(dmin, dmax),
                           min_value=dmin, max_value=dmax)
    bor_all = ["曼哈顿", "皇后区", "布鲁克林", "布朗克斯", "斯塔滕岛", "纽瓦克机场"]
    bor_sel = st.multiselect("上车行政区", bor_all, default=bor_all)
    pay_sel = st.multiselect("支付方式", list(PAY_CN.values()),
                             default=list(PAY_CN.values()))
    air_sel = st.radio("是否机场相关行程", ["全部", "机场相关", "非机场"], horizontal=True)
    st.caption("说明：时段热力图仅受日期与行政区筛选影响；"
               "其余组件同时响应支付方式与机场筛选。")
    st.markdown("---")
    st.caption("数据：NYC TLC Yellow Taxi 2024（官方公开数据）\n\n"
               "清洗后 3,919 万条行程 · 261 个区域")

mask = ((dzp["date"] >= pd.Timestamp(d0)) & (dzp["date"] <= pd.Timestamp(d1))
        & dzp["行政区"].isin(bor_sel) & dzp["支付方式"].isin(pay_sel))
if air_sel != "全部":
    mask &= dzp["机场"] == air_sel
df = dzp.loc[mask]

trips = float(df["trips"].sum())
revenue = float(df["revenue"].sum())
fare = float(df["fare"].sum())
tip = float(df["tip"].sum())
card = float(df.loc[df["支付方式"] == "信用卡", "trips"].sum())
card_tip_rate = float(df.loc[df["支付方式"] == "信用卡", "tip"].sum() /
                      max(df.loc[df["支付方式"] == "信用卡", "fare"].sum(), 1))

st.markdown("# 纽约黄色出租车运营分析大屏")
st.markdown(f'<div class="sub">筛选区间 {d0} 至 {d1} ｜ 行政区 {len(bor_sel)} 个 ｜ '
            f'支付方式 {len(pay_sel)} 类 ｜ 机场行程：{air_sel}</div>',
            unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
kpi_card(c1, "行程量", f"{trips/1e6:.2f} 百万", "筛选口径合计")
kpi_card(c2, "总收入", f"${revenue/1e6:.1f} 百万", f"车费 ${fare/1e6:.1f} 百万")
kpi_card(c3, "单均收入", f"${revenue/max(trips,1):.2f}", "含税费与小费")
kpi_card(c4, "信用卡占比", f"{card/max(trips,1)*100:.1f}%", f"卡付小费率 {card_tip_rate*100:.1f}%")
kpi_card(c5, "机场相关占比",
         f"{df.loc[df['机场']=='机场相关','trips'].sum()/max(trips,1)*100:.1f}%", "按计价代码/区域识别")
kpi_card(c6, "平均里程",
         f"{float((df['distance'].sum())/max(trips,1)):.2f} 英里", "全口径平均")

# ---------- 日趋势 + 支付结构 ----------
left, right = st.columns([2.05, 1])
trend = df.groupby("date", as_index=False).agg(trips=("trips", "sum"), revenue=("revenue", "sum"))
trend["ma7"] = trend["trips"].rolling(7, min_periods=3).mean()
trend["收入(百万美元)"] = trend["revenue"] / 1e6
fig = go.Figure()
fig.add_trace(go.Bar(x=trend["date"], y=trend["trips"], name="日行程量",
                     marker_color="#D6E2EC", hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f} 次<extra></extra>"))
fig.add_trace(go.Scatter(x=trend["date"], y=trend["ma7"], name="7 日移动平均",
                         line=dict(color=COLORS["primary"], width=2.2),
                         hovertemplate="%{x|%Y-%m-%d}<br>MA7 %{y:,.0f}<extra></extra>"))
flag = ad[ad["flag"] & ad["date"].between(pd.Timestamp(d0), pd.Timestamp(d1))]
fig.add_trace(go.Scatter(x=flag["date"], y=flag["trips"], mode="markers", name="异常日",
                         marker=dict(color=COLORS["danger"], size=9, symbol="x"),
                         hovertemplate="异常日 %{x|%m-%d}<br>%{y:,.0f} 次<extra></extra>"))
style(fig, 330)
fig.update_layout(title="日行程量趋势与异常日", barmode="overlay")
left.plotly_chart(fig, width="stretch")

payg = df.groupby("支付方式", as_index=False)["trips"].sum().sort_values("trips", ascending=False)
figp = px.pie(payg, names="支付方式", values="trips", hole=0.62,
              color="支付方式", color_discrete_sequence=[COLORS["primary"], COLORS["accent"],
                                                        COLORS["secondary"], COLORS["gray"],
                                                        COLORS["purple"]])
figp.update_traces(textinfo="percent", textposition="inside", hovertemplate="%{label}<br>%{value:,.0f} 次<extra></extra>")
style(figp, 330)
figp.update_layout(title="支付方式结构", showlegend=True, legend=dict(orientation="v", x=1.0, y=1.0))
right.plotly_chart(figp, width="stretch")

# ---------- 时段热力 + 区域气泡地图 ----------
left, right = st.columns([1.5, 1])
dh = dhb[(dhb["date"].between(pd.Timestamp(d0), pd.Timestamp(d1)))
         & dhb["行政区"].isin(bor_sel)].copy()
dh["weekday"] = dh["date"].dt.dayofweek
dh["weekday_cn"] = dh["weekday"].map({0: "周一", 1: "周二", 2: "周三", 3: "周四",
                                      4: "周五", 5: "周六", 6: "周日"})
days = dh.groupby("weekday")["date"].nunique()
mat = dh.groupby(["weekday_cn", "hour"], as_index=False)["trips"].sum()
mat["日均"] = mat.apply(lambda r: r["trips"] / max(days.get(
    {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}[r["weekday_cn"]], 1), 1),
    axis=1) / 1000
mat = mat.pivot(index="weekday_cn", columns="hour", values="日均").reindex(
    ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][::-1])
fig = go.Figure(go.Heatmap(z=mat.values, x=mat.columns, y=mat.index,
                           colorscale="YlGnBu",
                           colorbar=dict(title="千次/日"),
                           hovertemplate="%{y} %{x} 时<br>%{z:.2f} 千次/日<extra></extra>"))
style(fig, 360, legend_top=False)
fig.update_layout(title="星期 × 小时 平均行程量（按区域筛选）")
fig.update_xaxes(title="小时", dtick=2)
left.plotly_chart(fig, width="stretch")

zone_agg = df.groupby("PULocationID", as_index=False).agg(
    trips=("trips", "sum"), revenue=("revenue", "sum"), fare=("fare", "sum"))
zone_agg = zone_agg.merge(zd[["LocationID", "Zone", "Borough", "lat", "lng"]],
                          left_on="PULocationID", right_on="LocationID", how="left")
zone_agg = zone_agg.merge(zc[["PULocationID", "cluster_name"]], on="PULocationID", how="left")
zone_agg["平均车费"] = zone_agg["revenue"] / zone_agg["trips"]
zone_agg["区域"] = zone_agg["Zone"].fillna("未知")
zone_agg["行政区"] = zone_agg["Borough"].map(BOR_CN).fillna("其他")
zone_agg["功能类型"] = zone_agg["cluster_name"].fillna("未聚类")

figm = go.Figure()
for feat in GEO["features"]:
    g = feat["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        ring = poly[0]
        figm.add_trace(go.Scatter(x=[p[0] for p in ring], y=[p[1] for p in ring],
                                  fill="toself", fillcolor="#F4F6F8",
                                  line=dict(color="#D7DFE8", width=0.5),
                                  hoverinfo="skip", showlegend=False))
sizes = 6 + 46 * (zone_agg["trips"] / zone_agg["trips"].max()) ** 0.55
figm.add_trace(go.Scatter(
    x=zone_agg["lng"], y=zone_agg["lat"], mode="markers",
    marker=dict(size=sizes, color=zone_agg["平均车费"], colorscale="YlOrRd",
                cmin=15, cmax=60, showscale=True,
                colorbar=dict(title="平均<br>车费", thickness=10),
                line=dict(color="white", width=0.4), opacity=0.85),
    text=zone_agg["区域"], customdata=np.stack([zone_agg["行政区"], zone_agg["trips"],
                                               zone_agg["revenue"] / 1e6, zone_agg["功能类型"]], axis=-1),
    hovertemplate="<b>%{text}</b>（%{customdata[0]}）<br>行程量 %{customdata[1]:,.0f} 次"
                  "<br>收入 $%{customdata[2]:.2f} 百万<br>类型 %{customdata[3]}<extra></extra>"))
figm.update_layout(template="plotly_white", height=430, showlegend=False,
                   font=dict(family=FONT, size=11), margin=dict(l=4, r=4, t=44, b=4),
                   title=dict(text="区域行程分布（气泡=行程量，颜色=平均车费）", x=0.01, font=dict(size=14)))
for name, x, y in [("曼哈顿", -73.985, 40.775), ("布鲁克林", -73.95, 40.645),
                   ("皇后区", -73.82, 40.72), ("布朗克斯", -73.86, 40.855)]:
    figm.add_annotation(x=x, y=y, text=name, showarrow=False,
                        font=dict(size=10, color="#8D99AE"))
figm.update_xaxes(visible=False, range=[-74.27, -73.68])
figm.update_yaxes(visible=False, range=[40.52, 40.93], scaleanchor="x", scaleratio=1)
right.plotly_chart(figm, width="stretch")

# ---------- Top 区域榜 + 功能类型分布 ----------
left, right = st.columns([1.15, 1])
metric = left.radio("Top 区域排序指标", ["行程量", "收入", "平均车费"], horizontal=True)
top = zone_agg.sort_values({"行程量": "trips", "收入": "revenue", "平均车费": "平均车费"}[metric],
                           ascending=False).head(12).iloc[::-1]
fig = go.Figure(go.Bar(
    x=top[{"行程量": "trips", "收入": "revenue", "平均车费": "平均车费"}[metric]],
    y=[f"{z}" for z in top["区域"]], orientation="h",
    marker_color=COLORS["secondary"],
    text=[f"{v/1e6:.2f}M" if metric == "行程量" else (f"${v/1e6:.1f}M" if metric == "收入" else f"${v:.1f}")
          for v in top[{"行程量": "trips", "收入": "revenue", "平均车费": "平均车费"}[metric]]],
    textposition="outside", cliponaxis=False,
    hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"))
style(fig, 420, legend_top=False)
fig.update_layout(title=f"Top 12 区域（按{metric}）")
left.plotly_chart(fig, width="stretch")

cc = zc.dropna(subset=["lat", "lng"]).copy()
fig = go.Figure()
for name, sub in cc.groupby("cluster_name"):
    fig.add_trace(go.Scatter(
        x=sub["lng"], y=sub["lat"], mode="markers", name=name,
        marker=dict(size=5 + 26 * (sub["trips"] / cc["trips"].max()) ** 0.6,
                    color=CLUSTER_COLOR.get(name, COLORS["gray"]), opacity=0.8,
                    line=dict(color="white", width=0.4)),
        text=sub["Zone"], customdata=np.stack([sub["Borough"], sub["trips"], sub["avg_fare"]], axis=-1),
        hovertemplate="<b>%{text}</b>（%{customdata[0]}）<br>行程 %{customdata[1]:,.0f} 次"
                      "<br>平均车费 $%{customdata[2]:.1f}<extra></extra>"))
style(fig, 420)
fig.update_layout(title="区域功能类型（KMeans，全年口径）")
fig.update_xaxes(visible=False, range=[-74.27, -73.68])
fig.update_yaxes(visible=False, range=[40.52, 40.93], scaleanchor="x", scaleratio=1)
right.plotly_chart(fig, width="stretch")

# ---------- 站点下钻 ----------
st.markdown("### 站点下钻")
names = zone_agg.sort_values("trips", ascending=False)["区域"].drop_duplicates().tolist()
pick = st.selectbox("选择上车站点 / 区域", names, index=0)
row = zone_agg[zone_agg["区域"] == pick].iloc[0]
zsr = zs[zs["Zone"] == pick]
growth = float(zsr["growth_rate"].iloc[0]) * 100 if len(zsr) and pd.notna(zsr["growth_rate"].iloc[0]) else float("nan")
abc = zsr["abc_tier"].iloc[0] if len(zsr) else "—"
d1_, d2_, d3_, d4_, d5_ = st.columns(5)
kpi_card(d1_, "筛选期行程量", f"{row['trips']:,.0f}", pick)
kpi_card(d2_, "筛选期收入", f"${row['revenue']/1e6:.2f} 百万", f"平均车费 ${row['平均车费']:.2f}")
kpi_card(d3_, "下半年环比增速", "—" if pd.isna(growth) else f"{growth:+.1f}%", "相对上半年")
kpi_card(d4_, "ABC 分层", abc, "全年收入累计口径")
kpi_card(d5_, "功能类型", row["功能类型"], row["行政区"])

left, right = st.columns([1.1, 1])
zid = int(row["PULocationID"])
prof = zh[zh["PULocationID"] == zid].sort_values("hour")
if len(prof):
    prof = prof.set_index("hour").reindex(range(24), fill_value=0)
    share = prof["trips"] / max(float(prof["trips"].sum()), 1) * 100
    figz = go.Figure(go.Bar(x=list(range(24)), y=share.values, marker_color=COLORS["primary"],
                            hovertemplate="%{x} 时<br>出发占比 %{y:.1f}%<extra></extra>"))
    style(figz, 300, legend_top=False)
    figz.update_layout(title=f"{pick} 的 24 小时出发结构（全年）")
    figz.update_xaxes(title="小时", dtick=2)
    left.plotly_chart(figz, width="stretch")

dest = od[od["pu_zone"] == pick].sort_values("trips", ascending=False).head(10).iloc[::-1]
if len(dest):
    figd = go.Figure(go.Bar(x=dest["trips"], y=dest["do_zone"], orientation="h",
                            marker_color=COLORS["accent"],
                            text=[f"{v/1e3:.1f}k" for v in dest["trips"]], textposition="outside",
                            cliponaxis=False,
                            hovertemplate="%{y}<br>%{x:,.0f} 次<extra></extra>"))
    style(figd, 300, legend_top=False)
    figd.update_layout(title="Top 10 目的地区域")
    right.plotly_chart(figd, width="stretch")
else:
    right.info("该区域未进入 Top 500 OD 走廊，暂无可展示的目的地排行。")

# ---------- 自动洞察 ----------
st.markdown("### 自动洞察")
hh = df.groupby("hour" if "hour" in df.columns else "PULocationID", as_index=False)["trips"].sum() \
    if "hour" in df.columns else None
dh2 = dhb[(dhb["date"].between(pd.Timestamp(d0), pd.Timestamp(d1))) & dhb["行政区"].isin(bor_sel)]
peak_h = int(dh2.groupby("hour")["trips"].sum().idxmax())
top_share = float(zone_agg.nlargest(1, "trips")["trips"].iloc[0] / max(trips, 1) * 100)
tip_bor = df[df["支付方式"] == "信用卡"].groupby("行政区", as_index=False).agg(
    tip=("tip", "sum"), fare=("fare", "sum"))
tip_bor["小费率"] = tip_bor["tip"] / tip_bor["fare"].replace(0, np.nan)
best_bor = tip_bor.sort_values("小费率", ascending=False).iloc[0]
i1, i2, i3 = st.columns(3)
i1.info(f"**需求峰值**：筛选范围内 {peak_h} 时出发量最高，运力排班应重点覆盖该时段及其前一小时。")
i2.info(f"**区域集中度**：{zone_agg.nlargest(1, 'trips')['区域'].iloc[0]} 占筛选期行程的 "
        f"{top_share:.1f}%，单点故障风险与议价能力同时存在。")
i3.info(f"**小费表现**：{best_bor['行政区']} 的卡付小费率最高（{best_bor['小费率']*100:.1f}%），"
        f"可作为服务标准复制的标杆区域。")

# ---------- 明细表与下载 ----------
st.markdown("### 区域明细表")
det = zone_agg.merge(zs[["PULocationID", "growth_rate", "abc_tier", "revenue_share"]],
                     on="PULocationID", how="left")
det["收入份额"] = det["revenue_share"] * 100
det["环比增速"] = det["growth_rate"] * 100
det = det.sort_values("trips", ascending=False)
show = det[["区域", "行政区", "功能类型", "trips", "revenue", "平均车费", "收入份额", "环比增速", "abc_tier"]]
show.columns = ["区域", "行政区", "功能类型", "行程量", "收入(美元)", "平均车费(美元)",
                "收入份额(%)", "环比增速(%)", "ABC分层"]
show = show.reset_index(drop=True)
st.dataframe(show.style.format({"行程量": "{:,.0f}", "收入(美元)": "${:,.0f}",
                                "平均车费(美元)": "${:.2f}", "收入份额(%)": "{:.2f}",
                                "环比增速(%)": "{:+.1f}"}),
             width="stretch", height=360)
st.download_button("下载筛选结果 CSV", show.to_csv(index=False).encode("utf-8-sig"),
                   file_name="taxi_zone_summary.csv", mime="text/csv")

with st.expander("数据口径与质量说明"):
    st.markdown("""
- 数据源：NYC TLC Yellow Taxi Trip Records 2024（官方公开数据，12 个月度 Parquet）。
- 清洗后 3,919 万条行程（保留率 95.2%），剔除时长 1–240 分钟之外、距离异常、
  金额为负与区域越界记录；重复键仅统计不删除（TLC 无行程唯一编号）。
- 小费率仅对信用卡行程可观测，现金小费不计入小费分析。
- 时段热力图按“日期范围 + 行政区”联动；支付方式与机场筛选作用于其余组件。
- 区域功能类型来自全年 KMeans 聚类（24 小时出发结构 + 周末/机场/卡付特征）。
""")
st.caption("商业数据分析期末大作业 · 数据科学与大数据技术 · 2026")
