import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pathlib import Path
from pyrosm import OSM
import geopandas as gpd
import pandas as pd
from ady201.analys import count_pois, find_nearest
from ady201.grid_cell import get_grid_cell
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
    boundary = osm.get_boundaries(
        name=province_n
    )
    if boundary is None or boundary.empty:
        raise ValueError(f"Không tìm thấy ranh giới: {province_n}")
    osm = OSM(
        str(pbf_path),
        bounding_box=boundary.to_crs(4326).geometry.union_all(),
    )
    pois = osm.get_pois(
        custom_filter={"amenity": amenity}
    )
    target_crs = boundary.estimate_utm_crs()
    if pois is None or pois.empty:
        return gpd.GeoDataFrame(
            columns=["amenity", "geometry"], geometry="geometry", crs=target_crs
        )
    pois = pois.to_crs(target_crs).clip(boundary.to_crs(target_crs))

    return pois



def get_cell_pois(province_n, amenity, cell_points):
    categories = [amenity] if isinstance(amenity, str) else list(amenity)
    pois = get_pois(province_n, categories)

    points = cell_points.copy()

    if "points" in points.columns:
        points = points.set_geometry("points")

    target_crs = points.estimate_utm_crs()
    points = points.to_crs(target_crs)
    pois = pois.to_crs(target_crs)

    points = gpd.GeoDataFrame(
        {"cell_id": points["cell_id"]},
        geometry=points.geometry.rename("geometry"),
        crs=points.crs,
    )

    points["geometry"] = points.geometry.representative_point()

    pois = pois.copy()
    pois["category"] = pois["amenity"]
    pois["geometry"] = pois.geometry.representative_point()

    result = pd.DataFrame(points[["cell_id"]]).copy()

    for radius_m in (500, 1000, 2000):
        buffers = points.copy()
        buffers["geometry"] = points.geometry.buffer(radius_m)

        counts = count_pois(
            pois,
            buffers,
            radius_m,
            categories,
        )

        result = result.merge(
            counts,
            on="cell_id",
            how="left",
            validate="one_to_one",
        )

        count_columns = [
            f"{category}_count_{radius_m}m"
            for category in categories
        ]

        result[count_columns] = (
            result[count_columns].fillna(0).astype("int64")
        )

    for category in categories:
        nearest = find_nearest(points, pois, category)

        result = result.merge(
            nearest,
            on="cell_id",
            how="left",
            validate="one_to_one",
        )

    return result

