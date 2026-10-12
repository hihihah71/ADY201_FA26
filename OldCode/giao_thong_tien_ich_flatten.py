import json
import csv
from nt import write

INPUT_JSON = "Data/giao_thong_tien_ich_POI.json"
OUTPUT_CSV = "Flatten/giao_thong_tien_ich_POI.csv"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []

for e in data.get('elements'):
    tags = e.get('tags')

    if 'center' not in e:
        lat = e['lat']
        lon = e['lon']
    else:
        center = e.get('center')
        lat = center['lat']
        lon = center['lon']

    if lat == None or lon == None or e.get('id', None) == None or tags.get('amenity', None) == None:
        continue

    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        continue

    rows.append({
        'id': e.get('id'),
        'lat': lat,
        'lon': lon,
        'amenity': tags.get('amenity'),
        'name': tags.get('name')
    })

field_names = ['id', 'lat', 'lon', 'amenity', 'name']

with open(OUTPUT_CSV, "w", newline="", encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=field_names)
    writer.writeheader()
    writer.writerows(rows)

print("Write successfully")


