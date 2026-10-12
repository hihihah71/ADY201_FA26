# Kế hoạch chuyển đổi project thành pipeline tự động cho toàn Việt Nam

## 1. Mục tiêu

Chuyển project hiện tại từ các script riêng cho Hà Nội thành một pipeline có thể:

1. Chạy toàn bộ phân tích cho một tỉnh/thành bằng một lệnh.
2. Thêm tỉnh/thành mới bằng boundary và configuration, không sửa source code.
3. Chạy lần lượt tất cả đơn vị hành chính cấp tỉnh của Việt Nam.
4. Tiếp tục từ bước bị lỗi thay vì chạy lại từ đầu.
5. Lưu nhiều phiên bản dữ liệu và kết quả mà không ghi đè.
6. So sánh các khu vực trong một tỉnh hoặc so sánh trên phạm vi toàn quốc.

Giao diện mục tiêu:

```powershell
# Chạy một tỉnh/thành
ady201 run-region --region hanoi --snapshot 2026-10-11

# Tiếp tục lần chạy bị dừng
ady201 run-region --region hanoi --snapshot 2026-10-11 --resume

# Chạy toàn quốc
ady201 run-all --country vietnam --snapshot 2026-10-11 --resume

# Tổng hợp và clustering toàn quốc
ady201 aggregate-national --snapshot 2026-10-11 --model national-v1
```

---

## 2. Tiêu chí thành công quan trọng nhất

Pipeline được coi là tổng quát khi:

> Thêm một tỉnh/thành mới chỉ cần thêm boundary/registry; không được copy code, tạo notebook riêng hoặc sửa logic xử lý.

Các mốc kiểm chứng:

1. Hà Nội chạy end-to-end bằng một lệnh.
2. Đà Nẵng chạy bằng cùng lệnh và cùng source code.
3. Chạy lại Hà Nội với `--resume` không thực hiện lại các bước hợp lệ.
4. Một tỉnh lỗi không làm dừng toàn bộ batch toàn quốc.
5. Kết quả toàn quốc không đếm trùng POI hoặc hexagon ở vùng giáp ranh.

---

## 3. Hiện trạng cần thay đổi

Project hiện tại có các đặc điểm chưa phù hợp cho tự động hóa:

- Script riêng cho từng nhóm POI.
- Bounding box Hà Nội nằm trực tiếp trong source code.
- Đường dẫn `Data`, `RawData`, ổ `D:` hoặc `G:` chưa thống nhất.
- Tên input/output được hard-code.
- CSV chỉ giữ năm cột và làm mất `osm_type` cùng nhiều OSM tags.
- SQL chưa có `region_id`, `snapshot_id` hoặc `run_id`.
- Chưa có cơ chế cache, retry, resume và logging theo step.
- Chưa có package Python hoặc command-line interface thống nhất.
- Logic xử lý, khám phá dữ liệu và xuất kết quả chưa tách riêng.

Không mở rộng các script hiện tại bằng cách thêm nhiều `if city == ...`. Thay vào đó, chuyển logic chung vào package Python và truyền configuration vào từng bước.

---

## 4. Kiến trúc đích

```text
Geofabrik Vietnam PBF snapshot
            │
            ├── Province boundary registry
            │
            ├── POI toàn quốc, chuẩn hóa một lần
            │
            └── Pipeline theo từng tỉnh/thành
                    │
                    ├── Boundary chính thức
                    ├── Boundary có buffer
                    ├── Region PBF extract
                    ├── Walking graph
                    ├── Driving graph
                    ├── Hexagon
                    ├── POI/cell snapping
                    ├── Accessibility
                    ├── Service features
                    ├── Road features
                    ├── Composite index
                    ├── Within-region clustering
                    └── Maps/tables
                            │
                            └── National aggregation
                                  ├── National scaler
                                  ├── National clustering model
                                  ├── Cross-region comparison
                                  └── National maps/tables
```

### 4.1. Vai trò của công nghệ

- **Python**: orchestration, parsing PBF, chuẩn hóa POI, graph, Dijkstra, feature engineering, clustering và bản đồ.
- **PostgreSQL/PostGIS**: region registry, spatial index, canonical data, spatial join, run state và kết quả.
- **Osmium**: kiểm tra và cắt Vietnam PBF thành region PBF.
- **Pyrosm**: đọc local `.osm.pbf`, trích network/POI và tạo dữ liệu graph.
- **NetworkX/OSMnx**: shortest path, multi-source Dijkstra, snapping và graph utilities.
- **GeoParquet/GraphML**: artifact trung gian có thể đọc lại nhanh.

### 4.2. Hai lớp phạm vi không gian

Mỗi region có:

```text
analysis_boundary = polygon hành chính chính thức
extraction_boundary = analysis_boundary + buffer
```

- Chỉ tạo hexagon và báo cáo kết quả bên trong `analysis_boundary`.
- Tạo graph và chọn candidate POI trong `extraction_boundary`.
- Buffer ban đầu có thể là 2–3 km nhưng phải nằm trong config.
- POI ngoài tỉnh nhưng nằm trong buffer được phép dùng cho accessibility nếu quy tắc nghiên cứu cho phép.

Buffer giúp tránh cắt đứt đường đi và dịch vụ gần ranh giới tỉnh.

---

## 5. Nguyên tắc thiết kế bắt buộc

### 5.1. Configuration-driven

Không để trong source code:

- Tên tỉnh/thành.
- Bounding box hoặc tọa độ cố định.
- Đường dẫn máy cá nhân.
- Walking speed.
- Hex resolution.
- Danh sách category.
- Accessibility thresholds.
- Danh sách loại đường chính.
- Snapshot date.

