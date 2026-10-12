# Kế hoạch triển khai dự án phân tích dịch vụ đô thị và mạng lưới giao thông Hà Nội

## 1. Mục đích của tài liệu

Tài liệu này là kế hoạch làm việc chung cho ba thành viên:

- Thành: nhiệm vụ mức trung bình–khó.
- Hiếu: nhiệm vụ mức trung bình–khó.
- Quang: nhiệm vụ mức dễ–trung bình.

Mục tiêu không chỉ là chia việc để hoàn thành sản phẩm. Mỗi thành viên phải hiểu:

1. Dữ liệu đầu vào đến từ đâu và có hạn chế gì.
2. Dữ liệu được làm sạch, làm giàu và lưu trữ như thế nào.
3. Road graph được tạo từ OSM ra sao.
4. POI được nối vào road graph như thế nào.
5. Các chỉ số dịch vụ, accessibility và kết nối đường được tính như thế nào.
6. Feature được dùng để clustering và xây dựng chỉ số tổng hợp ra sao.
7. Cách đọc, kiểm tra và giải thích các bản đồ kết quả.

---

## 2. Quyết định kỹ thuật chính

### 2.1. Không chọn riêng SQL hoặc Python

Sử dụng mô hình kết hợp:

- **Python**: tải và xử lý file OSM, chuẩn hóa dữ liệu, làm giàu POI, tạo graph, snap POI, chạy hàm Dijkstra có sẵn, clustering và trực quan hóa.
- **PostgreSQL + PostGIS**: lưu dữ liệu chuẩn, áp dụng constraint, spatial index, spatial join, tổng hợp theo vùng và lưu kết quả cuối.
- **GeoParquet/GraphML**: lưu các sản phẩm trung gian lớn để pipeline không phải chạy lại từ đầu.

Không triển khai Dijkstra thủ công. Dùng hàm có sẵn của NetworkX/OSMnx và ghi rõ `weight` được sử dụng.

### 2.2. Phạm vi không gian

- Khu vực nghiên cứu: Hà Nội.
- Dùng **polygon ranh giới hành chính**, không dùng bounding box làm ranh giới cuối cùng.
- Bounding box chỉ được dùng để thử nghiệm hoặc tải dữ liệu nhanh.
- Các đối tượng nằm ngoài polygon Hà Nội phải được loại bỏ hoặc đánh dấu rõ.

### 2.3. Đơn vị phân tích

Dùng **hexagon** làm đơn vị phân tích chính vì:

- Các ô có hình dạng và diện tích gần đồng nhất.
- Phù hợp với heatmap, clustering và so sánh giữa các khu vực.
- Hạn chế sai lệch do đơn vị hành chính có diện tích quá khác nhau.

Quy tắc lựa chọn kích thước:

1. Thử ít nhất hai mức kích thước, ví dụ khoảng 500 m và 1 km.
2. Chọn mức không tạo quá nhiều ô rỗng nhưng vẫn thể hiện được khác biệt nội đô–ngoại thành.
3. Ghi kích thước hoặc H3 resolution cuối cùng trong `config/project.yaml`.
4. Không thay đổi resolution sau khi đã tạo feature matrix chính thức, trừ khi tạo một `run_id` mới.

Có thể tổng hợp bổ sung theo quận/huyện để báo cáo dễ đọc, nhưng clustering và chỉ số chính dùng hexagon.

### 2.4. Tạo hai mạng đường riêng

1. **Walking graph**:
   - Dùng cho thời gian đi bộ và accessibility.
   - Bao gồm đường đi bộ, ngõ, lối đi và các loại đường người đi bộ được phép sử dụng.
   - Trọng số chính: `travel_time_s`.

2. **Driving/street graph**:
   - Dùng để đo đặc điểm hạ tầng đường.
   - Giữ hướng đường một chiều.
   - Dùng để tính mật độ đường, mật độ giao lộ và tỷ lệ đường chính.

Không trộn hai graph khi tính toán. Mỗi kết quả phải có cột `network_type`.

### 2.5. Cách hiểu dữ liệu OSM

File Geofabrik chứa các OSM primitive:

- `node`: một điểm có tọa độ.
- `way`: một danh sách node có thứ tự, có thể biểu diễn đường hoặc vùng.
- `relation`: quan hệ giữa node/way/relation, ví dụ ranh giới, tuyến hoặc hạn chế rẽ.

File `.osm.pbf` **chưa phải là road graph sẵn sàng chạy Dijkstra**. Pipeline vẫn phải:

1. Lọc các way mang ý nghĩa đường.
2. Giải tham chiếu từ way đến node.
3. Xử lý đường một chiều và quyền truy cập.
4. Tạo directed edges `u → v`.
5. Tính chiều dài và thời gian đi qua edge.
6. Kiểm tra thành phần liên thông.
7. Snap điểm bắt đầu, điểm kết thúc và POI vào graph.

Một POI có `osm_type=node` không đồng nghĩa node đó là node của road graph.

---

## 3. Câu hỏi nghiên cứu và đầu ra tương ứng

| Câu hỏi | Chỉ số/Phương pháp | Đầu ra |
|---|---|---|
| Khu vực nào phát triển dịch vụ hơn? | Mật độ POI/km², số nhóm dịch vụ, độ đa dạng dịch vụ | Bảng xếp hạng và bản đồ mật độ |
| Khu vực nào thiếu dịch vụ thiết yếu? | Số POI thiết yếu, thời gian tới dịch vụ gần nhất, số loại dịch vụ trong 15 phút | Bản đồ vùng thiếu dịch vụ |
| Khả năng tiếp cận khi đi bộ ra sao? | Network travel time đến dịch vụ gần nhất; coverage 5/10/15 phút | Bản đồ accessibility |
| Nơi nào nhiều dịch vụ nhưng đường kém kết nối? | Service density cao kết hợp intersection/road density thấp | Bản đồ mismatch |
| Những vùng đô thị nào tương tự nhau? | Chuẩn hóa feature, K-Means baseline, silhouette và diễn giải cluster | Bản đồ cluster và bảng đặc trưng |
| Có thể tạo chỉ số tổng hợp không? | Accessibility score, service completeness, connectivity score | Bản đồ chỉ số tổng hợp |
| Hạ tầng giao thông khác nhau thế nào? | Mật độ đường, mật độ giao lộ, tỷ lệ đường chính, tỷ lệ loại đường | Bảng và bản đồ hạ tầng |

