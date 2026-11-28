"""项目公共配置：路径、中文字体、配色与图表/表格输出。

教材中的图表大多由 Power BI / Excel 生成，这里统一 matplotlib 风格，
让每份脚本都能独立运行并把结果落到 outputs/ 下。
"""
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"

for _d in (FIG, TAB):
    _d.mkdir(parents=True, exist_ok=True)

# 主色 + 辅助色，够 8 个系列使用
COLORS = [
    "#2E5E8C", "#E08A3C", "#4E9A7A", "#B5525A",
    "#7A6FA8", "#8C7A5E", "#5C8FA8", "#A8A05C",
]
ACCENT = "#C0392B"
GREY = "#8A8F98"

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"],
    "axes.unicode_minus": False,
    "figure.dpi": 110,
    "savefig.dpi": 160,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#C9CDD3",
    "axes.linewidth": 0.9,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": "#E3E6EA",
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 10.5,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.frameon": False,
    "legend.fontsize": 9.5,
})


def save_fig(fig: plt.Figure, name: str, tight: bool = True) -> Path:
    if tight:
        fig.tight_layout()
    path = FIG / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  图 -> outputs/figures/{name}.png")
    return path


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> Path:
    path = TAB / f"{name}.csv"
    df.to_csv(path, index=index, encoding="utf-8-sig")
    print(f"  表 -> outputs/tables/{name}.csv")
    return path


def yuan(x: float) -> str:
    """把金额格式化成中文习惯的万/亿。"""
    if abs(x) >= 1e8:
        return f"{x / 1e8:.2f} 亿元"
    if abs(x) >= 1e4:
        return f"{x / 1e4:.1f} 万元"
    return f"{x:,.0f} 元"
