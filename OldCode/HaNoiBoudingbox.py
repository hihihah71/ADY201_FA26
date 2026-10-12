import json
import requests

url = "https://nominatim.openstreetmap.org/search"

headers = {
    "User-Agent": "urban-accessibility-study/1.0"
}

params = {
    "q": "Hà Nội, Việt Nam",
    "format": "jsonv2",
    "limit" : 1  
}

r = requests.get(url, headers=headers, params = params, timeout=90)
r.raise_for_status()
data = r.json()

with open("HaNoiBoudingbox.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Đã tải dữ liệu thành công vào file dataOut.json!")