---

## 4. Phạm vi MVP và phần mở rộng

### 4.1. MVP bắt buộc

- Chuẩn hóa POI hiện có và giữ lại các OSM tags hữu ích.
- Bổ sung ít nhất `shop=supermarket` và dữ liệu điểm dừng giao thông công cộng.
- Lưu POI chuẩn vào PostGIS.
- Tạo hexagon cho toàn bộ Hà Nội.
- Tạo walking graph và driving graph từ Geofabrik PBF.
- Snap POI và tâm/điểm đại diện của hexagon vào walking graph.
- Tính accessibility đến các nhóm dịch vụ thiết yếu.
- Tính chỉ số dịch vụ và hạ tầng đường theo hexagon.
- Thực hiện clustering cơ bản.
- Tạo các bản đồ và báo cáo kết quả.

### 4.2. Phần mở rộng nếu còn thời gian

- Thêm dữ liệu dân số để tính dịch vụ trên đầu người.
- Thêm nhiều mức walking speed hoặc phân tích độ nhạy.
- So sánh accessibility ngày thường/cuối tuần nếu có `opening_hours` đủ tốt.
- Tạo dashboard tương tác.
- Dùng GTFS nếu muốn phân tích thời gian di chuyển bằng phương tiện công cộng.

### 4.3. Ngoài phạm vi MVP

- Giao thông thời gian thực.
- Tốc độ đi bộ thực đo của từng người.
- Định tuyến ô tô có đầy đủ turn restriction và tình trạng tắc đường.
- Đánh giá chất lượng thực tế của bệnh viện/trường học chỉ từ OSM.
- Thời gian hành trình bằng xe buýt chỉ dựa trên vị trí trạm.

OSM chỉ cho biết vị trí của trạm hoặc hạ tầng. Muốn đánh giá thời gian xe buýt cần thêm dữ liệu lịch trình như GTFS.

---

## 5. Nguồn dữ liệu

### 5.1. POI hiện tại

Project hiện có 12.265 POI trong `Flatten/Systhesis.csv`. Tuy nhiên file này chỉ giữ:

```text
id, lat, lon, amenity, name
```

Dữ liệu raw còn nhiều trường có thể dùng để làm giàu như địa chỉ, operator, brand, opening hours, phone và website. Do đó:

- Không dùng `Systhesis.csv` làm nguồn sự thật duy nhất.
- Luôn giữ raw JSON bất biến.
- Khóa OSM phải là `(osm_type, osm_id)`, không dùng riêng `id`.

### 5.2. Dữ liệu đường

Nguồn chính:

- `vietnam-latest.osm.pbf` từ Geofabrik.
- Trang tải: <https://download.geofabrik.de/asia/vietnam.html>

Quy tắc:

- Không commit file PBF vào Git.
- Lưu URL, ngày tải, timestamp dữ liệu, kích thước và checksum trong manifest.
- Sau khi tải, cắt riêng khu vực Hà Nội thành `hanoi.osm.pbf`.
- Dùng cùng một snapshot cho các lần chạy chính thức để đảm bảo tái lập.

### 5.3. Ranh giới Hà Nội

Lưu polygon chuẩn tại:

```text
data/boundary/hanoi.geojson
```

Kiểm tra:

- CRS là EPSG:4326.
- Geometry hợp lệ.
- Là Polygon hoặc MultiPolygon.
- Ghi nguồn, OSM relation ID và ngày lấy dữ liệu vào manifest.

### 5.4. Nhóm dịch vụ cần có

| Nhóm | OSM tags gợi ý |
|---|---|
| Y tế | `amenity=hospital/clinic/doctors/pharmacy/dentist` |
| Giáo dục | `amenity=school/kindergarten/college/university/library` |
| Mua sắm thiết yếu | `shop=supermarket/convenience`, `amenity=marketplace` |
| Giao thông công cộng | `highway=bus_stop`, `public_transport=platform/station`, `amenity=bus_station` |
| Tài chính | `amenity=bank/atm/post_office` |
| Ăn uống | `amenity=restaurant/cafe/fast_food/food_court` |
| An toàn/cộng đồng | `amenity=police/fire_station/community_centre` |

Không chỉ truy vấn `amenity`, vì supermarket và nhiều điểm dừng xe buýt dùng tag khác.

---

## 6. Cấu trúc repository đề xuất

```text
ADY201_FA26/
├── README.md
├── KE_HOACH_DU_AN.md
├── pyproject.toml                 # hoặc requirements.txt
├── .env.example
├── config/
│   └── project.yaml
├── data/
│   ├── README.md
│   ├── manifest.csv
│   ├── boundary/
│   │   └── hanoi.geojson
│   ├── raw/                      # gitignored
│   │   ├── poi/
│   │   └── osm/
│   │       ├── vietnam-latest.osm.pbf
│   │       └── hanoi.osm.pbf
│   ├── interim/                  # gitignored
│   └── processed/                # chỉ commit mẫu nhỏ nếu cần
├── src/
│   └── ady201/
│       ├── config.py
│       ├── poi/
│       │   ├── ingest.py
│       │   ├── normalize.py
│       │   └── validate.py
│       ├── network/
│       │   ├── extract.py
│       │   ├── build_graph.py
│       │   ├── snap.py
│       │   └── accessibility.py
│       ├── features/
│       │   ├── service.py
│       │   ├── roads.py
│       │   └── composite.py
│       ├── models/
│       │   └── clustering.py
│       └── visualization/
│           └── maps.py
├── sql/
│   ├── 001_extensions_schemas.sql
│   ├── 002_core_tables.sql
│   ├── 003_network_tables.sql
│   ├── 004_analytics_tables.sql
│   └── 005_quality_checks.sql
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_accessibility_check.ipynb
│   └── 03_clustering_report.ipynb
├── tests/
│   ├── test_poi.py
│   ├── test_network.py
│   ├── test_accessibility.py
│   └── test_features.py
└── outputs/
    ├── figures/
    ├── maps/
    └── tables/
```

Quy tắc: notebook chỉ dùng để khám phá và trình bày. Logic cần chạy lại phải nằm trong `src/`.

---

