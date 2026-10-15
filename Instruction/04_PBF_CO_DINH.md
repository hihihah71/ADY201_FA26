# Giai đoạn 04 — Chuẩn bị PBF cố định

## Mục tiêu

Chuẩn bị một file OSM Việt Nam để Pyrosm sử dụng trong toàn bộ dự án.

Giai đoạn này không xử lý boundary, không tạo boundary buffer, không quản lý snapshot và không lưu PBF vào DuckDB.

## Cần có trước

- Project đã cài được bằng `python -m pip install -e .`.
- DuckDB cơ bản đã chạy ở giai đoạn 03.
- Biết sử dụng `pathlib.Path`.

## Luồng

```text
Geofabrik Vietnam PBF
          ↓ tải một lần
data/raw/osm/vietnam.osm.pbf
          ↓ get_osm_path()
      Pyrosm OSM reader
          ↓
  POI và mạng đường ở các giai đoạn sau
```

## Quyết định đơn giản hóa

- Toàn bộ project dùng đúng một file `data/raw/osm/vietnam.osm.pbf`.
- Không tạo bản sao PBF cho từng region.
- Không có `snapshot_id`, checksum hoặc manifest.
- Boundary hành chính chỉ được đọc khi tạo hexagon ở giai đoạn 07.
- Phạm vi mạng đường được xác định bằng `network_bbox` trong `regions.json`, không bằng boundary buffer.

## Các bước thực hiện

### Bước 1 — Cài thư viện đọc PBF

- Thêm `pyrosm` và `geopandas` vào `pyproject.toml`.
- Chạy `python -m pip install -e .`.
- Kiểm tra import bằng `python -c "from pyrosm import OSM"`.
- Nếu import lỗi, xử lý cài đặt trước khi tải hoặc viết code mạng đường.

Kết quả cần thấy: Python import được `OSM` từ Pyrosm.

### Bước 2 — Tải và đặt tên file PBF

- Tạo thư mục `data/raw/osm/` nếu chưa có.
- Tải file Việt Nam `.osm.pbf` từ Geofabrik.
- Đổi tên thành đúng `data/raw/osm/vietnam.osm.pbf`.
- Không commit file này lên Git vì dung lượng lớn.
- Không thay file trong lúc pipeline đang chạy.

Kết quả cần thấy: project có đúng một file nguồn `vietnam.osm.pbf` và dung lượng lớn hơn `0`.

### Bước 3 — Viết `get_osm_path()`

- Tạo `src/ady201/osm_input.py`.
- Xác định đường dẫn PBF tương đối từ thư mục gốc project.
- Kiểm tra đường dẫn tồn tại, là file, có đuôi `.osm.pbf` và không rỗng.
- Nếu hợp lệ, trả về một đối tượng `Path`.
- Các module POI và network phải gọi hàm này thay vì tự viết lại đường dẫn.

Kết quả cần thấy: mọi module nhận cùng một đường dẫn PBF từ một hàm duy nhất.

### Bước 4 — Tạo lệnh `check-osm`

- Thêm command `ady201 check-osm` vào `main.py`.
- Command gọi `get_osm_path()` rồi thử tạo `OSM(str(pbf_path))`.
- Nếu file thiếu, rỗng hoặc Pyrosm không mở được, command kết thúc với lỗi rõ đường dẫn.
- Nếu thành công, chỉ hiển thị đường dẫn và trạng thái sẵn sàng.

Kết quả cần thấy:

```powershell
ady201 check-osm
```

xác nhận Pyrosm mở được `data/raw/osm/vietnam.osm.pbf`.

## File cần tạo hoặc sửa

```text
src/ady201/osm_input.py
src/ady201/main.py
pyproject.toml
data/raw/osm/vietnam.osm.pbf
```

Không tạo thêm file SQL trong giai đoạn này.

## Quy tắc

- Chỉ có một đường dẫn PBF chính thức trong project.
- Không hard-code đường dẫn tuyệt đối theo máy.
- Không thay PBF trong khi `run-region` hoặc `run-all` đang chạy.
- Không tạo `region.osm.pbf`.
- Không xử lý boundary trong giai đoạn này.

## Lỗi thường gặp

- Mỗi module tự khai báo một đường dẫn PBF khác nhau.
- Tải file chưa xong nhưng đã bắt đầu chạy Pyrosm.
- Đưa file PBF lớn lên Git.
- Dùng tên file tải về khác với tên mà `get_osm_path()` tìm kiếm.
- Thay PBF giữa chừng khiến POI và graph không còn cùng nguồn.

## Cần học trước

- `pathlib.Path`.
- Cách kiểm tra file tồn tại và dung lượng file.
- `pyrosm.OSM`.
- Khác nhau giữa PBF nguồn và các file Parquet/GraphML đầu ra.

## Tìm hiểu thêm

- Từ khóa: `Geofabrik Vietnam PBF`.
- Từ khóa: `Pyrosm read PBF OSM`.
- Từ khóa: `Python pathlib file exists size`.

## Phân công

### Thành

- Viết `osm_input.py` và `get_osm_path()`.
- Kiểm tra module POI và network dùng chung hàm này.

### Hiếu

- Cài Pyrosm và kiểm tra mở file PBF trên máy nhóm.
- Ghi lại dung lượng file, RAM và thời gian mở thử.

### Quang

- Thêm lệnh `check-osm` vào `main.py`.
- Kiểm tra `.gitignore` không cho commit PBF.

## Đầu ra

```text
data/raw/osm/vietnam.osm.pbf
src/ady201/osm_input.py
```

## Hoàn thành khi

- Ba thành viên import được Pyrosm.
- `ady201 check-osm` xác nhận PBF sẵn sàng.
- POI và network cùng lấy đường dẫn qua `get_osm_path()`.
- Giai đoạn 04 không có xử lý boundary hoặc buffer.
