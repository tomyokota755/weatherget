import os
import requests
from datetime import datetime

# 全空港リスト（機長が以前構築された110箇所以上のリスト）
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

def fetch_noaa(data_type):
    now = datetime.now()
    save_path = f"forecasts/{now.strftime('%Y/%m/%d')}"
    os.makedirs(save_path, exist_ok=True)
    
    # 信頼のNOAA API (XML形式で取得)
    url = f"https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource={data_type}s&requestType=retrieve&format=xml&hoursBeforeNow=2&stationString={','.join(AIRPORTS_ALL)}"
    
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200 and len(res.text) > 500:
            fname = f"{data_type.upper()}_All_{now.strftime('%Y%m%d')}.txt"
            # 追記モードで保存
            with open(os.path.join(save_path, fname), "a", encoding="utf-8") as f:
                f.write(res.text + "\n")
            print(f"✅ Captured {data_type.upper()}")
    except Exception as e:
        print(f"❌ Failed {data_type.upper()}: {e}")

if __name__ == "__main__":
    print(f"--- [TEXT MISSION START] {datetime.now()} ---")
    fetch_noaa("metar")
    fetch_noaa("taf")
    print("--- [FINISH] ---")
