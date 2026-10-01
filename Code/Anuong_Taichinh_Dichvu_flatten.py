import csv
import json
from nt import write
INPUT_JSON = "data/Anuong_Taichinh_Dichvu.json"
OUTPUT_CSV = "Flatten/Anuong_Taichinh_Dichvu.csv"

fields = [ "id", "lat", "lon", "amenity", "name" ]

def clean_text(text):
    if text is None:
        return ""
    return str(text).strip()

def get_coodinate(element):
    lat = element.get("lat")
    lon = element.get("lon")
    if not lat or not lon:
        lat = element.get("center", {}).get("lat")
        lon = element.get("center", {}).get("lon")
    return lat,lon

def flat_element(element):
    lat, lon = get_coodinate(element)
    id = element.get("id")
    amenity = element.get("tags", {}).get("amenity")
    name = element.get("tags", {}).get("name")

    if not(-90 <= lat <= 90 and -180 <= lon <= 180):
        return None

    if not amenity or not id:
        return None
    return {
        "id": id,
        "lat": lat,
        "lon": lon, 
        "amenity": clean_text(amenity),
        "name": clean_text(name)
    }
def main():
    with open(INPUT_JSON,"r",encoding="UTF-8") as f:
        data = json.load(f)

    with open(OUTPUT_CSV,"w",encoding="utf-8",newline="") as f:
        writer = csv.DictWriter(f,fields)
        writer.writeheader()
        for e in data["elements"]:
            cur_row = flat_element(e)
            writer.writerow(cur_row)


if __name__ == "__main__":
    main()  