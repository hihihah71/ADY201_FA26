# Giai đoạn 04 — PBF snapshot và ranh giới

## Mục tiêu

Biết chính xác file OSM và ranh giới nào được dùng cho mỗi lần phân tích.

## Cần có trước

- DuckDB đã khởi tạo ở giai đoạn 03.
- `regions.json` đã có ít nhất Hà Nội và Đà Nẵng.

## Luồng

```text
Vietnam .osm.pbf
      ↓ checksum + ngày dữ liệu
snapshot đã đăng ký

boundary GeoJSON
      ↓ kiểm tra + tạo buffer
analysis boundary + extraction boundary
```

## Các bước thực hiện

### Bước 1 — Đưa file PBF vào đúng chỗ

- Tạo thư mục `data/raw/osm/` nếu chưa có.
- Tải file Việt Nam có đuôi `.osm.pbf` từ Geofabrik.
- Trong lúc tải có thể giữ tên gốc. Sau khi đăng ký thành công, tên file đầu ra phải chứa `snapshot_id`, ví dụ `vietnam-2026-10-14.osm.pbf`.
- Kiểm tra file tồn tại và dung lượng lớn hơn `0` trước khi làm bước tiếp theo.

Kết quả cần thấy: có một file PBF đọc được trong `data/raw/osm/`, chưa xóa hoặc ghi đè snapshot cũ.

### Bước 2 — Tính checksum cho file PBF

- Trong `snapshots.py`, viết hàm nhận một `Path` và đọc file theo từng khối nhỏ.
- Cập nhật dần đối tượng `hashlib.sha256()` thay vì đọc toàn bộ file vào RAM.
- Trả về chuỗi checksum 64 ký tự và lưu chuỗi này trong manifest.
- Nếu checksum đã có trong DuckDB thì dùng lại snapshot đã đăng ký, không tạo bản ghi trùng.

Kết quả cần thấy: chạy hai lần với cùng một file cho cùng checksum; sửa file thì checksum thay đổi.

### Bước 3 — Đọc thời điểm dữ liệu OSM

- Cài công cụ Osmium và kiểm tra bằng `osmium --version`.
- Chạy `osmium fileinfo -e <duong-dan-pbf>` để xem metadata mở rộng.
- Lấy timestamp dữ liệu OSM từ kết quả của Osmium. Không dùng ngày tải file làm ngày dữ liệu.
- Nếu Osmium không đọc được file, dừng đăng ký vì PBF có thể tải chưa xong hoặc bị hỏng.

Kết quả cần thấy: biết rõ file được tải lúc nào và dữ liệu OSM bên trong mới đến thời điểm nào.

### Bước 4 — Tạo bảng quản lý snapshot

- Tạo `sql/010_snapshots.sql`; không thêm bảng này vào `001_schema.sql`.
- Bảng tối thiểu cần có: `snapshot_id`, `source_path`, `sha256`, `osm_timestamp`, `is_active`, `created_at`.
- Đặt `snapshot_id` làm khóa chính và `sha256` là giá trị duy nhất.
- Sửa `initialize_database()` để chạy thêm file SQL này khi bắt đầu giai đoạn 04.

Kết quả cần thấy: `SHOW TABLES` có thêm bảng `snapshots` và có thể chạy khởi tạo lại mà không lỗi.

### Bước 5 — Đăng ký và chọn snapshot đang dùng

- Viết hàm `register_snapshot()` nhận đường dẫn PBF.
- Hàm kiểm tra file, tính checksum, đọc timestamp rồi ghi một hàng vào `snapshots`.
- Khi chọn snapshot mới, cập nhật snapshot cũ thành `is_active = false` và snapshot mới thành `true` trong cùng một transaction.
- Ghi manifest JSON gồm cùng các thông tin trên vào `data/manifests/{snapshot_id}.json`.

Kết quả cần thấy: tại một thời điểm chỉ có một hàng `is_active = true`; đăng ký lại cùng file không sinh thêm hàng.

### Bước 6 — Kiểm tra boundary của từng khu vực

- Đọc `boundary_path` từ cấu hình region, không ghép tên file trực tiếp trong code.
- Dùng GeoPandas đọc GeoJSON và kiểm tra: file có dữ liệu, geometry không rỗng, CRS là EPSG:4326 và geometry là Polygon hoặc MultiPolygon.
- Nếu geometry không hợp lệ, thử `make_valid()` và kiểm tra lại. Không âm thầm bỏ các phần geometry bị lỗi.
- Vẽ nhanh boundary và đối chiếu tên khu vực trước khi đặt `enabled=true`.

