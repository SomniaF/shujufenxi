"""第 1 章 维度模型演示：把一张“大宽表”拆成事实表 + 维度表。

教材用 Power BI 的“模型视图”演示星型模型。Power BI 的模型本质是
  事实表（外键 + 度量）  ←  维度表（主键 + 描述属性）
关系方向为“维度表 1 → 事实表 *”，这样既能避免宽表冗余，
又能让同一套度量按任意维度组合下钻。

脚本做三件事：
  1. 从 Excel 的多张表构建 star schema，并做主外键/一致性校验；
  2. 用“事实 join 维度”的方式重算销售额、成本、毛利；
  3. 输出模型图与多维汇总结果。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from 教材src.config import COLORS, save_fig, save_table, yuan
from 教材src.diagram import draw_schema
from 教材src.io_utils import read_excel


def build_star() -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    fact = read_excel("ch01/mall_sales.xlsx", sheet_name="产品销售数据表")
    dim_product = read_excel("ch01/mall_sales.xlsx", sheet_name="产品信息表")
    dim_brand = read_excel("ch01/mall_sales.xlsx", sheet_name="品牌")
    dim_category = read_excel("ch01/mall_sales.xlsx", sheet_name="类别")
    dim_city = read_excel("ch01/mall_sales.xlsx", sheet_name="商铺城市")
    dim_date = read_excel("ch01/mall_sales.xlsx", sheet_name="日期表")

    # 事实表的商品编码是小写，维度表是大写，先统一再关联
    fact["产品编号"] = fact["产品编号"].str.upper()
    dim_product["产品编号"] = dim_product["产品编号"].str.upper()
    fact["订单日期"] = pd.to_datetime(fact["订单日期"])
    dim_date["日期"] = pd.to_datetime(dim_date["日期"])

    dims = {
        "dim_product": dim_product,
        "dim_brand": dim_brand,
        "dim_category": dim_category,
        "dim_city": dim_city,
        "dim_date": dim_date,
    }

    checks = []
    checks.append(("事实表-产品外键", fact["产品编号"].isin(dim_product["产品编号"]).all()))
    checks.append(("事实表-城市外键", fact["商铺城市"].isin(dim_city["商铺城市"]).all()))
    checks.append(("产品-品牌外键", dim_product["品牌名称"].isin(dim_brand["品牌名称"]).all()))
    checks.append(("产品-类别外键", dim_product["产品类别"].isin(dim_category["产品类别"]).all()))
    checks.append(("事实表日期范围", fact["订单日期"].between(dim_date["日期"].min(), dim_date["日期"].max()).all()))
    checks.append(("产品主键唯一", dim_product["产品编号"].is_unique))
    checks.append(("城市主键唯一", dim_city["商铺城市"].is_unique))
    checks.append(("日期主键唯一", dim_date["日期"].is_unique))

    check_df = pd.DataFrame(checks, columns=["校验项", "通过"])
    check_df["说明"] = check_df["通过"].map({True: "通过", False: "存在未匹配值"})
    return fact, dims, check_df


def main() -> None:
    fact, dims, check_df = build_star()
    print("模型校验：")
    print(check_df.to_string(index=False))
    save_table(check_df, "ch01_模型校验")

    star = (
        fact.merge(dims["dim_product"], on="产品编号", suffixes=("", "_产品"))
        .merge(dims["dim_brand"], on="品牌名称", how="left")
        .merge(dims["dim_city"], on="商铺城市", how="left")
        .merge(dims["dim_date"], left_on="订单日期", right_on="日期", how="left")
    )
    star["成本"] = star["采购单价"] * star["销售数量"]
    star["毛利"] = star["销售额"] - star["成本"]

    print(f"\n事实表 {len(fact):,} 行，星型连接后 {len(star):,} 行（未发生行膨胀）")
    print(f"销售额合计 {yuan(star['销售额'].sum())}，毛利合计 {yuan(star['毛利'].sum())}，"
          f"毛利率 {star['毛利'].sum() / star['销售额'].sum():.2%}")

    city_category = star.pivot_table(
        index="商铺城市", columns="产品类别", values="销售额", aggfunc="sum"
    )
    city_category["合计"] = city_category.sum(axis=1)
    city_category = city_category.sort_values("合计", ascending=False)
    save_table(city_category.rename_axis(index="商铺城市"), "ch01_城市类别销售额", index=True)

    brand_year = star.pivot_table(
        index="品牌名称", columns="年度", values="毛利", aggfunc="sum"
    )
    brand_margin = star.groupby("品牌名称").apply(
        lambda x: x["毛利"].sum() / x["销售额"].sum(), include_groups=False
    ).rename("毛利率")
    brand_table = brand_year.join(brand_margin)
    save_table(brand_table.rename_axis(index="品牌"), "ch01_品牌毛利与毛利率", index=True)

    yearly = star.groupby("年度").agg(
        销售额=("销售额", "sum"), 成本=("成本", "sum"), 毛利=("毛利", "sum")
    )
    yearly["毛利率"] = yearly["毛利"] / yearly["销售额"]
    save_table(yearly.rename_axis(index="年度"), "ch01_年度经营汇总", index=True)

    draw_schema(
        nodes={
            "dim_date 日期维": {"xy": (2.0, 5.9), "w": 2.9,
                                "fields": ["日期 (PK)", "年度 / 季度", "月 / 日"]},
            "dim_product 产品维": {"xy": (9.6, 5.9), "w": 3.2,
                                   "fields": ["产品编号 (PK)", "产品名称", "品牌名称 (FK)",
                                              "产品类别 (FK)", "采购单价", "销售单价"]},
            "fact_sales 销售事实": {"xy": (5.8, 3.55), "w": 3.3, "color": "#C0392B",
                                    "fields": ["订单日期 (FK)", "产品编号 (FK)", "商铺城市 (FK)",
                                               "销售数量", "销售单价", "销售额"]},
            "dim_city 城市维": {"xy": (2.0, 1.25), "w": 2.7,
                               "fields": ["城市编码 (PK)", "商铺城市"]},
            "dim_brand 品牌维": {"xy": (9.6, 1.25), "w": 2.7,
                                "fields": ["品牌编号 (PK)", "品牌名称", "所属企业"]},
            "dim_category 类别维": {"xy": (5.8, 0.62), "w": 2.5,
                                   "fields": ["类别编号 (PK)", "产品类别"]},
        },
        edges=[
            ("dim_product 产品维", "fact_sales 销售事实", "1 : *"),
            ("dim_city 城市维", "fact_sales 销售事实", "1 : *"),
            ("dim_date 日期维", "fact_sales 销售事实", "1 : *"),
            ("dim_brand 品牌维", "dim_product 产品维", "1 : *"),
            ("dim_category 类别维", "dim_product 产品维", "1 : *"),
        ],
        title="商场销售的星型模型：一张事实表 + 五个维度表",
        filename="ch01_星型模型",
    )

    # 用维度下钻：城市 × 类别销售额，验证“同一度量可切任意维度”
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    plot_df = city_category.drop(columns="合计").loc[city_category.index]
    bottom = pd.Series(0.0, index=plot_df.index)
    for i, col in enumerate(plot_df.columns):
        ax.bar(plot_df.index, plot_df[col] / 1e4, bottom=bottom / 1e4,
               color=COLORS[i], label=col, width=0.6)
        bottom += plot_df[col]
    ax.set_ylabel("销售额（万元）")
    ax.set_xlabel("商铺城市")
    ax.set_title("星型模型下钻：城市 × 产品类别销售额")
    ax.legend(title="产品类别", ncol=3)
    save_fig(fig, "ch01_城市类别销售构成")


if __name__ == "__main__":
    main()
