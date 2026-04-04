import os
import requests
from datetime import datetime, timedelta

# ターゲット空港リスト
TARGET_AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS", "RJFG"]
SAVE_DIR = "forecasts"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_and_cleanup():
    # フォルダを作成（存在しなければ）
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    # フォルダを強制認識させるための目印ファイル（重要！）
    with open(os.path.join(SAVE_DIR, ".gitkeep"), "w") as f:
        f.write("folder keep")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    print(f"--- Salvage Mission Started at {timestamp} ---")
    print(f"Targeting: {', '.join(TARGET_AIRPORTS)}")
    
    success_count = 0
    for icao in TARGET_AIRPORTS:
        # 画像URL（このパスでアクセスを試みます）
        url = f"https://www.data.jma.go.jp/airinfo/data/png/AWFO_{icao}.png"
        
        try:
            print(f"Checking {icao}...")
            res = requests.get(url, headers=HEADERS, timeout=20)
            
            if res.status_code == 200:
                filename = f"{icao}_{timestamp}.png"
                with open(os.path.join(SAVE_DIR, filename), "wb") as f:
                    f.write(res.content)
                print(f"  [SUCCESS] {icao} saved.")
                success_count += 1
            else:
                print(f"  [FAILED] {icao} (Status: {res.status_code})")
        except Exception as e:
            print(f"  [ERROR] {icao}: {e}")

    print(f"--- Mission Finished. Total Saved: {success_count} ---")

if __name__ == "__main__":
    fetch_and_cleanup()
