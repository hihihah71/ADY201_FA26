# Giai đoạn 12 — Run-all toàn quốc và cập nhật

## Mục tiêu

Chạy pipeline cho toàn bộ region, tổng hợp quốc gia và hỗ trợ snapshot mới.

## Nhiệm vụ tổng quát

- Tạo `run-all` tuần tự trước.
- Cô lập lỗi theo region.
- Region workers chỉ ghi Parquet/GraphML.
- Một bước duy nhất cập nhật DuckDB.
- Tạo national feature view/model.
- Tạo batch summary và cơ chế cập nhật snapshot.

## Luồng

```text
Active region registry
        ↓ sequential/bounded workers
Per-region Parquet + GraphML
        ↓ single aggregation writer
DuckDB national views
        ↓
National scaler/model/maps/report
```

Luồng cập nhật:

```text
Kiểm tra Geofabrik timestamp/checksum
        ↓ nếu thay đổi
Register snapshot mới
        ↓
National POI → region runs → national aggregation
```

## Những thứ cần thay đổi

Tạo:

```text
src/ady201/batch.py
src/ady201/aggregation.py
src/ady201/models/national.py
tests/test_batch_failure_isolation.py
```

CLI:

```powershell
ady201 run-all --snapshot <id> --max-workers 1 --resume
ady201 runs failures --snapshot <id>
ady201 aggregate-national --snapshot <id> --model national-v1
```

Quy tắc:

- Bắt đầu `max_workers=1`.
- Chỉ tăng sau benchmark RAM/runtime.
- Một region lỗi không dừng batch.
- Không cho nhiều worker ghi cùng file DuckDB.
- National model dùng feature raw + scaler chung.
- Không overwrite model/snapshot cũ.
- Scheduled update là bước cuối, không làm trước khi manual run-all ổn định.

## Kiến thức cần học

### Bắt buộc

- Batch processing.
- Failure isolation.
- Bounded concurrency.
- Parquet partition/glob scan.
- National normalization/model versioning.
- Snapshot update policy.

### Tìm hiểu sâu bên ngoài

- `concurrent.futures`.
- DuckDB Hive partitioning.
- Job scheduler/Prefect; chỉ sau MVP.
- Incremental OSM `.osc.gz`; ngoài MVP.

## Phân công

### Thành

- Owner national DuckDB views, aggregation và data checks.
- Kiểm tra duplicate/cell coverage.

### Hiếu

- Owner worker resource limits và graph artifact reuse.
- Benchmark RAM/runtime, đề xuất `max_workers`.

### Quang

- Owner batch CLI, failure summary, national clustering/maps.
- Tạo dashboard/report trạng thái tĩnh.

### Review

- Thành kiểm tra national data integrity.
- Hiếu kiểm tra resource safety.
- Quang kiểm tra report/coverage.

## Đầu ra

- Batch result theo snapshot.
- Danh sách completed/failed/skipped regions.
- National feature dataset.
- National model có version.
- National maps và summary tables.

## Hoàn thành khi

- Batch tiếp tục khi một region cố ý bị lỗi.
- `--resume` chỉ chạy region/step thiếu hoặc stale.
- National aggregation không double-count buffer POI.
- Tất cả kết quả truy được snapshot, config và model version.

