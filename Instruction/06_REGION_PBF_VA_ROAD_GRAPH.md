# Giai đoạn 06 — Region PBF và road graph

## Mục tiêu

Cắt PBF theo boundary buffer và tạo walking/driving graph dùng chung cho mọi region.

## Nhiệm vụ tổng quát

- Cắt region PBF bằng Osmium.
- Tạo walking graph cho accessibility.
- Tạo driving graph cho infrastructure features.
- Tính length/travel time.
- Validate connected components và one-way.
- Lưu GraphML và node/edge GeoParquet.

## Luồng

```text
Vietnam PBF + buffered boundary
        ↓ Osmium complete_ways
region.osm.pbf
        ├── walking network → walk.graphml
        └── driving network → drive.graphml
```

## Những thứ cần thay đổi

Tạo:

```text
src/ady201/network/extract_pbf.py
src/ady201/network/build_graph.py
src/ady201/network/validate.py
```

Artifact:

```text
extract/region.osm.pbf
network/walk.graphml
network/drive.graphml
network/walk_nodes.parquet
network/walk_edges.parquet
network/drive_nodes.parquet
network/drive_edges.parquet
network/quality.json
```

Walking edge:

```text
travel_time_s = length_m / walking_speed_mps
```

Quy tắc:

- Graph là directed `MultiDiGraph`.
- Giữ `u`, `v`, `key` cho parallel edges.
- Không loại component nhỏ trước khi báo cáo.
- Không đưa toàn bộ graph vào DuckDB nếu không cần.

## Kiến thức cần học

### Bắt buộc

- Osmium extract và `complete_ways`.
- Pyrosm `get_network`.
- Directed/multi graph.
- Graph simplification.
- Connected components và edge weights.

### Tìm hiểu sâu bên ngoài

- OSM access/oneway tags.
- OSMnx graph conversion/storage.
- GraphML limitations.
- Turn restrictions; ngoài MVP.

## Phân công

### Thành

- Định nghĩa graph metadata và artifact record trong DuckDB.
- Review node/edge schema.

### Hiếu

- Owner PBF extract, graph builder và graph validation.
- Benchmark RAM/runtime.

### Quang

- Vẽ graph mẫu và tạo quality summary.
- Smoke test output trên hai region nhỏ.

### Review

- Thành review schema.
- Quang kiểm tra trực quan.
- Hiếu xử lý graph defects.

## Đầu ra

- Walking và driving graph có thể load lại.
- Báo cáo node, edge, components và weight validity.

## Hoàn thành khi

- Tất cả routing edges có weight dương.
- Có ít nhất năm route mẫu hợp lý.
- Đổi `region_id` không cần sửa graph code.