Kết quả cần thấy: mỗi region đang bật có đúng một geometry hợp lệ và nằm đúng vị trí.

### Bước 7 — Tạo boundary dùng để cắt mạng đường

- Giữ nguyên boundary gốc làm `analysis_boundary`; đây là phạm vi tính count, density và bản đồ.
- Chuyển boundary sang CRS có đơn vị mét, sau đó buffer theo `road_buffer_m` trong `project.json`.
- Chuyển geometry buffer về EPSG:4326 và lưu thành `extraction_boundary`.
- Không gọi `buffer()` trực tiếp trên EPSG:4326 vì khi đó đơn vị là độ, không phải mét.

Kết quả cần thấy: extraction boundary bao trọn analysis boundary và rộng hơn đúng khoảng cấu hình.

### Bước 8 — Tạo hai lệnh CLI nhỏ

- `register-snapshot <pbf_path>` chỉ làm công việc của bước 2 đến bước 5.
- `prepare-boundary --region <region_id>` chỉ làm bước 6 và bước 7.
- Lệnh thành công in kết quả ngắn gọn gồm `snapshot_id` hoặc các đường dẫn boundary; lỗi phải dừng với thông báo rõ file nào sai.

Kết quả cần thấy: có thể chuẩn bị snapshot và boundary mà không mở pgAdmin hoặc sửa code.

## File cần tạo hoặc sửa

```text
src/ady201/snapshots.py
src/ady201/boundaries.py
src/ady201/main.py
sql/010_snapshots.sql
data/raw/osm/vietnam-{snapshot_id}.osm.pbf
data/boundaries/{boundary_version}/{region_id}.geojson
data/manifests/{snapshot_id}.json
```

Lệnh mục tiêu:

```powershell
ady201 register-snapshot data/raw/osm/vietnam-latest.osm.pbf
ady201 prepare-boundary --region hanoi
```

## Quy tắc

- Không ghi đè snapshot cũ.
- Mỗi thời điểm chỉ có một Vietnam snapshot được đánh dấu active.
- Không gọi một file là `latest` trong kết quả cuối; phải có `snapshot_id`.
- Boundary gốc lưu ở EPSG:4326.
- Chuyển sang CRS theo mét trước khi tạo buffer.
- Không hard-code số lượng tỉnh/thành.
- Kiểm tra boundary trên bản đồ trước khi đặt `enabled=true`.

## Lỗi thường gặp

- Đặt ngày tải file thành `osm_timestamp`: hai khái niệm này không giống nhau.
- Tạo buffer khi geometry còn ở EPSG:4326: khoảng cách buffer sẽ sai đơn vị.
- Ghi đè `vietnam-latest.osm.pbf`: không còn khả năng chạy lại đúng snapshot cũ.
- Dùng nhầm ranh giới quận/huyện thay cho ranh giới tỉnh/thành phố.

## Cần học trước

- SHA-256 checksum.
- Polygon và MultiPolygon.
- CRS EPSG:4326 và CRS theo mét.
- Buffer geometry.
- Lệnh cơ bản của Osmium.

## Tìm hiểu thêm

- Từ khóa: `Geofabrik Vietnam PBF`.
- Từ khóa: `osmium fileinfo`.
- Từ khóa: `GeoPandas to_crs buffer`.
- Từ khóa: `Shapely make_valid`.

## Phân công

### Thành

- Thiết kế metadata snapshot/boundary trong DuckDB.
- Kiểm tra trùng ID và geometry rỗng.

### Hiếu

- Viết hàm checksum, đọc PBF timestamp và tạo buffer.
- Kiểm tra đúng CRS và khoảng buffer.

### Quang

- Chuẩn hóa tên file và `region_id`.
- Tạo bản đồ xem nhanh boundary gốc và boundary buffer.

## Đầu ra

- Một PBF có `snapshot_id`.
- Boundary hợp lệ cho từng khu vực.
- Manifest cho biết đường dẫn, checksum và thời gian dữ liệu.

## Hoàn thành khi

- Truy được nguồn, checksum và timestamp của PBF.
- Boundary gốc nằm đúng vị trí.
- Boundary buffer lớn hơn boundary gốc và không bị sai đơn vị.
