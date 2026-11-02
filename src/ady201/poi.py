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
    pois = pois.to_crs(target_crs).clip(boundary.to_crs(target_crs)).reset_index(drop=True)

    return pois



def get_cell_pois(province_n, amenity, cell_points):
    categories = [amenity] if isinstance(amenity, str) else list(amenity)
    pois = get_pois(province_n, categories)

    points = cell_points.copy().reset_index(drop=True)

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

    for radius_m in (100, 200, 500, 1000, 2000, 5000):
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


