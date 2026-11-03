# 13 — Thiết kế POI Overture-only

## Quyết định hiện tại

POI trong project chỉ lấy từ Overture Places.

```text
OSM PBF       -> boundary + roads
Overture      -> POI
```

Không thực hiện matching, dedup hoặc merge POI giữa OSM và Overture.

## Tải dữ liệu

```powershell
ady201 download-overture-poi
```

Downloader trong `overture.py`:

1. Load DuckDB `spatial` và `httpfs`.
2. Attach Overture latest release.
3. Tìm boundary quốc gia Việt Nam.
4. Lọc bảng `place` bằng bbox và `ST_Intersects`.
5. Làm phẳng các trường cần dùng.
6. Ghi GeoParquet ZSTD vào file tạm.
7. Atomic replace sang file đích khi hoàn thành.

Output:

```text
data/raw/overture/vietnam_places.parquet
```

Nếu file đã tồn tại, downloader dừng để tránh ghi đè:

```powershell
ady201 download-overture-poi --force
```

## Cột Overture đã làm phẳng

```text
overture_id
name
category
basic_category
category_hierarchy
confidence
operating_status
brand
address
locality
region
postcode
country
phone
website
longitude
latitude
geometry
source
```

CRS của file là OGC:CRS84/WGS84.

## Category config

`config/categories.json` chứa toàn bộ category đã quan sát trong snapshot dùng để xây cấu hình, được nhóm theo `category_hierarchy[0]`.

Feature pipeline chỉ dùng:

- Tên 13 group.
- Danh sách 22 important categories cho nearest.

Danh sách category chi tiết trong mỗi group giúp kiểm tra taxonomy và xây UI/report, nhưng `poi.py` lấy group trực tiếp từ hierarchy của từng POI.

## Đọc theo vùng

`get_pois(boundary)` không đọc toàn bộ Việt Nam vào RAM rồi mới lọc. Nó push filter longitude/latitude xuống Parquet, sau đó clip chính xác theo boundary.

Kiểm tra số POI của một vùng:

```python
from pyrosm import OSM
from ady201.poi import get_pois

osm = OSM("data/raw/osm/vietnam-261014.osm.pbf")
boundary = osm.get_boundaries(name="Hà Nội")
pois = get_pois(boundary)

print(len(pois))
print(pois["category_group"].value_counts())
```

## Kiểm tra file quốc gia

```python
import pyarrow.parquet as pq

path = "data/raw/overture/vietnam_places.parquet"
file = pq.ParquetFile(path)

print(file.metadata.num_rows)
print(file.schema.names)
```

Số POI phụ thuộc release Overture và sẽ thay đổi khi chạy `--force` ở thời điểm khác.

## Không còn áp dụng

- Amenity list OSM.
- `normalize-poi`.
- CSV POI chuẩn hóa.
- Matching OSM ID với Overture ID.
- Loại trùng giữa hai nguồn POI.
