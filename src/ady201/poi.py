import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OVERTURE_PATH = PROJECT_ROOT / "data/raw/overture/vietnam_places.parquet"
CATEGORIES_PATH = PROJECT_ROOT / "config/categories.json"

CATEGORY_CONFIG = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
OVERTURE_GROUPS = list(CATEGORY_CONFIG["groups"])
NEAREST_CATEGORIES = list(CATEGORY_CONFIG["nearest_categories"])
POI_RADII_M = (100, 200, 500, 1000, 2000, 5000)


def get_pois(boundary):
    boundary = boundary.to_crs(4326)
    minx, miny, maxx, maxy = boundary.total_bounds
    pois = gpd.read_parquet(
        OVERTURE_PATH,
        filters=[
            ("longitude", ">=", minx),
            ("longitude", "<=", maxx),
            ("latitude", ">=", miny),
            ("latitude", "<=", maxy),
        ],
    ).to_crs(4326)
    pois = gpd.clip(pois, boundary).reset_index(drop=True)
    pois["category_group"] = pois["category_hierarchy"].str[0].fillna(
        "unclassified"
    )
    return pois


def _to_xy(frame):
    return np.column_stack((frame.geometry.x, frame.geometry.y))


def _nearest_distances(cell_xy, pois):
    if pois.empty:
        return np.full(len(cell_xy), np.nan)
    return cKDTree(_to_xy(pois)).query(cell_xy, workers=-1)[0]


def prepare_cell_layers(cell_points):
    polygons = cell_points[["cell_id", "geometry"]].copy()
    points = cell_points.copy().reset_index(drop=True).set_geometry("points")
    return polygons, points


def assign_pois_to_cells(pois, polygons):
    assigned = gpd.sjoin_nearest(
        pois[["overture_id", "category_group", "geometry"]],
        polygons,
        how="inner",
    )
    return (
        assigned.sort_values(["overture_id", "cell_id"])
        .drop_duplicates("overture_id")
        .reset_index(drop=True)
    )


def build_direct_poi_features(points, assigned, categories):
    cell_ids = points["cell_id"].to_numpy()
    counts = pd.crosstab(assigned["cell_id"], assigned["category_group"]).reindex(
        index=cell_ids,
        columns=categories,
        fill_value=0,
    )
    counts.index.name = "cell_id"
    counts.columns = [f"{category}_count" for category in counts.columns]

    result = counts.reset_index()
    result.insert(
        1,
        "poi_count",
        assigned.groupby("cell_id").size().reindex(cell_ids, fill_value=0).to_numpy(),
    )
    return result


def build_group_radius_features(points, pois, categories):
    cell_xy = _to_xy(points)
    features = {"cell_id": points["cell_id"].to_numpy()}

    for category in categories:
        selected = pois[pois["category_group"] == category]
        features[f"nearest_{category}_m"] = _nearest_distances(cell_xy, selected)
        tree = None if selected.empty else cKDTree(_to_xy(selected))

        for radius in POI_RADII_M:
            features[f"{category}_count_{radius}m"] = (
                np.zeros(len(points), dtype="int64")
                if tree is None
                else tree.query_ball_point(
                    cell_xy,
                    r=radius,
                    return_length=True,
                    workers=-1,
                )
            )

    return pd.DataFrame(features)


def build_important_nearest_features(points, pois):
    cell_xy = _to_xy(points)
    features = {"cell_id": points["cell_id"].to_numpy()}
    for category in NEAREST_CATEGORIES:
        selected = pois[pois["category"] == category]
        features[f"nearest_{category}_m"] = _nearest_distances(cell_xy, selected)
    return pd.DataFrame(features)


def get_cell_pois(boundary, categories, cell_points):
    polygons, points = prepare_cell_layers(cell_points)
    pois = get_pois(boundary).to_crs(points.crs)
    assigned = assign_pois_to_cells(pois, polygons.to_crs(points.crs))

    merge_options = {
        "on": "cell_id",
        "how": "left",
        "validate": "one_to_one",
    }
    return (
        build_direct_poi_features(points, assigned, categories)
        .merge(build_group_radius_features(points, pois, categories), **merge_options)
        .merge(build_important_nearest_features(points, pois), **merge_options)
    )
