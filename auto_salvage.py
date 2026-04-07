import os
import requests
import re
import hashlib
import time
from datetime import datetime, timedelta

# --- 基本設定 ---
BASE_DIR = "."
# 通信時の「身分証明書」：ブラウザからのアクセスを装い拒絶を防ぐ
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 日本国内の主要・地方空港（TAF/METAR発行箇所を網羅）
AIRPORTS_ALL = [
    "RJAA", "RJTT", "RJBB", "RJCC", "RJFF", "RJGG", "ROAH", "RJOO", "RJSN", "RJNK",
    "RJNT", "RJNW", "RJNS", "RJNY", "RJNA", "RJNB", "RJNC", "RJNE", "RJNG", "RJNH",
    "RJNI", "RJNJ", "RJNL", "RJNM", "RJNN", "RJNO", "RJNP", "RJNQ", "RJNR", "RJNU", 
    "RJNV", "RJNX", "RJNZ", "RJOA", "RJOB", "RJOC", "RJOD", "RJOE", "RJOF", "RJOG", 
    "RJOH", "RJOI", "RJOJ", "RJOK", "RJOM", "RJON", "RJOP", "RJOQ", "RJOR", "RJOS", 
    "RJOT", "RJOU", "RJOV", "RJOW", "RJOY", "RJOZ", "RJSA", "RJSB", "RJSC", "RJSD", 
    "RJSE", "RJSF", "RJSG", "RJSH", "RJSI", "RJSJ", "RJSK", "RJSL", "RJSM", "RJSN", 
    "RJSO", "RJSP", "RJSQ", "RJSR", "RJSS", "RJSY", "RJTO", "RODN", "ROIG", "ROKJ", 
    "ROMY", "RORS", "ROTM", "ROYN", "RJTY", "RJTF", "RJTI", "RJCJ"
]

# 取得する専門天気図の種類
CHART_TYPES = ["ASAS", "SPAS", "AUPQ35", "AUPQ78", "AXJP", "WTJP"]

def main():
    print(f"--- [START] Fully Enhanced Salvage Mission: {datetime.now()} ---")
    
    # 1. METAR/TAF 取得
    fetch_noaa_data("metar")
    fetch_noaa_data("taf")

    # 2. 重点空港の時系列予報(PNG) 取得
    fetch_jma_timelines()

    # 3. 専門天気図(PDF) のスマート取得（重複なし）
    fetch_jma_charts_smart()

    # 4. GitHub上の古いデータを掃除（30日間保持）
    cleanup_github_repo(days=30)

    print("--- [FINISH] All Checklists Complete ---")

def fetch_noaa_data(data_type):
    batch_size = 15
    for i in range(0, len(AIRPORTS_ALL), batch_size):
        batch = AIRPORTS_ALL[i:i+batch_size]
        icao_str = ",".join(batch)
        url = f"https://aviationweather.gov/api/data/{data_type}?ids={icao_str}&format=raw&hours=6&mostrecent=false"
        try:
            res = requests.get(url, headers=HEADERS, timeout=30)
            if res.status_code == 200:
                reports = [r.strip() + "=" for r in res.text.split('=') if len(r) > 10] if data_type == "taf" else res.text.split('\n')
                save_reports(reports, data_type)
        except: pass

def save_reports(reports, data_type):
    now = datetime.now()
    for r in reports:
        r = r.strip()
        if not r: continue
        match = re.search(r'(\d{2})(\d{2})(\d{2})Z', r)
        if not match: continue
        day_val = int(match.group(1))
        target_date = now.replace(day=day_val)
        if day_val > now.day + 1: target_date -= timedelta(days=28)
        
        path = os.path.join(target_date.strftime("%Y"), target_date.strftime("%m"), target_date.strftime("%d"))
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, f"{data_type.upper()}_All_{target_date.strftime('%Y%m%d')}.txt")
        
        content = ""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        if r not in content:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(r + "\n")

def fetch_jma_timelines():
    now = datetime.now()
    path = os.path.join(now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    os.makedirs(path, exist_ok=True)
    # 重点空港リスト（容量節約のためここでは11空港に限定）
    target_11 = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS"]
    for icao in target_11:
        url = f"https://www.jma.go.jp/bosai/aviation/data/v3/chart/timeline/{icao}.png"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                with open(os.path.join(path, f"{icao}_Timeline_{now.strftime('%H%M')}.png"), "wb") as f:
                    f.write(res.content)
        except: pass

def fetch_jma_charts_smart():
    """新しい天気図が発行された場合のみ、タイムスタンプを付けて高品質保存"""
    now = datetime.now()
    path = os.path.join(now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    os.makedirs(path, exist_ok=True)

    for c in CHART_TYPES:
        url = f"https://www.data.jma.go.jp/airinfo/data/pict/hbc/{c}.pdf"
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code == 200:
                current_content = res.content
                current_hash = hashlib.md5(current_content).hexdigest()
                
                # 同一フォルダ内の既存ファイルとハッシュ(指紋)を比較
                is_new = True
                for existing_file in os.listdir(path):
                    if existing_file.startswith(f"CHART_{c}"):
                        file_full_path = os.path.join(path, existing_file)
                        with open(file_full_path, "rb") as f:
                            if hashlib.md5(f.read()).hexdigest() == current_hash:
                                is_new = False
                                break
                
                if is_new:
                    filename = f"CHART_{c}_{now.strftime('%Y%m%d%H%M')}.pdf"
                    with open(os.path.join(path, filename), "wb") as f:
                        f.write(current_content)
                    print(f"  [NEW] {filename} captured.")
        except: pass

def cleanup_github_repo(days):
    limit = datetime.now() - timedelta(days=days)
    for root, dirs, files in os.walk(BASE_DIR, topdown=False):
        if ".git" in root or ".github" in root: continue
        for name in files:
            file_path = os.path.join(root, name)
            try:
                # フォルダ名 YYYY/MM/DD から日付を計算
                rel = os.path.relpath(file_path, BASE_DIR)
                parts = rel.split(os.sep)
                if len(parts) >= 3:
                    file_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    if file_date < limit:
                        os.remove(file_path)
            except: pass
        if not os.listdir(root) and root != ".":
            try: os.rmdir(root)
            except: pass

if __name__ == "__main__":
    main()
