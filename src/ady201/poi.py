import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OVERTURE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "overture"
    / "vietnam_places.parquet"
)
CATEGORIES_PATH = PROJECT_ROOT / "config" / "categories.json"

with CATEGORIES_PATH.open("r", encoding="utf-8") as file:
    CATEGORY_CONFIG = json.load(file)

OVERTURE_GROUPS = list(CATEGORY_CONFIG["groups"])
NEAREST_CATEGORIES = list(CATEGORY_CONFIG["nearest_categories"])
POI_RADII_M = (100, 200, 500, 1000, 2000, 5000)


def get_pois(boundary):
    boundary_wgs84 = boundary.to_crs(4326)
    minx, miny, maxx, maxy = boundary_wgs84.total_bounds

    pois = gpd.read_parquet(
        OVERTURE_PATH,
        filters=[
            ("longitude", ">=", minx),
            ("longitude", "<=", maxx),
            ("latitude", ">=", miny),
            ("latitude", "<=", maxy),
        ],
    )

    pois = pois.to_crs(boundary_wgs84.crs)
    pois = gpd.clip(pois, boundary_wgs84).reset_index(drop=True)
    pois = pois[
        pois["operating_status"].fillna("").ne("permanently_closed")
    ].copy()
    pois["category_group"] = (
        pois["category_hierarchy"].str[0].fillna("unclassified")
    )

    return pois


def _to_xy(geodataframe):
    return np.column_stack(
        [geodataframe.geometry.x, geodataframe.geometry.y]
    )


def _nearest_distances(cell_xy, selected_pois):
    if selected_pois.empty:
        return np.full(len(cell_xy), np.nan)

    tree = cKDTree(_to_xy(selected_pois))
    distances, _ = tree.query(cell_xy, k=1, workers=-1)
    return distances


def prepare_cell_layers(cell_points):
    polygons = cell_points[["cell_id", "geometry"]].copy()
    points = (
        cell_points.copy()
        .reset_index(drop=True)
        .set_geometry("points")
    )
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

    total_counts = (
        assigned.groupby("cell_id")
        .size()
        .reindex(cell_ids, fill_value=0)
        .to_numpy()
    )

    group_counts = pd.crosstab(
        assigned["cell_id"],
        assigned["category_group"],
    )
    group_counts = group_counts.reindex(
        index=cell_ids,
        columns=categories,
        fill_value=0,
    )
    group_counts.index.name = "cell_id"
    group_counts.columns = [
        f"{category}_count" for category in group_counts.columns
    ]

    result = group_counts.reset_index()
    result.insert(1, "poi_count", total_counts)
    return result


def build_group_radius_features(points, pois, categories):
    cell_xy = _to_xy(points)
    features = {"cell_id": points["cell_id"].to_numpy()}

    for category in categories:
        selected = pois[pois["category_group"] == category]
        features[f"nearest_{category}_m"] = _nearest_distances(
            cell_xy,
            selected,
        )

        if selected.empty:
            for radius_m in POI_RADII_M:
                features[f"{category}_count_{radius_m}m"] = np.zeros(
                    len(points),
                    dtype="int64",
                )
            continue

        tree = cKDTree(_to_xy(selected))
        for radius_m in POI_RADII_M:
            features[f"{category}_count_{radius_m}m"] = (
                tree.query_ball_point(
                    cell_xy,
                    r=radius_m,
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
        features[f"nearest_{category}_m"] = _nearest_distances(
            cell_xy,
            selected,
        )

    return pd.DataFrame(features)


def get_cell_pois(boundary, categories, cell_points):
    pois = get_pois(boundary)
    polygons, points = prepare_cell_layers(cell_points)

    pois = pois.to_crs(points.crs)
    polygons = polygons.to_crs(points.crs)
    assigned = assign_pois_to_cells(pois, polygons)

    direct_features = build_direct_poi_features(
        points,
        assigned,
        categories,
    )
    radius_features = build_group_radius_features(
        points,
        pois,
        categories,
    )
    nearest_features = build_important_nearest_features(points, pois)

    result = direct_features.merge(
        radius_features,
        on="cell_id",
        how="left",
        validate="one_to_one",
    )
    return result.merge(
        nearest_features,
        on="cell_id",
        how="left",
        validate="one_to_one",
    )
