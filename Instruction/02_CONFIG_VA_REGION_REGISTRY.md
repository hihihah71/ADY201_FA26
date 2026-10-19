# Giai đoạn 02 — Cấu hình và danh sách tỉnh

## Nhiệm vụ tổng quát

Đưa các giá trị thường thay đổi ra file JSON để chạy tỉnh khác mà không sửa code Python.

## Luồng

```text
project.json + categories.json + regions.json
                    ↓
          settings.py + regions.py
                    ↓
         config đã đọc thành dict
```

## Những thứ cần thay đổi

Chỉ dùng ba file:

- `config/project.json`: kích thước cell, bán kính và loại network.
- `config/categories.json`: quy tắc đổi OSM tag thành nhóm POI.
- `config/regions.json`: tên tỉnh và đường dẫn boundary.

Không cần H3 resolution, graph setting, tốc độ đường hoặc tham số Dijkstra.

## Các bước thực hiện

### Bước 1 — Rút gọn `project.json`

```json
{
  "cell_size_m": 1000,
  "poi_radii_m": [500, 1000, 2000],
  "road_radii_m": [500, 1000],
  "road_network_type": "walking"
}
```

- `cell_size_m`: cạnh của ô vuông, ban đầu dùng 1.000 m.
- `poi_radii_m`: các bán kính đếm POI.
- `road_radii_m`: các bán kính tính mật độ đường.
- `road_network_type`: loại đường Pyrosm cần lấy.

Nếu chạy quá chậm, thử tăng `cell_size_m` lên 2.000 m trước khi tối ưu code.

### Bước 2 — Giữ bốn category trong `categories.json`

```json
{
  "hospital": {"amenity": ["hospital"]},
  "school": {"amenity": ["school"]},
  "supermarket": {"shop": ["supermarket"]},
  "transit": {
    "public_transport": ["platform", "station", "stop_position"],
    "highway": ["bus_stop"]
  }
}
```

Nhóm có thể mở rộng sau, nhưng tên đầu ra phải giữ ổn định: `hospital`, `school`, `supermarket`, `transit`. Không gộp `clinic` vào `hospital` nếu cột kết quả mang tên `nearest_hospital_m`.

### Bước 3 — Khai báo từng tỉnh trong `regions.json`

```json
{
  "hanoi": {
    "name": "Hà Nội",
    "boundary_path": "data/raw/boundaries/hanoi.geojson",
    "enabled": true
  },
  "danang": {
    "name": "Đà Nẵng",
    "boundary_path": "data/raw/boundaries/danang.geojson",
    "enabled": true
  }
}
```

Bbox không cần nhập tay. Code lấy bbox bằng `boundary.total_bounds`.

### Bước 4 — Viết các hàm đọc config

Trong `settings.py`:

```python
from pathlib import Path
import json


def read_json(path):
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def get_project_config():
    return read_json("config/project.json")


def get_categories():
    return read_json("config/categories.json")
```

Trong `regions.py`:

```python
from ady201.settings import read_json


def get_region(region_id):
    regions = read_json("config/regions.json")
    if region_id not in regions:
        raise ValueError(f"Không tìm thấy region: {region_id}")
    return regions[region_id]
```

### Bước 5 — Kiểm tra đơn giản

- `cell_size_m > 0`.
- Bán kính là số dương.
- `boundary_path` tồn tại.
- `region_id` không trùng.
- Mỗi category có ít nhất một OSM tag.

Không cần tạo hệ thống validate riêng; kiểm tra ngay khi đọc file là đủ.

## Kiến thức cần học

- JSON object, list và kiểu Boolean.
- Python `dict`, `Path.exists()` và `raise ValueError`.
- Vì sao tên biến có hậu tố `_m` giúp tránh nhầm đơn vị.

Từ khóa tìm thêm: `Python json load`, `pathlib Path exists`.

## Phân công

### Thành — trung bình

- Rút gọn `project.json` và viết các hàm trong `settings.py`.

### Hiếu — trung bình

- Chốt bốn nhóm POI và đối chiếu tag trong `categories.json`.

### Quang — dễ/trung bình

- Thêm Hà Nội, Đà Nẵng và kiểm tra các file boundary có mở được.

Review chéo: Quang giải thích lại bốn tham số trong `project.json`; Thành và Hiếu kiểm tra config của nhau.

## Hoàn thành khi

- Có thể gọi `get_project_config()`, `get_categories()` và `get_region("hanoi")`.
- Không còn cấu hình H3, graph hoặc shortest path.
- Thêm tỉnh mới chỉ cần thêm boundary và một mục trong `regions.json`.