### 5.2. Idempotent

Chạy lại cùng input/config/code không tạo row hoặc file trùng.

### 5.3. Versioned

Mọi kết quả phải truy ngược được:

- Snapshot dữ liệu.
- Boundary version.
- Config version/hash.
- Git commit.
- Model version.
- Thời gian chạy.

### 5.4. Resumable

Step đã hoàn thành và còn hợp lệ phải được skip khi `--resume`.

### 5.5. Failure isolation

Một region thất bại không làm dừng toàn bộ national batch.

### 5.6. Comparable

Nếu so sánh toàn quốc thì mọi region phải dùng:

- Cùng H3 resolution.
- Cùng category mapping.
- Cùng walking speed.
- Cùng thresholds.
- Cùng feature definitions.
- Cùng scaler và clustering model.

---

## 6. Cấu trúc repository đề xuất

```text
ADY201_FA26/
├── README.md
├── KE_HOACH_DU_AN.md
├── KE_HOACH_TU_DONG_HOA_TOAN_QUOC.md
├── pyproject.toml
├── .env.example
├── config/
│   ├── project.yaml
│   ├── regions.yaml
│   ├── categories.yaml
│   └── clustering.yaml
├── data/
│   ├── README.md
│   ├── manifests/
│   ├── boundary/
│   │   └── {boundary_snapshot_id}/
│   ├── raw/                         # gitignored
│   │   └── osm/
│   └── artifacts/                   # gitignored, trừ sample nhỏ
│       └── {snapshot_id}/
│           └── {region_id}/
├── src/
│   └── ady201/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── context.py
│       ├── pipeline.py
│       ├── logging.py
│       ├── registry/
│       │   ├── regions.py
│       │   └── snapshots.py
│       ├── storage/
│       │   ├── database.py
│       │   ├── artifacts.py
│       │   └── state.py
│       ├── poi/
│       │   ├── extract.py
│       │   ├── normalize.py
│       │   ├── enrich.py
│       │   └── validate.py
│       ├── network/
│       │   ├── extract_pbf.py
│       │   ├── build_graph.py
│       │   ├── validate.py
│       │   ├── snap.py
│       │   └── accessibility.py
│       ├── grid/
│       │   └── hexagons.py
│       ├── features/
│       │   ├── services.py
│       │   ├── roads.py
│       │   └── composite.py
│       ├── models/
│       │   ├── within_region.py
│       │   └── national.py
│       └── visualization/
│           ├── maps.py
│           └── reports.py
├── sql/
│   ├── 001_extensions_schemas.sql
│   ├── 002_registry_tables.sql
│   ├── 003_core_tables.sql
│   ├── 004_network_tables.sql
│   ├── 005_analytics_tables.sql
│   ├── 006_pipeline_tables.sql
│   └── 007_quality_checks.sql
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_result_review.ipynb
├── tests/
│   ├── fixtures/
│   ├── test_config.py
│   ├── test_poi.py
│   ├── test_graph.py
│   ├── test_accessibility.py
│   ├── test_features.py
│   └── test_pipeline_resume.py
└── outputs/
    └── reports/
```

Notebook chỉ dùng để khám phá và trình bày. Logic cần tự động chạy phải nằm trong `src/ady201`.

---

## 7. Configuration

### 7.1. Project configuration

```yaml
# config/project.yaml

country:
  id: vietnam
  code: VN
  geofabrik_url: https://download.geofabrik.de/asia/vietnam-latest.osm.pbf

analysis:
  hex_resolution: 8
  extract_buffer_m: 3000
  walking_speed_kph: 4.8
  accessibility_thresholds_min: [5, 10, 15]
  projected_crs_strategy: local_utm

networks:
  accessibility: walking
  infrastructure: driving

roads:
  main_highway_types:
    - motorway
    - trunk
    - primary
    - secondary

runtime:
  max_workers: 1
  retry_count: 2
  resume: true
```

### 7.2. Category configuration

```yaml
# config/categories.yaml

categories:
  healthcare:
    amenity: [hospital, clinic, doctors]

  pharmacy:
    amenity: [pharmacy]

  education:
    amenity: [school, kindergarten, college, university]

  grocery:
    amenity: [marketplace]
    shop: [supermarket, convenience]

  transit:
    amenity: [bus_station]
    highway: [bus_stop]
    public_transport: [platform, station]

  finance:
    amenity: [bank, atm, post_office]
```

### 7.3. Region configuration

```yaml
# config/regions.yaml

regions:
  hanoi:
    name_vi: Hà Nội
    osm_relation_id: 1903516
    boundary_path: data/boundary/boundary-v1/hanoi.geojson
    extract_buffer_m: 3000
    enabled: true

  da-nang:
    name_vi: Đà Nẵng
    osm_relation_id: null
    boundary_path: data/boundary/boundary-v1/da_nang.geojson
    extract_buffer_m: 3000
    enabled: true
```

Registry trong database là nguồn chính thức sau khi quá trình bootstrap hoàn thành. YAML có thể dùng ở giai đoạn đầu và cho test.

---

## 8. RunContext và interface chung

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunContext:
    run_id: str
    region_id: str
    snapshot_id: str
    boundary_snapshot_id: str
    country_pbf_path: Path
    boundary_path: Path
    artifact_dir: Path
    config_hash: str