## 7. Mô hình dữ liệu

### 7.1. Bảng POI chuẩn

`core.poi`

| Cột | Ý nghĩa |
|---|---|
| `poi_id` | Surrogate key nội bộ |
| `osm_type` | node/way/relation |
| `osm_id` | ID OSM |
| `category` | Nhóm dịch vụ chuẩn |
| `subcategory` | Loại chi tiết |
| `name` | Tên chính |
| `name_vi`, `name_en` | Tên theo ngôn ngữ nếu có |
| `address` | Địa chỉ chuẩn hóa |
| `operator`, `brand` | Đơn vị vận hành/thương hiệu |
| `opening_hours` | Giờ mở cửa gốc |
| `phone`, `website` | Thông tin liên hệ |
| `tags` | JSONB chứa tags còn lại |
| `geom` | Point EPSG:4326 |
| `source` | Nguồn dữ liệu |
| `snapshot_date` | Ngày snapshot |
| `quality_flags` | Các cảnh báo chất lượng |

Constraint tối thiểu:

```text
UNIQUE (osm_type, osm_id)
category IS NOT NULL
geom IS NOT NULL
```

Với POI dạng polygon, dùng điểm đại diện nằm bên trong polygon thay vì mặc định dùng centroid có thể nằm ngoài polygon.

### 7.2. Bảng graph

`network.node`

```text
network_type, node_id, geom, degree
```

`network.edge`

```text
network_type, edge_id, u, v, edge_key,
osm_way_id, highway, oneway,
length_m, speed_kph, travel_time_s, geom
```

Khóa edge nên hỗ trợ parallel edges, ví dụ `(network_type, u, v, edge_key)`.

### 7.3. Bảng hexagon

`analytics.hex_cell`

```text
cell_id, resolution, area_km2, geom, representative_point
```

### 7.4. Bảng snap

`analytics.poi_snap`

```text
poi_id, network_type, node_id, snap_distance_m, status
```

`analytics.cell_snap`

```text
cell_id, network_type, node_id, snap_distance_m, status
```

### 7.5. Feature matrix

`analytics.cell_feature`

Một hàng tương ứng một hexagon và một `run_id`. Không ghi đè kết quả cũ.

---

## 8. Pipeline chi tiết

### Bước 0 — Chốt định nghĩa trước khi viết code

**Cả nhóm thực hiện.**

Chốt và ghi vào `config/project.yaml`:

- Polygon nghiên cứu.
- Hex resolution.
- Walking speed mặc định; đề xuất khởi đầu 4,8 km/h, nhưng phải ghi là giả định.
- Ngưỡng accessibility: 5, 10 và 15 phút.
- Danh sách nhóm dịch vụ thiết yếu.
- Danh sách `highway` được xem là đường chính.
- Quy tắc intersection.
- Snapshot date.
- CRS lưu trữ EPSG:4326 và CRS projected dùng để tính mét.

Định nghĩa đề xuất:

- Đường chính: `motorway`, `trunk`, `primary`, `secondary`.
- Giao lộ: node có degree không hướng từ 3 trở lên sau khi graph được simplify.
- Không dùng số segment làm “số tuyến đường chính”, vì một tuyến có thể bị chia thành nhiều OSM way. Ưu tiên **tổng chiều dài đường chính** và **tỷ lệ chiều dài đường chính**.

**Hoàn thành khi:** cả ba thành viên ký xác nhận data dictionary và không còn tên chỉ số chưa có công thức.

---

### Bước 1 — Sửa và chuẩn hóa pipeline POI hiện tại

1. Sửa `Data/...` thành đường dẫn lấy từ config.
2. Không hard-code thư mục hoặc ổ đĩa cá nhân.
3. Gộp các hàm chung:
   - Lấy tọa độ từ node hoặc center/representative point.
   - Làm sạch text.
   - Chuẩn hóa category.
   - Validate latitude/longitude.
4. Giữ `osm_type`, `osm_id` và toàn bộ `tags`.
5. Loại bản ghi trùng chính xác theo `(osm_type, osm_id)`.
6. Không loại POI chỉ vì thiếu `name`.
7. Tạo `quality_flags`, ví dụ:
   - `missing_name`
   - `missing_address`
   - `outside_boundary`
   - `invalid_geometry`
8. Xuất GeoParquet hoặc CSV chuẩn hóa và báo cáo chất lượng.

**Đầu ra:**

```text
data/interim/poi_normalized.parquet
outputs/tables/poi_quality_report.csv
```

**Hoàn thành khi:** chạy lại từ raw JSON cho ra kết quả xác định, không phụ thuộc máy cá nhân.

---

### Bước 2 — Làm giàu dữ liệu POI

Ưu tiên làm giàu từ chính OSM tags trước:

- Địa chỉ từ `addr:*`.
- Tên từ `name`, `name:vi`, `name:en`, `official_name`.
- `operator`, `brand`.
- `opening_hours`.
- `phone`, `website`.
- Các trường chuyên ngành như `healthcare`, `education`, `cuisine`.

Bổ sung dữ liệu còn thiếu trong danh mục:

- Supermarket/convenience từ tag `shop`.
- Bus stop/station/platform từ `highway` và `public_transport`.

Tạo các feature chất lượng:

- `is_named`.
- `has_address`.
- `has_contact`.
- `completeness_score`.

Không reverse-geocode hàng nghìn POI qua public Nominatim. Nếu cần địa giới, dùng point-in-polygon với boundary địa phương.

**Hoàn thành khi:** mỗi nhóm dịch vụ có mapping rõ ràng từ OSM tag sang `category/subcategory` và có thống kê số lượng trước/sau.

---

### Bước 3 — Xây dựng PostGIS

1. Tạo extensions:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

2. Tạo schema:

```text
staging
core
network
analytics
```

3. Tạo bảng và constraint theo mô hình dữ liệu.
4. Nạp dữ liệu bằng Python/psycopg hoặc `\copy`; không dùng server-side `COPY` với đường dẫn máy cá nhân.
5. Tạo geometry đúng thứ tự `Point(lon, lat)`.
6. Tạo index:
   - B-tree cho `category`, `subcategory`.
   - GiST cho geometry.
7. Lọc theo polygon Hà Nội bằng spatial predicate.
8. Lưu cả bản ghi bị loại và lý do vào bảng lỗi, không xóa âm thầm.

