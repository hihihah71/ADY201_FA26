# Giai đoạn 06 — Pyrosm và graph đường

## Mục tiêu

Dùng Pyrosm đọc trực tiếp `vietnam.osm.pbf`, lọc mạng đường theo `network_bbox` và tạo walking/driving graph cho từng region.

Không dùng Osmium và không tạo file `region.osm.pbf` trung gian.

## Cần có trước

- `vietnam.osm.pbf` và `get_osm_path()` từ giai đoạn 04.
- `network_bbox` của region trong `regions.json`.
- `pyrosm`, `geopandas` và `pyarrow` đã có trong dependency.
- Hiểu node, edge và graph có hướng ở mức cơ bản.

## Luồng

```text
vietnam.osm.pbf + network_bbox
                    ↓ Pyrosm OSM(..., bounding_box=bbox)
              dữ liệu trong bbox
                 ↙                     ↘
       get_network("walking")   get_network("driving")
                 ↓                     ↓
          walking graph          driving graph
                 ↓                     ↓
            GraphML + node/edge GeoParquet
```

## Vì sao không cần cắt PBF trước

- Pyrosm nhận danh sách `[min_lon, min_lat, max_lon, max_lat]` trong tham số `bounding_box`.
- Mọi bước vẫn đọc cùng file `vietnam.osm.pbf` nhưng chỉ trả dữ liệu thuộc vùng cần thiết.
- `network_bbox` được khai báo trực tiếp trong `regions.json`, không cần tạo boundary buffer.
- Project bớt một chương trình bên ngoài và bớt một loại file trung gian.

## Các bước thực hiện

### Bước 1 — Chuẩn bị input

- Thêm `networkx` vào `pyproject.toml` rồi chạy `python -m pip install -e .`.
- Lấy `pbf_path` bằng `get_osm_path()`.
- Lấy region bằng `get_region(region_id)`.
- Lấy `network_bbox` từ region theo thứ tự `[min_lon, min_lat, max_lon, max_lat]`.

Kết quả cần thấy: hàm build network có `pbf_path`, `region_id` và bốn giá trị bbox.

### Bước 2 — Tạo Pyrosm reader theo bbox

- Khởi tạo `OSM(str(pbf_path), bounding_box=network_bbox)`.
- Không khởi tạo `OSM(str(pbf_path))` không có bbox trong luồng theo region, vì như vậy Pyrosm có thể đọc dữ liệu toàn quốc không cần thiết.
- Nếu Pyrosm báo bbox hoặc PBF không hợp lệ, dừng trước khi tạo graph.

Code mục tiêu:

```python
osm = OSM(
    str(pbf_path),
    bounding_box=network_bbox,
)
```

Kết quả cần thấy: một reader chỉ áp dụng cho bbox của region hiện tại.

### Bước 3 — Đọc walking nodes và edges

- Gọi `osm.get_network(network_type="walking", nodes=True)`.
- Nhận hai GeoDataFrame: `walk_nodes` và `walk_edges`.
- Kiểm tra hai bảng không rỗng.
- Giữ các cột cần dùng như ID, `u`, `v`, `highway`, `oneway`, `access`, `length` và geometry.
- Không tự lọc lại danh sách loại đường nếu bộ lọc walking của Pyrosm đã đáp ứng mục tiêu.

Code mục tiêu:

```python
walk_nodes, walk_edges = osm.get_network(
    network_type="walking",
    nodes=True,
)
```

Kết quả cần thấy: có node và từng đoạn edge có thể dùng để tạo walking graph.

### Bước 4 — Đọc driving nodes và edges

- Gọi cùng reader với `network_type="driving"`.
- Nhận `drive_nodes` và `drive_edges`.
- Giữ thêm `maxspeed`, `lanes` và `service` nếu có.
- So sánh số node/edge với walking network; hai mạng không bắt buộc giống nhau.

Code mục tiêu:

```python
drive_nodes, drive_edges = osm.get_network(
    network_type="driving",
    nodes=True,
)
```

Kết quả cần thấy: đường dành riêng cho người đi bộ có thể chỉ nằm trong walking network, còn motorway chỉ nằm trong driving network.

### Bước 5 — Chuẩn hóa node, edge và chiều dài

- Đổi cột `length` của Pyrosm thành tên thống nhất `length_m`.
- Chuyển `length_m` về kiểu số và kiểm tra không null, không âm.
- Kiểm tra node có ID và tọa độ; edge có node đầu `u`, node cuối `v` và geometry.
- Chỉ giữ các tag thật sự được dùng trong routing hoặc road features để giảm dung lượng.
- Không tự tính chiều dài từ EPSG:4326 khi Pyrosm đã cung cấp chiều dài theo mét.

Kết quả cần thấy: node/edge có schema ổn định cho cả walking và driving.

### Bước 6 — Chuyển sang NetworkX graph

- Dùng `OSM.to_graph(nodes, edges, graph_type="networkx")` cho từng network.
- Kết quả phải là `MultiDiGraph` để giữ đường song song và chiều đi.
- Kiểm tra edge trong graph có `length_m` và các thuộc tính cần thiết.
- Kiểm tra một vài đường `oneway=yes` để bảo đảm graph không cho đi ngược chiều.
- Không tự viết lại toàn bộ logic nối node/edge nếu hàm Pyrosm đã tạo graph đúng.

