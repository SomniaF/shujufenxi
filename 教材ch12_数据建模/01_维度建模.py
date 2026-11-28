"""第 12 章：数据模型与数据建模（维度建模进阶）。

教材第 12 章讲维度建模方法，配套材料是一份零售数据模型白皮书。
这里用商场销售数据把四个关键概念做成可运行代码：
  1. 事实表粒度：先声明“一行代表什么”，再用主键组合验证；
  2. 星型 vs 雪花：产品维拆成 产品 → 品牌 → 类别 三张表，
     同一口径查询结果必须完全一致，只是 join 次数变多；
  3. 缓慢变化维 SCD2：产品调价时保留历史版本（生效/失效日期 + 版本号 + 当前标志），
     事实按订单日期关联到“当时”的价格，而不是今天的价格；
  4. 度量可加性：销售额可加、单价不可加，简单平均单价会偏离加权平均。
SCD2 的两次调价是**演示用模拟变更**（原始数据中单价两年未变），已在输出中标注。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import ACCENT, COLORS, GREY, save_fig, save_table
from src.diagram import draw_schema
from src.io_utils import read_excel

PRICE_CHANGES = [("A001", "2019-06-01", 200), ("B001", "2019-09-01", -150)]


def main() -> None:
    fact = read_excel("ch01/mall_sales.xlsx", sheet_name="产品销售数据表")
    fact.columns = [c.strip() for c in fact.columns]
    fact["产品编号"] = fact["产品编号"].astype(str).str.upper()
    fact["订单日期"] = pd.to_datetime(fact["订单日期"])
    fact["年"] = fact["订单日期"].dt.year
    fact["季度"] = fact["订单日期"].dt.quarter

    # 教材给的是 Excel 宽表，事实和维度字段混在一张表里，先拆出产品维
    products = (fact[["产品编号", "产品名称", "品牌名称", "产品类别"]]
                .drop_duplicates("产品编号")
                .sort_values("产品编号")
                .reset_index(drop=True))
    products["品牌编号"] = "BR-" + products["品牌名称"]
    products["类别编号"] = "CT-" + products["产品类别"]

    # 事实表只保留外键与度量，维度属性从宽表中剥离
    fact_core = fact[["订单日期", "商铺城市", "产品编号", "销售数量", "销售单价", "销售额"]]
    print(f"宽表 {fact.shape[1]} 列 → 事实表 {fact_core.shape[1]} 列"
          f"（3 个外键 + 3 个度量），产品属性拆入 dim_product")

    grain_keys = ["订单日期", "商铺城市", "产品编号"]
    dup = int(fact.duplicated(grain_keys).sum())
    print(f"事实表 {len(fact):,} 行；粒度声明：(订单日期, 商铺城市, 产品编号) 唯一，"
          f"重复 {dup} 行")
    print(f"覆盖 {fact['订单日期'].min():%Y-%m-%d} 至 {fact['订单日期'].max():%Y-%m-%d}，"
          f"{fact['商铺城市'].nunique()} 个城市、{fact['产品编号'].nunique()} 个产品")
    save_table(pd.DataFrame([{
        "字段组合": " + ".join(grain_keys), "行数": len(fact), "重复行数": dup,
        "粒度说明": "一行 = 某城市某产品在某一天的销售记录",
        "校验结论": "通过" if dup == 0 else "不通过",
    }]), "ch12_事实粒度校验")

    # 星型：产品维直接带品牌、类别
    dim_product_star = (products[["产品编号", "产品名称", "品牌名称", "产品类别"]]
                        .drop_duplicates("产品编号"))
    # 雪花：产品维只留品牌/类别编号，名称放到上游维表
    dim_product_snow = products[["产品编号", "产品名称", "品牌编号", "类别编号"]].drop_duplicates("产品编号")
    dim_brand = products[["品牌编号", "品牌名称"]].drop_duplicates("品牌编号")
    dim_category = products[["类别编号", "产品类别"]].drop_duplicates("类别编号")

    star = (fact_core.merge(dim_product_star, on="产品编号")
            .groupby("品牌名称", as_index=False)["销售额"].sum())
    snow = (fact_core.merge(dim_product_snow, on="产品编号")
            .merge(dim_brand, on="品牌编号")
            .groupby("品牌名称", as_index=False)["销售额"].sum())
    compare = star.merge(snow, on="品牌名称", suffixes=("_星型", "_雪花"))
    compare["差异"] = (compare["销售额_星型"] - compare["销售额_雪花"]).abs()
    same = bool((compare["差异"] < 1e-6).all())
    print(f"\n星型查询 {len(star)} 行，雪花查询 {len(snow)} 行，结果一致：{same}")
    print(compare.to_string(index=False))
    save_table(compare.round(2), "ch12_星型与雪花结果对比")

    draw_schema(
        {
            "dim_date": {"xy": (2.2, 4.9), "fields": ["日期键", "年", "季度", "月"]},
            "dim_product": {"xy": (6.0, 4.9), "w": 3.1,
                            "fields": ["产品编号", "产品名称", "品牌名称", "产品类别"]},
            "dim_city": {"xy": (9.6, 4.9), "fields": ["城市键", "商铺城市"]},
            "fact_sales": {"xy": (6.0, 2.0), "w": 3.1, "color": "#C0392B",
                           "fields": ["订单日期（FK）", "产品编号（FK）", "城市（FK）",
                                      "销售数量", "销售单价", "销售额"]},
        },
        [("dim_date", "fact_sales", "1:N"), ("dim_product", "fact_sales", "1:N"),
         ("dim_city", "fact_sales", "1:N")],
        "星型模型：事实表居中，维度各带描述字段（商场销售）",
        "ch12_星型模型_销售",
    )

    draw_schema(
        {
            "dim_product": {"xy": (6.6, 5.15), "w": 3.0,
                            "fields": ["产品编号", "产品名称", "品牌编号（FK）", "类别编号（FK）"]},
            "dim_brand": {"xy": (10.0, 6.35), "w": 2.3, "fields": ["品牌编号", "品牌名称"]},
            "dim_category": {"xy": (10.0, 3.95), "w": 2.3, "fields": ["类别编号", "产品类别"]},
            "fact_sales": {"xy": (6.6, 2.2), "w": 3.0, "color": "#C0392B",
                           "fields": ["订单日期（FK）", "产品编号（FK）", "城市（FK）",
                                      "销售数量", "销售单价", "销售额"]},
        },
        [("dim_product", "fact_sales", "1:N"), ("dim_product", "dim_brand", "N:1"),
         ("dim_product", "dim_category", "N:1")],
        "雪花模型：产品维继续拆成品牌、类别，join 变多但冗余更少",
        "ch12_雪花模型_销售",
    )

    # ---------- SCD2：模拟两次调价 ----------
    base_price = fact.groupby("产品编号")["销售单价"].first()
    start, end = pd.Timestamp("2018-01-01"), fact["订单日期"].max()
    rows = []
    for pid in sorted(fact["产品编号"].unique()):
        versions = [(start, float(base_price[pid]))]
        for pid_c, d, delta in PRICE_CHANGES:
            if pid == pid_c:
                versions.append((pd.Timestamp(d), float(base_price[pid]) + delta))
        for i, (eff, price) in enumerate(versions):
            expired = (versions[i + 1][0] - pd.Timedelta(days=1)) if i + 1 < len(versions) else end
            rows.append({"产品编号": pid, "版本号": i + 1, "生效日期": eff,
                         "失效日期": expired, "版本单价": price,
                         "是否当前": "是" if i == len(versions) - 1 else "否"})
    scd = pd.DataFrame(rows)
    scd = scd.merge(products[["产品编号", "产品名称"]], on="产品编号")
    scd = scd[["产品编号", "产品名称", "版本号", "生效日期", "失效日期", "版本单价", "是否当前"]]
    changed = scd[scd["版本号"] > 1]
    print(f"\nSCD2 拉链表 {len(scd)} 行，{len(changed)} 个产品存在调价版本：")
    print(changed.to_string(index=False))
    save_table(scd.assign(生效日期=scd["生效日期"].dt.strftime("%Y-%m-%d"),
                          失效日期=scd["失效日期"].dt.strftime("%Y-%m-%d")),
               "ch12_SCD2价格拉链", index=False)

    joined = fact_core.merge(scd, on="产品编号")
    joined = joined[(joined["订单日期"] >= joined["生效日期"])
                    & (joined["订单日期"] <= joined["失效日期"])]
    assert len(joined) == len(fact_core), "订单没有唯一匹配到价格版本"
    joined["原单价"] = joined["产品编号"].map(base_price)
    joined["原销售额"] = joined["销售数量"] * joined["原单价"]
    joined["模拟销售额"] = joined["销售数量"] * joined["版本单价"]
    # 对比基准取“原价×数量”，避开源表本身的金额录入误差（第 11 章查出 4 条）
    joined["影响金额"] = joined["模拟销售额"] - joined["原销售额"]
    impact = (joined.groupby("产品编号")
              .agg(订单数=("影响金额", "size"), 受影响订单=("影响金额", lambda s: int((s != 0).sum())),
                   影响金额=("影响金额", "sum"))
              .reset_index())
    impact["影响金额"] = impact["影响金额"].round(0)
    print("\nSCD2 模拟调价对销售额的影响（演示用，非真实变更）：")
    print(impact.to_string(index=False))
    save_table(impact, "ch12_SCD2模拟影响", index=False)

    # ---------- 可加性：单价平均值 ----------
    simple_mean = fact["销售单价"].mean()
    weighted = fact["销售额"].sum() / fact["销售数量"].sum()
    print(f"\n单价简单平均 {simple_mean:.2f} 元，按数量加权 {weighted:.2f} 元，"
          f"相差 {weighted - simple_mean:.2f} 元——单价不可加")
    add_tab = pd.DataFrame([
        {"度量": "销售额", "可加性": "可加", "说明": "可按任意维度求和"},
        {"度量": "销售数量", "可加性": "可加", "说明": "可按任意维度求和"},
        {"度量": "销售单价", "可加性": "不可加", "说明": "简单平均会失真，必须用 销售额/数量"},
        {"度量": "毛利率", "可加性": "不可加", "说明": "需用（销售额−成本）/销售额 重新计算"},
    ])
    save_table(add_tab, "ch12_度量可加性", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    for i, pid in enumerate(["A001", "B001"]):
        sub = scd[scd["产品编号"] == pid]
        xs, ys = [], []
        for _, r in sub.iterrows():
            xs += [r["生效日期"], r["失效日期"]]
            ys += [r["版本单价"], r["版本单价"]]
        ax.step(xs, ys, where="post", color=COLORS[i], lw=2, label=f"{pid} 价格版本")
    ax.set_xlabel("日期")
    ax.set_ylabel("版本单价（元）")
    ax.set_title("SCD2：调价时新增版本，旧版本保留失效日期（模拟示例）")
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
    ax.grid(axis="y")

    ax = axes[1]
    labeled = impact[impact["影响金额"] != 0]
    vals = labeled["影响金额"] / 1e4
    ax.bar(labeled["产品编号"], vals,
           color=[ACCENT if v < 0 else COLORS[0] for v in vals], width=0.34)
    span = float(vals.max() - vals.min())
    ax.set_ylim(float(vals.min()) - 0.16 * span, float(vals.max()) + 0.12 * span)
    for x, v in zip(labeled["产品编号"], vals):
        if v >= 0:
            ax.text(x, v + 0.02 * span, f"{v:+.1f} 万元", ha="center", va="bottom", fontsize=9)
        else:
            ax.text(x, v - 0.02 * span, f"{v:+.1f} 万元", ha="center", va="top", fontsize=9)
    ax.axhline(0, color=GREY, lw=1)
    ax.set_ylabel("销售额影响（万元）")
    ax.set_title("按历史价格重算：调价只影响生效日之后的订单")
    ax.grid(axis="y")
    save_fig(fig, "ch12_SCD2价格版本")


if __name__ == "__main__":
    main()