**Kiểm tra bắt buộc:**

- Số bản ghi staging và core.
- Số key trùng.
- Số geometry invalid.
- Số POI ngoài polygon.
- Số POI theo category.
- Tỷ lệ thiếu name/address.

---

### Bước 4 — Tạo hexagon

1. Tạo hexagon phủ polygon Hà Nội bằng Python H3 hoặc công cụ không gian tương đương.
2. Chỉ giữ ô giao với polygon.
3. Clip ô biên theo polygon nếu cần tính chính xác diện tích.
4. Tính `area_km2` từ CRS projected, không tính trực tiếp trên độ latitude/longitude.
5. Tạo điểm đại diện cho mỗi hexagon.
6. Nạp vào `analytics.hex_cell`.

**Lưu ý:** các chỉ số đếm phải chuyển thành mật độ theo diện tích khi so sánh các ô biên có diện tích khác nhau.

---

### Bước 5 — Tải và cắt PBF Hà Nội

1. Tải `vietnam-latest.osm.pbf` từ Geofabrik.
2. Ghi metadata và checksum vào `data/manifest.csv`.
3. Dùng polygon Hà Nội để cắt file.
4. Ưu tiên chiến lược `complete_ways` để giữ đủ node tham chiếu của way đi qua biên.

Lệnh minh họa:

```powershell
osmium fileinfo data/raw/osm/vietnam-latest.osm.pbf
osmium extract `
  -p data/boundary/hanoi.geojson `
  --strategy=complete_ways `
  data/raw/osm/vietnam-latest.osm.pbf `
  -o data/raw/osm/hanoi.osm.pbf
```

Không ghi đè file snapshot cũ. Đặt tên kèm ngày nếu có nhiều snapshot.

**Hoàn thành khi:** `osmium fileinfo` đọc được file Hà Nội và các way không bị thiếu node reference.

---

### Bước 6 — Tạo walking graph và driving graph

Quy trình đề xuất bằng Pyrosm + NetworkX/OSMnx:

1. Đọc `hanoi.osm.pbf`.
2. Tạo walking network.
3. Tạo driving network.
4. Chuyển thành directed `MultiDiGraph`.
5. Simplify graph nhưng giữ thuộc tính cần thiết.
6. Tính chiều dài edge theo mét.
7. Tạo `travel_time_s`.

Walking time:

```text
travel_time_s = length_m / walking_speed_mps
```

Driving time chỉ dùng nếu có chiến lược xử lý `maxspeed` và giá trị thiếu rõ ràng. MVP accessibility dùng walking time.

Lưu:

```text
data/processed/hanoi_walk.graphml
data/processed/hanoi_drive.graphml
data/processed/walk_nodes.parquet
data/processed/walk_edges.parquet
data/processed/drive_nodes.parquet
data/processed/drive_edges.parquet
```

Nạp node/edge cần thiết vào PostGIS để spatial join và hiển thị.

**Kiểm tra graph:**

- Số node và edge lớn hơn 0.
- Tất cả edge dùng cho routing có `length_m > 0`.
- Không có `travel_time_s` âm hoặc null.
- Báo cáo số connected components.
- Báo cáo tỷ lệ node/edge thuộc largest connected component.
- Kiểm tra một số đường một chiều trên driving graph.
- Vẽ thử graph của một khu vực nhỏ.

Không tự động loại các component nhỏ trước khi báo cáo. Sau khi kiểm tra, có thể dùng largest component cho routing và lưu quyết định trong metadata.

---

### Bước 7 — Snap POI và hexagon vào walking graph

1. Project POI, hex representative point và graph về cùng CRS theo mét.
2. Tìm nearest node theo batch, không loop từng điểm nếu thư viện hỗ trợ vectorization.
3. Lưu node ID và `snap_distance_m`.
4. Gắn trạng thái:
   - `ok`
   - `too_far`
   - `no_nearby_node`
   - `outside_network`
5. Kiểm tra thủ công các điểm có snap distance lớn.

MVP dùng nearest node. Nếu kết quả sai lệch nhiều trên các edge dài, phần mở rộng sẽ snap vào nearest edge và tạo connector.

Không gán POI vào road node chỉ dựa trên việc hai đối tượng có cùng OSM ID.

**Đầu ra:** `analytics.poi_snap` và `analytics.cell_snap`.

---

### Bước 8 — Tính accessibility bằng Dijkstra có sẵn

#### 8.1. Route A đến B để kiểm tra

Dùng hàm có sẵn, ví dụ:

- `networkx.shortest_path(..., weight="travel_time_s")`
- `networkx.single_source_dijkstra(...)`
- `osmnx.routing.shortest_path(...)`

Kiểm tra một số cặp A–B và vẽ đường đi lên bản đồ.

#### 8.2. Accessibility cho toàn bộ Hà Nội

Không chạy Dijkstra riêng cho mọi cặp hexagon–POI.

Với từng category thiết yếu:

1. Lấy tập node đã snap của tất cả POI thuộc category đó.
2. Chạy **multi-source Dijkstra** một lần để lấy thời gian đến dịch vụ gần nhất.
3. Với directed graph, kiểm tra chiều graph; có thể cần chạy trên reversed graph để đo từ origin tới destination.
4. Gán kết quả về node đại diện của từng hexagon.
5. Lưu thời gian ngắn nhất và POI đích nếu cần.

Các nhóm tối thiểu:

- Hospital/clinic.
- Pharmacy.
- School/kindergarten.
- Supermarket/marketplace.
- Public transport stop/station.

Tạo các cột:

```text
nearest_hospital_min
nearest_pharmacy_min
nearest_school_min
nearest_supermarket_min
nearest_transit_min
hospital_within_15m
school_within_15m
supermarket_within_15m
transit_within_15m
```

Với node không có đường đến dịch vụ, giữ `unreachable=true`; không thay bằng 0.

**Kiểm thử:**

- Tất cả edge weights không âm.
- Route trả về có tổng edge weight bằng kết quả Dijkstra.
- Điểm nằm ngay cạnh dịch vụ có thời gian nhỏ.
- Node ở component không có dịch vụ được đánh dấu unreachable.
- So sánh ngẫu nhiên kết quả multi-source với một số lần chạy point-to-point.

---

