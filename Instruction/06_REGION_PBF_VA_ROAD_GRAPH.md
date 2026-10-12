# Giai đoạn 06 — PBF khu vực và graph đường

## Mục tiêu

Cắt dữ liệu đường cho từng khu vực và tạo graph đi bộ, graph lái xe có thể dùng lại.

## Cần có trước

- PBF snapshot và boundary buffer từ giai đoạn 04.
- Hiểu node, edge và graph có hướng.

## Luồng

```text
Vietnam PBF + boundary buffer
             ↓ Osmium
         region.osm.pbf
          ↙          ↘
 walking graph     driving graph
```

## Các bước thực hiện

1. Dùng Osmium cắt PBF theo boundary buffer.
2. Dùng Pyrosm đọc mạng đi bộ và mạng lái xe.
3. Chuyển node/edge thành graph NetworkX.
4. Tính `length_m` cho edge.
5. Tính `travel_time_s` cho graph đi bộ và lái xe.
6. Giữ thông tin đường một chiều.
7. Lưu graph bằng GraphML và lưu node/edge bằng GeoParquet.
8. Tạo bảng tóm tắt số node, edge và connected component.

## File cần tạo hoặc sửa

```text
src/ady201/network.py
src/ady201/road_extract.py
src/ady201/road_graph.py
src/ady201/main.py
pyproject.toml
```

Lệnh mục tiêu:

```powershell
ady201 build-network --region hanoi --snapshot <snapshot_id>
```

Công thức đi bộ:

```text
travel_time_s = length_m / walking_speed_mps
```

`walking_speed_mps` lấy từ `project.json`, không viết cố định trong hàm.

## Quy tắc

- Graph dùng `MultiDiGraph` để giữ đường song song và chiều đi.
- Mỗi edge giữ `u`, `v`, `key`, `length_m` và `travel_time_s`.
- Weight dùng cho Dijkstra phải là số không âm.
- Không xóa component nhỏ trước khi tạo báo cáo.
- Không lưu toàn bộ graph vào DuckDB nếu GraphML/Parquet đã đủ.

## Cần học trước

- Node, edge, directed graph và weight.
- `MultiDiGraph` của NetworkX.
- Connected component.
- Tag OSM `highway`, `access` và `oneway`.

## Tìm hiểu thêm

- Từ khóa: `osmium extract complete ways`.
- Từ khóa: `Pyrosm get_network walking driving`.
- Từ khóa: `NetworkX MultiDiGraph`.
- Từ khóa: `OSMnx save graphml`.

## Phân công

### Thành

- Chốt schema node/edge và metadata artifact trong DuckDB.
- Kiểm tra file Parquet đọc được bằng SQL.

### Hiếu

- Viết phần cắt PBF và tạo hai graph.
- Kiểm tra one-way, component, weight và mức dùng RAM.

### Quang

- Vẽ graph mẫu trên boundary.
- Chọn năm cặp điểm và kiểm tra tuyến đường có hợp lý không.

## Đầu ra

```text
data/processed/{snapshot_id}/{region_id}/extract/region.osm.pbf
data/processed/{snapshot_id}/{region_id}/network/walk.graphml
data/processed/{snapshot_id}/{region_id}/network/drive.graphml
data/processed/{snapshot_id}/{region_id}/network/walk_nodes.parquet
data/processed/{snapshot_id}/{region_id}/network/walk_edges.parquet
data/processed/{snapshot_id}/{region_id}/network/drive_nodes.parquet
data/processed/{snapshot_id}/{region_id}/network/drive_edges.parquet
outputs/quality/{snapshot_id}/{region_id}/network_summary.json
```

## Hoàn thành khi

- Graph load lại được từ file.
- Edge dùng để routing đều có weight hợp lệ.
- Năm tuyến mẫu đi theo đường thay vì đường thẳng.
- Đổi `region_id` không cần sửa code graph.
