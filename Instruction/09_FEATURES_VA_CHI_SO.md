# Giai đoạn 09 — Feature và chỉ số tổng hợp

## Mục tiêu

Tạo feature matrix giải thích được cho từng hexagon.

## Nhiệm vụ tổng quát

- Tính service features.
- Tính road/connectivity features.
- Ghép accessibility features.
- Tạo service completeness, accessibility và connectivity score.
- Validate units, missing và outliers.

## Luồng

```text
POI membership ─────→ service features ┐
Road graph/edges ───→ road features    ├→ feature matrix
Accessibility ──────→ access features  ┘
                                      ↓
                             composite indices
```

## Những thứ cần thay đổi

Tạo:

```text
src/ady201/features/services.py
src/ady201/features/roads.py
src/ady201/features/composite.py
src/ady201/features/matrix.py
```

Feature chính:

```text
poi_density_km2
essential_poi_density_km2
service_category_count
service_diversity
nearest_*_min
road_density_km_per_km2
intersection_density_km2
avg_node_degree
dead_end_ratio
main_road_share
service_completeness_15m
accessibility_score
connectivity_score
```

Quy tắc:

- Count và density là hai feature khác nhau.
- Density dùng diện tích cell sau clip.
- Không double-count hai directed edges của một physical road.
- Feature phải có unit/data dictionary.
- Phân biệt 0, null và unreachable.
- Trọng số composite nằm trong config.

## Kiến thức cần học

### Bắt buộc

- Group by và aggregation.
- Density/ratio/diversity.
- Graph degree/intersection.
- Feature scaling cơ bản.
- Composite index và sensitivity.

### Tìm hiểu sâu bên ngoài

- Shannon entropy cho service diversity.
- Physical-edge deduplication.
- RobustScaler/log transform.
- Sensitivity analysis.

## Phân công

### Thành

- Owner service features và feature matrix schema.
- Viết SQL analytics trong DuckDB.

### Hiếu

- Owner road features và kiểm tra double-count.
- Cung cấp graph metrics.

### Quang

- Owner EDA feature, missing/outlier report.
- Chuẩn bị bảng mô tả feature.

### Review

- Thành và Hiếu review công thức chéo.
- Quang smoke test distribution.

## Đầu ra

```text
features/service_features.parquet
features/road_features.parquet
features/cell_features.parquet
features/data_dictionary.md
```

## Hoàn thành khi

- Mỗi feature có tên, công thức, unit và nguồn.
- Không có lỗi divide-by-zero.
- Ba vùng mẫu cho kết quả hợp lý khi kiểm tra trực quan.