### Bước 9 — Tính chỉ số dịch vụ theo hexagon

Các feature tối thiểu:

```text
poi_count_total
poi_density_km2
essential_poi_count
essential_poi_density_km2
service_category_count
service_diversity
healthcare_density
education_density
supermarket_density
transit_stop_density
finance_density
food_density
```

Quy tắc:

- Dùng spatial join point-in-polygon.
- POI trên biên chỉ được gán cho một cell theo một quy tắc cố định.
- Mật độ phải chia cho diện tích thực tế của cell sau khi clip.
- Nếu thêm dân số, giữ riêng `per_km2` và `per_1000_people`.
- Không xem POI không tên là POI không tồn tại.

`service_diversity` có thể là số category có mặt hoặc entropy; phải ghi rõ công thức.

---

### Bước 10 — Tính chỉ số mạng đường theo hexagon

Clip hoặc phân bổ edge theo hexagon để không tính toàn bộ chiều dài của một edge cho nhiều cell.

Các feature tối thiểu:

```text
road_length_m
road_density_km_per_km2
intersection_count
intersection_density_km2
avg_node_degree
dead_end_count
dead_end_ratio
main_road_length_m
main_road_share
footway_share hoặc local_road_share nếu phù hợp
```

Quy tắc tính:

- Tính degree trên graph không hướng/simple tương ứng để tránh đếm gấp đôi directed edge.
- Intersection là node degree từ 3 trở lên sau simplify.
- Dead end là node degree bằng 1, sau khi loại các node biên gây sai lệch nếu cần.
- `main_road_share = main_road_length_m / road_length_m`.
- Dùng chiều dài đã clip trong từng cell.
- Ghi rõ feature lấy từ walking hay driving graph.

Kiểm tra trực quan ít nhất ba vùng: nội đô dày đặc, vùng ven và vùng ít đường.

---

### Bước 11 — Xây dựng feature matrix

Ghép theo `cell_id`:

- Feature dịch vụ.
- Feature accessibility.
- Feature mạng đường.
- Diện tích và metadata.

Xử lý dữ liệu:

1. Phân biệt rõ `0` và `missing/unreachable`.
2. Kiểm tra phân phối và outlier.
3. Log-transform feature lệch mạnh nếu cần.
4. Loại một trong các feature tương quan gần như hoàn toàn.
5. Chuẩn hóa bằng StandardScaler hoặc RobustScaler.
6. Lưu cả feature gốc và feature đã scale.
7. Không đưa `cell_id`, tọa độ hoặc cluster label cũ vào model.

Feature gợi ý cho clustering baseline:

```text
poi_density_km2
service_category_count
nearest_hospital_min
nearest_school_min
nearest_supermarket_min
nearest_transit_min
road_density_km_per_km2
intersection_density_km2
main_road_share
dead_end_ratio
```

---

### Bước 12 — Clustering

Baseline dùng K-Means vì dễ triển khai và giải thích.

Quy trình:

1. Chạy với một dải `k`, ví dụ 2–8.
2. So sánh silhouette score.
3. Kiểm tra kích thước cluster; tránh cluster chỉ có vài cell do outlier.
4. Dùng PCA hai chiều để hỗ trợ quan sát, không dùng PCA plot làm bằng chứng duy nhất.
5. Lập bảng mean/median feature theo cluster.
6. Đặt tên cluster sau khi xem đặc trưng, ví dụ:
   - Dịch vụ cao – kết nối cao.
   - Dịch vụ cao – kết nối thấp.
   - Dịch vụ thấp – tiếp cận kém.
   - Ngoại thành – mật độ thấp.
7. Hiển thị cluster lên bản đồ và kiểm tra tính hợp lý về không gian.

Không chọn `k` chỉ vì silhouette cao nhất. Cần đồng thời xét khả năng giải thích và kích thước cluster.

DBSCAN/HDBSCAN là phần mở rộng, không thay baseline trước khi K-Means hoàn thành.

---

### Bước 13 — Chỉ số tổng hợp

### 13.1. Service completeness

Ví dụ với 5 nhóm thiết yếu:

```text
service_completeness_15m =
  số nhóm dịch vụ có thể tiếp cận trong 15 phút / 5
```

Giá trị nằm trong `[0, 1]` và dễ giải thích.

### 13.2. Accessibility score

Với từng nhóm dịch vụ, quy đổi thời gian thành điểm giảm dần và bằng 0 khi vượt ngưỡng tối đa. Sau đó lấy trung bình các nhóm.

Một công thức dễ giải thích:

```text
category_score = max(0, 1 - min(travel_time_min, 15) / 15)
accessibility_score = mean(category_score của các nhóm thiết yếu)
```

### 13.3. Connectivity score

Kết hợp các feature đã chuẩn hóa:

- Road density: chiều dương.
- Intersection density: chiều dương.
- Average degree: chiều dương.
- Dead-end ratio: chiều âm.

### 13.4. Chỉ số tổng hợp cuối

- Dùng trọng số bằng nhau làm baseline.
- Ghi trọng số trong config.
- Chạy sensitivity check với ít nhất một bộ trọng số khác.
- Không khẳng định chỉ số là “chất lượng sống” nếu dữ liệu không đo đủ khái niệm đó.

---

### Bước 14 — Phát hiện khu vực ưu tiên

Tạo các rule minh bạch:

### Khu vực thiếu dịch vụ

- `service_completeness_15m` thấp; hoặc
- Không có hospital/school/supermarket/transit trong 15 phút.

### Dịch vụ cao nhưng đường kém kết nối

- `poi_density_km2` thuộc nhóm cao, ví dụ top quartile.
- `connectivity_score` thuộc nhóm thấp, ví dụ bottom quartile.

### Hạ tầng tốt nhưng dịch vụ thiếu

- Connectivity cao.
- Service completeness thấp.

Các ngưỡng percentile phải được lưu trong config và ghi trong báo cáo, không chọn sau khi đã nhìn bản đồ để tạo kết quả mong muốn.

---

### Bước 15 — Trực quan hóa

Bản đồ bắt buộc:

1. Mật độ toàn bộ POI.
2. Mật độ từng nhóm dịch vụ thiết yếu.
3. Thời gian đi bộ đến bệnh viện gần nhất.
4. Thời gian đi bộ đến trường học gần nhất.
5. Service completeness trong 15 phút.
6. Road density.
7. Intersection density.
8. Tỷ lệ đường chính.
9. Khu vực nhiều dịch vụ nhưng kết nối kém.
10. Cluster map.
11. Composite accessibility map.

