import requests
import json

url = "https://overpass-api.de/api/interpreter"

headers = {
    "User-Agent": "urban-accessibility-study/1.0"
}
query = """
[out:json][timeout:180];
(
nwr["amenity"~"^(hospital|clinic|doctors|dentist|pharmacy)$"](20.5645154,105.2889615,21.3854176,106.0200407);
nwr["amenity"~"^(school|kindergarten|college|university|library)$"](20.5645154,105.2889615,21.3854176,106.0200407);
);
out center;
"""

r = requests.post(url, data={"data": query}, headers = headers, timeout = 120)
r.raise_for_status()
data  = r.json()

with open("HaNoipoi.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Đã tải dữ liệu thành công vào file dataOut.json!")
