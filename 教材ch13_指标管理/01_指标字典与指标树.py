"""第 13 章：指标管理（数据标准、指标标准、指标树与指标血缘）。

教材第 13 章给的是三份 Excel 模板：基础数据标准、指标标准、维度定义。
把它们迁移成 Python 后做四件事：
  1. 数据标准体检：编号规则、必填项、编码型标准是否给出代码规则；
  2. 指标标准体检：编号格式、指标类型、派生指标必须写清口径与关联标准；
  3. 维度与值域：维度编码唯一、值域编码唯一；
  4. 指标树/血缘：按“根指标 → 派生指标”组织指标，并用商场数据把口径真正算出来，
     验证派生指标的重算一致性（客单价、单均价、毛利率）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from 教材src.config import ACCENT, COLORS, GREY, save_fig, save_table
from 教材src.io_utils import read_excel

BASE_STD = "ch13/base_data_standard_template.xlsx"
METRIC_STD = "ch13/metric_standard_template.xlsx"


def check_standard(df: pd.DataFrame) -> pd.DataFrame:
    """基础数据标准的逐项体检，返回检查明细。"""
    rows = []
    n = len(df)
    for col in df.columns:
        filled = int(df[col].notna().sum())
        rows.append({"检查项": f"字段填写：{col}", "结果": f"{filled}/{n}",
                     "说明": "已填写" if filled == n else "存在空值"})
    ids = df["标准编号"].astype(str)
    rows.append({"检查项": "标准编号唯一", "结果": "通过" if ids.is_unique else "不通过",
                 "说明": f"{n} 条标准无重复"})
    bad_id = ids[~ids.str.match(r"^[A-Z]{2}\d{6}$")]
    rows.append({"检查项": "标准编号规则（2 位主题码 + 6 位流水）",
                 "结果": "通过" if bad_id.empty else "不通过",
                 "说明": "、".join(bad_id) if not bad_id.empty else "CM000001 符合"})
    code_std = df[df["标准类型"] == "编码型"]
    missing_rule = code_std[code_std["代码规则"].isin(["/", "-"]) | code_std["代码规则"].isna()]
    rows.append({"检查项": "编码型标准必须定义代码规则",
                 "结果": "通过" if missing_rule.empty else "不通过",
                 "说明": ("、".join(missing_rule["标准编号"]) + " 的代码规则为空")
                 if not missing_rule.empty else "已定义"})
    missing_owner = df[df[["管理负责人", "确认情况"]].isna().any(axis=1)]
    rows.append({"检查项": "管理负责人与确认情况必填",
                 "结果": "通过" if missing_owner.empty else "不通过",
                 "说明": ("、".join(missing_owner["标准编号"]) + " 未确认")
                 if not missing_owner.empty else "已确认"})
    return pd.DataFrame(rows)


def check_metrics(m: pd.DataFrame) -> pd.DataFrame:
    """指标标准：逐条核对编号、类型、口径与生效日期。"""
    rows = []
    for _, r in m.iterrows():
        issues = []
        if not pd.Series([r["编号"]]).str.match(r"^DZ-[A-Z]-\d{3}$").iloc[0]:
            issues.append("编号格式不符")
        if r["指标类型"] not in ("根指标", "组合指标", "派生指标"):
            issues.append("指标类型非法")
        if r["指标类型"] == "派生指标":
            if pd.isna(r["指标业务口径"]) or str(r["指标业务口径"]).strip() in ("", "/"):
                issues.append("派生指标缺口径")
            if pd.isna(r["关联标准"]):
                issues.append("派生指标缺关联标准")
        if pd.isna(r["生效时间"]):
            issues.append("缺生效时间")
        dims = [d for d in str(r["维度"]).split(",") if d.strip()]
        rows.append({
            "编号": r["编号"], "中文名称": r["中文名称"], "指标类型": r["指标类型"],
            "关联标准": r["关联标准"], "维度个数": len(dims),
            "维度": "、".join(dims),
            "结论": "通过" if not issues else "；".join(issues),
        })
    return pd.DataFrame(rows)


def check_dimensions(dim: pd.DataFrame, values: pd.DataFrame) -> pd.DataFrame:
    rows = []
    codes = dim["维度编号"].astype(str)
    rows.append({"检查项": "维度编号唯一", "结果": "通过" if codes.is_unique else "不通过",
                 "说明": f"{len(dim)} 个维度"})
    bad = codes[~codes.str.match(r"^PA-\d{3}$")]
    rows.append({"检查项": "维度编号规则（PA-3 位流水）",
                 "结果": "通过" if bad.empty else "不通过",
                 "说明": "、".join(bad) if not bad.empty else "全部符合"})
    dup_val = values.duplicated(["维度编码", "维度值编码"])
    rows.append({"检查项": "同一维度内值域编码唯一",
                 "结果": "通过" if not dup_val.any() else "不通过",
                 "说明": f"{values['维度编码'].nunique()} 个维度、{len(values)} 个值域"})
    bad_val = values["维度值编码"][~values["维度值编码"].astype(str).str.match(r"^\d{2}$")]
    rows.append({"检查项": "值域编码为 2 位数字",
                 "结果": "通过" if bad_val.empty else "不通过",
                 "说明": "、".join(bad_val.astype(str)) if not bad_val.empty else "全部符合"})
    orphan = values[~values["维度编码"].isin(set(codes))]
    rows.append({"检查项": "值域挂靠到已定义维度",
                 "结果": "通过" if orphan.empty else "不通过",
                 "说明": ("值域使用了维度定义中未登记的 " + "、".join(sorted(set(orphan["维度编码"])))
                          + "（维度定义只登记 PA-013 至 PA-016）")
                 if not orphan.empty else "无孤立值域"})
    return pd.DataFrame(rows)


def draw_metric_tree(groups, filename):
    """指标树：根节点 → 分类 → 指标，颜色区分根指标与派生指标。"""
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.axis("off")
    ax.set_xlim(0.5, 11.9)
    ax.set_ylim(0.45, 5.10)

    def box(x, y, w, h, text, color):
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h,
                                   facecolor=color + "18", edgecolor=color, lw=1.2))
        ax.text(x, y, text, ha="center", va="center",
                fontsize=9.5, fontweight="bold", color="#26313D")

    def line(p1, p2):
        ax.plot([p1[0], p1[0]], [p1[1], p2[1]], color=GREY, lw=1.1)
        ax.plot([p1[0], p2[0]], [p2[1], p2[1]], color=GREY, lw=1.1)

    box(6.0, 4.55, 3.0, 0.62, "业务主题：商场销售", COLORS[0])
    n_leaves = sum(len(items) for _, items in groups)
    span, left = 10.2, 1.4
    step = span / n_leaves
    idx = 0
    for gi, (gname, items) in enumerate(groups):
        xs = [left + step * (idx + i) + step / 2 for i in range(len(items))]
        idx += len(items)
        gx = sum(xs) / len(xs)
        gcolor = COLORS[1 + gi]
        box(gx, 3.05, 1.95, 0.52, gname, gcolor)
        line((6.0, 4.24), (gx, 3.31))
        for x, (name, kind, formula) in zip(xs, items):
            color = COLORS[0] if kind == "根指标" else ACCENT
            ax.add_patch(plt.Rectangle((x - 0.75, 1.57), 1.5, 0.96,
                                       facecolor=color + "10", edgecolor=color, lw=1.2))
            ax.text(x, 2.30, name, ha="center", va="center", fontsize=9,
                    fontweight="bold", color="#26313D")
            ax.text(x, 2.06, f"（{kind}）", ha="center", va="center",
                    fontsize=7.2, color=color)
            ax.text(x, 1.79, formula, ha="center", va="center", fontsize=7.2, color="#5B6470")
            line((gx, 2.79), (x, 2.53))

    ax.text(6.0, 0.78, "蓝色＝根指标（可直接汇总，可加）　红色＝派生指标（由根指标运算，不可加）",
            ha="center", fontsize=8.5, color="#5B6470")
    ax.set_title("商场销售指标树：根指标与派生指标分层管理", fontsize=13, fontweight="bold", pad=10)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.02)
    save_fig(fig, filename)


def main() -> None:
    # ---------- 1. 基础数据标准 ----------
    std = read_excel(BASE_STD, sheet_name="客户主题为例", header=1).dropna(how="all")
    std = std[std["标准编号"].notna()].reset_index(drop=True)
    std_check = check_standard(std)
    print("基础数据标准体检：")
    print(std_check.to_string(index=False))
    save_table(std_check, "ch13_数据标准检查", index=False)

    dist = read_excel(BASE_STD, sheet_name="标准分布统计", header=None)
    block = dist.iloc[3:15, 0:16].copy()
    header = [str(c).strip() for c in block.iloc[0]]
    block = block.iloc[1:].copy()
    block.columns = ["标准主题"] + header[1:]
    block = block[block["标准主题"].astype(str).str.strip() != "Grand Total"]
    block = block.drop(columns=[c for c in block.columns if c == "Grand Total"])
    dist = block.reset_index(drop=True)
    dist["标准主题"] = dist["标准主题"].astype(str).str.strip()
    num = dist.drop(columns=["标准主题"]).apply(pd.to_numeric, errors="coerce").fillna(0)
    by_subject = num.sum(axis=1)
    by_dept = num.sum(axis=0)
    total = int(by_subject.sum())
    assert total == int(by_dept.sum()), "主题合计与部门合计不一致"
    print(f"\n标准分布统计：{len(dist)} 个主题、{len(by_dept)} 个归口部门，"
          f"合计 {total} 项，横纵合计一致")
    print(pd.DataFrame({"标准主题": dist["标准主题"], "标准项数": by_subject.astype(int)})
          .sort_values("标准项数", ascending=False).to_string(index=False))

    # ---------- 2. 指标标准 ----------
    metrics = read_excel(METRIC_STD, sheet_name="标准定义", header=1)
    metric_check = check_metrics(metrics)
    print("\n指标标准体检：")
    print(metric_check.to_string(index=False))
    save_table(metric_check, "ch13_指标标准校验", index=False)
    reg = read_excel(METRIC_STD, sheet_name="维度定义", header=0)
    vals = read_excel(METRIC_STD, sheet_name="维度值代码定义", header=0, dtype=str)
    dim_check = check_dimensions(reg, vals)
    print("\n维度与值域体检：")
    print(dim_check.to_string(index=False))
    save_table(dim_check, "ch13_维度与值域校验", index=False)

    # ---------- 3. 指标树与血缘 ----------
    groups = [
        ("规模类", [("销售额", "根指标", "Σ 销售额"), ("销售数量", "根指标", "Σ 销售数量"),
                    ("购买记录数", "根指标", "count(*)")]),
        ("效率与效益类", [("单笔金额", "派生指标", "销售额 ÷ 记录数"),
                          ("单均价", "派生指标", "销售额 ÷ 数量"),
                          ("毛利率", "派生指标", "毛利额 ÷ 销售额")]),
    ]
    draw_metric_tree(groups, "ch13_指标树")
    lineage = pd.DataFrame([
        {"指标": "销售额", "类型": "根指标", "口径": "Σ 销售额", "依赖": "事实表", "可加性": "可加", "单位": "元"},
        {"指标": "销售数量", "类型": "根指标", "口径": "Σ 销售数量", "依赖": "事实表", "可加性": "可加", "单位": "件"},
        {"指标": "购买记录数", "类型": "根指标", "口径": "count(*)，粒度为一次购买记录", "依赖": "事实表", "可加性": "可加", "单位": "次"},
        {"指标": "单笔金额", "类型": "派生指标", "口径": "销售额 ÷ 购买记录数（源表无客户号，近似客单价）", "依赖": "销售额、购买记录数", "可加性": "不可加", "单位": "元/次"},
        {"指标": "单均价", "类型": "派生指标", "口径": "销售额 ÷ 销售数量", "依赖": "销售额、销售数量", "可加性": "不可加", "单位": "元/件"},
        {"指标": "毛利率", "类型": "派生指标", "口径": "（销售额 − 成本）÷ 销售额", "依赖": "销售额、成本", "可加性": "不可加", "单位": "%"},
    ])
    save_table(lineage, "ch13_指标血缘", index=False)

    # ---------- 4. 指标引擎：把口径算出来 ----------
    fact = read_excel("ch01/mall_sales.xlsx", sheet_name="产品销售数据表")
    fact.columns = [c.strip() for c in fact.columns]
    fact["产品编号"] = fact["产品编号"].astype(str).str.upper()
    fact["订单日期"] = pd.to_datetime(fact["订单日期"])
    products = read_excel("ch01/mall_sales.xlsx", sheet_name="产品信息表")
    products.columns = [c.strip() for c in products.columns]
    products["产品编号"] = products["产品编号"].astype(str).str.upper()
    fact = fact.merge(products[["产品编号", "采购单价"]], on="产品编号", how="left")
    fact["成本"] = fact["销售数量"] * fact["采购单价"]
    fact["毛利额"] = fact["销售额"] - fact["成本"]

    def aggregate(df):
        sales = df["销售额"].sum()
        qty = df["销售数量"].sum()
        records = len(df)
        profit = df["毛利额"].sum()
        return pd.Series({"销售额": sales, "销售数量": qty, "购买记录数": records,
                          "单笔金额": sales / records, "单均价": sales / qty,
                          "毛利率": profit / sales})

    overall = aggregate(fact)
    by_year = fact.groupby(fact["订单日期"].dt.year).apply(aggregate, include_groups=False)
    by_city = fact.groupby("商铺城市").apply(aggregate, include_groups=False)
    result = pd.concat([
        pd.DataFrame([{"口径": "整体", **overall.to_dict()}]),
        by_year.reset_index().rename(columns={"订单日期": "口径"}).assign(
            口径=lambda d: d["口径"].astype(str) + " 年"),
        by_city.reset_index().rename(columns={"商铺城市": "口径"}).assign(
            口径=lambda d: "城市：" + d["口径"]),
    ], ignore_index=True)
    result["毛利率"] = result["毛利率"] * 100
    print("\n指标计算结果（节选）：")
    print(result.head(8).round(2).to_string(index=False))
    save_table(result.round(2), "ch13_指标计算结果", index=False)

    # 派生指标不可加：城市之间简单平均 ≠ 按记录数/销售额加权
    city_avg = by_city["单笔金额"].mean()
    city_weighted = (by_city["单笔金额"] * by_city["购买记录数"]).sum() / by_city["购买记录数"].sum()
    margin_simple = by_city["毛利率"].mean()
    print(f"\n单笔金额：城市简单平均 {city_avg:.2f} 元，按记录数加权 {city_weighted:.2f} 元"
          f"（整体 {overall['单笔金额']:.2f} 元）")
    print(f"毛利率：城市简单平均 {margin_simple * 100:.2f}%，"
          f"按销售额重算 {overall['毛利率'] * 100:.2f}%——派生指标不能在城市间直接平均")

    # ---------- 5. 标准分布图 ----------
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.2),
                             gridspec_kw={"width_ratios": [1, 1.15]})
    ax = axes[0]
    s = pd.Series(by_subject.to_numpy(), index=dist["标准主题"]).sort_values()
    ax.barh(s.index, s.to_numpy(), color=COLORS[0], height=0.62)
    for y, v in enumerate(s.to_numpy()):
        ax.text(v + 4, y, f"{int(v)}", va="center", fontsize=8, color="#5B6470")
    ax.set_xlabel("标准项数")
    ax.set_title("按标准主题分布（共 2,011 项）")
    ax.grid(axis="x")

    ax = axes[1]
    d = pd.Series(by_dept.to_numpy(), index=by_dept.index.astype(str)).sort_values()
    ax.barh(d.index, d.to_numpy(), color=COLORS[2], height=0.62)
    for y, v in enumerate(d.to_numpy()):
        ax.text(v + 4, y, f"{int(v)}", va="center", fontsize=8, color="#5B6470")
    ax.set_xlabel("标准项数")
    ax.set_title("按归口管理部门分布")
    ax.grid(axis="x")
    fig.suptitle("数据标准分布：协议、产品、资产是标准最密集的三个主题",
                 fontsize=13, fontweight="bold", y=0.99)
    save_fig(fig, "ch13_标准分布")


if __name__ == "__main__":
    main()
