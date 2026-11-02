from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OVERTURE_POI_PATH = (
    PROJECT_ROOT / "data" / "raw" / "overture" / "vietnam_places.parquet"
)

# Used only to find Vietnam's country polygon efficiently. The POI query uses
# the bounds stored on that polygon, including any islands present in Overture.
VIETNAM_BOUNDARY_SEARCH_BBOX = (100.0, 0.0, 105.0, 25.0)
OVERTURE_LATEST_DATABASE = "https://stac.overturemaps.org/latest.ddb"


@dataclass(frozen=True)
class OvertureDownloadResult:
    output_path: Path
    row_count: int
    size_bytes: int


def _load_extension(connection: duckdb.DuckDBPyConnection, name: str) -> None:
    """Load a DuckDB extension, installing it on the first run if necessary."""
    try:
        connection.execute(f"LOAD {name}")
    except duckdb.Error:
        connection.execute(f"INSTALL {name}")
        connection.execute(f"LOAD {name}")


def _sql_string(value: Path | str) -> str:
    """Return a value safe to place inside a single-quoted SQL literal."""
    return str(value).replace("'", "''")


def download_vietnam_places(
    output_path: Path = DEFAULT_OVERTURE_POI_PATH,
    *,
    overwrite: bool = False,
) -> OvertureDownloadResult:
    """Download the latest Overture Places located inside Vietnam.

    The output is a flattened GeoParquet file in OGC:CRS84 (longitude/latitude),
    which can be opened directly with GeoPandas or queried with DuckDB.
    """
    output_path = Path(output_path).resolve()

    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"File already exists: {output_path}. Use --force to replace it."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(
        f".{output_path.stem}.{uuid4().hex}.partial.parquet"
    )

    search_xmin, search_ymin, search_xmax, search_ymax = (
        VIETNAM_BOUNDARY_SEARCH_BBOX
    )
    connection = duckdb.connect()

    try:
        print("Loading DuckDB spatial extensions...")
        _load_extension(connection, "spatial")
        _load_extension(connection, "httpfs")
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
              AND bbox.xmin BETWEEN {search_xmin} AND {search_xmax}
              AND bbox.ymin BETWEEN {search_ymin} AND {search_ymax}
            """
        )

        boundary_found = connection.execute(
            "SELECT geometry IS NOT NULL FROM vietnam_boundary"
        ).fetchone()[0]
        if not boundary_found:
            raise RuntimeError("Vietnam boundary was not found in Overture.")

        connection.execute(
            "SET VARIABLE vietnam_xmin = (SELECT xmin FROM vietnam_boundary)"
        )
        connection.execute(
            "SET VARIABLE vietnam_ymin = (SELECT ymin FROM vietnam_boundary)"
        )
        connection.execute(
            "SET VARIABLE vietnam_xmax = (SELECT xmax FROM vietnam_boundary)"
        )
        connection.execute(
            "SET VARIABLE vietnam_ymax = (SELECT ymax FROM vietnam_boundary)"
        )

        print("Downloading Vietnam POIs to GeoParquet...")
        output_sql = _sql_string(temporary_path.as_posix())
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
            ) TO '{output_sql}' (
                FORMAT PARQUET,
                COMPRESSION ZSTD
            )
            """
        )

        row_count = connection.execute(
            "SELECT count(*) FROM read_parquet(?)", [str(temporary_path)]
        ).fetchone()[0]

        # os.replace is atomic when source and destination are on the same drive.
        os.replace(temporary_path, output_path)
        return OvertureDownloadResult(
            output_path=output_path,
            row_count=row_count,
            size_bytes=output_path.stat().st_size,
        )
    finally:
        connection.close()
        if temporary_path.exists():
            temporary_path.unlink()
