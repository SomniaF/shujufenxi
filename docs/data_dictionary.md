# 数据字典

本文件说明 `data/clean/trips_sample.parquet` 与 `outputs/tables/` 中常用字段的含义。
原始 Parquet 的字段名以 TLC 2024 年数据页为准；清洗后统一重命名为下表右列。

## 1. 行程级字段（trips_sample.parquet，120 万行样本）

| 原始字段 | 清洗后字段 | 类型 | 说明 |
|---|---|---|---|
| `tpep_pickup_datetime` | `pickup` | datetime | 乘客上车时间（America/New_York，本地时间） |
| `tpep_dropoff_datetime` | `dropoff` | datetime | 乘客下车时间 |
| — | `duration_min` | float | 行程时长（分钟），`(dropoff − pickup)/60` |
| `trip_distance` | `distance_mi` | float | 行程里程（英里） |
| `passenger_count` | `passenger_count` | float | 乘客数，存在缺失，未插补 |
| `RatecodeID` | `RatecodeID` | int16 | 费率代码：1 标准、2 JFK、3 Newark、4 Nassau/Westchester、5 协商价、6 团体价、99 未知 |
| `PULocationID` | `PULocationID` | int16 | 上车出租车分区编号（1–263） |
| `DOLocationID` | `DOLocationID` | int16 | 下车出租车分区编号（1–263） |
| `payment_type` | `payment_type` | int16 | 支付方式：1 信用卡、2 现金、3 免收费、4 争议、5 未知、6 作废、0 未知/弹性 |
| `fare_amount` | `fare` | float | 计价车费（美元） |
| `tip_amount` | `tip` | float | 小费（美元）；现金小费不可观测 |
| `tolls_amount` | `tolls` | float | 路桥费（美元） |
| `congestion_surcharge` | `congestion` | float | 拥堵费（美元） |
| `Airport_fee` | `airport_fee` | float | 机场费（美元） |
| `total_amount` | `total` | float | 总金额（美元） |
| — | `date` | date | 上车日期 |
| — | `month` | int8 | 上车月份（1–12） |
| — | `weekday` | int8 | 星期（0=周一，6=周日） |
| — | `hour` | int8 | 上车小时（0–23） |
| — | `is_weekend` | bool | 是否周六/周日 |
| — | `is_rush` | bool | 是否工作日 7–9 时或 16–19 时 |
| — | `time_band` | category | 深夜（0–5）、早高峰（6–9）、日间平峰（10–15）、晚高峰（16–19）、夜间（20–23） |
| — | `speed_mph` | float | 平均速度（英里/小时），仅时长 > 0 时计算 |
| — | `is_card` | bool | 是否信用卡支付 |
| — | `airport` | bool | 是否机场相关：费率 2/3，或上下车分区属于 1/132/138 |
| — | `tip_rate` | float | 小费率 = 小费 / 车费，仅信用卡且车费 > 0，截断到 [0, 1] |
| — | `generous` | bool | 是否慷慨小费：`tip_rate ≥ 0.25` |
| — | `half` | category | 上半年 H1（1–6 月）或下半年 H2（7–12 月） |
| — | `zone_pu` / `borough_pu` | string | 上车分区名称 / 行政区 |
| — | `zone_do` / `borough_do` | string | 下车分区名称 / 行政区 |

## 2. 聚合表字段

| 文件 | 关键字段 | 说明 |
|---|---|---|
| `daily.csv` | `date`, `trips`, `revenue`, `fare`, `tip`, `distance`, `duration`, `airport_trips` | 按日汇总，收入为 `total_amount` 求和 |
| `monthly.csv` | `month`, `trips`, `revenue`, `avg_fare`, `avg_distance`, `tip_share` | 按月汇总 |
| `daily_hour_borough.csv` | `date`, `hour`, `borough_pu`, `trips`, `revenue`, `tip` | 日 × 小时 × 上车行政区 |
| `zone_stats.csv` | `PULocationID`, `Zone`, `Borough`, `trips`, `revenue`, `avg_fare`, `airport_share`, `abc_tier`, `cluster` | 分区画像与 ABC 分层 |
| `zone_hour.csv` | `PULocationID`, `hour`, `trips`, `revenue`, `tip`, `airport_trips` | 分区 × 小时 |
| `od_pairs.csv` / `od_top20.csv` | `PULocationID`, `DOLocationID`, `trips` | 起讫分区对与 Top 20 走廊 |
| `tip_airport.csv` | `airport`, `n`, `mean_tip_rate`, `generous_share`, `avg_fare` | 机场/非机场小费对比（信用卡行程） |
| `zone_clusters.csv` | `PULocationID`, `cluster`, `cluster_name`, `pca1`, `pca2` | K-Means 结果与 PCA 坐标 |
| `demand_forecast.csv` | `date`, `actual`, `forecast`, `lower`, `upper` | 12 月预测与 95% 置信区间 |
| `tip_roc.csv` | `fpr`, `tpr` | 小费分类模型 ROC 曲线 |

## 3. 口径说明

- 金额单位均为美元；`revenue` 为 `total_amount` 求和，包含车费、小费、路桥费、拥堵费、机场费与税费。
- 小费率仅对信用卡支付且 `fare > 0` 的行程计算；现金小费没有记录，不能视为 0。
- 原始数据无行程唯一编号，无法严格去重；“重复键”仅按（上下车时间、上下车分区、总金额）统计。
- 上车时间限定在 2024-01-01 至 2024-12-31；时长限定 1–240 分钟，里程限定 0.01–100 英里，金额非负，分区限定 1–263。
- 120 万行样本仅用于分布图、散点图与小费模型；总量、收入、分区排名与预测使用全量聚合表。
