# -*- coding: utf-8 -*-
"""run_all.py —— 一键复现入口。

用法：
    py -X utf8 run_all.py              # 数据已存在：清洗→建模→出图
    py -X utf8 run_all.py --download   # 首次运行：先下载 TLC 官方数据
    py -X utf8 run_all.py --docs       # 额外重建论文与合规声明 DOCX
    py -X utf8 run_all.py --dashboard  # 出图后拉起 Streamlit 大屏

依赖安装：pip install -r requirements.txt
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
RAW = ROOT / "data" / "raw"
MONTHS = [f"2024-{m:02d}" for m in range(1, 13)]
RAW_FILES = [RAW / f"yellow_tripdata_{m}.parquet" for m in MONTHS]
RAW_FILES += [RAW / "taxi_zone_lookup.csv", RAW / "taxi_zones.zip"]


def run(name: str, *args: str) -> None:
    cmd = [sys.executable, "-X", "utf8", str(SCRIPTS / name), *args]
    print("\n" + "=" * 72)
    print("[运行]", " ".join(cmd))
    print("=" * 72)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    missing = [p.name for p in RAW_FILES if not p.exists() or p.stat().st_size < 1024]
    if missing:
        print(f"[检查] 缺少 {len(missing)} 个原始文件，将从 TLC 官方地址下载")
    run("01_load.py")
    run("02_clean.py")
    run("03_analysis.py")
    run("04_visuals.py")

    if "--docs" in sys.argv:
        run("07_build_paper.py")
        run("08_compliance.py")

    print("\n全部静态产物已生成：outputs/figures、outputs/tables、data/clean")
    if "--dashboard" in sys.argv:
        print("\n启动交互大屏：http://localhost:8501 （Ctrl+C 退出）")
        subprocess.run([sys.executable, "-m", "streamlit", "run",
                        str(SCRIPTS / "05_dashboard.py")], cwd=ROOT)
    else:
        print("交互大屏：py -m streamlit run scripts/05_dashboard.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
