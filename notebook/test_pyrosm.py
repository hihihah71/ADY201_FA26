from pathlib import Path
from pyrosm import OSM

pbf_path = Path("data/raw/osm/vietnam-261014.osm.pbf")

# Một vùng nhỏ để test
bbox = [
    105.82,  # min lon
    21.02,   # min lat
    105.84,  # max lon
    21.04    # max lat
]

osm = OSM(
    str(pbf_path)
)

boundary = osm.get_boundaries(name="Thanh Hóa")

geom = boundary.geometry.iloc[0]

boundary.plot()



# nodes, edges = osm.get_network(
#     network_type="walking",
#     nodes=True
# )

# print("=== NODES ===")
# print(nodes.head())

# print("\n=== EDGES ===")
# print(edges.head())

# print("\nĐọc thành công")
# print("Nodes:", len(nodes))
# print("Edges:", len(edges))