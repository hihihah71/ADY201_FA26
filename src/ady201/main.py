import argparse
from pathlib import Path

from ady201 import __version__
from ady201.poi import normalize_poi_file
from ady201.database import initialize_database, check_database
from ady201.osm_input import check_osm
from ady201.regions import get_region_features


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ady201")
    parser.add_argument("--version", action="version", version=__version__)

    commands = parser.add_subparsers(dest="command", required=True)
    normalize_command = commands.add_parser("normalize-poi")
    normalize_command.add_argument("source", type=Path)
    normalize_command.add_argument("destination", type=Path)

    init_db_command = commands.add_parser("init-db")

    check_db_command = commands.add_parser("check-db")

    check_osm = commands.add_parser("check-osm")

    get_region_features = commands.add_parser("grf")
    get_region_features.add_argument("province")
    get_region_features.add_argument("region_id")

    return parser


def main(arguments: list[str] | None = None) -> int:
    parser = create_parser()
    options = parser.parse_args(arguments)

    if options.command == "normalize-poi":
        normalize_poi_file(options.source, options.destination)

    if options.command == "get_bbox":
        get_bbox(options.location)

    if options.command == "init-db":
        initialize_database()

    if options.command == "check-db":
        check_database()

    if options.command == "check-osm":
        check_osm()

    if options.command == "grf":
        network_type = "walking"
        amenity = ["cafe","fast_food","food_court","ice_cream","restaurant","bbq","pub","water_point"]
        get_region_features(options.region_id, options.province, network_type, amenity)
        
    return 0