Quy tắc bản đồ:

- Có tiêu đề, chú giải, đơn vị và nguồn dữ liệu.
- Cùng một chỉ số phải dùng cùng thang màu giữa các hình.
- Không dùng quá nhiều lớp cùng lúc.
- Có ghi snapshot date và walking speed.
- Với dữ liệu lệch mạnh, cân nhắc quantile classification nhưng phải ghi phương pháp.
- Xuất cả PNG cho báo cáo và HTML nếu dùng bản đồ tương tác.

---

## 9. Phân công nhiệm vụ

### 9.1. Thành — Data engineering và PostGIS

**Độ khó:** trung bình–khó.

### Nhiệm vụ chính

1. Refactor pipeline POI hiện tại.
2. Chuẩn hóa schema POI và mapping category.
3. Làm giàu từ OSM tags.
4. Tạo PostGIS schemas, tables, constraints và indexes.
5. Nạp POI, boundary, hexagon và kết quả feature vào database.
6. Tạo spatial join POI–hexagon.
7. Viết SQL quality checks.
8. Tạo service feature theo cell.

### File/module Thành chịu trách nhiệm chính

```text
src/ady201/poi/*
src/ady201/features/service.py
sql/001_extensions_schemas.sql
sql/002_core_tables.sql
sql/004_analytics_tables.sql
sql/005_quality_checks.sql
```

### Sản phẩm bàn giao

- `poi_normalized.parquet`.
- Bảng `core.poi`.
- Bảng `analytics.hex_cell`.
- Bảng service features.
- Data dictionary và quality report.

### Kiến thức Thành phải trình bày lại cho nhóm

- Tại sao khóa là `(osm_type, osm_id)`.
- Cách PostGIS lưu geometry và dùng spatial index.
- Cách POI được gán vào hexagon.
- Sự khác nhau giữa count, density và per-capita metric.

---

### 9.2. Hiếu — Road network và accessibility

**Độ khó:** trung bình–khó.

### Nhiệm vụ chính

1. Quản lý snapshot PBF và manifest.
2. Cắt PBF Việt Nam theo polygon Hà Nội.
3. Tạo walking graph và driving graph.
4. Validate graph và connected components.
5. Tính edge length và walking travel time.
6. Snap POI và hexagon vào graph.
7. Chạy Dijkstra/multi-source Dijkstra bằng hàm có sẵn.
8. Tính road feature theo hexagon.
9. Xuất route mẫu và kiểm thử accessibility.

### File/module Hiếu chịu trách nhiệm chính

```text
src/ady201/network/*
src/ady201/features/roads.py
sql/003_network_tables.sql
tests/test_network.py
tests/test_accessibility.py
```

### Sản phẩm bàn giao

- `hanoi.osm.pbf` và manifest, không commit PBF.
- Walking/driving GraphML.
- Node/edge GeoParquet.
- Bảng snap.
- Accessibility features.
- Road connectivity features.

### Kiến thức Hiếu phải trình bày lại cho nhóm

- Node, way, relation khác nhau thế nào.
- Vì sao PBF chưa phải graph hoàn chỉnh.
- `u`, `v`, directed edge, one-way và edge weight.
- Vì sao multi-source Dijkstra hiệu quả hơn chạy từng cặp.
- Cách xác định giao lộ và road density.

---

### 9.3. Quang — Data profiling, clustering và visualization

**Độ khó:** dễ–trung bình.

### Nhiệm vụ chính

1. Thực hiện EDA và missing-value report.
2. Kiểm tra phân phối category và feature theo vùng.
3. Ghép feature matrix từ các output đã thống nhất.
4. Xử lý missing/unreachable theo rule của nhóm.
5. Scale feature và chạy K-Means baseline.
6. Đánh giá silhouette, kích thước và đặc trưng cluster.
7. Tạo heatmap/hex map.
8. Tạo bảng xếp hạng khu vực và diễn giải kết quả.
9. Tích hợp hình ảnh vào báo cáo cuối.

### File/module Quang chịu trách nhiệm chính

```text
notebooks/01_eda.ipynb
notebooks/03_clustering_report.ipynb
src/ady201/models/clustering.py
src/ady201/visualization/maps.py
outputs/figures/*
outputs/maps/*
```

### Sản phẩm bàn giao

- EDA report.
- Feature matrix đã kiểm tra.
- Clustering result và cluster profile.
- Bộ bản đồ thống nhất.
- Bảng khu vực ưu tiên.

### Kiến thức Quang phải trình bày lại cho nhóm

- Ý nghĩa của các accessibility và road features.
- Tại sao cần scale trước K-Means.
- Silhouette score nói được và không nói được điều gì.
- Cách đọc bản đồ mismatch và composite index.

---

### 9.4. Ma trận owner–reviewer–tester

| Module | Owner | Reviewer kỹ thuật | Người chạy smoke test |
|---|---|---|---|
| POI normalization | Thành | Hiếu | Quang |
| PostGIS/schema | Thành | Hiếu | Quang |
| PBF và graph | Hiếu | Thành | Quang |
| Snap và accessibility | Hiếu | Thành | Quang |
| Service features | Thành | Quang | Hiếu |
| Road features | Hiếu | Thành | Quang |
| Feature matrix | Quang | Thành | Hiếu |
| Clustering | Quang | Hiếu | Thành |
| Maps/report | Quang | Thành + Hiếu | Cả nhóm |
| Composite index | Cả nhóm | Cả nhóm | Cả nhóm |

Owner chịu trách nhiệm triển khai, nhưng không sở hữu độc quyền kiến thức hoặc file.

---

## 10. Cơ chế để cả ba cùng hiểu dự án

### 10.1. Quy tắc bắt buộc

1. Mỗi pull request phải có ít nhất một reviewer khác owner.
2. Mỗi module phải có README ngắn hoặc docstring mô tả input, output và cách chạy.
3. Mỗi thành viên phải tự chạy toàn pipeline ít nhất một lần trên dataset mẫu nhỏ.
4. Mỗi tuần có một buổi demo 30–45 phút:
   - Owner chạy module.
   - Reviewer giải thích lại logic.
   - Người thứ ba đặt câu hỏi và chạy smoke test.