```

Quy tắc:

- Mọi pipeline step nhận `RunContext`.
- Step không tự đoán đường dẫn.
- Step không đọc global mutable variable.
- Output path được tạo qua một artifact manager chung.
- Step trả về metadata và đường dẫn output, không chỉ `print` trạng thái.

Ví dụ:

```python
def build_walking_graph(context: RunContext) -> StepResult:
    ...
```

Không viết:

```python
def build_hanoi_graph():
    ...
```

---

## 9. Mô hình dữ liệu

### 9.1. Registry vùng

```sql
CREATE TABLE core.region (
    region_id text PRIMARY KEY,
    region_code text,
    slug text UNIQUE NOT NULL,
    name_vi text NOT NULL,
    admin_level integer NOT NULL,
    osm_relation_id bigint,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    boundary_snapshot_id text NOT NULL,
    valid_from date,
    valid_to date,
    is_active boolean NOT NULL DEFAULT true
);
```

Không hard-code số lượng tỉnh/thành. Registry được sinh từ boundary cấp tỉnh hiện hành và phải được kiểm tra trước khi chạy toàn quốc.

### 9.2. Snapshot

```sql
CREATE TABLE pipeline.snapshot (
    snapshot_id text PRIMARY KEY,
    source_url text NOT NULL,
    source_timestamp timestamptz,
    downloaded_at timestamptz NOT NULL,
    file_path text NOT NULL,
    checksum text NOT NULL,
    file_size bigint NOT NULL
);
```

### 9.3. Run

```sql
CREATE TABLE pipeline.run (
    run_id uuid PRIMARY KEY,
    region_id text REFERENCES core.region(region_id),
    snapshot_id text REFERENCES pipeline.snapshot(snapshot_id),
    analysis_mode text NOT NULL,
    config_hash text NOT NULL,
    git_commit text,
    status text NOT NULL,
    started_at timestamptz,
    finished_at timestamptz,
    error_message text
);
```

### 9.4. Step state

```sql
CREATE TABLE pipeline.step_run (
    run_id uuid REFERENCES pipeline.run(run_id),
    step_name text NOT NULL,
    status text NOT NULL,
    input_hash text NOT NULL,
    output_path text,
    row_count bigint,
    started_at timestamptz,
    finished_at timestamptz,
    error_message text,
    PRIMARY KEY (run_id, step_name)
);
```

Trạng thái hợp lệ:

```text
pending
running
completed
failed
skipped
```

### 9.5. POI toàn quốc

```sql
CREATE TABLE core.poi (
    poi_id bigserial PRIMARY KEY,
    snapshot_id text NOT NULL,
    osm_type text NOT NULL,
    osm_id bigint NOT NULL,
    category text NOT NULL,
    subcategory text,
    name text,
    address text,
    operator text,
    brand text,
    opening_hours text,
    phone text,
    website text,
    tags jsonb NOT NULL,
    geom geometry(Point, 4326) NOT NULL,
    quality_flags jsonb,
    UNIQUE (snapshot_id, osm_type, osm_id)
);
```

### 9.6. Region–POI membership

```sql
CREATE TABLE core.region_poi (
    region_id text NOT NULL,
    snapshot_id text NOT NULL,
    poi_id bigint NOT NULL,
    membership_type text NOT NULL,
    PRIMARY KEY (region_id, snapshot_id, poi_id, membership_type)
);
```

`membership_type`:

- `inside`: nằm trong analysis boundary.
- `buffer`: nằm ngoài analysis boundary nhưng trong extraction boundary.

Cấu trúc này tránh copy POI và tránh đếm trùng khi tổng hợp toàn quốc.

### 9.7. Graph

Graph có thể được lưu chính trong GraphML/GeoParquet; PostGIS giữ node/edge cần truy vấn hoặc hiển thị.

Khóa graph phải có `graph_id` hoặc tổ hợp:

```text
region_id
snapshot_id
network_type
```

Node ID OSM có thể xuất hiện trong graph của nhiều region do buffer. Không dùng riêng `node_id` làm khóa toàn database.

### 9.8. Hexagon và feature

```text
analytics.hex_cell:
region_id, grid_version, cell_id, area_km2, geom, representative_point

analytics.cell_feature:
run_id, region_id, cell_id, feature_name/version hoặc các feature columns

