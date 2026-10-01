import requests
import json
import time

url = "https://overpass-api.de/api/interpreter"

headers = {
    "User-Agent": "urban-accessibility-study/1.0"
}


left = 20.5645154
right = 21.3854176
up = 105.2889615
down = 106.0200407

h_block = 1
w_block = 1

height = (down - up) / h_block
width = (right - left) / w_block

cnt = 0

left_corner = left
while left_corner < right:
    up_corner = up
    while up_corner < down:

        query = f"""
            [out:json][timeout:90];
            nwr["amenity"~"^(parking|fuel|bus_station|police|fire_station)$"]
            ({left_corner}, {up_corner}, {left_corner + width}, {up_corner + height});
            out center;
        """

        r = requests.post(url, headers=headers, data = {"data": query}, timeout = 120)

        r.raise_for_status()
        data = r.json()

        with open("giao_thong_tien_ich_POI.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        cnt += 1
        up_corner += height
        
    left_corner += width



