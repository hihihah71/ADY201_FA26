# Giai đoạn 07 — POI quanh cell và POI gần nhất

## Nhiệm vụ tổng quát

Từ điểm đại diện của mỗi cell:

- Đếm từng loại POI trong 500 m, 1.000 m và 2.000 m.
- Tính khoảng cách thẳng tới POI gần nhất của từng loại.

## Luồng

```text
cell points + POI points cùng CRS mét
              ├── buffer 500/1000/2000 m → sjoin → count
              └── sjoin_nearest → nearest_*_m
                               ↓
                    cell_poi_features.parquet
```

## Những thứ cần thay đổi

- Thêm các hàm POI feature vào `analysis.py`.
- Không gán POI vào một cell duy nhất.
- Không dùng network distance. `nearest_*_m` là khoảng cách thẳng.
- Buffer của các cell được phép chồng nhau.

## Các bước thực hiện

### Bước 1 — Tạo buffer cho một bán kính

```python
def create_buffers(cell_points, boundary, radius_m):
    buffers = cell_points[["cell_id", "geometry"]].copy()
    buffers["geometry"] = buffers.geometry.buffer(radius_m)
    buffers = buffers.clip(boundary)
    return buffers
```

Việc clip buffer theo boundary bảo đảm chỉ đo phần thuộc tỉnh. Đây là buffer phân tích quanh cell, không phải boundary buffer để tải thêm road.

### Bước 2 — Đếm POI trong buffer

```python
import pandas as pd
import geopandas as gpd


def count_pois(pois, buffers, radius_m, categories):
    joined = gpd.sjoin(
        pois[["category", "geometry"]],
        buffers[["cell_id", "geometry"]],
        how="inner",
        predicate="within",
    )

    counts = pd.crosstab(joined["cell_id"], joined["category"])
    counts = counts.reindex(columns=categories, fill_value=0)
    counts.columns = [f"{name}_count_{radius_m}m" for name in counts.columns]
    return counts.reset_index()
```

Truyền `categories = ["hospital", "school", "supermarket", "transit"]`. Chạy hàm lần lượt với `500`, `1000`, `2000`, rồi left join vào danh sách đầy đủ `cell_id`. Sau join, điền `0` cho các cột count bị thiếu.

### Bước 3 — Tìm một category gần nhất

```python
def find_nearest(cell_points, pois, category):
    selected = pois[pois["category"] == category]

    if selected.empty:
        result = cell_points[["cell_id"]].copy()
        result[f"nearest_{category}_m"] = None
        return result

    nearest = gpd.sjoin_nearest(
        cell_points[["cell_id", "geometry"]],
        selected[["geometry"]],
        how="left",
        distance_col=f"nearest_{category}_m",
    )

    return nearest[["cell_id", f"nearest_{category}_m"]].drop_duplicates("cell_id")
```

Gọi với:

```python
for category in ["hospital", "school", "supermarket", "transit"]:
    nearest = find_nearest(cell_points, pois, category)
```

### Bước 4 — Ghép output

Bắt đầu từ danh sách đầy đủ `cell_id`, sau đó left join:

1. Count 500 m.
2. Count 1.000 m.
3. Count 2.000 m.
4. Bốn bảng nearest.

Lưu:

```text
data/processed/{region_id}/cell_poi_features.parquet
```

## Kiểm tra kết quả

- Mỗi `cell_id` chỉ có một hàng.
- Mọi count là số nguyên không âm.
- Với cùng category: `count_500m <= count_1000m <= count_2000m`.
- Khoảng cách không âm và có đơn vị mét.
- Category không tồn tại trong tỉnh có nearest là null, không phải `0`.
- Số hàng sau mỗi lần merge không tăng.

## Kiến thức cần học

- `buffer()`, spatial join và `predicate="within"`.
- `pd.crosstab()`, left join và `fillna(0)`.
- `sjoin_nearest()` và `distance_col`.
- Vì sao mọi layer phải cùng CRS mét.

Từ khóa tìm thêm: `GeoPandas sjoin buffer`, `GeoPandas sjoin_nearest distance_col`.

## Phân công

### Thành — trung bình/khó

- Viết phần count, merge ba bán kính và kiểm tra count tăng dần.

### Hiếu — trung bình/khó

- Viết phần nearest cho bốn category và xử lý category rỗng.

### Quang — dễ/trung bình

- Chọn vài cell, đếm/đo thủ công trên bản đồ và đối chiếu kết quả.

Review chéo: Thành review nearest; Hiếu review count; Quang giải thích vì sao một POI có thể được tính cho nhiều cell.

## Hoàn thành khi

- Có đủ 12 cột count và 4 cột nearest.
- Bảng có đúng một hàng cho mỗi cell.
- Không có H3, Dijkstra hoặc gán POI cố định vào cell.