analytics.cluster_result:
run_id, model_version, region_id, cell_id, cluster_id
```

---

## 10. Toàn bộ pipeline

### Step 0 — Validate environment

Kiểm tra:

- Python và dependency versions.
- PostgreSQL/PostGIS connection.
- `osmium` executable.
- Thư mục dữ liệu có quyền đọc/ghi.
- Dung lượng ổ đĩa.
- Config parse được.

Nếu environment không hợp lệ, dừng trước khi tạo artifact.

### Step 1 — Download/register Vietnam snapshot

1. Tải `vietnam-latest.osm.pbf` từ Geofabrik.
2. Đọc timestamp bằng `osmium fileinfo`.
3. Tính checksum.
4. Đổi tên file theo snapshot:

```text
data/raw/osm/vietnam-{snapshot_id}.osm.pbf
```

5. Ghi metadata vào `pipeline.snapshot`.
6. Không ghi đè snapshot cũ.

Trong MVP, cập nhật bằng full snapshot theo đợt. Chưa cần áp dụng incremental `.osc.gz`.

### Step 2 — Bootstrap/validate region registry

1. Thu thập boundary cấp tỉnh hiện hành.
2. Chuẩn hóa tên, slug và mã vùng.
3. Kiểm tra geometry hợp lệ.
4. Đảm bảo không có overlap bất thường.
5. Kiểm tra tổng union nằm trong boundary Việt Nam.
6. Ghi `boundary_snapshot_id`.
7. Review thủ công trước khi bật `is_active=true`.

Không dựa hoàn toàn vào tìm kiếm tên tự động vì có thể trả nhầm cấp hành chính hoặc địa danh trùng tên.

### Step 3 — Chuẩn hóa POI toàn quốc

Đọc Vietnam PBF một lần cho mỗi snapshot để lấy POI:

- `amenity`.
- `shop`.
- `highway=bus_stop`.
- `public_transport`.
- Các tags khác theo `categories.yaml`.

Chuẩn hóa:

- `osm_type` và `osm_id`.
- Category/subcategory.
- Geometry đại diện.
- Name/address/contact.
- Tags JSONB.
- Quality flags.

Với POI dạng polygon, dùng representative point nằm bên trong geometry thay vì centroid có thể nằm ngoài.

Nạp vào `core.poi`, sau đó spatial join để tạo `core.region_poi`.

### Step 4 — Prepare region boundaries

Với từng region:

1. Lấy `analysis_boundary`.
2. Project sang CRS theo mét phù hợp.
3. Buffer theo `extract_buffer_m`.
4. Chuyển boundary buffer về EPSG:4326.
5. Lưu cả hai geometry.

Output:

```text
boundary.geojson
boundary_buffered.geojson
```

### Step 5 — Extract region PBF

Lệnh mục tiêu:

```powershell
osmium extract `
  -p data/artifacts/{snapshot_id}/{region_id}/boundary_buffered.geojson `
  --strategy=complete_ways `
  data/raw/osm/vietnam-{snapshot_id}.osm.pbf `
  -o data/artifacts/{snapshot_id}/{region_id}/extract/region.osm.pbf
```

Sau extract:

- Chạy `osmium fileinfo`.
- Kiểm tra file đọc được.
- Ghi checksum và size.
- Không overwrite artifact hợp lệ của cùng run.

Khi chạy toàn quốc, bắt đầu bằng xử lý tuần tự. Chỉ tăng concurrency sau khi đo RAM và runtime.

### Step 6 — Build walking graph

1. Đọc region PBF bằng Pyrosm.
2. Trích network type `walking`.
3. Chuyển thành directed `MultiDiGraph`.
4. Simplify graph theo một cấu hình thống nhất.
5. Tính `length_m`.
6. Tính:

```text
walking_speed_mps = walking_speed_kph / 3.6
travel_time_s = length_m / walking_speed_mps
```

7. Validate weights không âm/null.
8. Báo cáo connected components.
9. Lưu GraphML và node/edge GeoParquet.

Walking graph được dùng cho accessibility.

### Step 7 — Build driving graph

1. Trích network type `driving`.
2. Giữ one-way direction.
3. Tính `length_m`.
4. Giữ `highway`, `lanes`, `maxspeed`, `bridge`, `tunnel` nếu có.
5. Simplify nhất quán.
6. Lưu GraphML và GeoParquet.

Driving graph được dùng cho road-infrastructure features. MVP không bắt buộc routing ô tô hoặc xử lý đầy đủ turn restrictions.

### Step 8 — Generate hexagons

1. Sinh H3/hexagon với resolution chung.
2. Chỉ giữ cell giao với analysis boundary.
3. Clip cell biên nếu cần diện tích chính xác.
4. Tính `area_km2` trong CRS theo mét.
5. Tạo representative point.
6. Gắn `region_id` và `grid_version`.

Không sinh hexagon trong vùng buffer để báo cáo. Buffer chỉ phục vụ network và destination candidates.

### Step 9 — Select region POIs

Từ POI toàn quốc:

- `inside` POI: dùng cho density và thống kê region.
- `inside + buffer` POI: có thể làm destination cho accessibility.

Quy tắc phải nằm trong config, ví dụ:

```yaml
accessibility:
  allow_buffer_destinations: true
```

Không dùng buffer POI khi tính mật độ dịch vụ bên trong tỉnh.

### Step 10 — Snap POI và cells

1. Project point và graph về cùng CRS.
2. Tìm nearest node theo batch.
3. Lưu node ID và `snap_distance_m`.
4. Đặt trạng thái:

```text
ok
too_far
outside_network
no_nearby_node
```

5. Kiểm tra các outlier trên bản đồ.

MVP dùng nearest node. Phiên bản nâng cao có thể snap vào edge và thêm connector.

### Step 11 — Accessibility

Kiểm tra A–B bằng shortest path có sẵn. Đối với toàn bộ cell, dùng multi-source Dijkstra theo từng nhóm dịch vụ.

Với mỗi category:

1. Lấy các destination nodes.
2. Chạy multi-source Dijkstra một lần.
3. Nếu graph có hướng, kiểm tra việc chạy trên reversed graph để đo từ origin đến destination.
4. Gán thời gian về representative node của từng hexagon.
5. Đánh dấu unreachable thay vì thay bằng 0.

Feature tối thiểu:

```text
nearest_hospital_min
nearest_pharmacy_min
nearest_school_min
nearest_supermarket_min
nearest_transit_min
hospital_within_5m/10m/15m
school_within_5m/10m/15m
supermarket_within_5m/10m/15m
transit_within_5m/10m/15m
```

Không chạy Dijkstra riêng cho mọi cặp cell–POI.

### Step 12 — Service features

Chỉ dùng POI có membership `inside`.

Feature:

```text
poi_count_total
poi_density_km2
essential_poi_count
essential_poi_density_km2
service_category_count
service_diversity
healthcare_density
education_density
grocery_density
transit_stop_density
finance_density
food_density
```

Các cell biên phải chia cho diện tích thực tế sau clip.

### Step 13 — Road features

Clip hoặc phân bổ physical road edge theo hexagon.

Feature:

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
local_road_share
```

