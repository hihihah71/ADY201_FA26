# Giai đoạn 08 — Mật độ đường quanh cell

## Nhiệm vụ tổng quát

Với mỗi điểm đại diện, tính tổng chiều dài và mật độ đường trong bán kính 500 m và 1.000 m.

## Luồng

```text
cell points
    ↓ buffer 500/1000 m và clip theo tỉnh
vùng đo + road lines
    ↓ overlay intersection
đo đúng phần đường nằm trong từng vùng
    ↓ groupby cell_id
road length + road density
```

## Công thức

```text
road_length_km = tổng chiều dài đường theo mét / 1.000

buffer_area_km2 = diện tích buffer sau khi clip / 1.000.000

road_density_km_per_km2 = road_length_km / buffer_area_km2
```

## Những thứ cần thay đổi

- Thêm hàm road feature vào `analysis.py`.
- Chỉ dùng road lines từ `roads.parquet`.
- Không dùng nodes, graph, Dijkstra hoặc shortest path.

## Các bước thực hiện

### Bước 1 — Tạo buffer

Dùng lại `create_buffers()` của giai đoạn 07 với bán kính `500` và `1000`.

Boundary, cell points, buffer và road phải có cùng CRS mét.

### Bước 2 — Cắt đường theo từng buffer

```python
import geopandas as gpd


def clip_roads_to_buffers(roads, buffers):
    return gpd.overlay(
        roads[["geometry"]],
        buffers[["cell_id", "geometry"]],
        how="intersection",
        keep_geom_type=True,
    )
```

Phải cắt geometry. Nếu chỉ chọn đường có chạm buffer rồi cộng toàn bộ chiều dài, kết quả sẽ bị lớn hơn thực tế.

### Bước 3 — Tính feature cho một bán kính

```python
def calculate_road_features(roads, buffers, radius_m):
    road_parts = clip_roads_to_buffers(roads, buffers)
    road_parts["length_km"] = road_parts.length / 1000

    lengths = (
        road_parts.groupby("cell_id")["length_km"]
        .sum()
        .rename(f"road_length_{radius_m}m_km")
    )

    result = buffers[["cell_id", "geometry"]].copy()
    result["buffer_area_km2"] = result.area / 1_000_000
    result = result.join(lengths, on="cell_id")

    length_column = f"road_length_{radius_m}m_km"
    density_column = f"road_density_{radius_m}m_km_per_km2"
    result[length_column] = result[length_column].fillna(0)
    result[density_column] = result[length_column] / result["buffer_area_km2"]

    return result[["cell_id", length_column, density_column]]
```

### Bước 4 — Ghép hai bán kính

```python
road_500m = calculate_road_features(roads, buffers_500m, 500)
road_1000m = calculate_road_features(roads, buffers_1000m, 1000)
road_features = road_500m.merge(road_1000m, on="cell_id", how="left")
```

Lưu:

```text
data/processed/{region_id}/cell_road_features.parquet
```

## Kiểm tra kết quả

- Mỗi `cell_id` chỉ có một hàng.
- Chiều dài và mật độ không âm.
- Cell không có road nhận length và density bằng `0`.
- Không có `inf`; diện tích buffer phải lớn hơn 0.
- Cell sát biên dùng diện tích buffer sau khi clip, không dùng diện tích hình tròn đầy đủ.

Không bắt buộc `road_density_1000m` lớn hơn `road_density_500m`; density là tỷ lệ nên có thể tăng hoặc giảm.

## Kiến thức cần học

- `overlay(..., how="intersection")`.
- `GeoSeries.length`, `GeoSeries.area` và đổi đơn vị.
- `groupby().sum()`, `merge()` và `fillna()`.
- Sự khác nhau giữa tổng chiều dài và mật độ đường.

Từ khóa tìm thêm: `GeoPandas overlay intersection line polygon`, `road density km per km2`.

## Phân công

### Thành — trung bình/khó

- Review công thức, tên cột và kiểm tra đơn vị.

### Hiếu — trung bình/khó

- Viết hàm overlay, tổng chiều dài và mật độ cho hai bán kính.

### Quang — dễ/trung bình

- Vẽ một buffer cùng các đoạn đường đã cắt để kiểm tra trực quan.

Review chéo: Thành tính tay một cell; Hiếu giải thích kết quả cho Quang.

## Hoàn thành khi

- Có đủ bốn cột road length/density cho 500 m và 1.000 m.
- Kết quả chỉ dùng phần đường thật sự nằm trong buffer.
