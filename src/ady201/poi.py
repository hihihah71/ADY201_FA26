import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pathlib import Path
from pyrosm import OSM
import geopandas as gpd

@dataclass(frozen=True)
class Poi:
    osm_type: str
    osm_id: int
    lat: float
    lon: float
    amenity: str
    name: str


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def get_coordinates(element: dict[str, Any]) -> tuple[float, float] | None:
    latitude = element.get("lat")
    longitude = element.get("lon")

    if latitude is None or longitude is None:
        center = element.get("center")
        if not isinstance(center, dict):
            return None
        latitude = center.get("lat")
        longitude = center.get("lon")

    if not isinstance(latitude, (int, float)):
        return None
    if not isinstance(longitude, (int, float)):
        return None
    if not -90 <= latitude <= 90:
        return None
    if not -180 <= longitude <= 180:
        return None

    return float(latitude), float(longitude)


def create_poi(element: dict[str, Any]) -> Poi | None:
    tags = element.get("tags")
    if not isinstance(tags, dict):
        return None

    amenity = clean_text(tags.get("amenity"))
    if amenity == "":
        return None

    coordinates = get_coordinates(element)
    if coordinates is None:
        return None

    osm_type = clean_text(element.get("type"))
    osm_id = element.get("id")
    if osm_type == "" or not isinstance(osm_id, int):
        return None

    latitude, longitude = coordinates

    return Poi(
        osm_type=osm_type,
        osm_id=osm_id,
        lat=latitude,
        lon=longitude,
        amenity=amenity,
        name=clean_text(tags.get("name")),
    )


def read_pois(source: Path) -> list[Poi]:
    with source.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Nội dung JSON phải là một object")

    elements = data.get("elements")
    if not isinstance(elements, list):
        raise ValueError("File JSON phải có danh sách elements")

    pois = []

    for element in elements:
        if not isinstance(element, dict):
            continue

        poi = create_poi(element)
        if poi is not None:
            pois.append(poi)

    return pois


def save_pois(pois: list[Poi], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    columns = ["osm_type", "osm_id", "lat", "lon", "amenity", "name"]

    with destination.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for poi in pois:
            writer.writerow(asdict(poi))


def normalize_poi_file(source: Path, destination: Path) -> int:
    pois = read_pois(source)
    save_pois(pois, destination)
    return len(pois)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
pbf_path = PROJECT_ROOT / "data" / "raw" / "osm" / "vietnam-261014.osm.pbf"

def get_pois(province_n, amenity):
    osm = OSM(str(pbf_path))

    # Đọc ranh giới từ PBF.
    boundary = osm.get_boundaries(
        boundary_type="administrative",
        name=province_n,
        custom_filter={"admin_level": ["4"]},
    )

    if boundary is None or boundary.empty:
        raise ValueError(
            f"Không tìm thấy ranh giới '{province_n}' trong PBF"
        )

    boundary = boundary.to_crs(epsg=4326)

    # Giới hạn khu vực đọc POI bằng bounding box.
    osm = OSM(
        str(pbf_path),
        bounding_box=boundary.total_bounds.tolist(),
    )

    if isinstance(amenity, str):
        amenity = [amenity]

    pois = osm.get_pois(
        custom_filter={"amenity": amenity}
    )

    if pois is None:
        return gpd.GeoDataFrame(
            geometry=[],
            crs="EPSG:4326",
        )

    if pois.empty:
        return pois

    # Lọc lại theo hình dạng ranh giới tỉnh.
    province_geometry = boundary.geometry.union_all()
    pois = pois.to_crs(boundary.crs)

    pois = pois.loc[
        pois.geometry.intersects(province_geometry)
    ].copy()

    return pois


pois = get_pois(
    province_n="Thanh Hóa",
    amenity=["hospital", "clinic", "pharmacy"]
)

pois.plot(figsize = (20,20),color = 'whitesmoke',edgecolor = 'black',linestyle= ':')