Quy tắc:

- Không double-count hai directed edge của cùng physical road.
- Tính degree trên graph simple/undirected phù hợp.
- Intersection là node degree từ 3 trở lên sau simplify.
- `main_road_share = main_road_length_m / road_length_m`.
- Ghi rõ graph nguồn của mỗi feature.

### Step 14 — Build feature matrix

Ghép bằng:

```text
run_id + region_id + cell_id
```

Quy trình:

1. Phân biệt `0`, `null` và `unreachable`.
2. Kiểm tra phân phối.
3. Xử lý outlier có lý do.
4. Log-transform feature lệch mạnh nếu cần.
5. Loại feature trùng thông tin.
6. Lưu feature raw và scaled riêng.

### Step 15 — Composite indices

Service completeness:

```text
service_completeness_15m =
  số nhóm thiết yếu reachable trong 15 phút / tổng số nhóm thiết yếu
```

Accessibility category score:

```text
max(0, 1 - min(travel_time_min, 15) / 15)
```

Accessibility score là trung bình category score.

Connectivity score dùng road density, intersection density, average degree và inverse dead-end ratio sau chuẩn hóa.

Mọi trọng số phải nằm trong config và có sensitivity check.

### Step 16 — Within-region clustering

Dùng để phân nhóm các cell bên trong một region.

1. Scale feature trong region.
2. Chạy K-Means với một dải `k`.
3. Xem silhouette, cluster size và khả năng giải thích.
4. Lập cluster profile.
5. Hiển thị lên bản đồ.

Cluster ID chỉ có nghĩa trong region/run đó.

### Step 17 — Render regional outputs

Xuất:

- POI density map.
- Service completeness map.
- Accessibility maps.
- Road/intersection density map.
- Main-road-share map.
- High-service/low-connectivity map.
- Cluster map.
- Composite-index map.
- Summary tables.
- Quality report.

Mọi output phải ghi:

- Region.
- Snapshot.
- Run ID.
- Walking speed.
- Hex resolution.
- Data source.

### Step 18 — National aggregation

Chỉ chạy sau khi regional runs đạt quality gate.

1. Ghép các feature raw theo cell.
2. Loại duplicate bằng key chuẩn.
3. Kiểm tra coverage của tất cả active regions.
4. Fit một scaler chung.
5. Fit national clustering model hoặc áp dụng model đã version hóa.
6. Tính national percentiles.
7. Xuất bảng và bản đồ toàn quốc.

Không dùng các feature đã min-max riêng trong từng tỉnh để so sánh toàn quốc.

---

## 11. Orchestrator và cache

### 11.1. Pipeline steps

```python
REGION_STEPS = [
    "validate_environment",
    "prepare_boundaries",
    "extract_region_pbf",
    "build_walking_graph",
    "build_driving_graph",
    "generate_hexagons",
    "select_region_pois",
    "snap_pois",
    "snap_cells",
    "calculate_accessibility",
    "calculate_service_features",
    "calculate_road_features",
    "build_feature_matrix",
    "calculate_composite_indices",
    "cluster_within_region",
    "render_regional_outputs",
]
```

### 11.2. Cache key

Cache key của một step phải phụ thuộc vào:

```text
step_name
snapshot_id
boundary_snapshot_id
region_id
config_hash
code_version
input_checksums
```

Không skip chỉ vì output file tồn tại.

### 11.3. Resume

Khi `--resume`:

1. Đọc trạng thái lần chạy trước.
2. Kiểm tra cache key và output integrity.
3. Skip step còn hợp lệ.
4. Chạy lại step failed hoặc stale.
5. Chạy lại các downstream steps phụ thuộc vào output đã thay đổi.

### 11.4. Retry

Retry chỉ dùng cho lỗi tạm thời như download hoặc database connection. Không retry vô hạn với lỗi validation/code.

### 11.5. Artifact layout

```text
data/artifacts/{snapshot_id}/{region_id}/
├── manifest.json
├── boundary/
├── extract/
├── poi/
├── network/
├── grid/
├── snap/
├── accessibility/
├── features/
├── models/
├── maps/
└── logs/
```

---

## 12. Command-line interface

### Registry

```powershell
ady201 regions list
ady201 regions validate --boundary-snapshot boundary-v1
ady201 regions show --region hanoi
```

### Snapshot

```powershell
ady201 snapshots fetch --country vietnam
ady201 snapshots list
ady201 snapshots validate --snapshot 2026-10-11
```

### Một region

```powershell
ady201 run-region --region hanoi --snapshot 2026-10-11
ady201 run-region --region hanoi --snapshot 2026-10-11 --resume
ady201 run-region --region hanoi --from-step build-walking-graph
ady201 run-region --region hanoi --to-step calculate-accessibility
```

### Toàn quốc

```powershell
ady201 run-all `
  --country vietnam `
  --snapshot 2026-10-11 `
  --max-workers 1 `
  --resume
```

### Trạng thái

```powershell
ady201 runs list --snapshot 2026-10-11
ady201 runs status --run-id <uuid>
ady201 runs failures --snapshot 2026-10-11
```

### Tổng hợp

```powershell
ady201 aggregate-national `
  --snapshot 2026-10-11 `
  --model national-v1
```

---

## 13. Run-all pseudocode

