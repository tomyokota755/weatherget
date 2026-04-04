import os
import requests
from datetime import datetime, timedelta

# ターゲット空港リスト
TARGET_AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS", "RJFG"]
SAVE_DIR = "forecasts"
RETENTION_DAYS = 4

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_and_cleanup():
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    # フォルダ維持用の隠しファイル
    with open(os.path.join(SAVE_DIR, ".gitkeep"), "w") as f:
        f.write("folder keep")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    print(f"--- Salvage Mission Started at {timestamp} ---")
    
    success_count = 0
    for icao in TARGET_AIRPORTS:
        # 正解のURL構造: /pict/taf/QMCD98_{icao}.png
        url = f"https://www.data.jma.go.jp/airinfo/data/pict/taf/QMCD98_{icao}.png"
        
        try:
            print(f"Checking {icao}...")
            res = requests.get(url, headers=HEADERS, timeout=20)
            
            if res.status_code == 200:
                filename = f"{icao}_{timestamp}.png"
                filepath = os.path.join(SAVE_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(res.content)
                print(f"  [SUCCESS] {icao} saved.")
                success_count += 1
            else:
                print(f"  [FAILED] {icao} (Status: {res.status_code})")
        except Exception as e:
            print(f"  [ERROR] {icao}: {e}")

    # --- 96時間（4日）経過データの自動パージ ---
    now = datetime.now()
    cutoff = now - timedelta(days=RETENTION_DAYS)
    for filename in os.listdir(SAVE_DIR):
        if filename.endswith(".png"):
            try:
                parts = filename.split('_')
                if len(parts) >= 3:
                    file_date_str = f"{parts[1]}_{parts[2].split('.')[0]}"
                    file_date = datetime.strptime(file_date_str, "%Y%m%d_%H%M")
                    if file_date < cutoff:
                        os.remove(os.path.join(SAVE_DIR, filename))
                        print(f"  [PURGED] Old file deleted: {filename}")
            except:
                continue

    print(f"--- Mission Finished. Total Saved: {success_count} ---")

if __name__ == "__main__":
    fetch_and_cleanup()
