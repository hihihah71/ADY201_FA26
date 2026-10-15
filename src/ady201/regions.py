import json
import requests

url = "https://nominatim.openstreetmap.org/search"

headers = {
    "User-Agent": "urban-accessibility-study/1.0"
}

def get_bbox(location):
    params = {
        "q" : f"{location}, VietNam",
        "format": "jsonv2",
        "limit" : 1
    }
    r = requests.get(url, headers=headers, params = params, timeout=90)
    r.raise_for_status()
    data = r.json()

    print(data[0]['boundingbox'])

    return data[0]['boundingbox']
