# -*- coding: utf-8 -*-
"""06_snapshot.py —— 启动 Streamlit 并用 Selenium（Edge headless）截取大屏。

Selenium 仅用于本地大屏截图，不参与任何数据采集。
输出：outputs/dashboard/dashboard_overview.png / _mid.png / _drill.png / _full.png
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "dashboard"
PORT = 8508


def wait_port(port: int, timeout: int = 90) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        with socket.socket() as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(1)
    return False


def shot(driver, path: Path, height: int | None = None):
    if height:
        driver.set_window_size(1680, height)
        time.sleep(2.0)
    driver.save_screenshot(str(path))
    print(f"[截图] {path.name} ({path.stat().st_size/1e3:.0f} KB)")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "streamlit", "run", str(ROOT / "scripts" / "05_dashboard.py"),
           "--server.headless=true", f"--server.port={PORT}", "--browser.gatherUsageStats=false"]
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    driver = None
    try:
        if not wait_port(PORT):
            raise RuntimeError("Streamlit 未能启动")
        time.sleep(8)
        from selenium import webdriver
        op = webdriver.EdgeOptions()
        op.add_argument("--headless=new")
        op.add_argument("--disable-gpu")
        op.add_argument("--window-size=1680,1050")
        op.add_argument("--force-device-scale-factor=1")
        driver = webdriver.Edge(options=op)
        driver.set_page_load_timeout(90)
        driver.get(f"http://localhost:{PORT}")
        for _ in range(60):
            if driver.find_elements("css selector", "[data-testid='stAppViewContainer']"):
                break
            time.sleep(1)
        rendered = False
        for _ in range(90):
            if "区域明细表" in driver.execute_script("return document.body.innerText"):
                rendered = True
                break
            time.sleep(2)
        print("[渲染]", "完成" if rendered else "超时")
        time.sleep(3)

        def scroll_to(y):
            driver.execute_script("""
                const m = document.querySelector('[data-testid="stMain"]');
                if (m) { m.scrollTo(0, arguments[0]); } else { window.scrollTo(0, arguments[0]); }
            """, y)
            time.sleep(1.5)

        scroll_to(0)
        shot(driver, OUT / "dashboard_overview.png")

        total = driver.execute_script(
            "const m=document.querySelector('[data-testid=\"stMain\"]');"
            "return m ? m.scrollHeight : document.body.scrollHeight;")
        print("[页面高度]", total)
        scroll_to(int(total * 0.42))
        shot(driver, OUT / "dashboard_mid.png")

        scroll_to(total)
        shot(driver, OUT / "dashboard_drill.png")

        scroll_to(0)
        driver.set_window_size(1680, min(max(total + 140, 2600), 5200))
        time.sleep(2.5)
        shot(driver, OUT / "dashboard_full.png")
    finally:
        if driver is not None:
            driver.quit()
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("[完成] 大屏截图已写入 outputs/dashboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
