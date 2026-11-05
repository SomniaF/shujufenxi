# -*- coding: utf-8 -*-
"""02_clean.py —— TLC 2024 数据清洗、派生、区域维度与聚合表导出。

原始数据约 3600 万行，采用按月流式处理：逐月清洗、派生、聚合，
仅保留约 120 万行分层样本用于分布图与模型，避免一次性载入全部数据。
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import shapefile
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform as shp_transform

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (DATA_CLEAN, DATA_RAW, END_DATE, MONTHS, OUT_TAB,
                    RANDOM_SEED, START_DATE)

SAMPLE_PER_MONTH = 100_000
START = pd.Timestamp(START_DATE)
END = pd.Timestamp(END_DATE)

USE_COLS = [
    "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "RatecodeID", "PULocationID",
    "DOLocationID", "payment_type", "fare_amount", "extra", "mta_tax",
    "tip_amount", "tolls_amount", "improvement_surcharge", "total_amount",
    "congestion_surcharge", "Airport_fee",
]


def load_zone_dim() -> pd.DataFrame:
    lookup = pd.read_csv(DATA_RAW / "taxi_zone_lookup.csv")
    lookup = lookup[lookup["LocationID"].between(1, 263)].copy()
    lookup["LocationID"] = lookup["LocationID"].astype("int16")

    shp_dir = DATA_CLEAN / "_shp"
    shp_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DATA_RAW / "taxi_zones.zip") as zf:
        zf.extractall(shp_dir)
    shp_path = next(shp_dir.rglob("*.shp"))
    reader = shapefile.Reader(str(shp_path))
    fields = [f[0] for f in reader.fields[1:]]
    to_wgs = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)

    rows, features = [], []
    for sr in reader.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        loc = int(rec.get("LocationID", 0))
        if not 1 <= loc <= 263:
            continue
        geom = shape(sr.shape.__geo_interface__)
        geom = shp_transform(to_wgs.transform, geom)
        if geom.is_empty:
            continue
        pt = geom.representative_point()
        rows.append({"LocationID": loc, "lat": pt.y, "lng": pt.x})
        simple = geom.simplify(0.0003, preserve_topology=True)
        features.append({
            "type": "Feature",
            "properties": {"LocationID": loc,
                           "Zone": rec.get("zone", ""),
                           "Borough": rec.get("borough", "")},
            "geometry": mapping(simple),
        })
    centroids = pd.DataFrame(rows)
    dim = lookup.merge(centroids, on="LocationID", how="left")
    dim.to_csv(OUT_TAB / "zone_dim.csv", index=False, encoding="utf-8-sig")
    (OUT_TAB / "zone_boundaries.json").write_text(
        json.dumps({"type": "FeatureCollection", "features": features},
                   ensure_ascii=False), encoding="utf-8")
    print(f"[维度] 区域 {len(dim)} 个，边界 {len(features)} 个，经纬度缺失 {int(dim['lat'].isna().sum())} 个")
    return dim


def derive(df: pd.DataFrame, zone_dim: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pickup"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["dropoff"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    df["duration_min"] = (df["dropoff"] - df["pickup"]).dt.total_seconds() / 60.0
    df["date"] = df["pickup"].dt.normalize()
    df["month"] = df["pickup"].dt.month.astype("int8")
    df["weekday"] = df["pickup"].dt.weekday.astype("int8")
    df["hour"] = df["pickup"].dt.hour.astype("int8")
    df["is_weekend"] = df["weekday"] >= 5
    weekday = ~df["is_weekend"]
    df["is_rush"] = (weekday & df["hour"].between(7, 9)) | (weekday & df["hour"].between(16, 19))
    df["time_band"] = np.select(
        [df["hour"].between(0, 5), df["hour"].between(6, 9),
         df["hour"].between(10, 15), df["hour"].between(16, 19)],
        ["深夜", "早高峰", "日间平峰", "晚高峰"], default="夜间")

    rate = pd.to_numeric(df["RatecodeID"], errors="coerce").fillna(99).astype("int16")
    pay = pd.to_numeric(df["payment_type"], errors="coerce").fillna(0).astype("int16")
    pu = pd.to_numeric(df["PULocationID"], errors="coerce").fillna(0).astype("int16")
    do = pd.to_numeric(df["DOLocationID"], errors="coerce").fillna(0).astype("int16")
    df["RatecodeID"], df["payment_type"] = rate, pay
    df["PULocationID"], df["DOLocationID"] = pu, do

    df["distance_mi"] = pd.to_numeric(df["trip_distance"], errors="coerce")
    df["fare"] = pd.to_numeric(df["fare_amount"], errors="coerce")
    df["tip"] = pd.to_numeric(df["tip_amount"], errors="coerce")
    df["tolls"] = pd.to_numeric(df["tolls_amount"], errors="coerce").fillna(0)
    df["total"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df["congestion"] = pd.to_numeric(df["congestion_surcharge"], errors="coerce").fillna(0)
    df["airport_fee"] = pd.to_numeric(df["Airport_fee"], errors="coerce").fillna(0)
    duration_safe = df["duration_min"].where(df["duration_min"] > 0)
    df["speed_mph"] = df["distance_mi"] / (duration_safe / 60.0)

    df["is_card"] = pay == 1
    df["airport"] = rate.isin([2, 3]) | pu.isin([1, 132, 138]) | do.isin([1, 132, 138])
    zmap = zone_dim.set_index("LocationID")
    df["zone_pu"] = pu.map(zmap["Zone"])
    df["borough_pu"] = pu.map(zmap["Borough"])
    df["zone_do"] = do.map(zmap["Zone"])
    df["borough_do"] = do.map(zmap["Borough"])
    df["passenger_count"] = pd.to_numeric(df["passenger_count"], errors="coerce")

    tip_rate = df["tip"] / df["fare"].where(df["fare"] > 0)
    df["tip_rate"] = tip_rate.where(df["is_card"]).clip(lower=0, upper=1)
    df["generous"] = df["tip_rate"] >= 0.25
    df["half"] = np.where(df["date"] < pd.Timestamp("2024-07-01"), "H1", "H2")
    return df


def main() -> int:
    zone_dim = load_zone_dim()
    zone_ids = set(zone_dim["LocationID"].astype(int))

    sample_parts, daily_parts, dzp_parts, dh_parts, dhb_parts = [], [], [], [], []
    zh_parts, od_parts, pay_parts, rate_parts, bor_parts = [], [], [], [], []
    tip_hour_parts, tip_bh_parts, tip_air_parts, month_audit = [], [], [], []
    missing = {"passenger_count": 0, "RatecodeID": 0, "congestion_surcharge": 0,
               "Airport_fee": 0}
    totals = {"raw": 0, "in_year": 0, "core": 0, "out_of_year": 0,
              "bad_duration": 0, "bad_distance": 0, "negative_amount": 0,
              "bad_zone": 0, "duplicate_key": 0, "speed_over_60": 0}

    for month in MONTHS:
        path = DATA_RAW / f"yellow_tripdata_{month}.parquet"
        df = pd.read_parquet(path, columns=USE_COLS)
        raw_n = len(df)
        totals["raw"] += raw_n
        for col in missing:
            missing[col] += int(df[col].isna().sum())

        df = derive(df, zone_dim)
        in_year = df["pickup"].between(START, END, inclusive="left")
        totals["out_of_year"] += int((~in_year).sum())
        df = df.loc[in_year].copy()
        totals["in_year"] += len(df)

        bad_dur = ~df["duration_min"].between(1, 240)
        bad_dist = ~df["distance_mi"].between(0.01, 100)
        bad_amt = (df["fare"] < 0) | (df["total"] < 0)
        bad_zone = ~(df["PULocationID"].isin(zone_ids) & df["DOLocationID"].isin(zone_ids))
        dup = df.duplicated(subset=["tpep_pickup_datetime", "tpep_dropoff_datetime",
                                     "PULocationID", "DOLocationID", "total_amount"])
        totals["bad_duration"] += int(bad_dur.sum())
        totals["bad_distance"] += int(bad_dist.sum())
        totals["negative_amount"] += int(bad_amt.sum())
        totals["bad_zone"] += int(bad_zone.sum())
        totals["duplicate_key"] += int(dup.sum())

        keep = ~(bad_dur | bad_dist | bad_amt | bad_zone)
        df = df.loc[keep].copy()
        totals["core"] += len(df)
        totals["speed_over_60"] += int((df["speed_mph"] > 60).sum())

        sample_cols = ["pickup", "date", "month", "weekday", "hour", "is_weekend",
                       "is_rush", "time_band", "duration_min", "distance_mi", "speed_mph",
                       "passenger_count", "VendorID", "fare", "tip", "tolls", "total",
                       "congestion", "airport_fee", "tip_rate", "generous", "is_card",
                       "airport", "payment_type", "RatecodeID", "PULocationID",
                       "DOLocationID", "zone_pu", "borough_pu", "zone_do", "borough_do"]
        n = min(SAMPLE_PER_MONTH, len(df))
        sample_parts.append(df.sample(n=n, random_state=RANDOM_SEED + int(month[-2:]))[sample_cols])
        daily_parts.append(df.groupby("date", observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), fare=("fare", "sum"),
            tip=("tip", "sum"), tolls=("tolls", "sum"), distance=("distance_mi", "sum"),
            duration=("duration_min", "sum"), card_trips=("is_card", "sum"),
            airport_trips=("airport", "sum"), passengers=("passenger_count", "sum")))
        dzp_parts.append(df.groupby(["date", "PULocationID", "borough_pu", "payment_type", "airport"],
                                    observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), fare=("fare", "sum"),
            tip=("tip", "sum"), distance=("distance_mi", "sum"),
            duration=("duration_min", "sum"), card_trips=("is_card", "sum")))
        dh_parts.append(df.groupby(["date", "hour"], observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"),
            card_trips=("is_card", "sum"), airport_trips=("airport", "sum")))
        dhb_parts.append(df.groupby(["date", "hour", "borough_pu"], observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), tip=("tip", "sum")))
        zh_parts.append(df.groupby(["PULocationID", "hour"], observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), tip=("tip", "sum"),
            card_trips=("is_card", "sum"), airport_trips=("airport", "sum"),
            distance=("distance_mi", "sum"), duration=("duration_min", "sum")))
        od_parts.append(df.groupby(["PULocationID", "DOLocationID"], observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), fare=("fare", "sum"),
            distance=("distance_mi", "sum"), duration=("duration_min", "sum")))
        pay_parts.append(df.groupby("payment_type", observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), tip=("tip", "sum"),
            fare=("fare", "sum"), card_trips=("is_card", "sum")))
        rate_parts.append(df.groupby("RatecodeID", observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), tip=("tip", "sum"),
            fare=("fare", "sum")))
        bor_parts.append(df.groupby("borough_pu", observed=True).agg(
            trips=("pickup", "size"), revenue=("total", "sum"), tip=("tip", "sum"),
            fare=("fare", "sum"), distance=("distance_mi", "sum"),
            duration=("duration_min", "sum"), card_trips=("is_card", "sum"),
            airport_trips=("airport", "sum")))

        card = df.loc[df["is_card"] & df["tip_rate"].notna()]
        tip_hour_parts.append(card.groupby("hour", observed=True).agg(
            n=("tip_rate", "size"), rate_sum=("tip_rate", "sum"),
            gen=("generous", "sum"), tip=("tip", "sum"), fare=("fare", "sum")))
        tip_bh_parts.append(card.groupby(["borough_pu", "hour"], observed=True).agg(
            n=("tip_rate", "size"), rate_sum=("tip_rate", "sum"), gen=("generous", "sum")))
        tip_air_parts.append(card.groupby("airport", observed=True).agg(
            n=("tip_rate", "size"), rate_sum=("tip_rate", "sum"),
            gen=("generous", "sum"), tip=("tip", "sum"), fare=("fare", "sum")))

        month_audit.append({"month": month, "raw_rows": raw_n,
                            "in_year_rows": int(in_year.sum()), "core_rows": len(df),
                            "card_share": round(float(df["is_card"].mean()), 4),
                            "airport_share": round(float(df["airport"].mean()), 4),
                            "avg_duration_min": round(float(df["duration_min"].mean()), 2),
                            "avg_distance_mi": round(float(df["distance_mi"].mean()), 2)})
        print(f"[清洗] {month}: 原始 {raw_n:,} -> 年内 {int(in_year.sum()):,} -> 核心 {len(df):,}")

    def cat(parts):
        return pd.concat([p.reset_index() for p in parts], ignore_index=True) if parts else pd.DataFrame()

    sample = pd.concat(sample_parts, ignore_index=True)
    sample.to_parquet(DATA_CLEAN / "trips_sample.parquet", index=False)

    daily = cat(daily_parts).groupby("date", as_index=False).sum(numeric_only=True)
    dzp = cat(dzp_parts)
    dzp["date"] = pd.to_datetime(dzp["date"])
    dh = cat(dh_parts).groupby(["date", "hour"], as_index=False).sum(numeric_only=True)
    dhb = cat(dhb_parts).groupby(["date", "hour", "borough_pu"], as_index=False).sum(numeric_only=True)
    zh = cat(zh_parts).groupby(["PULocationID", "hour"], as_index=False).sum(numeric_only=True)
    od = cat(od_parts).groupby(["PULocationID", "DOLocationID"], as_index=False).sum(numeric_only=True)
    pay = cat(pay_parts).groupby("payment_type", as_index=False).sum(numeric_only=True)
    rate = cat(rate_parts).groupby("RatecodeID", as_index=False).sum(numeric_only=True)
    bor = cat(bor_parts).groupby("borough_pu", as_index=False).sum(numeric_only=True)

    daily["date"] = pd.to_datetime(daily["date"])
    daily["avg_speed"] = daily["distance"] / (daily["duration"] / 60.0)
    daily["avg_fare"] = daily["revenue"] / daily["trips"]
    zones_by_day = dzp.groupby("date")["PULocationID"].nunique()
    daily["active_zones"] = daily["date"].map(zones_by_day)
    daily["month"] = daily["date"].dt.month
    daily["weekday"] = daily["date"].dt.weekday

    monthly = daily.groupby("month", as_index=False).agg(
        trips=("trips", "sum"), revenue=("revenue", "sum"), tip=("tip", "sum"),
        distance=("distance", "sum"), duration=("duration", "sum"),
        card_trips=("card_trips", "sum"), airport_trips=("airport_trips", "sum"),
        active_days=("date", "nunique"))
    monthly["avg_fare"] = monthly["revenue"] / monthly["trips"]
    monthly["avg_distance"] = monthly["distance"] / monthly["trips"]
    monthly["tip_share"] = monthly["tip"] / monthly["revenue"]

    zdim = zone_dim[["LocationID", "Borough", "Zone", "service_zone", "lat", "lng"]]
    zs = zh.groupby("PULocationID", as_index=False).sum(numeric_only=True)
    zs = zs.merge(zdim, left_on="PULocationID", right_on="LocationID", how="left")
    zs["avg_fare"] = zs["revenue"] / zs["trips"]
    zs["avg_distance"] = zs["distance"] / zs["trips"]
    zs["avg_duration"] = zs["duration"] / zs["trips"]
    zs["card_share"] = zs["card_trips"] / zs["trips"]
    zs["airport_share"] = zs["airport_trips"] / zs["trips"]

    cutoff = pd.Timestamp("2024-07-01")
    h1 = dzp.loc[dzp["date"] < cutoff].groupby("PULocationID")["trips"].sum()
    h2 = dzp.loc[dzp["date"] >= cutoff].groupby("PULocationID")["trips"].sum()
    zs["h1_trips"] = zs["PULocationID"].map(h1).fillna(0)
    zs["h2_trips"] = zs["PULocationID"].map(h2).fillna(0)
    zs["growth_rate"] = (zs["h2_trips"] - zs["h1_trips"]) / zs["h1_trips"].replace(0, np.nan)

    zs["revenue_share"] = zs["revenue"] / zs["revenue"].sum()
    zs["trip_share"] = zs["trips"] / zs["trips"].sum()
    zs = zs.sort_values("revenue", ascending=False).reset_index(drop=True)
    zs["cum_revenue_share"] = zs["revenue_share"].cumsum()
    zs["abc_tier"] = np.where(zs["cum_revenue_share"] <= 0.70, "A",
                              np.where(zs["cum_revenue_share"] <= 0.90, "B", "C"))
    zs.to_csv(OUT_TAB / "zone_stats.csv", index=False, encoding="utf-8-sig")

    od = od.sort_values("trips", ascending=False).head(500).reset_index(drop=True)
    od = od.merge(zdim[["LocationID", "Zone", "Borough"]], left_on="PULocationID",
                  right_on="LocationID", how="left").rename(
        columns={"Zone": "pu_zone", "Borough": "pu_borough"}).drop(columns="LocationID")
    od = od.merge(zdim[["LocationID", "Zone", "Borough"]], left_on="DOLocationID",
                  right_on="LocationID", how="left").rename(
        columns={"Zone": "do_zone", "Borough": "do_borough"}).drop(columns="LocationID")
    od["avg_fare"] = od["revenue"] / od["trips"]
    od["avg_distance"] = od["distance"] / od["trips"]
    od["avg_duration"] = od["duration"] / od["trips"]
    od.to_csv(OUT_TAB / "od_pairs.csv", index=False, encoding="utf-8-sig")

    pay["share"] = pay["trips"] / pay["trips"].sum()
    pay["avg_tip"] = pay["tip"] / pay["trips"]
    pay["name"] = pay["payment_type"].map(lambda x: {1: "信用卡", 2: "现金", 3: "免收费",
                                                     4: "争议", 5: "未知", 6: "作废",
                                                     0: "未知/弹性计价"}.get(int(x), f"类型{int(x)}"))
    pay.to_csv(OUT_TAB / "payment_stats.csv", index=False, encoding="utf-8-sig")

    rate["name"] = rate["RatecodeID"].map(lambda x: {1: "标准计价", 2: "JFK机场", 3: "纽瓦克机场",
                                                     4: "纳苏/韦郡", 5: "协商价", 6: "团体价",
                                                     99: "未知"}.get(int(x), f"类型{int(x)}"))
    rate["share"] = rate["trips"] / rate["trips"].sum()
    rate.to_csv(OUT_TAB / "ratecode_stats.csv", index=False, encoding="utf-8-sig")

    bor["avg_fare"] = bor["revenue"] / bor["trips"]
    bor["avg_distance"] = bor["distance"] / bor["trips"]
    bor["avg_duration"] = bor["duration"] / bor["trips"]
    bor["card_share"] = bor["card_trips"] / bor["trips"]
    bor["airport_share"] = bor["airport_trips"] / bor["trips"]
    bor["share"] = bor["trips"] / bor["trips"].sum()
    bor.to_csv(OUT_TAB / "borough_stats.csv", index=False, encoding="utf-8-sig")

    th = cat(tip_hour_parts).groupby("hour", as_index=False).sum(numeric_only=True)
    th["mean_tip_rate"] = th["rate_sum"] / th["n"]
    th["generous_share"] = th["gen"] / th["n"]
    th["avg_tip"] = th["tip"] / th["n"]
    th["avg_fare"] = th["fare"] / th["n"]
    th.to_csv(OUT_TAB / "tip_hour.csv", index=False, encoding="utf-8-sig")

    tbh = cat(tip_bh_parts).groupby(["borough_pu", "hour"], as_index=False).sum(numeric_only=True)
    tbh["mean_tip_rate"] = tbh["rate_sum"] / tbh["n"]
    tbh["generous_share"] = tbh["gen"] / tbh["n"]
    tbh.to_csv(OUT_TAB / "tip_borough_hour.csv", index=False, encoding="utf-8-sig")

    ta = cat(tip_air_parts).groupby("airport", as_index=False).sum(numeric_only=True)
    ta["mean_tip_rate"] = ta["rate_sum"] / ta["n"]
    ta["generous_share"] = ta["gen"] / ta["n"]
    ta["avg_tip"] = ta["tip"] / ta["n"]
    ta["avg_fare"] = ta["fare"] / ta["n"]
    ta.to_csv(OUT_TAB / "tip_airport.csv", index=False, encoding="utf-8-sig")

    dh["weekday"] = pd.to_datetime(dh["date"]).dt.weekday
    days = dh.groupby("weekday")["date"].nunique()
    havg = dh.groupby(["weekday", "hour"], as_index=False)["trips"].sum()
    havg["avg_trips"] = havg["trips"] / havg["weekday"].map(days)
    havg.to_csv(OUT_TAB / "hourly_avg.csv", index=False, encoding="utf-8-sig")

    daily.to_csv(OUT_TAB / "daily.csv", index=False, encoding="utf-8-sig")
    monthly.to_csv(OUT_TAB / "monthly.csv", index=False, encoding="utf-8-sig")
    dzp.to_parquet(DATA_CLEAN / "daily_zone_payment.parquet", index=False)
    dh.to_parquet(DATA_CLEAN / "daily_hour.parquet", index=False)
    dhb.to_csv(OUT_TAB / "daily_hour_borough.csv", index=False, encoding="utf-8-sig")
    zh.to_csv(OUT_TAB / "zone_hour.csv", index=False, encoding="utf-8-sig")

    audit = {
        "raw_rows": totals["raw"],
        "in_year_rows": totals["in_year"],
        "analysis_rows": totals["core"],
        "retention_rate": round(totals["core"] / max(totals["in_year"], 1), 6),
        "excluded": {k: totals[k] for k in ["out_of_year", "bad_duration", "bad_distance",
                                            "negative_amount", "bad_zone"]},
        "duplicate_key_rows": totals["duplicate_key"],
        "speed_over_60_rows": totals["speed_over_60"],
        "missing_by_field": missing,
        "months": month_audit,
        "rules": [
            "仅保留上车时间位于 2024-01-01 至 2024-12-31 的记录。",
            "行程时长限定 1–240 分钟，距离限定 0.01–100 英里，fare/total 非负。",
            "上下车区域须在 TLC 1–263 号区域内；不删除乘客数缺失记录。",
            "小费率仅对信用卡支付且 fare>0 的行程计算，现金小费不可观测。",
            "重复键按（上下车时间、上下车区域、总金额）识别，仅统计不删除。",
        ],
        "sample_rows": int(len(sample)),
        "note": "TLC 数据无行程唯一编号，无法做严格去重；重复键计数用于质量披露。",
    }
    (OUT_TAB / "clean_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[完成] 样本 {len(sample):,} 行；区域 {len(zs)} 个；OD {len(od)} 对")
    print(f"[留存] 年内 {totals['in_year']:,} -> 分析 {totals['core']:,} "
          f"({audit['retention_rate']*100:.2f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
