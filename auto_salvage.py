import os
import requests
import re
from datetime import datetime, timedelta

# --- 基本設定 ---
BASE_DIR = "."
# 日本国内のほぼ全空港（TAF/METAR発行箇所を網羅）
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

def main():
    print(f"--- Global Salvage Mission Start: {datetime.now()} ---")
    
    # 1. METAR/TAF 取得 (全空港分)
    fetch_noaa_data("metar")
    fetch_noaa_data("taf")

    # 2. 時系列予報(PNG) 取得 (全空港分)
    fetch_jma_timelines()

    # 3. 専門天気図(PDF) 取得
    fetch_jma_charts()

    # 4. GitHub上の「軽量化」：まずは30日で設定
    # ※容量が厳しくなったらここを 14 (2週間) に変更します
    cleanup_github_repo(days=30)

    print("--- Mission Completed ---")

def fetch_noaa_data(data_type):
    # 大量のICAOを一度に送るとエラーになるため10個ずつ分割
    batch_size = 10
    for i in range(0, len(AIRPORTS_ALL), batch_size):
        batch = AIRPORTS_ALL[i:i+batch_size]
        icao_str = ",".join(batch)
        url = f"https://aviationweather.gov/api/data/{data_type}?ids={icao_str}&format=raw&hours=6&mostrecent=false"
        try:
            res = requests.get(url, timeout=30)
            if res.status_code == 200:
                # TAFは'='で区切り、METARは改行で区切る
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
        # 月を跨ぐ場合の処理
        if day_val > now.day + 1: target_date -= timedelta(days=28)
        
        path = os.path.join(target_date.strftime("%Y"), target_date.strftime("%m"), target_date.strftime("%d"))
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, f"{data_type.upper()}_All_{target_date.strftime('%Y%m%d')}.txt")
        
        # 重複チェックして追記
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
    # 全空港の時系列予報をトライ
    for icao in AIRPORTS_ALL:
        url = f"https://www.jma.go.jp/bosai/aviation/data/v3/chart/timeline/{icao}.png"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                with open(os.path.join(path, f"{icao}_Timeline_{now.strftime('%H%M')}.png"), "wb") as f:
                    f.write(res.content)
        except: pass

def fetch_jma_charts():
    charts = ["ASAS", "SPAS", "AUPQ35", "AUPQ78"]
    now = datetime.now()
    path = os.path.join(now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    os.makedirs(path, exist_ok=True)
    for c in charts:
        url = f"https://www.data.jma.go.jp/airinfo/data/pict/hbc/{c}.pdf"
        try:
            res = requests.get(url, timeout=20)
            if res.status_code == 200:
                with open(os.path.join(path, f"CHART_{c}_{now.strftime('%H%M')}.pdf"), "wb") as f:
                    f.write(res.content)
        except: pass

def cleanup_github_repo(days):
    limit = datetime.now() - timedelta(days=days)
    for root, dirs, files in os.walk(BASE_DIR, topdown=False):
        if ".git" in root: continue
        for name in files:
            file_path = os.path.join(root, name)
            try:
                # フォルダ名 YYYY/MM/DD から日付判定
                p = rel_path = os.path.relpath(file_path, BASE_DIR).split(os.sep)
                file_date = datetime(int(p[0]), int(p[1]), int(p[2]))
                if file_date < limit:
                    os.remove(file_path)
            except: pass
        if not os.listdir(root) and root != ".":
            try: os.rmdir(root)
            except: pass

if __name__ == "__main__":
    main()
