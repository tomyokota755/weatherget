import os
import requests
import time
import random
import re
from datetime import datetime, timedelta

# ==========================================
# 🧠 司令部設定：基本パラメータ
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.hbc.co.jp/weather/aviation/"
}

# 重点空港（時系列予報 PNG取得対象）
TARGET_AIRPORTS = ["RJTT", "RJAA", "RJCC", "RJFF", "ROAH", "RJOA", "RJOT", "RJSA", "RJSK", "RJFK", "RORS"]

# 全空港リスト（METAR/TAF 取得対象）
AIRPORTS_ALL = [
    "RJAA", "RJTT", "RJBB", "RJCC", "RJFF", "RJGG", "ROAH", "RJOO", "RJSN", "RJNK",
    "RJNT", "RJNW", "RJNS", "RJNY", "RJNA", "RJNB", "RJNC", "RJNE", "RJNG", "RJNH",
    "RJNI", "RJNJ", "RJNL", "RJNM", "RJNN", "RJNO", "RJNP", "RJNQ", "RJNR", "RJNU", 
    "RJNV", "RJNX", "RJNZ", "RJOA", "RJOB", "RJOC", "RJOD", "RJOE", "RJOF", "RJOG", 
    "RJOH", "RJOI", "RJOJ", "RJOK", "RJOM", "RJON", "RJOP", "RJOQ", "RJOR", "RJOS", 
    "RJOT", "RJOU", "RJOV", "RJOW", "RJOY", "RJOZ", "RJSA", "RJSB", "RJSC", "RJSD", 
    "RJSE", "RJSF", "RJSG", "RJSH", "RJSI", "RJSJ", "RJSK", "RJSL", "RJSM", "RJSN", 
    "RJSO", "RJSP", "RJSQ", "RJSR", "RJSS", "RJSY", "RJTO", "RODN", "ROIG", "ROKJ", 
    "ROMY", "RORS", "ROTM", "ROYN", "RJTY", "RJTF", "RJTI", "RJCJ", "RJCH", "RJEC",
    "RJCW", "RJCK", "RJCM", "RJCB", "RJCN", "RJCO", "RJEB", "RJER", "RJEO", "RJCT",
    "RJTH", "RJAH", "RJAF", "RJAN", "RJAZ", "RJTR", "RJAL", "RJAK", "RJNF", "RJBE",
    "RJBD", "RJBK", "RJBT", "RJDC", "RJFS", "RJFE", "RJFC", "RJFA", "RJFN", "RJFY",
    "RJFZ", "RJFG", "RJDU", "ROMD", "ROKR", "RJAM", "RJAW"
]

# 専門天気図の種類
CHART_TYPES = ["ASAS", "SPAS", "AUPQ35", "AUPQ78", "AXJP", "WTJP"]

def main():
    print(f"--- [START] Fully Enhanced Salvage Mission: {datetime.now()} ---")
    
    # 1. METAR/TAF 取得 (NOAA APIを使用)
    fetch_noaa_data("metar")
    fetch_noaa_data("taf")
    
    # 2. 重点空港の時系列予報(PNG) 取得 (HBCミラー)
    fetch_hbc_timelines()
    
    # 3. 専門天気図(PDF) 取得 (HBCミラー)
    fetch_hbc_charts()
    
    # 4. 30日間経過した古いデータの削除
    cleanup_repo(days=30)
    
    print("--- [FINISH] All Checklists Complete ---")

# ==========================================
# 🛰️ データ取得関数
# ==========================================

def fetch_noaa_data(data_type):
    """NOAA (AWC) から METAR/TAF を取得"""
    now = datetime.now()
    save_path = f"forecasts/{now.strftime('%Y/%m/%d')}"
    os.makedirs(save_path, exist_ok=True)
    
    url = f"https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource={data_type}s&requestType=retrieve&format=xml&hoursBeforeNow=3&stationString={','.join(AIRPORTS_ALL)}"
    
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            fname = f"{data_type.upper()}_All_{now.strftime('%Y%m%d')}.txt"
            # 既存ファイルがあれば追記、なければ新規作成
            mode = "a" if os.path.exists(os.path.join(save_path, fname)) else "w"
            with open(os.path.join(save_path, fname), mode, encoding="utf-8") as f:
                f.write(res.text)
            print(f"✅ NOAA {data_type.upper()}: 収穫成功")
    except Exception as e:
        print(f"❌ NOAA {data_type.upper()}: 失敗 ({e})")

def fetch_hbc_timelines():
    """HBCのミラーサイトから時系列予報画像を収穫"""
    now = datetime.now()
    save_path = f"forecasts/{now.strftime('%Y/%m/%d')}"
    os.makedirs(save_path, exist_ok=True)

    for icao in TARGET_AIRPORTS:
        url = f"https://www.hbc.co.jp/weather/aviation/img/as/AS_{icao}.png"
        fname = f"{icao}_Forecast_{now.strftime('%H%M')}.png"
        path = os.path.join(save_path, fname)
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code == 200:
                with open(path, "wb") as f:
                    f.write(res.content)
                print(f"✅ Timeline: {icao}")
            time.sleep(random.uniform(2, 4))
        except: pass

def fetch_hbc_charts():
    """HBCのミラーサイトからPDF天気図を収穫"""
    now = datetime.now()
    save_path = f"forecasts/{now.strftime('%Y/%m/%d')}"
    os.makedirs(save_path, exist_ok=True)

    for c_type in CHART_TYPES:
        url = f"https://www.hbc.co.jp/weather/chart/pdf/{c_type.lower()}.pdf"
        fname = f"CHART_{c_type}_{now.strftime('%Y%m%d%H')}.pdf"
        path = os.path.join(save_path, fname)
        
        if os.path.exists(path): continue

        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code == 200:
                with open(path, "wb") as f:
                    f.write(res.content)
                print(f"✅ Chart: {c_type}")
            time.sleep(random.uniform(3, 5))
        except: pass

def cleanup_repo(days):
    """古いデータを削除してリポジトリの肥大化を防ぐ"""
    threshold = datetime.now() - timedelta(days=days)
    for root, dirs, files in os.walk("forecasts"):
        for file in files:
            fpath = os.path.join(root, file)
            if datetime.fromtimestamp(os.path.getmtime(fpath)) < threshold:
                try: os.remove(fpath)
                except: pass

if __name__ == "__main__":
    main()
