# 11 — Chạy pipeline cho một region

## CLI

```powershell
ady201 grf <province> <region_id>
```

Ví dụ Hà Nội:

```powershell
ady201 grf "Hà Nội" 29_3
```

Ví dụ Thanh Hóa:

```powershell
ady201 grf "Thanh Hóa" 38_1
```

`province` dùng để tìm boundary OSM. `region_id` chỉ xác định thư mục output.

## Luồng bên trong

```text
main.py
  -> get_region_features(region_id, province, "walking", OVERTURE_GROUPS)
      -> boundary
      -> get_grid_cell(boundary, 200)
      -> get_road_features(...)
      -> get_cell_pois(...)
      -> build_cell_features(...)
      -> feature_process(...)
      -> assertions
      -> to_parquet(...)
```

## Output

```text
data/processed/{region_id}/cell_features.parquet
```

Thư mục cha được tạo tự động. File hiện có sẽ bị ghi lại bởi `to_parquet()`.

## Chuẩn bị trước khi chạy

```powershell
Test-Path data\raw\osm\vietnam-261014.osm.pbf
Test-Path data\raw\overture\vietnam_places.parquet
```

Cả hai lệnh phải trả về `True`.

## Kiểm tra sau khi chạy

```python
import geopandas as gpd

features = gpd.read_parquet(
    "data/processed/29_3/cell_features.parquet"
)

print(features.shape)
print(features.crs)
assert features["cell_id"].is_unique
assert features["cell_id"].notna().all()
```

## Thời gian chạy

Pipeline không có progress log chi tiết. Bước đường có thể mất nhiều thời gian; terminal im lặng không nhất thiết là treo.

Kiểm tra process từ PowerShell khác:

```powershell
Get-Process python -ErrorAction SilentlyContinue |
    Select-Object Id, CPU, WorkingSet, StartTime
```

## Lỗi thường gặp

### Không tìm thấy boundary

Kiểm tra dấu tiếng Việt và tên trong OSM. Không dùng tên viết tắt nếu OSM không có.

### Duplicate labels khi merge/reindex

Nguồn feature phải có một dòng cho mỗi `cell_id`. Kiểm tra:

```python
assert poi_features["cell_id"].is_unique
assert road_features["cell_id"].is_unique
```

### Thiếu file Overture

```powershell
ady201 download-overture-poi
```

### Chạy lại tốn thời gian

Nếu lỗi xảy ra sau khi đã có `cell_features.parquet`, phân tích và đánh giá trực tiếp trên file này; không chạy lại `grf` khi không cần thay feature nguồn.
