import os
import requests
import time
import random
from datetime import datetime

# --- 司令部設定 ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.hbc.co.jp/weather/aviation/"
}

# 重点空港
TARGET_AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS"]
CHART_TYPES = ["ASAS", "SPAS", "AUPQ35", "AUPQ78"]

def is_real_file(content, file_type):
    """
    ファイルの中身が本物（PDFやPNG）かを確認する「検品」関数
    """
    if file_type == "pdf":
        return content.startswith(b"%PDF") # PDFは必ず %PDF から始まる
    if file_type == "png":
        return content.startswith(b"\x89PNG") # PNGは必ず \x89PNG から始まる
    return False

def download_verified_file(url, save_path, file_type):
    """
    検品を通ったファイルだけをディスクに書き込む
    """
    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        # ステータスが200、かつ中身が本物であること
        if res.status_code == 200 and is_real_file(res.content, file_type):
            with open(save_path, "wb") as f:
                f.write(res.content)
            print(f"  ✅ Verified & Saved: {os.path.basename(save_path)}")
            return True
        else:
            print(f"  ❌ Invalid Content (404/HTML): {os.path.basename(save_path)}")
            return False
    except Exception as e:
        print(f"  ⚠️ Network Error: {e}")
        return False

def main():
    now = datetime.now()
    save_dir = f"forecasts/{now.strftime('%Y/%m/%d')}"
    os.makedirs(save_dir, exist_ok=True)

    print(f"--- [START] Defensive Salvage Mission: {now} ---")

    # 1. 専門天気図(PDF) の収穫
    for c_type in CHART_TYPES:
        url = f"https://www.hbc.co.jp/weather/chart/pdf/{c_type.lower()}.pdf"
        fname = f"CHART_{c_type}_{now.strftime('%Y%m%d%H')}.pdf"
        download_verified_file(url, os.path.join(save_dir, fname), "pdf")
        time.sleep(random.uniform(5, 8)) # 警戒されないよう長めのインターバル

    # 2. 飛行場時系列予報(PNG) の収穫
    # ※JMAのAPI構造に合わせた予備ルート
    for icao in TARGET_AIRPORTS:
        # HBCミラーとJMA本陣のどちらかを試行
        url = f"https://www.hbc.co.jp/weather/aviation/img/as/AS_{icao}.png"
        fname = f"{icao}_Forecast_{now.strftime('%H%M')}.png"
        download_verified_file(url, os.path.join(save_dir, fname), "png")
        time.sleep(random.uniform(5, 8))

    print("--- [FINISH] Mission Complete ---")

if __name__ == "__main__":
    main()
