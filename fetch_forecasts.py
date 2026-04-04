import os
import requests
from datetime import datetime, timedelta

TARGET_AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS"]
SAVE_DIR = "forecasts"
RETENTION_DAYS = 4

def fetch_and_cleanup():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    print(f"Starting fetch at {timestamp}...")
    
    for icao in TARGET_AIRPORTS:
        url = f"https://www.data.jma.go.jp/airinfo/data/png/AWFO_{icao}.png"
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                with open(f"{SAVE_DIR}/{icao}_{timestamp}.png", "wb") as f:
                    f.write(res.content)
                print(f" Saved: {icao}")
        except Exception as e:
            print(f" Error {icao}: {e}")

    now = datetime.now()
    cutoff = now - timedelta(days=RETENTION_DAYS)
    for filename in os.listdir(SAVE_DIR):
        try:
            parts = filename.split('_')
            if len(parts) < 3: continue
            file_date_str = f"{parts[1]}_{parts[2].split('.')[0]}"
            file_date = datetime.strptime(file_date_str, "%Y%m%d_%H%M")
            if file_date < cutoff:
                os.remove(os.path.join(SAVE_DIR, filename))
                print(f" Purged: {filename}")
        except Exception as e:
            print(f" Skip purge for {filename}: {e}")

if __name__ == "__main__":
    fetch_and_cleanup()
