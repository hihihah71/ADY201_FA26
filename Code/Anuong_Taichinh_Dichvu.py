import requests
import json
import time

left = 20.5645154
right = 21.3854176
up = 105.2889615
down = 106.0200407

url = "https://overpass-api.de/api/interpreter"
headers = {
    "User-Agent": "urban-accessibility-study/1.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json",
}

height = abs(left - right)
width = abs(up - down)

div_height = height 
div_width = width 

coor_x1 = left 
coor_y1 = up 
coor_x2 = left + div_height
coor_y2 = up + div_width

all_elements = []

while coor_y1 < down:
    query = f"""
    [out:json][timeout:60];
    nwr["amenity"~"^(restaurant|cafe|fast_food|food_court|bank|atm|post_office|marketplace|community_centre)$"]
    ({coor_x1},{coor_y1},{coor_x2},{coor_y2});
    out center;
    """
    
    r = requests.post(url, headers=headers, data={"data": query}, timeout=90)
    r.raise_for_status()
    data = r.json() 

    if "elements" in data:
        all_elements.extend(data["elements"])

    coor_x1 += div_height
    
    if coor_x1 >= right:
        coor_x1 = left
        coor_y1 += div_width
        
    coor_x2 = coor_x1 + div_height
    coor_y2 = coor_y1 + div_width
    
    time.sleep(1)

final_data = {
    "version": 0.6,
    "elements": all_elements
}

with open("quan_an.json", "w", encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)