# Giai đoạn 04 — Chuẩn bị PBF và ranh giới

## Mục tiêu

Chuẩn bị một file OSM Việt Nam và boundary của các khu vực để dùng cố định cho toàn bộ dự án.

Giai đoạn này không tạo bảng `snapshots`, không tính checksum, không tạo manifest và không lưu PBF vào DuckDB.

## Cần có trước

- DuckDB cơ bản đã chạy ở giai đoạn 03.
- `regions.json` đã có ít nhất Hà Nội và Đà Nẵng.
- Mỗi region đã có `boundary_path` rõ ràng.

## Luồng

```text
Geofabrik Vietnam PBF
        ↓ tải một lần + kiểm tra
data/raw/osm/vietnam.osm.pbf
        ↓ giữ nguyên tới khi hoàn thành dự án
POI toàn quốc + PBF đường theo từng khu vực

boundary GeoJSON
        ↓ kiểm tra geometry + tạo buffer
analysis boundary + extraction boundary
```

## Quyết định đơn giản hóa

- Toàn bộ project chỉ đọc `data/raw/osm/vietnam.osm.pbf`.
- Không có `snapshot_id` trong hàm, lệnh CLI, bảng hoặc đường dẫn output.
- Không thay file này khi một lần xử lý đang chạy.
- Nếu sau này muốn dùng PBF mới, thay file rồi chạy lại toàn bộ pipeline từ đầu. Việc cập nhật định kỳ không thuộc phạm vi đồ án hiện tại.

## Các bước thực hiện

### Bước 1 — Tải và đặt tên file PBF

- Tạo thư mục `data/raw/osm/` nếu chưa có.
- Tải file Việt Nam `.osm.pbf` từ Geofabrik.
- Đổi tên file thành đúng `data/raw/osm/vietnam.osm.pbf`.
- Không commit file này lên Git vì dung lượng lớn.

Kết quả cần thấy: project có đúng một file nguồn `vietnam.osm.pbf` và dung lượng lớn hơn `0`.

### Bước 2 — Kiểm tra PBF trước khi sử dụng

- Cài Osmium và chạy `osmium --version`.
- Chạy `osmium fileinfo -e data/raw/osm/vietnam.osm.pbf`.
- Kiểm tra Osmium đọc được header, bounding box và thông tin dữ liệu.
- Nếu lệnh lỗi, tải lại file trước khi viết code xử lý POI hoặc đường.

Kết quả cần thấy: Osmium đọc file thành công và phạm vi dữ liệu bao phủ Việt Nam.

### Bước 3 — Viết hàm lấy PBF cố định

- Tạo `osm_input.py`.
- Khai báo đường dẫn tương đối từ project tới `data/raw/osm/vietnam.osm.pbf`.
- Viết `get_osm_path()` để kiểm tra file tồn tại, là file và không rỗng rồi trả về `Path`.
- Các module sau gọi hàm này; không tự viết lại đường dẫn ở nhiều file.

Kết quả cần thấy: mọi phần POI và road network đều nhận cùng một `Path` nguồn.

### Bước 4 — Kiểm tra boundary của từng region

- Thêm `geopandas` vào `pyproject.toml` rồi chạy `python -m pip install -e .`.
- Đọc `boundary_path` từ `regions.json`, không ghép tên region trực tiếp trong code.
- Dùng GeoPandas đọc GeoJSON và kiểm tra file có dữ liệu, geometry không rỗng và CRS là EPSG:4326.
- Geometry phải là Polygon hoặc MultiPolygon.
- Nếu geometry không hợp lệ, dùng `make_valid()` rồi kiểm tra lại.
- Vẽ nhanh boundary để chắc chắn không lấy nhầm quận, huyện hoặc khu vực khác.

Kết quả cần thấy: mỗi region đang bật có một boundary hợp lệ và nằm đúng vị trí.

### Bước 5 — Tạo boundary buffer để cắt mạng đường

