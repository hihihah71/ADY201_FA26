# Giai đoạn 09 — Ghép và xuất bảng feature

## Nhiệm vụ tổng quát

Ghép cell, POI feature và road feature thành một bảng cuối có đúng một hàng cho mỗi cell.

Giai đoạn này chưa cần tạo chỉ số tổng hợp. Giữ các cột gốc để kết quả dễ kiểm tra và giải thích.

## Luồng

```text
cells
  + cell_poi_features
  + cell_road_features
          ↓ left join theo cell_id
   cell_features GeoDataFrame
          ├── GeoParquet có geometry
          └── CSV không có geometry
```

## Những thứ cần thay đổi

- Thêm `build_cell_features()` vào `analysis.py`.
- Không thêm giao lộ, tỷ lệ loại đường hoặc score ở phiên bản đầu.
- DuckDB chỉ tạo view sau khi file output đã tồn tại.

## Các bước thực hiện

### Bước 1 — Ghép bằng left join

```python
def build_cell_features(cells, poi_features, road_features):
    features = cells.merge(poi_features, on="cell_id", how="left")
    features = features.merge(road_features, on="cell_id", how="left")
    return features
```

Luôn bắt đầu từ `cells` để cell không có POI hoặc road vẫn xuất hiện.

### Bước 2 — Xử lý giá trị thiếu

- Các cột `*_count_*`, `road_length_*` và `road_density_*`: điền `0` sau khi xác nhận bước tính đã chạy thành công.
- Các cột `nearest_*_m`: giữ null nếu cả tỉnh không có category đó.
- Không điền khoảng cách nearest bằng `0`; `0` có nghĩa dịch vụ nằm đúng tại điểm đại diện.

### Bước 3 — Thêm region và sắp xếp cột

Thứ tự nên là:

1. `region_id`, `cell_id`, `cell_area_km2`.
2. Count POI theo category và bán kính.
3. Khoảng cách nearest.
4. Road length và road density.
5. `geometry`.

### Bước 4 — Kiểm tra khóa

```python
assert len(features) == len(cells)
assert features["cell_id"].is_unique
assert features["cell_id"].notna().all()
```

Thêm kiểm tra:

- Count, distance, length và density không âm.
- Với mỗi category: count 500 m không lớn hơn 1.000 m; count 1.000 m không lớn hơn 2.000 m.
- Geometry và CRS còn nguyên.

### Bước 5 — Xuất hai định dạng

```python
features.to_parquet(parquet_path)
features.drop(columns="geometry").to_csv(csv_path, index=False)
```

Output:

```text
data/processed/{region_id}/cell_features.parquet
data/processed/{region_id}/cell_features.csv
```

### Bước 6 — Cho DuckDB đọc kết quả

Gọi `create_feature_view()` từ giai đoạn 03, sau đó chạy:

```sql
SELECT
    region_id,
    COUNT(*) AS cells,
    AVG(nearest_hospital_m) AS avg_nearest_hospital_m
FROM cell_features
GROUP BY region_id;
```

## Data dictionary tối thiểu

Tạo `data/processed/data_dictionary.md`. Với mỗi cột, ghi:

- Ý nghĩa.
- Đơn vị.
- Cách tính.
- Null hoặc `0` có nghĩa gì.

## Kiến thức cần học

- Khóa chính, left join và duplicate key.
- Khác nhau giữa `0` và null.
- GeoParquet so với CSV.
- SQL `COUNT`, `AVG` và `GROUP BY`.

Từ khóa tìm thêm: `pandas left merge validate one_to_one`, `GeoPandas to_parquet`.

## Phân công

### Thành — trung bình/khó

- Viết `build_cell_features()`, xuất file và kết nối view DuckDB.

### Hiếu — trung bình/khó

- Viết toàn bộ kiểm tra khóa, null, đơn vị và quan hệ count.

### Quang — dễ/trung bình

- Viết data dictionary và mở thử CSV/GeoParquet để đối chiếu cột.

Review chéo: Quang chọn năm cột và yêu cầu Thành/Hiếu giải thích lại cách tính, đơn vị và ý nghĩa của null.

## Hoàn thành khi

- Bảng cuối có đúng một hàng cho mỗi cell.
- CSV và GeoParquet đều mở lại được.
- DuckDB truy vấn được output mà không cần import thủ công.
