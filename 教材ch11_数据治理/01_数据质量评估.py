"""第 11 章：数据质量评估与数据管理能力自评。

教材第 11 章是数据治理（DCMM 国标、数据治理指引），没有配套数据表。
这里把治理落到可执行的 Python 检查上：
  1. 用“完整性、唯一性、有效性、一致性、准确性、及时性”六个维度，
     对项目里真实使用的银行数据（7 张表）和商场销售事实表做体检；
  2. 每个维度按“通过记录数 / 检查记录数”打分，输出 0—100 的得分；
  3. 按 DCMM 的 8 个能力域做 1—5 级课程项目自评，画雷达图。
注意：DCMM 自评是教学用的评分表，不是正式评估结论；正式评估需按 GB/T 36073 执行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from 教材src.config import ACCENT, COLORS, GREY, save_fig, save_table
from 教材src.io_utils import read_csv, read_excel


def main() -> None:
    clients = read_csv("ch01/bank/clients.csv")
    accounts = read_csv("ch01/bank/accounts.csv")
    loans = read_csv("ch01/bank/loans.csv")
    card = read_csv("ch01/bank/card.csv")
    disp = read_csv("ch01/bank/disp.csv")
    district = read_csv("ch01/bank/district.csv")
    order = read_csv("ch01/bank/order.csv")

    fact = read_excel("ch01/mall_sales.xlsx", sheet_name="产品销售数据表")
    fact.columns = [c.strip() for c in fact.columns]
    products = read_excel("ch01/mall_sales.xlsx", sheet_name="产品信息表")
    products.columns = [c.strip() for c in products.columns]

    checks = []

    def add(table, dim, name, total, failed, note=""):
        checks.append({"数据表": table, "维度": dim, "检查项": name,
                       "检查记录数": int(total), "问题记录数": int(failed),
                       "通过率%": round((1 - failed / total) * 100, 2) if total else 100.0,
                       "说明": note})

    # ---------- 完整性 ----------
    for name, d in [("clients", clients), ("accounts", accounts), ("loans", loans),
                    ("card", card), ("disp", disp), ("order", order)]:
        add(f"bank.{name}", "完整性", "空值检查", d.size, int(d.isna().sum().sum()))
    add("mall.产品销售数据表", "完整性", "空值检查", fact.size, int(fact.isna().sum().sum()))

    # ---------- 唯一性 ----------
    pk = {"clients": (clients, "client_id"), "accounts": (accounts, "account_id"),
          "loans": (loans, "loan_id"), "card": (card, "card_id"),
          "disp": (disp, "disp_id"), "order": (order, "order_id")}
    for name, (d, key) in pk.items():
        add(f"bank.{name}", "唯一性", f"主键 {key} 重复", len(d), int(d.duplicated(key).sum()))
    add("mall.产品销售数据表", "唯一性", "整行完全重复", len(fact),
        int(fact.duplicated().sum()))

    # ---------- 有效性 ----------
    status_set = {"A", "B", "C", "D"}
    add("bank.clients", "有效性", "性别取值域 {男, 女}",
        len(clients), int((~clients["sex"].isin(["男", "女"])).sum()))
    add("bank.loans", "有效性", "贷款状态取值域 {A,B,C,D}",
        len(loans), int((~loans["status"].isin(status_set)).sum()))
    add("bank.loans", "有效性", "贷款期限 ∈ {12,24,36,48,60}",
        len(loans), int((~loans["duration"].isin([12, 24, 36, 48, 60])).sum()))
    add("bank.card", "有效性", "卡类型 ∈ {普通卡, 青年卡, 金卡}",
        len(card), int((~card["type"].isin(["普通卡", "青年卡", "金卡"])).sum()))
    add("bank.loans", "有效性", "贷款金额 > 0",
        len(loans), int((loans["amount"] <= 0).sum()))
    add("bank.order", "有效性", "转账金额 > 0",
        len(order), int((order["amount"] <= 0).sum()))
    add("mall.产品销售数据表", "有效性", "销售数量 > 0 且单价 > 0",
        len(fact), int(((fact["销售数量"] <= 0) | (fact["销售单价"] <= 0)).sum()))

    # ---------- 一致性 ----------
    add("bank.loans", "一致性", "account_id 可在 accounts 匹配",
        len(loans), int((~loans["account_id"].isin(accounts["account_id"])).sum()))
    add("bank.card", "一致性", "disp_id 可在 disp 匹配",
        len(card), int((~card["disp_id"].isin(disp["disp_id"])).sum()))
    add("bank.disp", "一致性", "client_id 可在 clients 匹配",
        len(disp), int((~disp["client_id"].isin(clients["client_id"])).sum()))
    add("bank.disp", "一致性", "account_id 可在 accounts 匹配",
        len(disp), int((~disp["account_id"].isin(accounts["account_id"])).sum()))
    add("bank.clients", "一致性", "district_id 可在 district 匹配",
        len(clients), int((~clients["district_id"].isin(district["A1"])).sum()))
    add("bank.order", "一致性", "account_id 可在 accounts 匹配",
        len(order), int((~order["account_id"].isin(accounts["account_id"])).sum()))

    fact_pid = fact["产品编号"].astype(str).str.upper()
    prod_pid = set(products["产品编号"].astype(str).str.upper())
    add("mall.产品销售数据表", "一致性", "产品编号可在产品信息表匹配",
        len(fact), int((~fact_pid.isin(prod_pid)).sum()))

    # ---------- 准确性 ----------
    acct_date = dict(zip(accounts["account_id"], pd.to_datetime(accounts["date"])))
    loan_date = pd.to_datetime(loans["date"])
    add("bank.loans", "准确性", "贷款日期不早于开户日期", len(loans),
        int((loan_date < loans["account_id"].map(acct_date)).sum()))
    add("bank.loans", "准确性", "月供 × 期数 ≥ 贷款本金", len(loans),
        int(((loans["payments"] * loans["duration"] < loans["amount"])).sum()))
    birth = pd.to_datetime(clients["birth_date"])
    add("bank.clients", "准确性", "出生日期在 1900—1998 年之间", len(clients),
        int(((birth < "1900-01-01") | (birth > "1998-12-31")).sum()))
    calc = fact["销售数量"] * fact["销售单价"]
    add("mall.产品销售数据表", "准确性", "销售额 = 数量 × 单价（容差 1 元）",
        len(fact), int((np.abs(fact["销售额"] - calc) > 1).sum()))

    # ---------- 及时性 ----------
    ref_end = pd.Timestamp("1998-12-31")
    latest = loan_date.max()
    add("bank.loans", "及时性", "最新业务日期距参考期末 ≤ 30 天",
        len(loans), 0 if (ref_end - latest).days <= 30 else len(loans),
        note=f"最新 {latest:%Y-%m-%d}，滞后 {(ref_end - latest).days} 天")
    add("bank.card", "及时性", "最新发卡日期距参考期末 ≤ 30 天",
        len(card), len(card) if (ref_end - pd.to_datetime(card["issued"]).max()).days > 30 else 0,
        note=f"最新 {pd.to_datetime(card['issued']).max():%Y-%m-%d}")

    detail = pd.DataFrame(checks)
    print("数据质量检查明细（仅列未满分项）：")
    print(detail[detail["通过率%"] < 100].to_string(index=False))
    save_table(detail, "ch11_数据质量检查明细", index=False)

    score = (detail.groupby("维度", sort=False)
             .apply(lambda g: np.average(g["通过率%"], weights=g["检查记录数"]),
                    include_groups=False)
             .reindex(["完整性", "唯一性", "有效性", "一致性", "准确性", "及时性"]))
    score_tab = pd.DataFrame({
        "维度": score.index,
        "得分": score.round(2),
        "检查项数": detail.groupby("维度", sort=False)["检查项"].count()
        .reindex(score.index).to_numpy(),
        "问题记录数": detail.groupby("维度", sort=False)["问题记录数"].sum()
        .reindex(score.index).to_numpy(),
    })
    score_tab["问题率%"] = (100 - score_tab["得分"]).round(2)
    print("\n六维度得分：")
    print(score_tab.to_string(index=False))
    save_table(score_tab, "ch11_数据质量评分", index=False)

    lowest = detail.loc[detail["通过率%"].idxmin()]
    print(f"\n最低项：{lowest['数据表']} · {lowest['检查项']}，"
          f"通过率 {lowest['通过率%']}%（{lowest['问题记录数']} 条）")

    # ---------- DCMM 8 个能力域自评 ----------
    dcmm = pd.DataFrame({
        "能力域": ["数据战略", "数据治理", "数据架构", "数据应用",
                   "数据安全", "数据质量", "数据标准", "数据生存周期"],
        "自评等级": [2, 2, 3, 3, 2, 4, 3, 2],
        "评分依据": [
            "课程项目有分析目标，但没有正式的数据战略文件",
            "有统一目录与命名规范，缺少治理组织与考核机制",
            "第 1、12 章完成星型模型与维度建模，有总线矩阵",
            "第 2、10 章完成六类分析、分解与预测应用",
            "客户表含出生日期等个人信息，未做脱敏与权限分级",
            "本脚本六维度量化检查，问题可定位到记录",
            "第 13 章建立指标字典与指标树，编码规则可校验",
            "无归档、保留期与销毁流程，历史数据仅本副本",
        ],
    })
    print("\nDCMM 自评（1 初始 / 2 受管理 / 3 稳健 / 4 量化管理 / 5 持续优化）：")
    print(dcmm.to_string(index=False))
    save_table(dcmm, "ch11_DCMM自评", index=False)

    fig = plt.figure(figsize=(13.2, 5.0))
    ax1 = fig.add_subplot(1, 2, 1)
    plot = score_tab.iloc[::-1]
    bars = ax1.barh(plot["维度"], plot["问题率%"],
                    color=[ACCENT if v > 0 else COLORS[0] for v in plot["问题率%"]],
                    height=0.55)
    for bar, rate, sc in zip(bars, plot["问题率%"], plot["得分"]):
        ax1.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                 f"{rate:.2f}%（得分 {sc:.2f}）", va="center", fontsize=8.8)
    ax1.set_xlim(0, max(plot["问题率%"].max() * 1.9, 0.2))
    ax1.set_xlabel("问题记录占比（%，越低越好）")
    ax1.set_title(f"六维度问题率：完整性 {score_tab.loc[score_tab['维度'] == '完整性', '问题率%'].iloc[0]:.2f}%，"
                  "其余维度基本无问题")
    ax1.grid(axis="x")
    ax1.grid(axis="y", visible=False)

    ax2 = fig.add_subplot(1, 2, 2, polar=True)
    labels = dcmm["能力域"].tolist()
    values = dcmm["自评等级"].tolist()
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    ax2.plot(angles + angles[:1], values + values[:1], color=COLORS[0], lw=1.8)
    ax2.fill(angles + angles[:1], values + values[:1], color=COLORS[0], alpha=0.2)
    ax2.set_xticks(angles, labels, fontsize=9)
    ax2.set_ylim(0, 5)
    ax2.set_yticks([1, 2, 3, 4, 5], ["1 初始", "2 受管理", "3 稳健", "4 量化", "5 持续"],
                   fontsize=7)
    ax2.set_title("DCMM 8 个能力域课程项目自评", pad=22)
    save_fig(fig, "ch11_数据质量与DCMM")


if __name__ == "__main__":
    main()
