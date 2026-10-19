# Giai đoạn 04 — Chuẩn bị file OSM PBF

## Nhiệm vụ tổng quát

Dùng một file Geofabrik Việt Nam làm nguồn OSM cho toàn project.

## Luồng

```text
Geofabrik Vietnam
        ↓ tải một lần
data/raw/osm/vietnam.osm.pbf
        ↓
Pyrosm đọc theo bbox của từng tỉnh
```

## Những thứ cần thay đổi

- Đặt file tại đúng một đường dẫn cố định.
- `osm_input.py` chỉ kiểm tra file tồn tại và trả về đường dẫn.
- Không tạo snapshot, checksum, manifest hay bản PBF riêng cho từng tỉnh.
- Không tạo buffer quanh boundary tỉnh ở giai đoạn này.

## Các bước thực hiện

### Bước 1 — Chuẩn bị thư mục

```text
data/raw/osm/vietnam.osm.pbf
```

Không commit file PBF vào Git.

### Bước 2 — Kiểm tra dependency

Trong môi trường Python đang dùng:

```powershell
python -c "from pyrosm import OSM; print('ok')"
```

Nếu lệnh lỗi, sửa việc cài `pyrosm` trước khi viết code xử lý.

### Bước 3 — Viết hàm lấy đường dẫn

Trong `osm_input.py`:

```python
from pathlib import Path


OSM_PATH = Path("data/raw/osm/vietnam.osm.pbf")


def get_osm_path():
    if not OSM_PATH.exists():
        raise FileNotFoundError(f"Thiếu file OSM: {OSM_PATH}")
    return OSM_PATH
```

### Bước 4 — Mở file thử

```python
from pyrosm import OSM
from ady201.osm_input import get_osm_path

osm = OSM(str(get_osm_path()))
```

Chưa gọi lấy toàn bộ POI hoặc road ở bước này.

## Kiến thức cần học

- PBF là file dữ liệu OpenStreetMap đã nén.
- `Path.exists()` và `FileNotFoundError`.
- Pyrosm có thể đọc một phần PBF theo bounding box.

Từ khóa tìm thêm: `Geofabrik Vietnam PBF`, `Pyrosm bounding box`.

## Phân công

### Thành — trung bình

- Kiểm tra Pyrosm đọc được file và hoàn thiện `osm_input.py`.

### Hiếu — trung bình

- Kiểm tra dung lượng/RAM khi mở PBF trên máy nhóm.

### Quang — dễ

- Tải file, đặt đúng tên, cập nhật `.gitignore` nếu cần và ghi nguồn/ngày tải trong README.

Review chéo: Quang chạy lại hàm của Thành trên máy mình.

## Hoàn thành khi

- `get_osm_path()` trả về đúng file.
- Pyrosm mở được file.
- Repository không theo dõi file PBF.
