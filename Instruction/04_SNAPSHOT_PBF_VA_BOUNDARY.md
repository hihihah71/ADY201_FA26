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

1. Tải file Vietnam PBF từ Geofabrik và đặt trong `data/raw/osm/`.
2. Tính SHA-256 để nhận biết file có thay đổi hay không.
3. Dùng Osmium đọc timestamp của PBF.
4. Lưu thông tin snapshot vào DuckDB và đánh dấu snapshot đang sử dụng là active.
5. Đọc boundary của từng khu vực và kiểm tra geometry.
6. Tạo một boundary gốc để phân tích và một boundary có buffer để cắt đường.
7. Thêm lệnh đăng ký snapshot và chuẩn bị boundary vào `main.py`.

## File cần tạo hoặc sửa

```text
src/ady201/snapshots.py
src/ady201/boundaries.py
src/ady201/main.py
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
