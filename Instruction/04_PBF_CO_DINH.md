# 04 — Input OSM PBF

## Đường dẫn bắt buộc

Code hiện cố định file:

```text
data/raw/osm/vietnam-261014.osm.pbf
```

Đường dẫn này xuất hiện trong `regions.py`, `network.py` và `osm_input.py`.

## Vai trò của PBF

OSM PBF chỉ cung cấp:

- Boundary theo tên tỉnh/thành.
- Walking road network.

POI không lấy từ PBF. Nguồn POI duy nhất là Overture Places.

## Kiểm tra thủ công

```powershell
Get-Item data\raw\osm\vietnam-261014.osm.pbf |
    Select-Object FullName, Length, LastWriteTime
```

Mở thử bằng Pyrosm:

```python
from pyrosm import OSM

osm = OSM("data/raw/osm/vietnam-261014.osm.pbf")
boundary = osm.get_boundaries(name="Hà Nội")
print(boundary[["name", "geometry"]].head())
```

## Lưu ý về `check-osm`

Lệnh `ady201 check-osm` tồn tại nhưng phần kiểm tra kích thước file trong `osm_input.py` hiện chưa đúng cho file hợp lệ. Không dùng lệnh này làm điều kiện chạy pipeline; kiểm tra bằng `Get-Item` và đoạn Pyrosm ở trên.

## Thay PBF mới

Vì tên file đang hard-code, có hai lựa chọn:

1. Đổi tên file mới thành `vietnam-261014.osm.pbf`.
2. Sửa đồng thời hằng đường dẫn trong `regions.py`, `network.py` và `osm_input.py`.

Không cần thêm POI vào PBF vì pipeline không đọc POI từ nguồn này.
