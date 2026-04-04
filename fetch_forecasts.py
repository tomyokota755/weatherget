import os
import requests
from datetime import datetime, timedelta

# 保存先
SAVE_DIR = "forecasts"
RETENTION_DAYS = 4 # 96時間保存

# 1. ターゲット空港（時系列予報）
TARGET_AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS", "RJFG"]

# 2. 物理裏付けチャート（地上・高層予想図）
# 気象庁の最新画像（固定URL）をターゲットにします
TARGET_CHARTS = {
    "ASAS": "https://www.data.jma.go.jp/airinfo/data/pict/as/asas.png",     # 地上解析図
    "FSAS24": "https://www.data.jma.go.jp/airinfo/data/pict/fs/fsas24.png", # 地上24h予想
    "FXJP85": "https://www.data.jma.go.jp/airinfo/data/pict/fxjp/fxjp854.png", # 850hPa 24h予想
    "FXJP50": "https://www.data.jma.go.jp/airinfo/data/pict/fxjp/fxjp504.png", # 500hPa 24h予想
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_all():
    os.makedirs(SAVE_DIR, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M")
    print(f"--- Salvage Mission (Full Set) Started at {timestamp} ---")
    
    success_count = 0

    # --- 空港時系列予報の取得 ---
    for icao in TARGET_AIRPORTS:
        url = f"https://www.data.jma.go.jp/airinfo/data/pict/taf/QMCD98_{icao}.png"
        if download_image(url, f"{icao}_{timestamp}.png"):
            success_count += 1

    # --- 天気図（チャート）の取得 ---
    for name, url in TARGET_CHARTS.items():
        if download_image(url, f"CHART_{name}_{timestamp}.png"):
            success_count += 1

    # --- 古いデータの削除 ---
    cleanup(now)
    print(f"--- Mission Finished. Total Files Processed: {success_count} ---")

def download_image(url, filename):
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code == 200:
            filepath = os.path.join(SAVE_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(res.content)
            print(f"  [SUCCESS] Saved: {filename}")
            return True
        else:
            print(f"  [FAILED] {filename} (Status: {res.status_code})")
            return False
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
        return False

def cleanup(now):
    cutoff = now - timedelta(days=RETENTION_DAYS)
    for filename in os.listdir(SAVE_DIR):
        if filename.endswith(".png"):
            try:
                # ファイル名の末尾（日時部分）から判断
                parts = filename.replace(".png", "").split("_")
                if len(parts) >= 2:
                    date_str = f"{parts[-2]}_{parts[-1]}"
                    file_date = datetime.strptime(date_str, "%Y%m%d_%H%M")
                    if file_date < cutoff:
                        os.remove(os.path.join(SAVE_DIR, filename))
                        print(f"  [PURGED] Deleted: {filename}")
            except:
                continue

if __name__ == "__main__":
    fetch_all()
