from pathlib import Path
import geopandas as gpd
import pandas as pd


def create_buffers(cell_points: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame, radius_m: float) -> gpd.GeoDataFrame:
    buffers = cell_points[["cell_id", "geometry"]].copy()
    buffers["geometry"] = buffers.geometry.buffer(radius_m)
    buffers = buffers.clip(boundary)
    return buffers


def count_pois(pois: gpd.GeoDataFrame, buffers: gpd.GeoDataFrame, radius_m: float, categories: list) -> pd.DataFrame:
    joined = gpd.sjoin(
        pois[["category", "geometry"]],
        buffers[["cell_id", "geometry"]],
        how="inner",
        predicate="within",
    )

    counts = pd.crosstab(joined["cell_id"], joined["category"])
    counts = counts.reindex(columns=categories, fill_value=0)
    counts.columns = [f"{name}_count_{radius_m}m" for name in counts.columns]
    return counts.reset_index()


def find_nearest(cell_points: gpd.GeoDataFrame, pois: gpd.GeoDataFrame, category: str) -> pd.DataFrame:
    selected = pois[pois["category"] == category]

    if selected.empty:
        result = cell_points[["cell_id"]].copy()
        result[f"nearest_{category}_m"] = None
        return result

    nearest = gpd.sjoin_nearest(
        cell_points[["cell_id", "geometry"]],
        selected[["geometry"]],
        how="left",
        distance_col=f"nearest_{category}_m",
    )

    return nearest[["cell_id", f"nearest_{category}_m"]].drop_duplicates("cell_id")


