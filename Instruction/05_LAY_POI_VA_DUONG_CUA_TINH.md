# 05 — Đọc POI và đường của một tỉnh/thành

## Đầu vào

```text
province name
    ├── OSM PBF: boundary + roads
    └── Overture GeoParquet: POI
```

Ví dụ province name:

```text
Hà Nội
Thanh Hóa
```

## Boundary

`regions.py` tạo một Pyrosm reader toàn quốc rồi đọc boundary:

```python
boundary = osm.get_boundaries(name=province_n)
```

Boundary được truyền cho grid và POI. `network.py` đọc lại boundary khi tạo road feature.

## POI Overture

`poi.get_pois(boundary)` thực hiện:

1. Chuyển boundary sang WGS84.
2. Lấy bbox để push filter vào `gpd.read_parquet()`.
3. Clip POI chính xác theo boundary.
4. Loại `operating_status == permanently_closed`.
5. Lấy `category_hierarchy[0]` làm `category_group`.

Nguồn:

```text
data/raw/overture/vietnam_places.parquet
```

POI sau đó được chuyển sang CRS mét của cell trước khi tính khoảng cách.

## Road network OSM

Pipeline gọi:

```python
road_features = get_road_features(
    province_n,
    "walking",
    cell_points,
)
```

`network.py` lấy đường từ OSM PBF và tính feature cho buffer 500 m, 1000 m.

## Thứ tự thực tế

Trong `regions.get_region_features()`:

```text
boundary
  -> grid 200 m
  -> road features
  -> POI features
  -> merge
  -> fill missing
  -> one final parquet
```

## Không có file trung gian

Hàm không lưu `boundary.parquet`, `pois.parquet`, `roads.parquet` hoặc `cells.parquet`. Muốn debug một bước, gọi hàm tương ứng trong notebook và giữ kết quả trong bộ nhớ.

## Lỗi thường gặp

- Boundary rỗng: tên province không khớp OSM.
- Không tìm thấy Overture: chưa chạy downloader hoặc sai đường dẫn.
- Chạy đường lâu: overlay road buffer là bước nặng nhất.
- Thiếu RAM: giảm vùng thử nghiệm hoặc chạy một tỉnh nhỏ trước.
