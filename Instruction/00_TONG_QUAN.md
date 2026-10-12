# Tổng quan lộ trình DuckDB

## Mục tiêu cuối

Tạo một pipeline chạy hoàn toàn bằng lệnh, không cần mở pgAdmin hoặc import dữ liệu thủ công:

```powershell
ady201 run-region --region hanoi --snapshot <snapshot_id>
ady201 run-all --snapshot <snapshot_id> --resume
```

Stack chính:

- Python: điều phối toàn bộ pipeline.
- DuckDB: metadata, SQL analytics, quality checks và kết quả tổng hợp.
- GeoParquet: POI, node, edge, hexagon và feature.
- GraphML: graph dùng lại cho routing.
- Osmium + Pyrosm: xử lý `.osm.pbf`.
- NetworkX/OSMnx: graph, snap và Dijkstra có sẵn.
- GeoPandas/Shapely/H3: xử lý không gian.
- scikit-learn: clustering.

## Luồng tổng thể

```text
Vietnam PBF snapshot
        ↓
Boundary registry
        ↓
POI toàn quốc + region PBF
        ↓
Walking graph + driving graph
        ↓
Hexagon + spatial join
        ↓
Snap POI/cell vào graph
        ↓
Accessibility + road/service features
        ↓
Clustering + composite index + maps
        ↓
Run-all toàn quốc + cập nhật snapshot
```

## Danh sách giai đoạn

| Giai đoạn | Nội dung | Kết quả chính |
|---|---|---|
| [01](01_CHUAN_HOA_PROJECT.md) | Chuẩn hóa project Python | Package, môi trường, test mẫu |
| [02](02_CONFIG_VA_REGION_REGISTRY.md) | Config và region registry | Không còn hard-code Hà Nội |
| [03](03_DUCKDB_VA_RUN_STATE.md) | DuckDB và run state | Database tự khởi tạo từ Python |
| [04](04_SNAPSHOT_PBF_VA_BOUNDARY.md) | Snapshot PBF và boundary | Dữ liệu đầu vào có version |
| [05](05_POI_TOAN_QUOC.md) | POI toàn quốc | POI chuẩn hóa một lần/snapshot |
| [06](06_REGION_PBF_VA_ROAD_GRAPH.md) | Region PBF và graph | Walking/driving graph |
| [07](07_HEXAGON_VA_SPATIAL_JOIN.md) | Hexagon và spatial join | Đơn vị phân tích thống nhất |
| [08](08_SNAP_VA_ACCESSIBILITY.md) | Snap và accessibility | Thời gian tới dịch vụ gần nhất |
| [09](09_FEATURES_VA_CHI_SO.md) | Feature và chỉ số | Feature matrix theo cell |
| [10](10_CLUSTERING_VA_BAN_DO.md) | Clustering và bản đồ | Cluster, heatmap, báo cáo |
| [11](11_TU_DONG_HOA_MOT_REGION.md) | Tự động hóa một region | `run-region`, cache, resume |
| [12](12_RUN_ALL_VA_CAP_NHAT.md) | Chạy toàn quốc và cập nhật | `run-all`, national aggregation |

## Kiến thức cả nhóm phải nắm

### Bắt buộc

- Git branch, pull request và code review.
- Python package, module, virtual environment và logging.
- OSM `node`, `way`, `relation`, tags và `.osm.pbf`.
- CRS EPSG:4326, CRS theo mét, point/line/polygon.
- DuckDB connection, table, view và SQL cơ bản.
- Parquet/GeoParquet và lý do không dùng CSV cho geometry.
- Graph: node, edge, directed graph, weight, connected component.
- Dijkstra, multi-source Dijkstra và unreachable node.
- Count, density, accessibility và composite index.
- Scale feature, K-Means và silhouette score.

### Tìm hiểu sâu bên ngoài khi đến giai đoạn tương ứng

- DuckDB spatial extension và Parquet scan.
- Osmium extract strategies.
- Pyrosm network types và graph conversion.
- OSMnx nearest nodes/edges.
- NetworkX multi-source shortest path.
- H3 indexing.
- GeoPandas spatial join/overlay.
- scikit-learn preprocessing và clustering.

## Phân công tổng quát

### Thành — trung bình–khó

- POI, DuckDB schema, SQL analytics, data quality và service features.

### Hiếu — trung bình–khó

- PBF, boundary buffer, graph, snap, accessibility và road features.

### Quang — dễ–trung bình

- Config/registry support, EDA, feature validation, clustering, bản đồ và báo cáo chạy.

## Quy tắc làm việc

1. Mỗi giai đoạn có owner, reviewer và smoke tester.
2. Không bắt đầu giai đoạn sau khi đầu ra bắt buộc của giai đoạn trước chưa đạt.
3. Không thêm xử lý riêng kiểu `if region == "hanoi"`.
4. Notebook chỉ dùng khám phá; logic chạy lại phải nằm trong `src/`.
5. SQL được Python tự chạy trong DuckDB; không có bước import thủ công.
6. File PBF, GraphML lớn, DuckDB và full Parquet không commit vào Git.
7. Mỗi người phải chạy pipeline mẫu và trình bày lại một module không do mình làm chính.

## Thứ tự ưu tiên

```text
Một vùng mẫu nhỏ
    → Hà Nội end-to-end
    → Đà Nẵng không sửa source
    → resume/cache
    → run-all tuần tự
    → national analysis
    → scheduled update
```

