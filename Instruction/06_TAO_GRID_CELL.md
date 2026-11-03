# 06 — Tạo grid cell 200 m

## Hàm chính

```python
from ady201.grid_cell import get_grid_cell

cells = get_grid_cell(boundary, 200)
```

## Luồng

1. Chuyển boundary sang UTM phù hợp bằng `estimate_utm_crs()`.
2. Tạo các polygon vuông 200 x 200 m phủ bbox.
3. Clip grid theo boundary.
4. Loại geometry rỗng.
5. Gán `cell_id` tuần tự.
6. Tính diện tích thực sau clip.
7. Tạo điểm đại diện bên trong mỗi cell.

## Cột output

| Cột | Ý nghĩa |
|---|---|
| `cell_id` | Khóa duy nhất dạng `cell_000000` |
| `cell_area_km2` | Diện tích cell sau clip |
| `geometry` | Polygon cell |
| `points` | Representative point dùng để đo khoảng cách |

Cell nằm sát ranh giới có thể nhỏ hơn 0,04 km² vì đã bị clip.

## Vì sao dùng representative point

`centroid` có thể nằm ngoài polygon lõm hoặc polygon bị cắt. `representative_point()` bảo đảm điểm nằm trong geometry và phù hợp để dùng làm vị trí đại diện.

## Kiểm tra

```python
assert cells["cell_id"].is_unique
assert cells["cell_id"].notna().all()
assert cells.geometry.notna().all()
assert (cells["cell_area_km2"] > 0).all()
```

Vẽ nhanh:

```python
cells.plot(facecolor="none", edgecolor="black", linewidth=0.1)
```

## Trạng thái hiện tại

Kích thước 200 m được truyền trực tiếp trong `regions.py`, không lấy từ `project.json`.

Với region `29_3`, file cuối có 85.249 cell.

## Lưu ý hiệu năng

Grid càng nhỏ thì số cell, số truy vấn KD-tree và số overlay road càng tăng. Đổi từ 200 m xuống 100 m có thể làm số cell tăng xấp xỉ bốn lần.