```python
def run_all_regions(snapshot_id: str, resume: bool) -> BatchResult:
    results = []

    for region in region_registry.list_active():
        try:
            result = run_region(
                region_id=region.region_id,
                snapshot_id=snapshot_id,
                resume=resume,
            )
        except Exception as exc:
            state_store.record_region_failure(
                region_id=region.region_id,
                snapshot_id=snapshot_id,
                error=exc,
            )
            results.append(RegionResult.failed(region.region_id, exc))
            continue

        results.append(result)

    return BatchResult.from_region_results(results)
```

Sau khi tuần tự ổn định mới dùng bounded concurrency:

```text
max_workers = 2 hoặc 3 sau khi benchmark
```

Không dùng concurrency cao mặc định vì build graph có thể tốn RAM.

---

## 14. Quality gates

### Gate A — Environment

- [ ] Package cài được trên máy của cả ba thành viên.
- [ ] Osmium chạy được.
- [ ] PostGIS connection hoạt động.
- [ ] Test dataset nhỏ chạy được.

### Gate B — POI toàn quốc

- [ ] Có `osm_type` và `osm_id`.
- [ ] Không trùng `(snapshot_id, osm_type, osm_id)`.
- [ ] Geometry hợp lệ.
- [ ] Có category mapping.
- [ ] Có `shop` và public-transport POI, không chỉ `amenity`.
- [ ] Có quality report.

### Gate C — Một region

- [ ] Boundary hợp lệ.
- [ ] Extract PBF đọc được.
- [ ] Walking/driving graph hợp lệ.
- [ ] Hexagon chỉ nằm trong analysis boundary.
- [ ] Snap report có tỷ lệ thành công và outlier.
- [ ] Accessibility có xử lý unreachable.
- [ ] Service và road features có đơn vị.
- [ ] Maps có metadata.

### Gate D — Hai-region test

- [ ] Hà Nội và Đà Nẵng chạy cùng source.
- [ ] Chỉ khác registry/config.
- [ ] Không có notebook riêng cho mỗi region.
- [ ] Không có điều kiện `if hanoi` hoặc `if da_nang` trong pipeline logic.

### Gate E — Resume

- [ ] Step hoàn thành được skip.
- [ ] Step stale được chạy lại.
- [ ] Downstream dependency được invalidated đúng.
- [ ] Lỗi giữa chừng có thể tiếp tục.

### Gate F — National batch

- [ ] Một region lỗi không dừng batch.
- [ ] Có summary thành công/thất bại.
- [ ] Không đếm trùng buffer POI.
- [ ] National features dùng chung định nghĩa.
- [ ] Có danh sách region thiếu output.

---

## 15. Kiểm thử

### Unit tests

- Parse config.
- Category mapping.
- Composite OSM key.
- Geometry validation.
- Artifact path generation.
- Cache-key generation.
- Accessibility score.
- Road metrics không double-count.

### Integration tests

- PBF fixture nhỏ → graph.
- Raw POI → normalized POI → database.
- POI/cell → snap.
- Graph + destination nodes → accessibility.
- Regional features → maps.

### Pipeline tests

- Chạy end-to-end trên vùng mẫu nhỏ.
- Chạy lại với resume.
- Thay config và kiểm tra invalidation.
- Giả lập failure tại một step.
- Chạy hai region liên tiếp.

### Data tests

- Row-count expectations.
- Unique keys.
- Non-null required fields.
- Geometry validity.
- Non-negative edge weights.
- Feature ranges.
- Region coverage.
- Outlier reports.

---

## 16. Clustering nội tỉnh và toàn quốc

### 16.1. Nội tỉnh

```text
analysis_mode = within_region
```

- Fit scaler riêng.
- Fit K-Means riêng.
- Kết quả cho biết tương quan giữa các vùng trong cùng tỉnh.
- Cluster ID không so sánh trực tiếp giữa các tỉnh.

### 16.2. Toàn quốc

```text
analysis_mode = national
```

- Ghép feature raw của mọi region.
- Fit một scaler chung.
- Fit một model chung.
- Lưu `model_version`.
- Có thể so sánh cluster và percentile giữa các tỉnh.

### 16.3. Model registry tối thiểu

```text
model_version
analysis_mode
snapshot_id
feature_list
scaler_path
model_path
training_row_count
metrics
created_at
```

---

## 17. Phân công nhóm

### 17.1. Thành — Database, POI và pipeline state

**Mức độ:** trung bình–khó.

Nhiệm vụ:

1. Tạo schemas và migration SQL.
2. Tạo `region`, `snapshot`, `run`, `step_run`.
3. Chuyển POI thành bảng canonical toàn quốc.
4. Tạo `region_poi` membership.
5. Refactor normalize/enrich POI theo config.
6. Tạo database quality checks.
7. Tạo service features theo region/cell.

Đầu ra:

- Database schema.
- POI toàn quốc.
- Region membership.
- Run-state API.
- Service-feature table.

### 17.2. Hiếu — PBF, graph và accessibility

**Mức độ:** trung bình–khó.

Nhiệm vụ:

1. Download/validate snapshot.
2. Cắt PBF theo buffered boundary.
3. Build walking/driving graph theo `RunContext`.
4. Graph validation và artifacts.
5. Snap POI/cells.
6. Multi-source Dijkstra.
7. Road features.
8. Benchmark RAM/runtime.

Đầu ra:

- PBF extractor.
- Graph builder.
- Snap tables.
- Accessibility features.
- Road features.

### 17.3. Quang — CLI, EDA, clustering và maps

**Mức độ:** dễ–trung bình.

Nhiệm vụ:

1. Hỗ trợ CLI và status report.
2. Tạo EDA/quality summaries.
3. Ghép feature matrix.
4. Within-region clustering.
5. National clustering sau khi có đủ data.
6. Template bản đồ dùng chung.
7. Batch summary/report.

