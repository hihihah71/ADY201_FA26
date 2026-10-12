# Giai đoạn 08 — Snap và accessibility

## Mục tiêu

Đưa POI/cell vào walking graph và tính khả năng tiếp cận dịch vụ bằng hàm Dijkstra có sẵn.

## Nhiệm vụ tổng quát

- Snap POI và representative point vào nearest graph node.
- Lưu snap distance và status.
- Kiểm thử một số route A–B.
- Chạy multi-source Dijkstra theo category.
- Tạo feature 5/10/15 phút.

## Luồng

```text
POI/cell points + walking graph
        ↓ nearest-node batch
Snapped nodes
        ↓ category destinations
Multi-source Dijkstra
        ↓
Accessibility features theo cell
```

## Những thứ cần thay đổi

Tạo:

```text
src/ady201/network/snap.py
src/ady201/network/accessibility.py
tests/test_snap.py
tests/test_accessibility.py
```

Snap output:

```text
object_type
object_id
region_id
network_type
node_id
snap_distance_m
status
```

Accessibility output tối thiểu:

```text
nearest_hospital_min
nearest_pharmacy_min
nearest_school_min
nearest_supermarket_min
nearest_transit_min
*_within_5m
*_within_10m
*_within_15m
unreachable flags
```

Quy tắc:

- Project graph/points về cùng CRS.
- Snap theo batch, không loop nếu thư viện hỗ trợ vectorization.
- Không thay unreachable bằng 0.
- Không chạy Dijkstra cho mọi cặp cell–POI.
- Với directed graph, kiểm tra chiều graph/reversed graph.

## Kiến thức cần học

### Bắt buộc

- Nearest node/edge.
- Dijkstra weight và non-negative cost.
- Multi-source Dijkstra.
- Directed graph/reverse graph.
- Unreachable/component handling.

### Tìm hiểu sâu bên ngoài

- OSMnx nearest nodes/edges.
- NetworkX multi-source Dijkstra.
- KD-tree/Ball-tree.
- Edge snapping và connector; phần nâng cao.

## Phân công

### Thành

- Định nghĩa accessibility output schema.
- Viết quality SQL/DuckDB queries.

### Hiếu

- Owner snapping, route tests và multi-source Dijkstra.
- Kiểm tra outlier/unreachable.

### Quang

- Vẽ snap outliers và route mẫu.
- Kiểm tra phân phối travel time.

### Review

- Thành kiểm tra schema/count.
- Quang kiểm tra trực quan.
- Hiếu xác minh thuật toán/weight.

## Đầu ra

```text
snap/poi_snap.parquet
snap/cell_snap.parquet
accessibility/cell_accessibility.parquet
accessibility/quality.json
```

## Hoàn thành khi

- Multi-source result khớp route point-to-point mẫu.
- Có snap-distance report.
- Unreachable được xử lý rõ ràng.

