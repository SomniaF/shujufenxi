"""一键运行全部章节脚本，重新生成 outputs/ 下的图表。

用法：py run_all.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    scripts = sorted(ROOT.glob("ch*/*.py"))
    if not scripts:
        print("未找到章节脚本")
        return 1
    failed = []
    start = time.perf_counter()
    for script in scripts:
        name = script.relative_to(ROOT).as_posix()
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(script)], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        cost = time.perf_counter() - t0
        if proc.returncode == 0:
            print(f"[OK]   {name}  ({cost:.1f}s)")
        else:
            print(f"[FAIL] {name}  ({cost:.1f}s)")
            print(proc.stdout[-2000:])
            print(proc.stderr[-2000:])
            failed.append(name)
    total = time.perf_counter() - start
    figures = len(list((ROOT / "outputs" / "figures").glob("*.png")))
    tables = len(list((ROOT / "outputs" / "tables").glob("*.csv")))
    print(f"\n共 {len(scripts)} 个脚本，失败 {len(failed)} 个，用时 {total:.1f}s")
    print(f"输出：{figures} 张图、{tables} 张表 -> outputs/")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
