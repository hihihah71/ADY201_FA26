import argparse
from pathlib import Path

from ady201 import __version__
from ady201.poi import OVERTURE_GROUPS
from ady201.database import initialize_database, check_database
from ady201.osm_input import check_osm
from ady201.overture import DEFAULT_OVERTURE_POI_PATH, download_vietnam_places
from ady201.regions import get_region_features


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ady201")
    parser.add_argument("--version", action="version", version=__version__)

    commands = parser.add_subparsers(dest="command", required=True)
    init_db_command = commands.add_parser("init-db")

    check_db_command = commands.add_parser("check-db")

    check_osm = commands.add_parser("check-osm")

    get_region_features = commands.add_parser("grf")
    get_region_features.add_argument("province")
    get_region_features.add_argument("region_id")

    overture_command = commands.add_parser(
        "download-overture-poi",
        help="Download the latest Vietnam POIs from Overture Maps",
    )
    overture_command.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OVERTURE_POI_PATH,
        help=f"Output GeoParquet path (default: {DEFAULT_OVERTURE_POI_PATH})",
    )
    overture_command.add_argument(
        "--force",
        action="store_true",
        help="Replace the output file if it already exists",
    )

    return parser


def main(arguments: list[str] | None = None) -> int:
    parser = create_parser()
    options = parser.parse_args(arguments)

    if options.command == "init-db":
        initialize_database()

    if options.command == "check-db":
        check_database()

    if options.command == "check-osm":
        check_osm()

    if options.command == "grf":
        get_region_features(
            options.region_id,
            options.province,
            "walking",
            OVERTURE_GROUPS,
        )

    if options.command == "download-overture-poi":
        result = download_vietnam_places(
            options.output,
            overwrite=options.force,
        )

        size_mb = result.size_bytes / (1024 * 1024)
        print(f"Saved {result.row_count:,} POIs to: {result.output_path}")
        print(f"File size: {size_mb:.1f} MB")

    return 0
