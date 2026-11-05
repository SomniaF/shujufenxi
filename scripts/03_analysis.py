# -*- coding: utf-8 -*-
"""03_analysis.py —— 需求预测、区域聚类、小费模型、ABC/BCG 与异常检测。"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, f1_score,
                             precision_score, recall_score, roc_auc_score, roc_curve,
                             silhouette_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.statespace.sarimax import SARIMAX

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_CLEAN, OUT_TAB, RANDOM_SEED

warnings.filterwarnings("ignore")
SEED = RANDOM_SEED
HOLIDAYS = pd.to_datetime([
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-05-27", "2024-06-19",
    "2024-07-04", "2024-09-02", "2024-10-14", "2024-11-11", "2024-11-28",
    "2024-12-25",
])


def dump(obj, name: str):
    (OUT_TAB / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def mape(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    mask = y != 0
    return float(np.mean(np.abs((y[mask] - yhat[mask]) / y[mask])) * 100)


def main() -> int:
    daily = pd.read_csv(OUT_TAB / "daily.csv", parse_dates=["date"]).sort_values("date")
    monthly = pd.read_csv(OUT_TAB / "monthly.csv")
    zs = pd.read_csv(OUT_TAB / "zone_stats.csv")
    zh = pd.read_csv(OUT_TAB / "zone_hour.csv")
    od = pd.read_csv(OUT_TAB / "od_pairs.csv")
    pay = pd.read_csv(OUT_TAB / "payment_stats.csv")
    tip_hour = pd.read_csv(OUT_TAB / "tip_hour.csv")
    havg = pd.read_csv(OUT_TAB / "hourly_avg.csv")
    sample = pd.read_parquet(DATA_CLEAN / "trips_sample.parquet")

    total_trips = float(daily["trips"].sum())
    total_revenue = float(daily["revenue"].sum())
    card_pay = pay.loc[pay["payment_type"] == 1].iloc[0]
    kpi = {
        "total_trips": total_trips,
        "total_revenue": total_revenue,
        "avg_fare": total_revenue / total_trips,
        "avg_distance": float(daily["distance"].sum() / total_trips),
        "avg_duration": float(daily["duration"].sum() / total_trips),
        "card_share": float(daily["card_trips"].sum() / total_trips),
        "airport_share": float(daily["airport_trips"].sum() / total_trips),
        "tip_total": float(daily["tip"].sum()),
        "tip_rate_card": float(card_pay["tip"] / card_pay["fare"]),
        "active_zones": int(zs["PULocationID"].nunique()),
    }

    # ---------- 1. 日需求预测：SARIMAX + 周季节 + 节假日 ----------
    s = daily.set_index("date")["trips"].asfreq("D").astype(float)
    exog = pd.DataFrame(index=s.index)
    exog["holiday"] = exog.index.isin(HOLIDAYS).astype(int)
    exog["thanks_week"] = ((exog.index >= "2024-11-24") &
                           (exog.index <= "2024-11-30")).astype(int)

    # 以 11 月为验证集选择结构，再滚动至 12 月做最终检验，避免用测试月选型
    val_train, val_test = s.loc[:"2024-10-31"], s.loc["2024-11-01":"2024-11-30"]
    cands = [(p, 1, q, P, Q) for p in (1, 2) for q in (1, 2)
             for P, Q in [(1, 1), (1, 0), (0, 1)]]
    val_rows, chosen = [], None
    for p, d, q, P, Q in cands:
        try:
            m = SARIMAX(val_train, exog=exog.loc[val_train.index], order=(p, d, q),
                        seasonal_order=(P, 0, Q, 7), enforce_stationarity=False,
                        enforce_invertibility=False)
            f = m.fit(disp=False, maxiter=120)
            vp = np.asarray(f.get_forecast(
                steps=len(val_test), exog=exog.loc[val_test.index]).predicted_mean)
            vm = mape(val_test.values, vp)
            val_rows.append({"order": str((p, d, q)),
                             "seasonal_order": str((P, 0, Q, 7)),
                             "val_mape": round(vm, 2), "val_aic": round(float(f.aic), 1)})
            if chosen is None or vm < chosen[0]:
                chosen = (vm, (p, d, q), (P, 0, Q, 7))
        except Exception:
            continue
    if chosen is None:
        raise RuntimeError("SARIMAX 拟合失败")
    _, order, sorder = chosen
    pd.DataFrame(val_rows).sort_values("val_mape").to_csv(
        OUT_TAB / "forecast_validation.csv", index=False, encoding="utf-8-sig")

    train, test = s.loc[:"2024-11-30"], s.loc["2024-12-01":]
    mod = SARIMAX(train, exog=exog.loc[train.index], order=order,
                  seasonal_order=sorder, enforce_stationarity=False,
                  enforce_invertibility=False)
    fit = mod.fit(disp=False, maxiter=200)
    fc = fit.get_forecast(steps=len(test), exog=exog.loc[test.index])
    pred = np.asarray(fc.predicted_mean)
    ci = np.asarray(fc.conf_int(alpha=0.05))
    err = test.values - pred
    lb_p = None
    try:
        lb_p = float(acorr_ljungbox(fit.resid, lags=[14], return_df=True)["lb_pvalue"].iloc[0])
    except Exception:
        pass
    fmetrics = {
        "model": "SARIMAX", "order": list(order), "seasonal_order": list(sorder),
        "exog": ["is_holiday", "thanksgiving_week"], "aic": float(fit.aic),
        "train_days": int(len(train)), "test_days": int(len(test)),
        "val_month": "2024-11", "val_mape": float(chosen[0]),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))), "mape": mape(test.values, pred),
        "r2": float(1 - np.sum(err ** 2) / np.sum((test.values - test.mean()) ** 2)),
        "ljung_box_p": lb_p,
        "dec_actual_total": float(test.sum()), "dec_forecast_total": float(pred.sum()),
        "dec_total_error_pct": float((pred.sum() - test.sum()) / test.sum() * 100),
    }
    fdf = pd.DataFrame({"date": test.index, "actual": test.values, "forecast": pred,
                        "lower": np.clip(ci[:, 0], 0, None), "upper": ci[:, 1]})
    fdf.to_csv(OUT_TAB / "demand_forecast.csv", index=False, encoding="utf-8-sig")
    fit_df = pd.DataFrame({"date": train.index, "actual": train.values,
                           "fitted": np.asarray(fit.fittedvalues)}).tail(90)
    fit_df.to_csv(OUT_TAB / "demand_fit.csv", index=False, encoding="utf-8-sig")
    dump(fmetrics, "forecast_metrics.json")
    print(f"[预测] SARIMAX{order}{sorder} 验证 MAPE={chosen[0]:.2f}% "
          f"测试 MAPE={fmetrics['mape']:.2f}% RMSE={fmetrics['rmse']:.0f}")

    # ---------- 2. 区域功能聚类：24 小时出发结构 + 周末/机场/支付特征 ----------
    dzp = pd.read_parquet(DATA_CLEAN / "daily_zone_payment.parquet")
    dzp["weekday"] = pd.to_datetime(dzp["date"]).dt.weekday
    wk = dzp.groupby(["PULocationID", "weekday"])["trips"].sum().unstack(fill_value=0)
    weekend_share = wk[[5, 6]].sum(axis=1) / wk.sum(axis=1)
    pivot = zh.pivot_table(index="PULocationID", columns="hour",
                           values="trips", aggfunc="sum").fillna(0)
    zidx = zs.set_index("PULocationID")
    common = pivot.index.intersection(zidx.index[zidx["trips"] >= 2000])
    shares = pivot.loc[common].div(pivot.loc[common].sum(axis=1), axis=0)
    extra = pd.DataFrame({
        "weekend_share": weekend_share.reindex(common).fillna(0),
        "airport_share": zidx.loc[common, "airport_share"],
        "card_share": zidx.loc[common, "card_share"],
        "log_fare": np.log1p(zidx.loc[common, "avg_fare"]),
    }, index=common)
    features = pd.concat([shares, extra], axis=1)
    features.columns = features.columns.astype(str)
    Z = StandardScaler().fit_transform(features)

    scores, models = {}, {}
    for k in (4, 5, 6):
        km = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(Z)
        scores[k] = float(silhouette_score(Z, km.labels_))
        models[k] = km
    k_best = max(scores, key=scores.get)
    km = models[k_best]
    labels = km.labels_
    pca = PCA(n_components=2, random_state=SEED).fit_transform(Z)

    prof = shares.groupby(labels).mean()
    summ = pd.DataFrame(index=range(k_best))
    summ["n_zones"] = pd.Series(labels).value_counts().sort_index()
    summ["airport_share"] = extra["airport_share"].groupby(labels).mean()
    summ["weekend_share"] = extra["weekend_share"].groupby(labels).mean()
    summ["trips"] = zidx.loc[common, "trips"].groupby(labels).sum()
    summ["revenue"] = zidx.loc[common, "revenue"].groupby(labels).sum()
    summ["trip_share"] = summ["trips"] / total_trips
    peak = prof.idxmax(axis=1)

    names, used = {}, set()
    for c in range(k_best):
        if summ.loc[c, "airport_share"] > 0.25:
            base = "机场枢纽型"
        elif summ.loc[c, "trip_share"] > 0.40:
            base = "核心商业区型"
        elif peak[c] <= 5 or peak[c] >= 22:
            base = "夜间活力型"
        elif 6 <= peak[c] <= 9 and summ.loc[c, "weekend_share"] >= 0.30:
            base = "通勤休闲混合型"
        elif 6 <= peak[c] <= 9:
            base = "早高峰通勤型"
        elif 16 <= peak[c] <= 20:
            base = "晚高峰通勤型"
        else:
            base = "日间综合型"
        name, j = base, 2
        while name in used:
            name, j = f"{base}{j}", j + 1
        names[c] = name
        used.add(name)

    pca_df = pd.DataFrame(pca, index=common, columns=["pca1", "pca2"])
    zc = zs[zs["PULocationID"].isin(common)].copy().merge(
        pca_df, left_on="PULocationID", right_index=True, how="left")
    zc["cluster"] = zc["PULocationID"].map(dict(zip(common, labels))).astype(int)
    zc["cluster_name"] = zc["cluster"].map(names)
    zc.to_csv(OUT_TAB / "zone_clusters.csv", index=False, encoding="utf-8-sig")

    prof_out = prof.copy()
    prof_out.columns = [f"h{int(c)}" for c in prof.columns]
    prof_out.index.name = "cluster"
    prof_out = prof_out.reset_index()
    prof_out["cluster_name"] = prof_out["cluster"].map(names)
    prof_out["n_zones"] = prof_out["cluster"].map(summ["n_zones"])
    prof_out["trips"] = prof_out["cluster"].map(summ["trips"])
    prof_out["revenue"] = prof_out["cluster"].map(summ["revenue"])
    prof_out["airport_share"] = prof_out["cluster"].map(summ["airport_share"])
    prof_out.to_csv(OUT_TAB / "cluster_profiles.csv", index=False, encoding="utf-8-sig")

    clusters = []
    for c in range(k_best):
        sub = zc[zc["cluster"] == c].nlargest(5, "trips")
        clusters.append({
            "cluster": int(c), "name": names[c], "n_zones": int(summ.loc[c, "n_zones"]),
            "trips": float(summ.loc[c, "trips"]), "revenue": float(summ.loc[c, "revenue"]),
            "trip_share": float(summ.loc[c, "trips"] / total_trips),
            "revenue_share": float(summ.loc[c, "revenue"] / total_revenue),
            "airport_share": float(summ.loc[c, "airport_share"]),
            "weekend_share": float(summ.loc[c, "weekend_share"]),
            "peak_hour": int(peak[c]),
            "top_zones": [f"{r['Zone']}（{r['Borough']}）" for _, r in sub.iterrows()],
        })
    dump({"k": int(k_best), "silhouette": scores[k_best],
          "silhouette_by_k": scores, "clusters": clusters}, "cluster_summary.json")
    print(f"[聚类] k={k_best} 轮廓系数={scores[k_best]:.3f}；{['%s:%d' % (names[c], summ.loc[c,'n_zones']) for c in range(k_best)]}")

    # ---------- 3. 小费行为模型：信用卡行程是否慷慨给小费 ----------
    t = sample.loc[sample["is_card"] & sample["tip_rate"].notna()].copy()
    t = t[t["fare"].between(3, 200) & t["distance_mi"].between(0.1, 50)
          & t["duration_min"].between(1, 180)].copy()
    t["generous"] = (t["tip_rate"] >= 0.25).astype(int)
    t["passenger_count"] = t["passenger_count"].fillna(0).clip(0, 6)
    t["airport_i"] = t["airport"].astype(int)
    num_cols = ["hour", "weekday", "month", "distance_mi", "duration_min",
                "fare", "passenger_count", "airport_i"]
    X = t[num_cols].copy()
    for col in ["borough_pu", "time_band", "RatecodeID"]:
        dummies = pd.get_dummies(t[col].astype(str), prefix=col, drop_first=True, dtype=int)
        X = pd.concat([X, dummies], axis=1)
    X = X.fillna(0)
    y = t["generous"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.30, stratify=y,
                                          random_state=SEED)
    gb = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.07, max_depth=6,
                                        early_stopping=True, validation_fraction=0.1,
                                        random_state=SEED)
    gb.fit(Xtr, ytr)
    prob = gb.predict_proba(Xte)[:, 1]
    pred = (prob >= 0.5).astype(int)
    auc = float(roc_auc_score(yte, prob))
    fpr, tpr, _ = roc_curve(yte, prob)
    pd.DataFrame({"fpr": fpr, "tpr": tpr}).to_csv(
        OUT_TAB / "tip_roc.csv", index=False, encoding="utf-8-sig")

    lr = LogisticRegression(max_iter=250, solver="lbfgs")
    scaler = StandardScaler()
    lr.fit(scaler.fit_transform(Xtr), ytr)
    prob_lr = lr.predict_proba(scaler.transform(Xte))[:, 1]
    auc_lr = float(roc_auc_score(yte, prob_lr))

    idx = np.random.RandomState(SEED).choice(len(Xte), min(15000, len(Xte)), replace=False)
    imp = permutation_importance(gb, Xte.iloc[idx], yte.iloc[idx], n_repeats=3,
                                 scoring="roc_auc", random_state=SEED, n_jobs=1)
    importance = pd.DataFrame({"feature": X.columns, "importance": imp.importances_mean,
                               "std": imp.importances_std}).sort_values(
        "importance", ascending=False)
    importance.to_csv(OUT_TAB / "tip_importance.csv", index=False, encoding="utf-8-sig")

    tmetrics = {
        "model": "HistGradientBoostingClassifier", "rows": int(len(t)),
        "train_rows": int(len(Xtr)), "test_rows": int(len(Xte)),
        "positive_rate": float(y.mean()), "auc": auc, "auc_logit": auc_lr,
        "accuracy": float(accuracy_score(yte, pred)),
        "precision": float(precision_score(yte, pred)),
        "recall": float(recall_score(yte, pred)),
        "f1": float(f1_score(yte, pred)),
        "brier": float(brier_score_loss(yte, prob)),
        "top_features": importance.head(10)["feature"].tolist(),
        "note": "仅信用卡行程；慷慨小费定义为小费率≥25%（高于默认 20% 档）；现金小费不可观测，结论不外推到现金支付。",
    }
    dump(tmetrics, "tip_model.json")
    print(f"[小费] n={len(t):,} AUC={auc:.3f} (LR={auc_lr:.3f})")

    # ---------- 4. BCG 式区域机会矩阵 ----------
    z = zs[(zs["trips"] >= 500) & (zs["h1_trips"] > 0)].copy()
    z["growth"] = z["growth_rate"].clip(-0.5, 0.5)
    gmid, smid = z["growth"].median(), z["revenue_share"].median()
    hi_g, hi_s = z["growth"] >= gmid, z["revenue_share"] >= smid
    z["quadrant"] = np.select(
        [hi_g & hi_s, hi_g & ~hi_s, ~hi_g & hi_s],
        ["明星", "问题", "现金牛"], default="瘦狗")
    z.to_csv(OUT_TAB / "bcg_matrix.csv", index=False, encoding="utf-8-sig")
    bcg = z.groupby("quadrant").agg(zones=("PULocationID", "size"),
                                    trips=("trips", "sum"),
                                    revenue=("revenue", "sum")).reset_index()
    bcg["revenue_share"] = bcg["revenue"] / total_revenue
    dump({"growth_median": float(gmid), "share_median": float(smid),
          "quadrants": bcg.to_dict("records")}, "bcg_summary.json")

    # ---------- 5. 需求异常检测：STL 残差 ----------
    series = daily.set_index("date")["trips"].asfreq("D").astype(float)
    stl = STL(series, period=7, robust=True).fit()
    resid = pd.Series(stl.resid, index=series.index)
    zscore = (resid - resid.mean()) / resid.std()
    ad = pd.DataFrame({"date": series.index, "trips": series.values,
                       "resid": resid.values, "z": zscore.values})
    ad["flag"] = ad["z"].abs() >= 2.5
    ad.to_csv(OUT_TAB / "anomaly_days.csv", index=False, encoding="utf-8-sig")
    anomalies = ad[ad["flag"]].sort_values("z", key=lambda x: x.abs(), ascending=False)
    dump({"method": "STL(period=7, robust=True)", "threshold_z": 2.5,
          "count": int(ad["flag"].sum()),
          "days": anomalies[["date", "trips", "z"]].assign(
              date=lambda d: d["date"].dt.strftime("%Y-%m-%d")).to_dict("records")},
         "anomaly_summary.json")

    # ---------- 6. OD 走廊集中度 ----------
    od["share"] = od["trips"] / total_trips
    top20 = od.head(20).copy()
    top20.to_csv(OUT_TAB / "od_top20.csv", index=False, encoding="utf-8-sig")
    od_conc = {"top1_share": float(od["share"].iloc[0]),
               "top20_share": float(top20["share"].sum()),
               "top100_share": float(od.head(100)["share"].sum()),
               "top500_share": float(od["share"].sum())}
    dump(od_conc, "od_concentration.json")

    # ---------- 7. 汇总 ----------
    peak_hour = int(havg.groupby("hour")["avg_trips"].mean().idxmax())
    peak_idx = daily["trips"].idxmax()
    summary = dict(kpi)
    summary.update({
        "peak_day": str(daily.loc[peak_idx, "date"].date()),
        "peak_day_trips": float(daily.loc[peak_idx, "trips"]),
        "peak_hour": peak_hour,
        "top_zone": str(zs.iloc[0]["Zone"]),
        "top_zone_borough": str(zs.iloc[0]["Borough"]),
        "top_zone_revenue_share": float(zs.iloc[0]["revenue_share"]),
        "forecast": fmetrics,
        "clusters": {"k": int(k_best), "silhouette": scores[k_best],
                     "names": [names[c] for c in range(k_best)]},
        "tip_model": tmetrics,
        "anomaly_days": int(ad["flag"].sum()),
        "top20_od_share": od_conc["top20_share"],
    })
    dump(summary, "summary_metrics.json")

    model_rows = [
        ["需求预测", "SARIMAX", "MAPE(%)", round(fmetrics["mape"], 2)],
        ["需求预测", "SARIMAX", "RMSE", round(fmetrics["rmse"], 1)],
        ["区域聚类", "KMeans", "轮廓系数", round(scores[k_best], 3)],
        ["小费行为", "HistGradientBoosting", "AUC", round(auc, 3)],
        ["小费行为", "LogisticRegression", "AUC", round(auc_lr, 3)],
        ["异常检测", "STL", "异常天数", int(ad["flag"].sum())],
    ]
    pd.DataFrame(model_rows, columns=["业务问题", "模型", "指标", "取值"]).to_csv(
        OUT_TAB / "model_summary.csv", index=False, encoding="utf-8-sig")

    print(f"[完成] 总收入 ${total_revenue/1e6:.1f}M；预测 MAPE={fmetrics['mape']:.2f}%；"
          f"聚类 k={k_best}；小费 AUC={auc:.3f}；异常 {int(ad['flag'].sum())} 天")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
