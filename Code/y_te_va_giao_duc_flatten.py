import json
import csv
from pathlib import Path

INPUT_JSON = "Data/y_te_va_giao_duc_poi.json"
OUTPUT_CSV = "Flatten/y_te_va_giao_duc_poi.csv"

fields = [
    "id", "lat", "lon", "amenity", "name",
]
rows = []
def get_coordinate(e):
    lat = e.get("lat")
    lon = e.get("lon")

    if lat is None or lon is None:
        center = e.get("center",{})
        lat = center.get("lat")
        lon = center.get("lon")
    return lat, lon

def flatten(e):
    tags = e.get("tags")
    lat,lon = get_coordinate(e)

    if e.get("id") is None:
        return None

    if lat is None or lon is None:
        return None

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None

    row = {
        "id": e["id"],
        "name": tags.get("name"),
        "amenity": tags.get("amenity"),
        "lat": lat,
        "lon": lon
    }

    rows.append(row)


with open(INPUT_JSON,"r",encoding = "utf-8") as f:
    data = json.load(f)

for e in data.get('elements'):
    flatten(e)

with open(OUTPUT_CSV,"w",newline = "",encoding = "utf-8") as f:
    wri = csv.DictWriter(f,fieldnames = fields)
    wri.writeheader()
    wri.writerows(rows)