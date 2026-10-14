import argparse
from pathlib import Path

from ady201 import __version__
from ady201.poi import normalize_poi_file
from ady201.regions import get_bbox


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ady201")
    parser.add_argument("--version", action="version", version=__version__)

    commands = parser.add_subparsers(dest="command", required=True)
    normalize_command = commands.add_parser("normalize-poi")
    normalize_command.add_argument("source", type=Path)
    normalize_command.add_argument("destination", type=Path)

    get_bbox_command = commands.add_parser("get_bbox")
    get_bbox_command.add_argument("location", type=Path)

    return parser


def main(arguments: list[str] | None = None) -> int:
    parser = create_parser()
    options = parser.parse_args(arguments)

    if options.command == "normalize-poi":
        normalize_poi_file(options.source, options.destination)

    if options.command == "get_bbox":
        get_bbox(options.location)
        
    return 0
