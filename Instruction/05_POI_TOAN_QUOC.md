# Giai đoạn 05 — POI toàn quốc

## Mục tiêu

Tạo một bộ POI chuẩn hóa cho toàn Việt Nam ở mỗi snapshot, thay cho nhiều script riêng theo loại dịch vụ.

## Cần có trước

- PBF đã được đăng ký ở giai đoạn 04.
- `categories.json` đã có mapping POI.
- Hiểu các hàm đang có trong `poi.py`.

## Luồng

```text
Vietnam PBF + categories.json
              ↓ lọc OSM tags
            POI thô
              ↓ làm sạch + làm giàu
       POI GeoParquet toàn quốc
              ↓
          DuckDB view
```

## Các bước thực hiện

1. Thêm `pyrosm`, `geopandas` và `pyarrow` vào dependency khi bắt đầu giai đoạn này.
2. Đọc các tag cần thiết từ PBF theo `categories.json`.
3. Dùng lại logic làm sạch trong `poi.py`.
4. Chuyển tag OSM thành `category` và `subcategory` thống nhất.
5. Thêm thông tin như địa chỉ, thương hiệu và giờ mở cửa nếu có.
6. Với polygon, tạo một representative point nằm trong polygon.
7. Loại bản ghi trùng theo OSM ID trong cùng snapshot.
8. Ghi GeoParquet và tạo DuckDB view đọc file này.

## File cần tạo hoặc sửa

```text
src/ady201/poi.py
src/ady201/poi_extract.py
src/ady201/poi_enrich.py
src/ady201/main.py
sql/010_poi_views.sql
pyproject.toml
```

Schema tối thiểu:

```text
snapshot_id
osm_type
osm_id
category
subcategory
name
address
operator
brand
opening_hours
phone
website
geometry
quality_flags
```

Lệnh mục tiêu:

```powershell
ady201 build-national-poi --snapshot <snapshot_id>
```

## Quy tắc

- Khóa duy nhất là `(snapshot_id, osm_type, osm_id)`.
- Không xóa POI chỉ vì thiếu tên.
- Đọc cả tag `amenity`, `shop`, `highway` và `public_transport` khi cần.
- Giữ dữ liệu gốc đủ để kiểm tra lại mapping.
- Không reverse-geocode hàng loạt bằng API công cộng.
- Dữ liệu có geometry lưu GeoParquet, không dùng CSV làm nguồn chính.

## Cần học trước

- OSM `node`, `way`, `relation` và tags.
- GeoDataFrame và geometry.
- Parquet/GeoParquet.
- Missing value và duplicate.

## Tìm hiểu thêm

- Từ khóa: `Pyrosm custom filter POI`.
- Từ khóa: `OpenStreetMap taginfo amenity shop`.
- Từ khóa: `GeoPandas representative_point`.

## Phân công

### Thành

- Viết extraction, normalize và enrich POI.
- Chốt schema, mapping category và kiểm tra duplicate.

### Hiếu

- Kiểm tra cách Pyrosm đọc node/way/relation.
- Đo RAM và thời gian trên một phần PBF nhỏ trước.

### Quang

- So sánh số lượng trước và sau chuẩn hóa.
- Tạo bảng số POI theo category và `quality_flags`.

## Đầu ra

```text
data/processed/{snapshot_id}/national/poi.parquet
outputs/quality/{snapshot_id}/poi_summary.csv
```

## Hoàn thành khi

- Một lệnh xử lý được mọi category.
- Không trùng khóa `(snapshot_id, osm_type, osm_id)`.
- Geometry không rỗng và nằm trong phạm vi Việt Nam.
- DuckDB đọc được trực tiếp file Parquet đầu ra.
