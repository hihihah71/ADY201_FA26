# Giai đoạn 04 — Snapshot PBF và boundary

## Mục tiêu

Quản lý Vietnam PBF và ranh giới tỉnh/thành có version, checksum và khả năng tái lập.

## Nhiệm vụ tổng quát

- Tải/register Vietnam PBF snapshot.
- Đọc timestamp bằng Osmium.
- Tính checksum và lưu manifest.
- Thu thập/validate boundary cấp tỉnh.
- Tạo analysis boundary và buffered extraction boundary.

## Luồng

```text
Geofabrik Vietnam PBF
        ↓ version + checksum
Vietnam snapshot

Boundary source
        ↓ validate/project/buffer
analysis_boundary + extraction_boundary
```

## Những thứ cần thay đổi

Tạo:

```text
data/raw/osm/vietnam-{snapshot_id}.osm.pbf
data/manifests/{snapshot_id}.json
data/boundary/{boundary_snapshot_id}/{region_id}.geojson
src/ady201/registry/snapshots.py
src/ady201/registry/boundaries.py
```

Quy tắc:

- Không dùng file `latest` mà không ghi timestamp.
- Không overwrite snapshot cũ.
- Boundary lưu EPSG:4326.
- Buffer được tạo trong CRS theo mét rồi chuyển lại EPSG:4326.
- Không hard-code số lượng tỉnh/thành.
- Registry phải được kiểm tra thủ công trước `enabled=true`.

## Kiến thức cần học

### Bắt buộc

- File checksum.
- Osmium `fileinfo`.
- Polygon/MultiPolygon validity.
- CRS transform và buffer theo mét.
- Administrative boundary.

### Tìm hiểu sâu bên ngoài

- Geofabrik snapshot/update files.
- Osmium boundary extraction.
- Shapely `make_valid`.
- UTM zone selection.

## Phân công

### Thành

- Thiết kế snapshot/boundary metadata trong DuckDB.
- Viết quality checks cho geometry và registry.

### Hiếu

- Viết download/register PBF và Osmium wrapper.
- Viết boundary buffer.

### Quang

- Chuẩn hóa tên/slug region.
- Vẽ boundary preview và tạo validation report.

### Review

- Thành kiểm tra metadata.
- Hiếu kiểm tra CRS/buffer.
- Quang kiểm tra trực quan boundary.

## Đầu ra

- Một Vietnam PBF có snapshot ID.
- Boundary registry hợp lệ.
- Boundary gốc và buffer cho region thử nghiệm.

## Hoàn thành khi

- Có thể truy ra URL, timestamp và checksum của PBF.
- Hà Nội/Đà Nẵng boundary hợp lệ và buffer đúng đơn vị mét.

