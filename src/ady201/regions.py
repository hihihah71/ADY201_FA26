from pathlib import Path
from pyrosm import OSM
from ady201.poi import get_cell_pois
from ady201.network import get_road_features
from ady201.analys import create_buffers, count_pois, find_nearest
from ady201.grid_cell import get_grid_cell
from ady201.feature_process import feature_process, build_cell_features

PROJECT_ROOT = Path(__file__).resolve().parents[2]
pbf_path = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "osm"
    / "vietnam-261014.osm.pbf"
)

osm = OSM(str(pbf_path))


def get_region_features(region_id, province_n, network_type, amenity):
    output_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / region_id
        / "cell_features.parquet"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    boundary = osm.get_boundaries(name=province_n)
    cell_points = get_grid_cell(boundary, 1000)
    road_features = get_road_features(province_n, network_type, cell_points)
    poi_features = get_cell_pois(province_n, amenity, cell_points)

    features = build_cell_features(cell_points, poi_features, road_features)
    features = feature_process(features)

    assert len(features) == len(cell_points)
    assert features["cell_id"].is_unique
    assert features["cell_id"].notna().all()

    features.to_parquet(output_path)



