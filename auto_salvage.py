import os
import requests
import hashlib
from datetime import datetime, timedelta

# --- 基本設定 ---
BASE_DIR = "."
AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS"]
# 取得する天気図のリスト（3日のバリエーションを網羅）
CHART_TYPES = ["ASAS", "SPAS", "AUPQ35", "AUPQ78", "AXJP", "WTJP"]

def main():
    print(f"--- Enhanced Salvage Start: {datetime.now()} ---")
    
    # 1. METAR/TAF (全空港分)
    fetch_noaa_data("metar")
    fetch_noaa_data("taf")

    # 2. 重点11空港の時系列予報(PNG)
    fetch_jma_timelines()

    # 3. 専門天気図(PDF) のスマート取得
    fetch_jma_charts_smart()

    # 4. GitHub上の掃除（30日間保持）
    cleanup_github_repo(days=30)

def fetch_jma_charts_smart():
    """新しい天気図が発行された場合のみ、タイムスタンプを付けて保存"""
    now = datetime.now()
    path = os.path.join(now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    os.makedirs(path, exist_ok=True)

    for c in CHART_TYPES:
        url = f"https://www.data.jma.go.jp/airinfo/data/pict/hbc/{c}.pdf"
        try:
            res = requests.get(url, timeout=20)
            if res.status_code == 200:
                current_content = res.content
                current_hash = hashlib.md5(current_content).hexdigest()
                
                # 同じ日の既存ファイルをチェックし、中身が違う場合のみ保存
                is_new = True
                for existing_file in os.listdir(path):
                    if existing_file.startswith(f"CHART_{c}"):
                        with open(os.path.join(path, existing_file), "rb") as f:
                            if hashlib.md5(f.read()).hexdigest() == current_hash:
                                is_new = False
                                break
                
                if is_new:
                    # 3日の形式に近い YYYYMMDDHH 形式で保存
                    filename = f"CHART_{c}_{now.strftime('%Y%m%d%H%M')}.pdf"
                    with open(os.path.join(path, filename), "wb") as f:
                        f.write(current_content)
                    print(f"  [NEW CHART] {filename} saved.")
        except: pass

# --- (fetch_noaa_data, fetch_jma_timelines, cleanup_github_repo は前回と同じものを継続) ---
# ※ 文字数制限のため省略しますが、前回のコードのそれら関数をそのまま繋げてください。
