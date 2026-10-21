from dataclasses import dataclass
from pathlib import Path
from pyrosm import OSM
import geopandas as gpd
from ady201.grid_cell import get_grid_cell


@dataclass(frozen=True)
class RoadNetworkFiles:
    nodes: Path
    edges: Path

pbf_path = Path("../data/raw/osm/vietnam-261014.osm.pbf")
osm = OSM(
    str(pbf_path)
)
def read_network(ten_tinh, network_type):
    boundary = osm.get_boundaries(name=ten_tinh)
    osm_tinh = OSM(pbf_path,bounding_box=boundary.geometry.iloc[0])
    tim_network = osm_tinh.get_network(network_type=network_type,nodes=True)
    return tim_network

    
def create_buffers(cell_points,boundary,roads,radius_m):
    target_crs = cell_points.estimate_utm_crs()

    cell_points = cell_points.to_crs(target_crs)
    boundary = boundary.to_crs(target_crs)
    roads = roads.to_crs(target_crs)

    buffers = cell_points[["cell_id","geometry"]].copy()
    buffers["geometry"] = buffers.geometry.buffer(radius_m)
    buffers = buffers.clip(boundary)
    return buffers

def clip_roads_to_buffers(roads,buffers):
    roads=roads.to_crs(roads.estimate_utm_crs())
    buffers=buffers.to_crs(roads.crs)
    return gpd.overlay(
        roads[["geometry"]],
        buffers[["cell_id","geometry"]],
        how="intersection",
        keep_geom_type = True
    )

def calculate_road_features(roads,buffers,radius_m):
    road_parts = clip_roads_to_buffers(roads,buffers)
    road_parts["length_km"] = road_parts.length/1000

    lengths = (
        road_parts.groupby("cell_id")["length_km"].sum().rename(f"road_length_{radius_m}m_km")
    )

    result = buffers[["cell_id","geometry"]].copy()
    result["buffers_area_km2"] = result.area / 1_000_000
    result = result.join(lengths, on="cell_id")

    length_column = f"road_length_{radius_m}m_km"
    density_column = f"road_density_{radius_m}m_km_per_km2"
    result[length_column] = result[length_column].fillna(0)
    result[density_column] = result[length_column] / result["buffers_area_km2"]

    return result[["cell_id",length_column,density_column]]

def get_road_features(ten_tinh,network_type,cell_points):
    boundary = osm.get_boundaries(name=ten_tinh)
    roads = osm.get_network(network_type=network_type)

    buffers_500m = create_buffers(cell_points, boundary, roads, 500)
    buffers_1000m = create_buffers(cell_points, boundary, roads, 1000)

    road_500m = calculate_road_features(roads,buffers_500m,500)
    road_1000m = calculate_road_features(roads,buffers_1000m,1000)
    road_features = road_500m.merge(road_1000m,on="cell_id",how="left")

    return road_features