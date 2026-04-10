import os
import requests
from datetime import datetime

# 全空港リスト（機長が以前構築された 110箇所の官署リスト）
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

def fetch_text_data(data_type):
    """
    NOAAから生テキストデータを取得する。
    XML形式ではなく、処理しやすいプレーンな形式（CSV/TXT）を狙います。
    """
    now = datetime.now()
    # 保存先パス: forecasts/YYYY/MM/DD
    save_path = f"forecasts/{now.strftime('%Y/%m/%d')}"
    os.makedirs(save_path, exist_ok=True)
    
    # 信頼性の高いNOAAのDataServer URL (TXT形式でリクエスト)
    url = f"https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource={data_type}s&requestType=retrieve&format=xml&hoursBeforeNow=2&stationString={','.join(AIRPORTS_ALL)}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            content = response.text
            # 取得したデータが空でないか確認
            if len(content) > 200:
                fname = f"{data_type.upper()}_All_{now.strftime('%Y%m%d')}.txt"
                file_full_path = os.path.join(save_path, fname)
                
                # 追記モードで保存
                with open(file_full_path, "a", encoding="utf-8") as f:
                    f.write(content + "\n")
                print(f"✅ {data_type.upper()} captured and appended to {fname}")
            else:
                print(f"⚠️ {data_type.upper()} data is too short, skipping.")
    except Exception as e:
        print(f"❌ Error fetching {data_type}: {e}")

if __name__ == "__main__":
    print(f"--- [TEXT SALVAGE START] {datetime.now()} ---")
    fetch_text_data("metar")
    fetch_text_data("taf")
    print("--- [FINISH] ---")
