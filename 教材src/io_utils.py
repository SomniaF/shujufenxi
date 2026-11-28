"""统一读取 教材data/ 下的数据。

教材原始 CSV 为 GBK 编码，项目内已转成 UTF-8-SIG；
脚本只依赖 教材data/ 中的规范化副本，换机器也能直接运行。
"""
import pandas as pd

from .config import DATA


def read_csv(rel: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(DATA / rel, encoding="utf-8-sig", **kwargs)


def read_excel(rel: str, sheet_name=0, **kwargs) -> pd.DataFrame:
    return pd.read_excel(DATA / rel, sheet_name=sheet_name, **kwargs)


def read_excel_raw(rel: str, sheet_name=0):
    """无表头读取，用于教材模板这类带说明行的表。"""
    return pd.read_excel(DATA / rel, sheet_name=sheet_name, header=None)
