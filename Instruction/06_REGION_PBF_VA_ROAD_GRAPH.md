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

### Bước 1 — Cắt PBF cho một khu vực

- Lấy Vietnam PBF theo `snapshot_id` và extraction boundary đã buffer ở giai đoạn 04.
- Chạy lệnh tương đương: `osmium extract --polygon <boundary.geojson> --strategy complete_ways --output <region.osm.pbf> <vietnam.osm.pbf>`.
- Ghi file vào đúng thư mục của `snapshot_id` và `region_id`; không dùng chung một `region.osm.pbf` cho mọi lần chạy.
- Dùng `osmium fileinfo` kiểm tra file đầu ra trước khi Pyrosm đọc.

Kết quả cần thấy: PBF khu vực nhỏ hơn PBF Việt Nam và có thêm phần đường gần biên nhờ extraction boundary.

### Bước 2 — Trích xuất hai loại mạng đường

- Trong `road_extract.py`, đọc cùng một region PBF hai lần theo loại network: walking và driving.
- Walking graph chỉ giữ các đường người đi bộ được phép sử dụng; driving graph giữ đường xe cơ giới phù hợp.
- Giữ các tag cần cho phân tích như `highway`, `oneway`, `access`, `maxspeed`, `name` và geometry.
- Kiểm tra node/edge không rỗng trước khi chuyển sang graph.

Kết quả cần thấy: walking và driving có số node/edge khác nhau vì quy tắc di chuyển khác nhau.

### Bước 3 — Tạo `MultiDiGraph`

- Chuyển bảng node/edge thành `networkx.MultiDiGraph` trong `road_graph.py`.
- Node cần có `node_id`, `x`, `y`; edge cần có `u`, `v`, `key` và các thuộc tính đường.
- Dùng graph có hướng để giữ chiều đi; dùng multi-graph để không làm mất các đoạn đường song song giữa cùng hai node.
- Kiểm tra mọi `u` và `v` của edge đều tồn tại trong bảng node.

Kết quả cần thấy: có thể chọn một edge bằng bộ khóa `(u, v, key)` và graph không có edge mồ côi.

### Bước 4 — Chuẩn hóa chiều dài edge

- Ưu tiên trường chiều dài do thư viện trích xuất cung cấp nếu đơn vị và nguồn rõ ràng.
- Nếu phải tự tính, chuyển geometry sang CRS theo mét rồi tính độ dài.
- Đổi về số thực và đặt tên thống nhất là `length_m`.
- Dừng bước nếu có `length_m` âm, bằng null hoặc bằng 0 bất thường.

Kết quả cần thấy: mọi edge dùng cho routing có chiều dài theo mét và không âm.

### Bước 5 — Tạo weight thời gian di chuyển

- Với walking graph, tính `travel_time_s = length_m / walking_speed_mps`.
- Lấy `walking_speed_mps` từ `project.json`, không ghi số cố định trong hàm.
- Với driving graph, chuẩn hóa tốc độ về m/s rồi tính thời gian; nếu thiếu `maxspeed`, dùng bảng tốc độ mặc định theo `highway` và ghi cờ đã ước lượng.
- Kiểm tra `travel_time_s` là số hữu hạn và không âm.

Kết quả cần thấy: Dijkstra có thể dùng trực tiếp `travel_time_s` làm weight.

### Bước 6 — Giữ đúng chiều đi của đường

- Với đường một chiều, chỉ tạo edge theo chiều được phép.
- Với đường hai chiều, graph cần có edge cho cả hai hướng nhưng vẫn phải nhận biết đây là cùng một đoạn đường vật lý khi tính tổng chiều dài ở giai đoạn 09.
- Kiểm tra một vài đường có tag `oneway=yes`, vòng xuyến và đường cấm truy cập.
- Không đổi toàn bộ graph thành undirected chỉ để routing dễ hơn.

Kết quả cần thấy: tuyến mẫu không đi ngược chiều trên đoạn đường một chiều.

### Bước 7 — Lưu artifact và đọc thử lại

- Lưu walking/driving graph thành hai file GraphML riêng.
- Lưu node và edge thành GeoParquet để DuckDB và GeoPandas phân tích mà không cần load graph.
- Sau khi ghi, mở lại GraphML rồi kiểm tra kiểu dữ liệu của `length_m` và `travel_time_s`; GraphML có thể đọc thuộc tính số thành chuỗi.
- So sánh số node/edge trước và sau khi lưu.

Kết quả cần thấy: graph load lại có cùng số node/edge và weight vẫn chuyển được về số.

### Bước 8 — Tạo báo cáo chất lượng mạng đường

- Ghi số node, edge, tổng chiều dài và số connected component cho từng network.
- Ghi kích thước component lớn nhất để nhận ra graph bị đứt bất thường.
- Thống kê số edge thiếu weight, weight bằng 0 và số edge một chiều.
- Lưu báo cáo vào `network_summary.json` để so sánh giữa các snapshot.

Kết quả cần thấy: người kiểm tra không cần mở GraphML vẫn biết graph có đủ dữ liệu cơ bản hay không.

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

## Lỗi thường gặp

- Cắt đúng boundary gốc mà không buffer, khiến đường bị đứt ngay sát biên.
- Tính chiều dài trực tiếp trên EPSG:4326 nên nhận đơn vị độ thay vì mét.
- Chuyển graph thành vô hướng và làm mất quy tắc đường một chiều.
- Load GraphML rồi truyền weight dạng chuỗi vào thuật toán đường đi.

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
