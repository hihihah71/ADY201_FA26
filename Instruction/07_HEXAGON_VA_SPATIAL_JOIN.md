# Giai đoạn 07 — Hexagon và gán dữ liệu theo vị trí

## Mục tiêu

Chia mỗi khu vực thành các cell thống nhất và xác định POI thuộc cell nào.

## Cần có trước

- Boundary hợp lệ từ giai đoạn 04.
- POI toàn quốc từ giai đoạn 05.
- Graph đường từ giai đoạn 06.

## Luồng

```text
analysis boundary
       ↓ tạo và cắt hexagon
     các cell
       ↓ tính diện tích + điểm đại diện
   cell phân tích

POI toàn quốc + cell
       ↓ spatial join
POI thuộc region/cell
```

## Các bước thực hiện

1. Thêm thư viện H3 khi bắt đầu giai đoạn này.
2. Đọc `hex_resolution` từ `project.json`.
3. Tạo hexagon phủ boundary.
4. Cắt cell biên theo boundary thật.
5. Tính `area_km2` trong CRS theo mét.
6. Tạo representative point cho mỗi cell.
7. Gán POI vào region và cell bằng spatial join.
8. Tách POI dùng cho mật độ và POI buffer dùng cho accessibility.

## File cần tạo hoặc sửa

```text
src/ady201/hexagons.py
src/ady201/spatial_join.py
src/ady201/main.py
sql/020_region_views.sql
pyproject.toml
```

Schema cell:

```text
snapshot_id
region_id
grid_version
cell_id
area_km2
geometry
representative_point
```

Lệnh mục tiêu:

```powershell
ady201 build-grid --region hanoi --snapshot <snapshot_id>
```

## Quy tắc

- Dùng cùng H3 resolution nếu muốn so sánh giữa các khu vực.
- Cell biên dùng diện tích sau khi clip.
- POI trong boundary gốc dùng tính count và density.
- POI trong vùng buffer chỉ bổ sung cho tính accessibility.
- POI nằm đúng đường biên chỉ được gán một lần theo quy tắc cố định.
- Không dùng tọa độ độ để tính diện tích km².

## Cần học trước

- Point, polygon và spatial join.
- `within`, `covers` và `intersects`.
- Clip/overlay geometry.
- CRS theo mét và cách tính diện tích.

## Tìm hiểu thêm

- Từ khóa: `H3 Python polygon to cells`.
- Từ khóa: `GeoPandas sjoin`.
- Từ khóa: `GeoPandas overlay clip`.

## Phân công

### Thành

- Viết phần gán POI vào region/cell.
- Kiểm tra POI bị gán trùng và số lượng trước/sau join.

### Hiếu

- Kiểm tra CRS, cell biên và representative point.
- Kiểm tra điểm đại diện có thể snap vào graph.

### Quang

- Tạo hexagon và bản đồ xem nhanh.
- So sánh hai resolution trên một khu vực nhỏ.

## Đầu ra

```text
data/processed/{snapshot_id}/{region_id}/grid/hexagons.parquet
data/processed/{snapshot_id}/{region_id}/poi/region_membership.parquet
outputs/quality/{snapshot_id}/{region_id}/grid_summary.json
```

## Hoàn thành khi

- Không có cell nằm hoàn toàn ngoài boundary.
- Tổng diện tích cell gần bằng diện tích boundary.
- Mỗi POI dùng cho density chỉ thuộc một cell.
- Bản đồ cell phủ đúng khu vực.
