# -*- coding: utf-8 -*-
"""项目全局配置：路径、配色、中文字体、业务字典。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEAN = ROOT / "data" / "clean"
OUT_FIG = ROOT / "outputs" / "figures"
OUT_TAB = ROOT / "outputs" / "tables"
OUT_DASH = ROOT / "outputs" / "dashboard"
DOCS = ROOT / "docs"
for _p in (DATA_CLEAN, OUT_FIG, OUT_TAB, OUT_DASH, DOCS):
    _p.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42

# 分析窗口：2024 全年（含 2 月 29 日）
START_DATE = "2024-01-01"
END_DATE = "2025-01-01"
YEAR = 2024

# 原始文件
MONTHS = [f"2024-{m:02d}" for m in range(1, 13)]
TLC_BASE = "https://d37ci6vzurychx.cloudfront.net"
TRIP_URL = TLC_BASE + "/trip-data/yellow_tripdata_{month}.parquet"
ZONE_LOOKUP_URL = TLC_BASE + "/misc/taxi_zone_lookup.csv"
ZONE_SHP_URL = TLC_BASE + "/misc/taxi_zones.zip"
SOURCE_PAGE = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"

# 统一配色：深海蓝 + 青绿 + 暖橙，兼顾色盲友好与印刷对比度
COLORS = {
    "primary": "#1F4E79",
    "secondary": "#2A9D8F",
    "accent": "#F4A261",
    "danger": "#E76F51",
    "gold": "#E9C46A",
    "purple": "#7B61A8",
    "gray": "#8D99AE",
    "light": "#EAF2F8",
    "dark": "#102A43",
}
PALETTE = ["#1F4E79", "#2A9D8F", "#F4A261", "#E76F51", "#E9C46A",
           "#7B61A8", "#8D99AE", "#4C9F70", "#D1495B", "#3E92CC"]
DIVERGING = ["#E76F51", "#F4A261", "#E9C46A", "#8FC0A9", "#2A9D8F", "#1F4E79"]

PAYMENT_CN = {
    1: "信用卡", 2: "现金", 3: "免收费", 4: "争议", 5: "未知", 6: "作废",
    0: "未知/弹性计价",
}
RATECODE_CN = {
    1: "标准计价", 2: "JFK 机场", 3: "纽瓦克机场", 4: "纳苏/韦郡",
    5: "协商价", 6: "团体价", 99: "未知",
}
BOROUGH_CN = {
    "Manhattan": "曼哈顿", "Brooklyn": "布鲁克林", "Queens": "皇后区",
    "Bronx": "布朗克斯", "Staten Island": "斯塔滕岛", "EWR": "纽瓦克机场",
    "Unknown": "未知",
}
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def borough_cn(name: str | None) -> str:
    if not name:
        return "未知"
    return BOROUGH_CN.get(str(name), str(name))


def payment_cn(code) -> str:
    try:
        return PAYMENT_CN.get(int(code), f"类型{int(code)}")
    except (TypeError, ValueError):
        return "未知"


def usd(x: float) -> str:
    return f"${x:,.2f}"


def usd_short(x: float) -> str:
    """把美元金额压缩成中文可读单位。"""
    if abs(x) >= 1e8:
        return f"${x/1e8:.2f}亿"
    if abs(x) >= 1e4:
        return f"${x/1e4:.1f}万"
    if abs(x) >= 1e3:
        return f"${x/1e3:.1f}千"
    return f"${x:.0f}"


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    preferred = ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((f for f in preferred if f in available), "DejaVu Sans")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [chosen, "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 120,
        "savefig.dpi": 200,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#BFC9D4",
        "axes.labelcolor": "#243B53",
        "axes.titlecolor": "#102A43",
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.color": "#486581",
        "ytick.color": "#486581",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.frameon": False,
        "grid.color": "#E4EAF1",
        "grid.linewidth": 0.8,
        "axes.grid": True,
        "axes.axisbelow": True,
        "figure.autolayout": False,
    })
    return plt


def save_fig(fig, filename: str, tight: bool = True):
    from matplotlib import pyplot as plt
    path = OUT_FIG / filename
    fig.savefig(path, dpi=200, bbox_inches="tight" if tight else None, facecolor="white")
    plt.close(fig)
    return path
