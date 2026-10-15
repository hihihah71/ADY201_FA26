from pathlib import Path

import duckdb


# Đi từ src/ady201/database.py lên thư mục gốc của project.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "database" / "ady201.duckdb"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "001_schema.sql"


def connect_database(
    database_path: Path = DATABASE_PATH,
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(database_path), read_only=read_only)


def initialize_database(
    database_path: Path = DATABASE_PATH,
) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    connection = connect_database(database_path)

    try:
        connection.execute(schema_sql)
    finally:
        connection.close()