5. Trước bảo vệ, mỗi thành viên trình bày một module không do mình làm chính.

### 10.2. Phân công trình bày chéo đề xuất

- Thành trình bày graph và Dijkstra của Hiếu.
- Hiếu trình bày clustering và map của Quang.
- Quang trình bày pipeline POI/PostGIS của Thành.

### 10.3. Interface contract

Trước khi làm song song, cả nhóm thống nhất schema của:

- `core.poi`.
- `analytics.hex_cell`.
- `network.node` và `network.edge`.
- `analytics.poi_snap` và `cell_snap`.
- `analytics.cell_feature`.

Mọi thay đổi cột phải được cập nhật data dictionary và thông báo cho hai người còn lại.

---

## 11. Lịch triển khai đề xuất trong 6 tuần

Có thể co giãn theo lịch môn học, nhưng không thay đổi thứ tự dependency.

### Tuần 1 — Chốt phạm vi và dựng nền

**Cả nhóm**

- Đọc và thống nhất tài liệu này.
- Chốt category, hex size, walking speed và metric definitions.
- Tạo data dictionary và config.
- Chuẩn hóa cấu trúc repository và môi trường.

**Thành**

- Refactor một pipeline POI mẫu.
- Thiết kế schema PostGIS.

**Hiếu**

- Tải/cắt một PBF mẫu nhỏ.
- Tạo thử graph cho một khu vực nhỏ.

**Quang**

- EDA dữ liệu hiện tại.
- Tạo baseline quality report.

**Mốc:** mọi người chạy được pipeline mẫu trên cùng dữ liệu.

### Tuần 2 — POI chuẩn và PBF Hà Nội

**Thành**

- Hoàn thành normalize/enrich POI.
- Nạp `core.poi` và quality checks.

**Hiếu**

- Hoàn thành manifest và `hanoi.osm.pbf`.
- Tạo walking/driving graph bản đầu.

**Quang**

- Kiểm tra dữ liệu POI trước/sau.
- Chuẩn bị style và template bản đồ.

**Mốc:** có POI chuẩn và hai graph có thể đọc lại từ disk.

### Tuần 3 — Hexagon, graph QA và snapping

**Thành**

- Tạo hexagon.
- Spatial join POI–hexagon.

**Hiếu**

- Validate graph.
- Tính travel time.
- Snap POI và hexagon.

**Quang**

- Vẽ bản đồ POI/hex baseline.
- Kiểm tra các snap outlier do Hiếu cung cấp.

**Mốc:** mỗi POI/cell hợp lệ có node gần nhất hoặc trạng thái lỗi rõ ràng.

### Tuần 4 — Accessibility và road features

**Thành**

- Hoàn thành service features.

**Hiếu**

- Hoàn thành multi-source Dijkstra.
- Hoàn thành road network features.

**Quang**

- Kiểm tra phân phối feature.
- Vẽ accessibility và road maps bản đầu.

**Mốc:** có `cell_feature` chưa clustering nhưng đã đủ ba nhóm feature.

### Tuần 5 — Clustering, index và phân tích

**Quang**

- Scale feature, chạy clustering và profile cluster.
- Hoàn thiện bộ bản đồ.

**Thành + Hiếu**

- Review ý nghĩa feature và cluster.
- Cùng Quang thiết kế composite index và sensitivity check.

**Cả nhóm**

- Xác định các khu vực thiếu dịch vụ và mismatch.

**Mốc:** có kết quả phân tích có thể giải thích, không chỉ có bản đồ đẹp.

### Tuần 6 — Kiểm thử, báo cáo và bảo vệ

- Freeze snapshot và config.
- Chạy lại pipeline từ đầu.
- Lưu runtime, row counts và run metadata.
- Sửa lỗi cuối, không thêm feature lớn mới.
- Hoàn thiện báo cáo, slide và README.
- Thực hiện trình bày chéo.
- Chuẩn bị câu trả lời về giới hạn dữ liệu và giả định.

**Mốc:** một máy sạch có thể tái tạo kết quả theo README.

---

## 12. Thứ tự chạy pipeline cuối cùng

Tên command dưới đây là giao diện mục tiêu; nhóm sẽ hiện thực dần:

```powershell
# 1. Chuẩn hóa POI
python -m ady201.poi.ingest --config config/project.yaml
python -m ady201.poi.normalize --config config/project.yaml
python -m ady201.poi.validate --config config/project.yaml

# 2. Khởi tạo database
psql -f sql/001_extensions_schemas.sql
psql -f sql/002_core_tables.sql
psql -f sql/003_network_tables.sql
psql -f sql/004_analytics_tables.sql

# 3. Tạo/cập nhật graph
python -m ady201.network.extract --config config/project.yaml
python -m ady201.network.build_graph --config config/project.yaml
python -m ady201.network.snap --config config/project.yaml

# 4. Tính feature
python -m ady201.network.accessibility --config config/project.yaml
python -m ady201.features.service --config config/project.yaml
python -m ady201.features.roads --config config/project.yaml
python -m ady201.features.composite --config config/project.yaml

# 5. Phân cụm và bản đồ
python -m ady201.models.clustering --config config/project.yaml
python -m ady201.visualization.maps --config config/project.yaml

# 6. Test và quality checks
pytest
psql -f sql/005_quality_checks.sql
```

Mỗi lần chạy chính thức tạo một `run_id` và lưu:

- Git commit hash.
- Snapshot date.
- Config hash hoặc bản sao config.
- Số hàng đầu vào/đầu ra.
- Runtime.
- Cảnh báo và lỗi.

---

## 13. Tiêu chí hoàn thành từng nhóm kết quả

### 13.1. Dữ liệu POI

- [ ] Có `osm_type` và `osm_id`.
- [ ] Không trùng composite key.
- [ ] Geometry hợp lệ.
- [ ] Có category mapping được tài liệu hóa.
- [ ] Có báo cáo missingness.
- [ ] Có snapshot/source metadata.
- [ ] Không invent tên hoặc địa chỉ thiếu.

### 13.2. Road graph

