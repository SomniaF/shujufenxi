# -*- coding: utf-8 -*-
"""01_load.py —— 官方渠道获取 NYC TLC 2024 黄色出租车数据并审计。

数据页：https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
下载域：https://d37ci6vzurychx.cloudfront.net
方式：HTTPS 直接下载官方 parquet/csv/zip，不使用爬虫、不解析网页。
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (DATA_RAW, MONTHS, OUT_TAB, SOURCE_PAGE, TLC_BASE,
                    TRIP_URL, ZONE_LOOKUP_URL, ZONE_SHP_URL)

UA = {"User-Agent": "Mozilla/5.0 (course-project)"}


def head_size(url):
    try:
        req = Request(url, method="HEAD", headers=UA)
        with urlopen(req, timeout=30) as resp:
            value = resp.headers.get("Content-Length")
            return int(value) if value else None
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None


def download(url, dest, retries=3):
    remote = head_size(url)
    if dest.exists() and dest.stat().st_size > 1024:
        if remote is None or dest.stat().st_size == remote:
            return "skip"
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        have = tmp.stat().st_size if tmp.exists() else 0
        headers = dict(UA)
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=120) as resp, open(tmp, "ab") as fh:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    fh.write(chunk)
            tmp.replace(dest)
            return "download"
        except (HTTPError, URLError, TimeoutError, ConnectionError) as exc:
            print(f"  重试 {attempt}/{retries}: {exc}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"下载失败: {url}")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parquet_meta(path):
    pf = pq.ParquetFile(path)
    return {"rows": pf.metadata.num_rows, "columns": pf.schema_arrow.names}


def main():
    force = "--force" in sys.argv
    items = [(TRIP_URL.format(month=m), DATA_RAW / f"yellow_tripdata_{m}.parquet") for m in MONTHS]
    items += [(ZONE_LOOKUP_URL, DATA_RAW / "taxi_zone_lookup.csv"),
              (ZONE_SHP_URL, DATA_RAW / "taxi_zones.zip")]
    if force:
        for _, path in items:
            path.unlink(missing_ok=True)

    print(f"检查/下载 {len(items)} 个官方文件 ...")
    for url, path in items:
        status = download(url, path)
        print(f"  [{status}] {path.name}  {path.stat().st_size/1048576:.1f} MB")

    files, total_bytes, total_rows = [], 0, 0
    for month in MONTHS:
        path = DATA_RAW / f"yellow_tripdata_{month}.parquet"
        meta = parquet_meta(path)
        item = {"name": path.name, "month": month,
                "url": TRIP_URL.format(month=month),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path), **meta}
        files.append(item)
        total_bytes += item["bytes"]
        total_rows += item["rows"]
        print(f"  {month}: {meta['rows']:,} 行, {len(meta['columns'])} 列")

    extra = []
    for name, url in [("taxi_zone_lookup.csv", ZONE_LOOKUP_URL),
                      ("taxi_zones.zip", ZONE_SHP_URL)]:
        path = DATA_RAW / name
        extra.append({"name": name, "url": url, "bytes": path.stat().st_size,
                      "sha256": sha256_file(path)})

    audit = {
        "dataset": "NYC TLC Yellow Taxi Trip Records 2024",
        "publisher": "New York City Taxi and Limousine Commission (TLC)",
        "source_page": SOURCE_PAGE,
        "download_base": TLC_BASE,
        "license": "纽约市政府公开发布的匿名行程数据；按 TLC 数据页与 NYC Open Data 使用条款使用，按原样提供、不作担保。",
        "acquisition_method": "HTTPS 直接下载官方 parquet/csv/zip（TLC 官方 CloudFront 托管），未使用网页爬虫、未模拟登录。",
        "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analysis_window": "2024-01-01 至 2024-12-31",
        "timezone": "America/New_York（时间戳为本地时间，未做时区换算）",
        "totals": {"files": len(files), "bytes": total_bytes, "rows": total_rows},
        "files": files,
        "auxiliary_files": extra,
        "notes": [
            "TLC 数据不含乘客/司机身份标识，仅含上下车时间、区域编号、计价与支付字段。",
            "区域编号需与 taxi_zone_lookup.csv 及 taxi_zones.zip 关联使用。",
            "原始数据不纳入版本库，运行 01_load.py 可重新下载并复核 SHA-256。",
        ],
    }
    OUT_TAB.mkdir(parents=True, exist_ok=True)
    out = OUT_TAB / "raw_audit.json"
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n合计 {total_bytes/1048576:.1f} MB, {total_rows:,} 行 -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
