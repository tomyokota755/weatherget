import os
import requests
import re
import csv
import math
import time
from datetime import datetime, timedelta

# --- 基本設定 ---
BASE_DIR = r"E:\Aviation_QAR\Forecasts"
AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS"]
CHART_TYPES = ["ASAS", "AUPQ78", "AUPQ35", "FSAS24", "FEAS502"]
HOURS = ["00", "03", "06", "09", "12", "15", "18", "21"]

# 横風計算用：滑走路方位（真方位）
RWY_DATA = {
    "RJTT": 337, "RJAA": 156, "RJCC": 12, "RJFF": 156, "ROAH": 182,
    "RJOA": 102, "RJOT": 77, "RJSA": 63, "RJSK": 102, "RJFK": 157, "RORS": 171
}

# ブラウザ偽装ヘッダー（HBC/JMA共通）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/pdf,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Referer': 'https://www.hbc.co.jp/tecweather/archive/index.html'
}

def main():
    print("--- Aviation Weather Salvager (AWS) : Full-Spec Mission ---")
    now = datetime.now()
    
    # PHASE 1: 今日の最新情報 & リスク解析
    today_path = get_path(now)
    ts = now.strftime("%H%M")
    analysis_data = []

    print(f"\n[PHASE 1] Analyzing 11 Airports...")
    for icao in AIRPORTS:
        # PNG予報の保存
        png_url = f"https://www.data.jma.go.jp/airinfo/data/pict/taf/QMCD98_{icao}.png"
        download_stealth(png_url, f"{icao}_Forecast_{ts}.png", today_path)
        
        # METAR取得と診断
        metar = fetch_metar(icao)
        if metar:
            analysis_data.append(analyze_metar(icao, metar))

    if analysis_data:
        write_csv(analysis_data, today_path, ts)

    # PHASE 2: 専門天気図の遡りサルベージ（4月1日〜今日まで）
    print(f"\n[PHASE 2] Salvaging Archive Charts (HBC Stealth Mode)...")
    target_date = datetime(2026, 4, 1)
    while target_date <= now:
        date_str = target_date.strftime("%Y%m%d")
        path = get_path(target_date)
        for t in CHART_TYPES:
            for hh in HOURS:
                filename = f"{t}_{date_str}{hh}.pdf"
                url = f"https://www.hbc.co.jp/tecweather/archive/pdf/{filename}"
                download_stealth(url, f"CHART_{filename}", path, min_size=50000)
        target_date += timedelta(days=1)

    print(f"\n--- Mission Accomplished. All data secured in E: drive. ---")
    input("Press Enter to close...")

def get_path(date_obj):
    p = os.path.join(BASE_DIR, date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d"))
    os.makedirs(p, exist_ok=True)
    return p

def fetch_metar(icao):
    url = f"https://www.data.jma.go.jp/airinfo/data/metar/taf_QMCD98_{icao}.html"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            lines = [l.strip() for l in res.text.split('\n') if icao in l and 'METAR' in l]
            return lines[0] if lines else None
    except: return None

def analyze_metar(icao, metar):
    res = {"ICAO": icao, "SUMMARY": "NORMAL", "VIS": "OK", "CEIL": "OK", "XWIND": "OK", "WX": "OK", "METAR": metar}
    # 視程・雲高・横風・雷の判定（先日のロジック）
    v_m = re.search(r'\s(\d{4})\s', metar)
    if v_m:
        v = int(v_m.group(1))
        if v < 550: res["VIS"] = f"RED: {v}m"; res["SUMMARY"] = "CAUTION"
        elif v < 1000: res["VIS"] = f"ORANGE: {v}m"; res["SUMMARY"] = "CAUTION"
    c_m = re.findall(r'(BKN|OVC)(\d{3})', metar)
    if c_m:
        c = min([int(x[1])*100 for x in c_m])
        if c < 500: res["CEIL"] = f"RED: {c}ft"; res["SUMMARY"] = "CAUTION"
        elif c < 1000: res["CEIL"] = f"ORANGE: {c}ft"; res["SUMMARY"] = "CAUTION"
    w_m = re.search(r'(\d{3}|VRB)(\d{2})(G\d{2})?KT', metar)
    if w_m and w_m.group(1) != "VRB":
        wdir, wspd = int(w_m.group(1)), int(w_m.group(2))
        xw = abs(wspd * math.sin(math.radians(wdir - RWY_DATA.get(icao, 0))))
        if xw >= 25: res["XWIND"] = f"RED: {xw:.1f}kt"; res["SUMMARY"] = "CAUTION"
    if "TS" in metar: res["WX"] = "RED: TS-DETECTED"; res["SUMMARY"] = "CAUTION"
    return res

def write_csv(data, path, ts):
    f = os.path.join(path, f"Weather_Risk_Analysis_{ts}.csv")
    with open(f, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["ICAO", "SUMMARY", "VIS", "CEIL", "XWIND", "WX", "METAR"])
        writer.writeheader()
        writer.writerows(data)

def download_stealth(url, filename, save_path, min_size=0):
    dest = os.path.join(save_path, filename)
    if os.path.exists(dest): return False
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200 and len(res.content) > min_size:
            with open(dest, "wb") as f: f.write(res.content)
            print(f"      [SAVED] {filename}")
            return True
    except: pass
    return False

if __name__ == "__main__":
    main()