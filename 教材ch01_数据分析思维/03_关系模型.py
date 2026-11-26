"""第 1 章 关系模型演示：多张表靠主外键连接，而不是拼成一张宽表。

教材用 Power BI 演示关系型数据模型（并明确不建议用它做关系建模）。
这里用 pandas 的 join 还原同一个银行数据结构：
    district ← clients ← disp → accounts → loans / trans / order
其中 disp 是“客户-账户”的多对多桥接表，贷款挂在账户而不是客户上。
先建立关系，再按业务问题逐层连接，避免宽表带来的重复计数。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from src.config import COLORS, save_fig, save_table, yuan
from src.diagram import draw_schema
from src.io_utils import read_csv


def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")


def load_bank() -> dict:
    tables = {name: read_csv(f"ch01/bank/{name}.csv")
              for name in ["clients", "disp", "accounts", "loans", "card", "district", "order", "trans_sample"]}
    for name in ["loans", "trans_sample"]:
        for col in ["amount", "balance", "payments"]:
            if col in tables[name].columns:
                tables[name][col] = to_num(tables[name][col])
    return tables


def main() -> None:
    t = load_bank()
    clients, disp, accounts = t["clients"], t["disp"], t["accounts"]
    loans, card, district = t["loans"], t["card"], t["district"]
    trans = t["trans_sample"]

    print("各表规模：")
    for name, df in t.items():
        print(f"  {name:<12} {len(df):>8,} 行 × {df.shape[1]} 列")
    print("说明：trans 为 105.6 万行原表的 3 万行随机抽样（2.84%），趋势可用，绝对额需按比例还原。\n")

    # ① 贷款按地区汇总：loans → accounts → district
    loan_district = (
        loans.merge(accounts, on="account_id", how="left")
        .merge(district.rename(columns={"A1": "district_id"}), on="district_id", how="left")
    )
    # ② 客户数按地区：clients → district（一个客户只算一次）
    client_count = (
        clients.merge(disp[["client_id", "account_id"]], on="client_id", how="left")
        .drop_duplicates("client_id")
        .groupby("district_id")["client_id"].nunique()
    )
    district_summary = (
        loan_district.groupby("district_id")
        .agg(贷款笔数=("loan_id", "nunique"), 贷款总额=("amount", "sum"),
             笔均贷款=("amount", "mean"))
        .join(client_count.rename("客户数"))
        .join(district.set_index("A1")[["GDP", "A4", "A11", "A12"]]
              .rename(columns={"A4": "人口", "A11": "平均工资", "A12": "失业率95"}))
    )
    district_summary["人均贷款"] = district_summary["贷款总额"] / district_summary["客户数"]
    district_summary["人均GDP"] = district_summary["GDP"] * 1000 / district_summary["人口"]
    district_summary = district_summary.sort_values("贷款总额", ascending=False)
    save_table(district_summary.head(15), "ch01_区域贷款TOP15", index=True)

    print(f"贷款总额 {yuan(loans['amount'].sum())}，涉及 {loans['account_id'].nunique():,} 个账户、"
          f"{len(district_summary)} 个地区")

    status_map = {"A": "已结清-正常", "B": "已结清-违约", "C": "未结清-正常", "D": "未结清-欠款"}
    status = loans.assign(状态=loans["status"].map(status_map)).groupby("状态").agg(
        笔数=("loan_id", "count"), 金额=("amount", "sum")
    )
    status["金额占比"] = status["金额"] / status["金额"].sum()
    save_table(status.reset_index(), "ch01_贷款状态汇总")
    print("\n贷款状态：")
    print(status.to_string(float_format=lambda v: f"{v:,.3f}"))

    # ③ 客户-账户多对多关系
    multi = disp.groupby("account_id")["client_id"].nunique()
    print(f"\n账户持有人：{(multi > 1).sum():,} 个账户由多人共有，最多 {multi.max()} 人；"
          f"客户人均持有账户 {len(disp) / disp['client_id'].nunique():.2f} 个")
    card_holders = disp[disp["disp_id"].isin(card["disp_id"])]["client_id"].nunique()
    print(f"信用卡：{card['card_id'].nunique():,} 张，持卡客户 {card_holders:,} 人，"
          f"占客户总数 {card_holders / clients['client_id'].nunique():.2%}")

    # ④ 交易：关系表按时间聚合
    trans["date"] = pd.to_datetime(trans["date"])
    trans["月份"] = trans["date"].dt.to_period("M").astype(str)
    monthly = trans.pivot_table(index="月份", columns="type", values="amount", aggfunc="sum").fillna(0)
    save_table(monthly, "ch01_月度交易额_抽样", index=True)
    op = trans.groupby(["type", "operation"])["amount"].agg(["count", "sum"]).reset_index()
    save_table(op, "ch01_交易类型汇总_抽样")

    # 关系模型的价值：事实分开存储，直接按账户连接会产生“扇出”，金额被重复计算
    loan_cnt = loans.groupby("account_id").size()
    trans_cnt = trans.groupby("account_id").size()
    fanout = int(loan_cnt.mul(trans_cnt, fill_value=0).sum())
    print(f"\n若把贷款与交易直接按 account_id 连接，会产生 {fanout:,} 行（扇出），"
          f"而分开聚合再连接只有 {len(loans) + len(trans):,} 行；"
          "扇出后 sum(amount) 会被重复累加，必须先聚合到同一粒度再连接。")

    draw_schema(
        nodes={
            "dim_district 地区": {"xy": (2.1, 6.25), "w": 2.5,
                                  "fields": ["A1 地区编号 (PK)", "GDP / 人口", "平均工资", "失业率"]},
            "clients 客户": {"xy": (2.1, 4.35), "w": 2.5,
                             "fields": ["client_id (PK)", "sex", "birth_date", "district_id (FK)"]},
            "disp 客户-账户": {"xy": (5.3, 4.35), "w": 2.6, "color": "#C0392B",
                               "fields": ["disp_id (PK)", "client_id (FK)", "account_id (FK)", "type"]},
            "accounts 账户": {"xy": (8.15, 4.35), "w": 2.3,
                              "fields": ["account_id (PK)", "district_id (FK)", "frequency", "date"]},
            "loans 贷款": {"xy": (11.05, 6.15), "w": 2.2,
                           "fields": ["loan_id (PK)", "account_id (FK)", "amount", "duration", "status"]},
            "trans 交易": {"xy": (11.05, 3.55), "w": 2.2,
                           "fields": ["trans_id (PK)", "account_id (FK)", "date", "type", "amount"]},
            "order 汇款单": {"xy": (8.15, 1.35), "w": 2.3,
                             "fields": ["order_id (PK)", "account_id (FK)", "bank_to", "amount"]},
            "card 信用卡": {"xy": (5.3, 1.35), "w": 2.3,
                            "fields": ["card_id (PK)", "disp_id (FK)", "issued", "type"]},
        },
        edges=[
            ("dim_district 地区", "clients 客户", "1 : *"),
            ("dim_district 地区", "accounts 账户", "1 : *"),
            ("clients 客户", "disp 客户-账户", "1 : *"),
            ("accounts 账户", "disp 客户-账户", "1 : *"),
            ("accounts 账户", "loans 贷款", "1 : *"),
            ("accounts 账户", "trans 交易", "1 : *"),
            ("accounts 账户", "order 汇款单", "1 : *"),
            ("disp 客户-账户", "card 信用卡", "1 : *"),
        ],
        title="银行数据的关系模型：disp 是客户与账户之间的多对多桥接表",
        filename="ch01_关系模型ER图",
    )

    # 图：贷款总额与人均贷款 Top 10
    top = district_summary.head(10).iloc[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    axes[0].barh(top.index.astype(str), top["贷款总额"] / 1e6, color=COLORS[0])
    axes[0].set_xlabel("贷款总额（百万元）")
    axes[0].set_ylabel("地区编号")
    axes[0].set_title("贷款总额 Top 10 地区")
    axes[1].barh(top.index.astype(str), top["人均贷款"] / 1e3, color=COLORS[1])
    axes[1].set_xlabel("人均贷款（千元）")
    axes[1].set_title("人均贷款 Top 10 地区（除以地区客户数）")
    for ax in axes:
        ax.grid(axis="x")
        ax.grid(axis="y", visible=False)
    save_fig(fig, "ch01_区域贷款对比")

    # 图：贷款状态 + 月度交易额
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    axes[0].bar(status.index, status["笔数"], color=[COLORS[2], "#C0392B", COLORS[0], COLORS[1]], width=0.55)
    for i, (n, v) in enumerate(zip(status["笔数"], status["金额占比"])):
        axes[0].text(i, n + 8, f"{n} 笔\n{v:.1%}", ha="center", fontsize=9)
    axes[0].set_ylabel("贷款笔数")
    axes[0].set_title("贷款状态：违约与欠款占比不低")
    axes[0].set_ylim(0, status["笔数"].max() * 1.28)

    for i, col in enumerate(monthly.columns):
        axes[1].plot(range(len(monthly)), monthly[col] / 1e6, color=COLORS[i], label=f"{col}方")
    step = max(1, len(monthly) // 8)
    axes[1].set_xticks(range(0, len(monthly), step), monthly.index[::step], rotation=30)
    axes[1].set_ylabel("月交易额（百万元，抽样）")
    axes[1].set_title("月度交易额：贷方流入与借方流出")
    axes[1].legend()
    save_fig(fig, "ch01_贷款状态与交易趋势")


if __name__ == "__main__":
    main()
