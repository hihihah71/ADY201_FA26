from dataclasses import dataclass
from pathlib import Path
from pyrosm import OSM


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