Đầu ra:

- CLI commands.
- Feature matrix validation.
- Cluster results.
- Regional/national maps.
- Run summary.

### 17.4. Review chéo

| Module               | Owner          | Reviewer  | Smoke test |
| -------------------- | -------------- | --------- | ---------- |
| Registry/database    | Thành         | Hiếu     | Quang      |
| POI toàn quốc      | Thành         | Quang     | Hiếu      |
| PBF/graph            | Hiếu          | Thành    | Quang      |
| Accessibility        | Hiếu          | Thành    | Quang      |
| CLI/state            | Quang + Thành | Hiếu     | Cả nhóm  |
| Clustering/maps      | Quang          | Hiếu     | Thành     |
| National aggregation | Cả nhóm      | Cả nhóm | Cả nhóm  |

---

## 18. Roadmap triển khai

### Phase 1 — Foundation

1. Tạo `pyproject.toml` và package `src/ady201`.
2. Tạo config loader.
3. Tạo `RunContext`.
4. Tạo artifact manager.
5. Chuẩn hóa logging.
6. Tạo database migration đầu tiên.

**Exit condition:** chạy được một command mẫu và tạo run record.

### Phase 2 — Generic POI

1. Gộp ba flatten script.
2. Giữ `osm_type`, `osm_id`, tags và geometry.
3. Di chuyển category mapping vào YAML.
4. Tạo POI quality report.
5. Nạp POI canonical.

**Exit condition:** cùng một module xử lý mọi category, không có script riêng cho từng nhóm.

### Phase 3 — Generic regional graph

1. Region registry bản đầu.
2. Boundary và buffer.
3. PBF extract.
4. Walking/driving graph.
5. Graph validation.

**Exit condition:** `build_graph(context)` không chứa Hà Nội trong logic.

### Phase 4 — End-to-end Hà Nội

1. Hexagon.
2. Snap.
3. Accessibility.
4. Service/road features.
5. Composite indices.
6. Map/report.

**Exit condition:** một command tạo đầy đủ output Hà Nội.

### Phase 5 — Đà Nẵng validation

1. Thêm boundary/registry Đà Nẵng.
2. Chạy cùng command.
3. Sửa lỗi tổng quát, không thêm branch riêng cho Đà Nẵng.
4. So sánh schema/output giữa hai region.

**Exit condition:** không sửa source chỉ vì đổi region.

### Phase 6 — Resume và state

1. Step states.
2. Cache keys.
3. Resume.
4. Retry tạm thời.
5. Failure simulation tests.

**Exit condition:** lỗi ở clustering không làm dựng graph lại.

### Phase 7 — National batch

1. Hoàn thiện region registry.
2. Chạy tuần tự tất cả region.
3. Ghi summary.
4. Sửa các region edge cases.
5. Benchmark và tăng bounded concurrency nếu an toàn.

**Exit condition:** batch hoàn thành hoặc báo lỗi riêng từng region, không dừng toàn bộ.

### Phase 8 — National analytics

1. National feature matrix.
2. Shared scaler.
3. National clustering model.
4. National percentile/ranking.
5. National maps/report.

**Exit condition:** các chỉ số chéo tỉnh dùng cùng thang đo và model version.

### Phase 9 — Scheduled updates

1. Chọn lịch snapshot.
2. Kiểm tra source timestamp/checksum.
3. Tạo snapshot mới nếu dữ liệu thay đổi.
4. Chạy POI national step một lần.
5. Chạy region batch có resume.
6. Chạy national aggregation.
7. Publish status report.

Trong giai đoạn đầu nên dùng full snapshot theo lịch thay vì incremental update phức tạp.

---

## 19. Backlog theo thứ tự pull request

### PR 1 — Project package

- `pyproject.toml`.
- `src/ady201`.
- Config loader.
- Tests cho config.

### PR 2 — Registry và database metadata

- Region/snapshot/run/step tables.
- Migration runner.
- DB connection module.

### PR 3 — Generic POI pipeline

- Normalize/enrich/validate.
- Category YAML.
- Canonical POI schema.
- Quality report.

### PR 4 — Boundary và PBF extract

- Boundary loader.
- Buffer.
- Osmium wrapper.
- Artifact manifest.

### PR 5 — Graph pipeline

- Walking/driving graph.
- Graph validation.
- Graph artifacts.

### PR 6 — Grid, snap và accessibility

- Hexagon.
- POI/cell snapping.
- Multi-source Dijkstra.
- Accessibility tests.

### PR 7 — Feature pipeline

- Service features.
- Road features.
- Feature matrix.
- Composite indices.

### PR 8 — CLI và resume

- `run-region`.
- Step state.
- Cache key.
- Resume tests.

### PR 9 — Regional analytics

- Clustering.
- Maps.
- Summary reports.

### PR 10 — Run-all và national aggregation

- Batch runner.
- Failure isolation.
- National scaler/model.
- National reports.

---

## 20. Rủi ro và cách xử lý