- [ ] Có walking và driving graph tách biệt.
- [ ] Edge có chiều dài dương.
- [ ] Walking edge có travel time hợp lệ.
- [ ] Có connected-component report.
- [ ] Có graph metadata và snapshot.
- [ ] Có ít nhất năm route A–B được kiểm tra trực quan.

### 13.3. Accessibility

- [ ] POI và cell có snap status.
- [ ] Có phân phối snap distance.
- [ ] Có xử lý unreachable.
- [ ] Có kiểm tra multi-source với point-to-point.
- [ ] Có kết quả cho ít nhất năm nhóm dịch vụ thiết yếu.
- [ ] Có các ngưỡng 5/10/15 phút.

### 13.4. Road metrics

- [ ] Edge được clip/phân bổ đúng theo cell.
- [ ] Directed edges không làm double-count chiều dài.
- [ ] Intersection definition rõ ràng.
- [ ] Main-road definition rõ ràng.
- [ ] Các feature đều có đơn vị.

### 13.5. Clustering

- [ ] Feature đã scale.
- [ ] Có missing-data rule.
- [ ] Có silhouette và cluster-size report.
- [ ] Có cluster profile.
- [ ] Cluster được kiểm tra trên bản đồ.
- [ ] Không đặt tên cluster trước khi xem đặc trưng.

### 13.6. Bản đồ và báo cáo

- [ ] Có nguồn dữ liệu và snapshot date.
- [ ] Có đơn vị và legend.
- [ ] Có mô tả giả định walking speed.
- [ ] Có phần limitations.
- [ ] Kết luận trả lời đúng câu hỏi nghiên cứu.
- [ ] Không suy diễn quan hệ nhân quả từ phân tích mô tả.

---

## 14. Rủi ro và cách xử lý

| Rủi ro | Hậu quả | Cách xử lý |
|---|---|---|
| File PBF quá lớn | Tốn RAM/thời gian | Cắt Hà Nội trước; lưu graph/Parquet trung gian |
| Thiếu package native trên Windows | Không cài được Pyrosm/Osmium | Pin version; thử môi trường trong tuần 1; dùng WSL/conda nếu cần |
| POI thiếu tên | Không thể hiển thị tên | Giữ POI, gắn quality flag, phân tích theo category |
| Supermarket/bus stop không nằm trong `amenity` | Đánh giá thiếu dịch vụ sai | Bổ sung `shop`, `highway`, `public_transport` |
| Bounding box chứa vùng ngoài Hà Nội | Sai số thống kê | Lọc bằng polygon hành chính |
| Snap distance quá lớn | Accessibility sai | Lưu distance, đặt ngưỡng QA, kiểm tra bản đồ |
| Graph bị phân mảnh | Nhiều cell unreachable | Báo cáo component, kiểm tra quyền access, chọn component có lý do |
| Đếm directed edge gấp đôi | Road density sai | Chuyển về unique physical edge hoặc graph không hướng khi thống kê |
| Hex biên có diện tích nhỏ | Density bị phóng đại | Dùng diện tích sau clip; cân nhắc lọc ô quá nhỏ và ghi rule |
| Clustering bị chi phối bởi scale/outlier | Cluster không có ý nghĩa | Scale, inspect distribution, RobustScaler/log transform |
| Chỉ số tổng hợp phụ thuộc trọng số | Kết luận thiếu ổn định | Công khai trọng số và sensitivity check |
| OSM không đầy đủ đồng đều | Ngoại thành có vẻ thiếu dịch vụ | Ghi limitation; không đồng nhất “không có trong OSM” với “không tồn tại” |
| Lệch snapshot giữa POI và road | Khó tái lập | Ghi snapshot; ưu tiên cùng thời điểm; tạo `run_id` |
| Merge code làm hỏng pipeline người khác | Chậm tiến độ | Interface contract, PR nhỏ, review chéo, test mẫu |

---

## 15. Sản phẩm cuối cùng

### Dữ liệu và code

- Pipeline Python có thể chạy lại.
- SQL migration/schema có thứ tự.
- POI chuẩn hóa và enriched.
- Walking/driving graph.
- Hexagon và feature matrix.
- Kết quả clustering và composite index.
- Automated tests và data quality checks.

### Phân tích

- So sánh phát triển dịch vụ giữa các vùng.
- Danh sách và bản đồ vùng thiếu dịch vụ thiết yếu.
- Accessibility trong 5/10/15 phút đi bộ.
- Chỉ số hạ tầng và kết nối đường.
- Vùng dịch vụ cao nhưng đường kết nối thấp.
- Cluster các kiểu khu vực đô thị.
- Chỉ số tổng hợp và sensitivity analysis.

### Trình bày

- Báo cáo cuối.
- Slide thuyết trình.
- Bộ PNG cho báo cáo.
- Bản đồ HTML tương tác nếu có.
- README hướng dẫn tái tạo kết quả.
- Data dictionary và limitations.

---

## 16. Tài liệu kỹ thuật tham khảo

- Geofabrik Vietnam downloads: <https://download.geofabrik.de/asia/vietnam.html>
- Osmium Tool manual, tạo geographic extract: <https://osmcode.org/osmium-tool/manual.html#extracting-geographical-regions>
- Pyrosm quickstart: <https://pyrosm.readthedocs.io/en/stable/quickstart.html>
- Pyrosm graph workflow: <https://pyrosm.readthedocs.io/en/stable/graphs.html>
- OSMnx user reference: <https://osmnx.readthedocs.io/en/stable/user-reference.html>
- NetworkX shortest paths: <https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html>
- PostGIS `ST_DWithin`: <https://postgis.net/docs/ST_DWithin.html>
- PostgreSQL/PostGIS spatial indexes: <https://postgis.net/documentation/faq/spatial-indexes/>

---

## 17. Việc cần làm ngay trong buổi tiếp theo

1. Cả nhóm đọc tài liệu và chốt các định nghĩa ở Bước 0.
2. Thành tạo schema đề xuất và refactor một pipeline POI mẫu.
3. Hiếu xác nhận Osmium/Pyrosm chạy được trên máy và tạo graph cho một vùng nhỏ.
4. Quang tạo EDA report từ dữ liệu hiện tại.
5. Cả nhóm thống nhất schema interface trước khi tiếp tục làm song song.
6. Chỉ sau khi pilot nhỏ chạy thành công mới xử lý toàn bộ Hà Nội.
