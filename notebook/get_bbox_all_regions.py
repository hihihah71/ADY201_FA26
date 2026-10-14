import json
from ady201.regions import get_bbox

with open('config/regions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

result_data = {}
for location in data["provinces"]:
    result_data[location] = get_bbox(location)


with open('Config/bbox.json', 'w', encoding='utf-8') as f:
    json.dump(result_data, f, ensure_ascii=False, indent=4)

