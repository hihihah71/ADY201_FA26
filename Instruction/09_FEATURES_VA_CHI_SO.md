# 09 — Ghép và xuất bảng feature

## Hàm ghép

```python
features = build_cell_features(
    cell_points,
    poi_features,
    road_features,
)
features = feature_process(features)
```

`build_cell_features()` dùng left join theo `cell_id`, nên mọi cell từ grid được giữ lại.

## Xử lý missing

`feature_process()` fill 0 cho các cột chứa:

- `count`.
- `road_length`.
- `road_density`.

Các cột nearest không được fill 0 vì 0 là khoảng cách hợp lệ.

## Kiểm tra khóa

Pipeline kiểm tra trước khi ghi:

```python
assert len(features) == len(cell_points)
assert features["cell_id"].is_unique
assert features["cell_id"].notna().all()
```

## Output duy nhất

```text
data/processed/{region_id}/cell_features.parquet
```

Ví dụ:

```text
data/processed/29_3/cell_features.parquet
```

Không có CSV output trong code hiện tại.

## Nhóm cột

### Cell

```text
cell_id
cell_area_km2
geometry
points
```

### POI trực tiếp

```text
poi_count
{group}_count
```

### POI theo khoảng cách

```text
nearest_{group}_m
{group}_count_{radius}m
nearest_{important_category}_m
```

`radius` thuộc `100, 200, 500, 1000, 2000, 5000`.

### Road

```text
road_length_500m_km
road_density_500m_km_per_km2
road_length_1000m_km
road_density_1000m_km_per_km2
```

## Trạng thái `29_3`

```text
85.249 rows
135 columns
CRS: WGS 84 / UTM zone 48N (EPSG:32648)
```

## Đọc file

```python
import geopandas as gpd

features = gpd.read_parquet(
    "data/processed/29_3/cell_features.parquet"
)
```

Từ notebook nằm trong `notebook/`, dùng `../data/...` hoặc dựa vào `Path.cwd()`.