- Giữ boundary gốc làm `analysis_boundary`; phạm vi này dùng để tính count, density và bản đồ.
- Chuyển boundary sang CRS có đơn vị mét.
- Buffer theo `road_buffer_m` trong `project.json` rồi chuyển lại EPSG:4326.
- Lưu geometry mới làm `extraction_boundary`; phạm vi này chỉ dùng để lấy thêm đường và POI gần biên.
- Không gọi `buffer()` trực tiếp trên EPSG:4326 vì đơn vị khi đó là độ.

Kết quả cần thấy: extraction boundary bao trọn analysis boundary và lớn hơn đúng khoảng cấu hình.

### Bước 6 — Tạo hai lệnh kiểm tra đầu vào

- `ady201 check-osm` gọi `get_osm_path()` và xác nhận file sẵn sàng.
- `ady201 prepare-boundary --region <region_id>` kiểm tra boundary rồi tạo boundary buffer.
- Hai lệnh chỉ in kết quả ngắn gọn và báo rõ đường dẫn khi file bị thiếu.
- Không tạo lệnh `register-snapshot`.

Kết quả cần thấy: kiểm tra được PBF và boundary mà không mở pgAdmin hoặc sửa source code.

## File cần tạo hoặc sửa

```text
src/ady201/osm_input.py
src/ady201/boundaries.py
src/ady201/main.py
pyproject.toml
data/raw/osm/vietnam.osm.pbf
data/boundaries/v1/{region_id}.geojson
data/processed/{region_id}/boundary/extraction_boundary.geojson
```

Không tạo thêm file SQL trong giai đoạn này.

Lệnh mục tiêu:

```powershell
ady201 check-osm
ady201 prepare-boundary --region hanoi
```

## Quy tắc

- Chỉ có một đường dẫn PBF chính thức trong project.
- Không thay hoặc sửa PBF khi pipeline đang chạy.
- Boundary gốc lưu ở EPSG:4326.
- Phải chuyển sang CRS theo mét trước khi buffer.
- Không hard-code Hà Nội hoặc Đà Nẵng trong hàm xử lý.
- PBF, boundary buffer và các file xử lý lớn không đưa lên Git.

## Lỗi thường gặp

- Mỗi module dùng một đường dẫn PBF khác nhau.
- Tải file chưa xong nhưng đã bắt đầu chạy Pyrosm.
- Tạo buffer trên EPSG:4326 nên khoảng cách sai đơn vị.
- Dùng bounding box hình chữ nhật thay cho boundary hành chính thật.
- Thay PBF giữa chừng khiến POI và graph đường đến từ hai bộ dữ liệu khác nhau.

## Cần học trước

- `pathlib.Path` và cách kiểm tra file.
- Polygon và MultiPolygon.
- CRS EPSG:4326 và CRS theo mét.
- Buffer geometry.
- Lệnh `osmium fileinfo`.

## Tìm hiểu thêm

- Từ khóa: `Geofabrik Vietnam PBF`.
- Từ khóa: `osmium fileinfo`.
- Từ khóa: `GeoPandas to_crs buffer`.
- Từ khóa: `Shapely make_valid`.

## Phân công

### Thành

- Viết `osm_input.py` và lệnh `check-osm`.
- Kiểm tra các module sau chỉ lấy PBF qua `get_osm_path()`.

### Hiếu

- Viết phần đọc, kiểm tra và buffer boundary.
- Kiểm tra CRS và khoảng buffer bằng một region mẫu.

### Quang

- Chuẩn hóa `boundary_path` trong `regions.json`.
- Vẽ bản đồ so sánh boundary gốc và boundary buffer.

## Đầu ra

```text
data/raw/osm/vietnam.osm.pbf
data/boundaries/v1/{region_id}.geojson
data/processed/{region_id}/boundary/extraction_boundary.geojson
```

## Hoàn thành khi

- `ady201 check-osm` xác nhận file PBF hợp lệ.
- Boundary gốc nằm đúng vị trí và có geometry hợp lệ.
- Boundary buffer lớn hơn boundary gốc và không sai đơn vị.
- Không có bảng, hàm, tham số hoặc thư mục nào dùng `snapshot_id`.