Code mục tiêu:

```python
walk_graph = OSM.to_graph(
    walk_nodes,
    walk_edges,
    graph_type="networkx",
)
```

Kết quả cần thấy: graph có thể tìm một đường đi mẫu bằng NetworkX.

### Bước 7 — Thêm thời gian di chuyển

- Walking graph dùng `travel_time_s = length_m / walking_speed_mps`.
- Lấy `walking_speed_mps` từ `project.json`.
- Driving graph dùng `maxspeed` khi hợp lệ; nếu thiếu thì dùng bảng tốc độ mặc định theo `highway` và đánh dấu giá trị ước lượng.
- Đổi km/h sang m/s trước khi tính driving time.
- Kiểm tra mọi `travel_time_s` dùng cho Dijkstra là số hữu hạn và không âm.

Kết quả cần thấy: cả hai graph có weight `travel_time_s` dùng được cho shortest path.

### Bước 8 — Lưu và kiểm tra artifact

- Lưu walking/driving graph thành GraphML.
- Lưu bốn bảng node/edge thành GeoParquet.
- Mở lại GraphML và chuyển `length_m`, `travel_time_s` về số nếu chúng được đọc thành chuỗi.
- Ghi `network_summary.json`: số node, edge, tổng chiều dài, component, edge thiếu weight và edge một chiều.
- Vẽ ít nhất năm tuyến mẫu để kiểm tra graph bám theo đường thật.

Kết quả cần thấy: graph load lại được, Parquet đọc được và tuyến mẫu không phải đường thẳng nối hai điểm.

## File cần tạo hoặc sửa

```text
src/ady201/network.py
src/ady201/main.py
pyproject.toml
```

Không tạo `road_extract.py`, không gọi Osmium và không sinh `region.osm.pbf`.

Lệnh mục tiêu:

```powershell
ady201 build-network --region hanoi
```

## Các hàm nên có trong `network.py`

- `read_network(pbf_path, network_bbox, network_type)`: gọi Pyrosm và trả node/edge.
- `create_graph(nodes, edges)`: gọi `OSM.to_graph()`.
- `add_walking_time(graph, walking_speed_mps)`: thêm thời gian đi bộ.
- `add_driving_time(graph)`: thêm thời gian lái xe.
- `save_network(region_id, ...)`: ghi GraphML, GeoParquet và summary.
- `build_network(region_id)`: lấy PBF từ `osm_input.py`, lấy bbox từ `regions.py` rồi gọi các hàm trên theo đúng thứ tự.

## Quy tắc

- Pyrosm luôn nhận `network_bbox` khi xử lý một region.
- Graph dùng `MultiDiGraph`.
- Edge routing có `u`, `v`, `key`, `length_m` và `travel_time_s`.
- Không xóa component nhỏ trước khi tạo quality report.
- Không lưu toàn bộ graph vào DuckDB khi GraphML/GeoParquet đã đủ.
- Không tạo bản sao PBF theo region.

## Lỗi thường gặp

- Quên truyền bbox khiến Pyrosm đọc mạng đường toàn Việt Nam.
- Đảo thứ tự latitude và longitude trong bbox.
- Chọn bbox quá nhỏ khiến điểm cần phân tích nằm ngoài graph.
- Tự tính lại chiều dài trên tọa độ độ dù Pyrosm đã có `length` theo mét.
- Load GraphML rồi đưa weight dạng chuỗi vào Dijkstra.

## Cần học trước

- `pyrosm.OSM` và bbox `[minx, miny, maxx, maxy]`.
- `get_network(..., nodes=True)`.
- `OSM.to_graph()`.
- Node, edge, `MultiDiGraph` và weight.
- Tag OSM `highway`, `access`, `oneway` và `maxspeed`.

## Tìm hiểu thêm

- Từ khóa: `Pyrosm bounding box list`.
- Từ khóa: `Pyrosm get_network walking driving`.
- Từ khóa: `Pyrosm to_graph NetworkX`.
- Từ khóa: `NetworkX MultiDiGraph`.

## Phân công

### Thành

- Chốt schema node/edge và kiểm tra Parquet bằng DuckDB.
- Kiểm tra cột dùng cho road features không bị thiếu.

### Hiếu

- Viết các hàm Pyrosm, tạo graph và thêm travel time.
- Kiểm tra one-way, component, weight, RAM và thời gian đọc PBF.

### Quang

- Tạo `build-network` trong `main.py`.
- Vẽ graph và năm tuyến mẫu để phát hiện kết quả bất thường.

## Đầu ra

```text
data/processed/{region_id}/network/walk.graphml
data/processed/{region_id}/network/drive.graphml
data/processed/{region_id}/network/walk_nodes.parquet
data/processed/{region_id}/network/walk_edges.parquet
data/processed/{region_id}/network/drive_nodes.parquet
data/processed/{region_id}/network/drive_edges.parquet
outputs/quality/{region_id}/network_summary.json
```

## Hoàn thành khi

- `build-network` đọc trực tiếp `vietnam.osm.pbf` bằng Pyrosm.
- Không tồn tại bước cắt PBF hoặc file `region.osm.pbf`.
- Walking/driving graph load lại được và có weight hợp lệ.
- Năm tuyến mẫu đi theo mạng đường.
- Đổi `region_id` không cần sửa code.
