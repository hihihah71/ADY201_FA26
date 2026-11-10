import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OVERTURE_POI_PATH = PROJECT_ROOT / "data/raw/overture/vietnam_places.parquet"
VIETNAM_BOUNDARY_SEARCH_BBOX = (100.0, 0.0, 105.0, 25.0)
OVERTURE_LATEST_DATABASE = "https://stac.overturemaps.org/latest.ddb"


@dataclass(frozen=True)
class OvertureDownloadResult:
    output_path: Path
    row_count: int
    size_bytes: int


def _load_extensions(connection):
    for name in ("spatial", "httpfs"):
        try:
            connection.execute(f"LOAD {name}")
        except duckdb.Error:
            connection.execute(f"INSTALL {name}")
            connection.execute(f"LOAD {name}")


def _sql_string(value):
    return str(value).replace("'", "''")


def download_vietnam_places(
    output_path=DEFAULT_OVERTURE_POI_PATH,
    *,
    overwrite=False,
):
    output_path = Path(output_path).resolve()
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"File already exists: {output_path}. Use --force to replace it."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(
        f".{output_path.stem}.{uuid4().hex}.partial.parquet"
    )
    xmin, ymin, xmax, ymax = VIETNAM_BOUNDARY_SEARCH_BBOX
    connection = duckdb.connect()

    try:
        print("Loading DuckDB spatial extensions...")
        _load_extensions(connection)
        connection.execute("SET s3_region = 'us-west-2'")
        connection.execute("SET preserve_insertion_order = false")
        connection.execute("PRAGMA enable_progress_bar")

        print("Connecting to the latest Overture release...")
        connection.execute(
            f"ATTACH '{OVERTURE_LATEST_DATABASE}' AS overture (READ_ONLY)"
        )

        print("Reading the Vietnam boundary...")
        connection.execute(
            f"""
            CREATE TEMP TABLE vietnam_boundary AS
            SELECT
                ST_Union_Agg(geometry) AS geometry,
                min(bbox.xmin) AS xmin,
                min(bbox.ymin) AS ymin,
                max(bbox.xmax) AS xmax,
                max(bbox.ymax) AS ymax
            FROM overture.division_area
            WHERE subtype = 'country'
              AND country = 'VN'
              AND bbox.xmin BETWEEN {xmin} AND {xmax}
              AND bbox.ymin BETWEEN {ymin} AND {ymax}
            """
        )

        found = connection.execute(
            "SELECT geometry IS NOT NULL FROM vietnam_boundary"
        ).fetchone()[0]
        if not found:
            raise RuntimeError("Vietnam boundary was not found in Overture.")

        for axis in ("xmin", "ymin", "xmax", "ymax"):
            connection.execute(
                f"SET VARIABLE vietnam_{axis} = "
                f"(SELECT {axis} FROM vietnam_boundary)"
            )

        print("Downloading Vietnam POIs to GeoParquet...")
        connection.execute(
            f"""
            COPY (
                SELECT
                    p.id AS overture_id,
                    p.names.primary AS name,
                    p.taxonomy.primary AS category,
                    p.basic_category,
                    p.taxonomy.hierarchy AS category_hierarchy,
                    p.confidence,
                    p.operating_status,
                    p.brand.names.primary AS brand,
                    p.addresses[1].freeform AS address,
                    p.addresses[1].locality AS locality,
                    p.addresses[1].region AS region,
                    p.addresses[1].postcode AS postcode,
                    p.addresses[1].country AS country,
                    p.phones[1] AS phone,
                    p.websites[1] AS website,
                    ST_X(p.geometry) AS longitude,
                    ST_Y(p.geometry) AS latitude,
                    p.geometry,
                    'overture' AS source
                FROM overture.place AS p
                CROSS JOIN vietnam_boundary AS vn
                WHERE p.bbox.xmin BETWEEN getvariable('vietnam_xmin')
                                      AND getvariable('vietnam_xmax')
                  AND p.bbox.ymin BETWEEN getvariable('vietnam_ymin')
                                      AND getvariable('vietnam_ymax')
                  AND ST_Intersects(vn.geometry, p.geometry)
            ) TO '{_sql_string(temporary_path.as_posix())}' (
                FORMAT PARQUET,
                COMPRESSION ZSTD
            )
            """
        )

        row_count = connection.execute(
            "SELECT count(*) FROM read_parquet(?)",
            [str(temporary_path)],
        ).fetchone()[0]
        os.replace(temporary_path, output_path)
        return OvertureDownloadResult(
            output_path,
            row_count,
            output_path.stat().st_size,
        )
    finally:
        connection.close()
        temporary_path.unlink(missing_ok=True)
