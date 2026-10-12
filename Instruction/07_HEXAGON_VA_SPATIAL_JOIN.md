# Giai đoạn 07 — Hexagon và spatial join

## Mục tiêu

Tạo đơn vị phân tích thống nhất và gán POI/road data vào đúng region/cell.

## Nhiệm vụ tổng quát

- Tạo H3/hexagon theo resolution chung.
- Clip cell biên theo analysis boundary.
- Tính diện tích theo km².
- Tạo representative point.
- Gán POI `inside` và `buffer` theo spatial relation.
- Chuẩn bị cell cho feature calculation.

## Luồng

```text
Analysis boundary
    ↓ H3/hex generation
Hex cells
    ↓ clip + area + representative point
analytics cells

National POI + analysis/buffer boundary
    ↓ spatial join
region_poi membership
```

## Những thứ cần thay đổi

Tạo:

```text
src/ady201/grid/hexagons.py
src/ady201/poi/region_membership.py
sql/region_views.sql
```

Schema cell:

```text
region_id
grid_version
cell_id
area_km2
geometry
representative_point
```

Quy tắc:

- Dùng cùng resolution nếu muốn so sánh toàn quốc.
- Cell biên dùng diện tích thực sau clip.
- POI `inside` dùng cho density.
- POI `inside + buffer` có thể dùng cho accessibility.
- POI trên biên chỉ gán một region/cell theo rule cố định.

## Kiến thức cần học

### Bắt buộc

- H3 resolution/cell ID.
- Spatial join, intersects, within/covers.
- Overlay/clip.
- Tính area trong projected CRS.

### Tìm hiểu sâu bên ngoài

- H3 Python API.
- GeoPandas `sjoin`/`overlay`.
- DuckDB spatial join functions.
- Boundary precision và sliver polygons.

## Phân công

### Thành

- Owner POI–region/cell membership và DuckDB views.
- Kiểm tra duplicate assignment.

### Hiếu

- Tạo buffered boundary output đúng CRS.
- Kiểm tra representative point gần road network.

### Quang

- Owner hex generation và preview maps.
- Thử hai resolution trên Hà Nội.

### Review

- Thành kiểm tra counts.
- Hiếu kiểm tra CRS.
- Quang kiểm tra trực quan cell biên.

## Đầu ra

```text
grid/hexagons.parquet
poi/region_membership.parquet
grid/quality.json
```

## Hoàn thành khi

- Không có cell ngoài analysis boundary.
- Tổng diện tích cell hợp lý so với boundary.
- Không double-count POI trong density.

