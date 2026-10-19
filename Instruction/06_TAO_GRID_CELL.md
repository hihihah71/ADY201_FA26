# Giai đoạn 06 — Tạo grid cell

## Nhiệm vụ tổng quát

Chia tỉnh thành các ô vuông, cắt ô theo biên tỉnh và chọn một điểm đại diện cho mỗi ô.

## Luồng

```text
boundary ở CRS mét + cell_size_m
                ↓
           grid ô vuông
                ↓ clip theo tỉnh
        cell polygon trong tỉnh
                ↓ representative_point()
       một điểm đại diện mỗi cell
```

## Những thứ cần thay đổi

- Tạo `analysis.py` nếu file này chưa có.
- Viết hai hàm chính: `create_cells()` và `create_cell_points()`.
- Không dùng H3 và không cần gán POI cố định vào cell.

## Các bước thực hiện

### Bước 1 — Dùng boundary ở CRS mét

```python
boundary = boundary.to_crs(boundary.estimate_utm_crs())
```

Cell 1.000 m chỉ có ý nghĩa khi CRS dùng mét.

### Bước 2 — Tạo grid vuông

```python
import numpy as np
import geopandas as gpd
from shapely.geometry import box


def create_cells(boundary, cell_size_m):
    minx, miny, maxx, maxy = boundary.total_bounds
    polygons = []

    for x in np.arange(minx, maxx, cell_size_m):
        for y in np.arange(miny, maxy, cell_size_m):
            polygons.append(box(x, y, x + cell_size_m, y + cell_size_m))

    grid = gpd.GeoDataFrame(geometry=polygons, crs=boundary.crs)
    cells = gpd.clip(grid, boundary)
    cells = cells[~cells.geometry.is_empty].copy()
    cells["cell_id"] = [f"cell_{i:06d}" for i in range(len(cells))]
    cells["cell_area_km2"] = cells.area / 1_000_000
    return cells[["cell_id", "cell_area_km2", "geometry"]]
```

Các cell sát biên có thể nhỏ hơn ô đầy đủ vì đã bị cắt theo boundary. Đây là kết quả đúng.

### Bước 3 — Chọn điểm đại diện

```python
def create_cell_points(cells):
    points = cells[["cell_id"]].copy()
    points = gpd.GeoDataFrame(
        points,
        geometry=cells.geometry.representative_point(),
        crs=cells.crs,
    )
    return points
```

Dùng `representative_point()` thay cho `centroid` để điểm chắc chắn nằm trong phần cell đã clip.

### Bước 4 — Thêm `region_id` và lưu

```python
cells["region_id"] = region_id
cells.to_parquet(output_path)
```

Output:

```text
data/processed/{region_id}/cells.parquet
```

Không bắt buộc lưu `cell_points.parquet`; có thể tạo lại điểm từ cell khi cần.

## Kiểm tra kết quả

- `cell_id` không null và không trùng.
- Mỗi cell có area lớn hơn 0.
- Mỗi cell tạo đúng một Point.
- Point đại diện nằm trong cell tương ứng.
- CRS là CRS mét, không phải EPSG:4326.

## Kiến thức cần học

- Vòng lặp lồng nhau và `numpy.arange()`.
- `shapely.box()`, `gpd.clip()` và `representative_point()`.
- Sự khác nhau giữa polygon cell và point đại diện.

Từ khóa tìm thêm: `GeoPandas create square grid`, `Shapely representative_point`.

## Phân công

### Thành — trung bình

- Review cấu hình `cell_size_m` và cách tạo `cell_id` ổn định.

### Hiếu — trung bình/khó

- Viết `create_cells()` và `create_cell_points()`.

### Quang — dễ/trung bình

- Vẽ boundary, cell và point trên cùng một hình để kiểm tra trực quan.

Review chéo: Quang chọn ngẫu nhiên 10 cell để Thành/Hiếu xác nhận point nằm đúng trong cell.

## Hoàn thành khi

- `cells.parquet` có một polygon, một ID và một điểm đại diện có thể tạo lại cho mỗi cell.
- Không có H3 hoặc spatial join POI-to-cell ở giai đoạn này.
