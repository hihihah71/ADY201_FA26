# Giai đoạn 11 — Tự động hóa một region

## Mục tiêu

Gộp các module thành pipeline một lệnh, có trạng thái, cache và resume.

## Nhiệm vụ tổng quát

- Tạo CLI `run-region`.
- Xác định dependency giữa steps.
- Ghi run/step state vào DuckDB.
- Tạo artifact manifest và cache key.
- Hỗ trợ `--resume`, `--from-step`, `--to-step`.
- Tách lỗi validation khỏi lỗi tạm thời.

## Luồng

```text
CLI + region_id + snapshot_id
        ↓ create RunContext
Step dependency runner
        ↓
Artifacts + state + logs
        ↓
Regional outputs
```

## Những thứ cần thay đổi

Tạo:

```text
src/ady201/cli.py
src/ady201/pipeline.py
src/ady201/storage/artifacts.py
src/ady201/storage/state.py
tests/test_pipeline_resume.py
```

Step list:

```text
validate_environment
prepare_boundaries
extract_region_pbf
build_walking_graph
build_driving_graph
generate_hexagons
select_region_pois
snap_pois
snap_cells
calculate_accessibility
calculate_service_features
calculate_road_features
build_feature_matrix
calculate_indices
cluster_within_region
render_outputs
```

Cache key gồm:

```text
step + snapshot + boundary version + region
+ config hash + code version + input checksums
```

## Kiến thức cần học

### Bắt buộc

- CLI command design.
- Dependency graph đơn giản.
- Idempotency.
- Checksum/cache invalidation.
- Retry/resume.
- Structured logging.

### Tìm hiểu sâu bên ngoài

- Typer.
- Content-addressed artifacts.
- Workflow engines; chưa cần dùng ngay.

## Phân công

### Thành

- Owner DuckDB run/step state và transaction.
- Đảm bảo SQL tự chạy đúng step.

### Hiếu

- Định nghĩa dependency/caching cho graph và accessibility.
- Tạo failure test tại các step nặng.

### Quang

- Owner CLI commands, progress/status và summary report.
- Viết smoke test end-to-end.

### Review

- Cả nhóm chạy pipeline trên máy riêng.
- Thành kiểm tra state.
- Hiếu kiểm tra không rebuild graph sai.

## Đầu ra

```powershell
ady201 run-region --region hanoi --snapshot <id>
ady201 run-region --region hanoi --snapshot <id> --resume
```

## Hoàn thành khi

- Hà Nội chạy end-to-end một lệnh.
- Đà Nẵng chạy chỉ bằng thay `region_id`.
- Lỗi ở clustering không làm build lại graph khi resume.

