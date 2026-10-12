# Giai đoạn 03 — DuckDB và trạng thái chạy

## Mục tiêu

Dùng một file DuckDB được Python tự khởi tạo; không thao tác qua pgAdmin hoặc import thủ công.

## Nhiệm vụ tổng quát

- Tạo database manager.
- Tự chạy SQL schema từ Python.
- Tạo bảng region, snapshot, run và step state.
- Tạo cơ chế transaction và quality query.
- Quy định chỉ một process ghi DuckDB tại một thời điểm.

## Luồng

```text
Python CLI
    ↓ duckdb.connect()
sql/*.sql
    ↓ tự động execute
data/database/ady201.duckdb
```

## Những thứ cần thay đổi

Tạo:

```text
data/database/                 # gitignored
sql/001_schema.sql
sql/002_registry.sql
sql/003_run_state.sql
sql/004_views.sql
src/ady201/storage/duckdb.py
src/ady201/storage/state.py
```

Bảng tối thiểu:

```text
region
snapshot
pipeline_run
pipeline_step_run
artifact_manifest
model_registry
```

Lệnh mục tiêu:

```powershell
ady201 db init
ady201 db migrate
ady201 db check
```

Quy tắc:

- SQL được lưu thành file có version.
- Python đọc và execute SQL.
- Không commit file `.duckdb`.
- Region workers ghi Parquet; bước aggregation duy nhất ghi DuckDB.

## Kiến thức cần học

### Bắt buộc

- DuckDB Python API.
- SQL DDL, table, view, primary/unique key.
- Transaction và rollback.
- Parquet scan.
- Spatial extension: `INSTALL/LOAD spatial`.

### Tìm hiểu sâu bên ngoài

- DuckDB concurrency model.
- DuckDB spatial functions.
- Schema migration đơn giản.

## Phân công

### Thành

- Thiết kế schema và SQL migrations.
- Viết database manager và quality queries.

### Hiếu

- Định nghĩa metadata graph/artifact cần lưu.
- Kiểm tra transaction khi step graph thất bại.

### Quang

- Tạo CLI `db init/check`.
- Tạo view/report cho trạng thái run.

### Review

- Hiếu review artifact schema.
- Quang chạy init từ database trống.
- Thành xác nhận schema output.

## Đầu ra

- `ady201.duckdb` được tạo tự động.
- Có run/step record.
- Có thể xóa database và dựng lại bằng lệnh.

## Hoàn thành khi

Một máy mới chạy `ady201 db init` mà không mở bất kỳ GUI database nào.

