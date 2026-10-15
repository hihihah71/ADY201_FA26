from pathlib import Path
from pyrosm import OSM

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OSM_PATH = PROJECT_ROOT / "data" / "raw" / "osm" / "vietnam-261014.osm.pbf"

def get_osm_path():
    if not OSM_PATH.exists():
        raise FileNotFoundError()

    if not OSM_PATH.is_file():
        raise ValueError()

    if not OSM_PATH.stat().st_size == 0:
        raise ValueError()

    return OSM_PATH

def check_osm():
    pbf_path = get_osm_path()
    try:
        OSM(str(pbf_path))
    except:
        raise RuntimeError(f"Couldn't open file {pbf_path}")