| Rủi ro                                     | Cách xử lý                                                      |
| ------------------------------------------- | ------------------------------------------------------------------ |
| Vietnam PBF thay đổi liên tục           | Version snapshot, checksum và không overwrite                    |
| Geofabrik không chia sẵn tỉnh            | Dùng region registry và Osmium polygon extract                   |
| Boundary thay đổi                         | Version boundary,`valid_from/to`, review registry                |
| PBF/graph tốn RAM                          | Cắt theo region, chạy tuần tự trước, benchmark concurrency   |
| Buffer làm trùng POI                      | Canonical POI +`region_poi` membership                           |
| Edge/node trùng giữa graph vùng          | Key có`graph_id/region_id/snapshot/network_type`                |
| Route gần biên bị cắt                   | Dùng buffered extraction boundary                                 |
| Public-transport POI thiếu                 | Lấy cả`highway`, `public_transport`, không chỉ `amenity` |
| Graph phân mảnh                           | Component report, snap status, không giấu unreachable            |
| Directed edge làm road length gấp đôi   | Quy về physical edge khi tính infrastructure                     |
| Cache cũ được dùng nhầm               | Cache key gồm snapshot/config/code/input checksums                |
| Một region lỗi dừng batch                | Exception isolation và per-region state                           |
| Cluster giữa tỉnh không so sánh được | National scaler/model riêng                                       |
| OSM coverage không đồng đều            | Quality indicators và limitation trong báo cáo                  |
| Windows khó cài native dependency         | Kiểm tra trong Phase 1; dùng conda/WSL nếu cần                 |
| Scheduled job vượt tài nguyên           | Giới hạn workers, disk quota, cleanup policy                     |

---

## 21. Logging và báo cáo vận hành

Mỗi log record nên có:

```text
timestamp
run_id
region_id
snapshot_id
step_name
level
message
duration
```

Batch summary:

```text
snapshot_id
total_regions
completed_regions
failed_regions
skipped_regions
total_runtime
failed_step_counts
artifact_size
```

Không chỉ dùng `print("Write successfully")` vì không đủ để debug batch toàn quốc.

---

## 22. Chính sách lưu trữ

### Commit vào Git

- Source code.
- SQL.
- Config không chứa secret.
- Boundary nhỏ nếu license và kích thước phù hợp.
- Data dictionary.
- Sample fixtures.
- Báo cáo/ảnh cần thiết.

### Không commit vào Git

- Vietnam/region PBF.
- GraphML lớn.
- Full Parquet outputs.
- Database credentials.
- HTML/map artifact quá lớn.
- Logs đầy đủ.

### Retention

- Giữ raw snapshot dùng trong báo cáo cuối.
- Giữ manifest của mọi snapshot.
- Có thể xóa intermediate region PBF/graph cũ sau khi xác minh kết quả và có chính sách rõ ràng.
- Không xóa artifact của một run đang được báo cáo hoặc dùng cho model.

---

## 23. Definition of Done toàn hệ thống

- [ ] Không còn hard-code Hà Nội trong pipeline logic.
- [ ] Có package và CLI thống nhất.
- [ ] Có region registry đã validate.
- [ ] Có snapshot/version metadata.
- [ ] POI được chuẩn hóa toàn quốc một lần mỗi snapshot.
- [ ] Có walking và driving graph theo region.
- [ ] Có boundary buffer.
- [ ] Có hexagon, snap và accessibility.
- [ ] Có service/road features.
- [ ] Có regional clustering và maps.
- [ ] Có run/step state.
- [ ] Có resume và cache validation.
- [ ] Hà Nội và Đà Nẵng chạy không sửa source.
- [ ] `run-all` không dừng vì một region lỗi.
- [ ] Có national feature matrix.
- [ ] Có national scaler/model version.
- [ ] Có quality report và limitations.
- [ ] Một máy mới có thể chạy theo README.

---

## 24. Việc cần làm ngay

Không bắt đầu bằng việc tải và xử lý toàn bộ tỉnh/thành. Thực hiện đúng thứ tự:

1. Tạo `pyproject.toml` và `src/ady201`.
2. Tạo `config/project.yaml`, `categories.yaml`, `regions.yaml`.
3. Tạo `RunContext`.
4. Tạo database tables cho region/snapshot/run/step.
5. Refactor một POI flow thành hàm generic.
6. Viết generic boundary buffer và PBF extract.
7. Viết generic graph builder.
8. Viết `run_region`.
9. Chạy end-to-end Hà Nội.
10. Thêm Đà Nẵng chỉ qua registry.
11. Thêm cache/resume.
12. Sau khi hai-region test đạt mới viết `run_all_regions`.

Mốc đầu tiên của nhóm nên là:

```powershell
ady201 run-region --region hanoi --snapshot <snapshot_id>
```

Khi lệnh này chạy ổn, mốc tiếp theo là:

```powershell
ady201 run-region --region da-nang --snapshot <snapshot_id>
```

Nếu lệnh thứ hai chạy được mà không sửa source code, nhóm đã xây đúng nền móng để mở rộng ra toàn quốc.

---

## 25. Tài liệu tham khảo

- Geofabrik Vietnam: [https://download.geofabrik.de/asia/vietnam.html](https://download.geofabrik.de/asia/vietnam.html)
- Osmium Tool manual: [https://osmcode.org/osmium-tool/manual.html#extracting-geographical-regions](https://osmcode.org/osmium-tool/manual.html#extracting-geographical-regions)
- Pyrosm quickstart: [https://pyrosm.readthedocs.io/en/stable/quickstart.html](https://pyrosm.readthedocs.io/en/stable/quickstart.html)
- Pyrosm graph workflow: [https://pyrosm.readthedocs.io/en/stable/graphs.html](https://pyrosm.readthedocs.io/en/stable/graphs.html)
- OSMnx user reference: [https://osmnx.readthedocs.io/en/stable/user-reference.html](https://osmnx.readthedocs.io/en/stable/user-reference.html)
- NetworkX shortest paths: [https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html](https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html)
- PostGIS documentation: [https://postgis.net/docs/](https://postgis.net/docs/)
