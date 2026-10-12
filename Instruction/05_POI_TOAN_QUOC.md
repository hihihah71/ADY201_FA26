# Giai đoạn 05 — POI toàn quốc

## Mục tiêu

Trích và chuẩn hóa POI một lần cho mỗi Vietnam snapshot, thay cho nhiều script riêng theo nhóm và theo tỉnh.

## Nhiệm vụ tổng quát

- Đọc POI từ PBF theo `categories.yaml`.
- Giữ `osm_type`, `osm_id`, tags và geometry.
- Chuẩn hóa category/subcategory.
- Làm giàu từ OSM tags.
- Xuất GeoParquet và đăng ký trong DuckDB.

## Luồng

```text
Vietnam PBF
    ↓ filter tags
Raw POI
    ↓ normalize/enrich/validate
poi_vietnam.parquet
    ↓ DuckDB view/metadata
Canonical POI dataset
```

## Những thứ cần thay đổi

Thay ba cặp script tải/flatten bằng:

```text
src/ady201/poi/extract.py
src/ady201/poi/normalize.py
src/ady201/poi/enrich.py
src/ady201/poi/validate.py
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
tags
geometry
quality_flags
```

Quy tắc:

- Unique key: `(snapshot_id, osm_type, osm_id)`.
- Không loại POI chỉ vì thiếu tên.
- Dạng polygon dùng representative point.
- Lấy cả `amenity`, `shop`, `highway`, `public_transport`.
- Không reverse-geocode hàng loạt qua public API.

## Kiến thức cần học

### Bắt buộc

- OSM tag filtering.
- Node/way/relation identity.
- GeoParquet schema.
- Data validation và missing-value flags.

### Tìm hiểu sâu bên ngoài

- Pyrosm POI/custom criteria.
- OSM tag conventions.
- GeoPandas representative point.
- Arrow nested/JSON columns.

## Phân công

### Thành

- Owner extract/normalize/enrich.
- Thiết kế schema và category mapping.
- Viết duplicate/missingness checks.

### Hiếu

- Kiểm tra cách Pyrosm đọc PBF và geometry.
- Đánh giá memory/runtime trên file mẫu.

### Quang

- EDA trước/sau chuẩn hóa.
- Báo cáo count theo category và quality flags.

### Review

- Hiếu review PBF extraction.
- Quang smoke test output.
- Thành duyệt data quality.

## Đầu ra

```text
data/processed/{snapshot_id}/national/poi.parquet
outputs/quality/{snapshot_id}/poi_report.*
```

## Hoàn thành khi

- Không còn cần `Systhesis.csv` làm nguồn chính.
- Cùng một pipeline xử lý mọi category.
- Không trùng composite key và geometry hợp lệ.

