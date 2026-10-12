# Giai đoạn 09 — Feature và chỉ số tổng hợp

## Mục tiêu

Tạo một bảng trong đó mỗi hàng là một cell và mỗi cột mô tả dịch vụ, khả năng tiếp cận hoặc mạng đường của cell đó.

## Cần có trước

- Cell và POI membership từ giai đoạn 07.
- Accessibility từ giai đoạn 08.
- Node và edge của graph từ giai đoạn 06.

## Khái niệm đơn giản

- **Count**: số lượng, ví dụ số bệnh viện trong cell.
- **Density**: số lượng chia cho diện tích.
- **Ratio**: tỷ lệ giữa hai đại lượng.
- **Feature matrix**: bảng số liệu dùng cho phân tích và clustering.
- **Composite score**: một điểm được ghép từ nhiều feature.

## Luồng

```text
POI theo cell ───────→ service features ┐
Node/edge theo cell ─→ road features    ├→ feature matrix
Accessibility ───────→ access features  ┘
                                          ↓
                                  composite scores
```

## Các bước thực hiện

1. Tính số POI và mật độ POI theo category.
2. Tính số loại dịch vụ có trong mỗi cell.
3. Ghép thời gian tiếp cận từ giai đoạn 08.
4. Tính chiều dài đường, mật độ đường và số giao lộ.
5. Tính tỷ lệ đường chính, ngõ cụt và degree trung bình.
6. Ghép tất cả bảng theo `cell_id`.
7. Xử lý rõ ba trường hợp: `0`, `null` và `unreachable`.
8. Tạo các score tổng hợp với trọng số nằm trong config.
9. Viết data dictionary giải thích từng cột.

## File cần tạo hoặc sửa

```text
src/ady201/service_features.py
src/ady201/road_features.py
src/ady201/feature_matrix.py
src/ady201/scores.py
src/ady201/main.py
config/scores.json
```

Feature chính:

```text
poi_density_km2
essential_poi_density_km2
service_category_count
nearest_hospital_min
nearest_school_min
road_density_km_per_km2
intersection_density_km2
average_node_degree
dead_end_ratio
main_road_share
service_completeness_score
accessibility_score
connectivity_score
```

Lệnh mục tiêu:

```powershell
ady201 build-features --region hanoi --snapshot <snapshot_id>
```

## Quy tắc

- Count và density là hai cột khác nhau.
- Density dùng `area_km2` sau khi clip.
- Không đếm hai chiều của cùng một đoạn đường thành hai physical roads.
- Mỗi feature phải có công thức, đơn vị và nguồn.
- Trọng số score không viết trực tiếp trong code.
- Không chia cho 0 khi cell có diện tích lỗi.

## Cần học trước

- SQL `GROUP BY` và aggregation.
- Count, density, ratio và phần trăm.
- Graph degree và intersection.
- Join bảng theo khóa.
- Min-max scale hoặc robust scale cơ bản.

## Tìm hiểu thêm

- Từ khóa: `DuckDB group by parquet`.
- Từ khóa: `road network intersection density`.
- Từ khóa: `composite index normalization weights`.
- Từ khóa: `Shannon diversity index`.

## Phân công

### Thành

- Viết service features và schema feature matrix.
- Viết SQL tổng hợp POI theo cell.

### Hiếu

- Viết road/connectivity features.
- Kiểm tra đường hai chiều không bị double-count.

### Quang

- Viết data dictionary.
- Tạo bảng missing, min, max và các giá trị bất thường.

## Đầu ra

```text
data/processed/{snapshot_id}/{region_id}/features/service_features.parquet
data/processed/{snapshot_id}/{region_id}/features/road_features.parquet
data/processed/{snapshot_id}/{region_id}/features/cell_features.parquet
outputs/{snapshot_id}/{region_id}/feature_data_dictionary.md
```

## Hoàn thành khi

- Mỗi cell chỉ có một hàng trong `cell_features.parquet`.
- Mỗi feature có công thức và đơn vị.
- Không có giá trị vô cực hoặc lỗi chia cho 0.
- Kiểm tra thủ công một số cell trên bản đồ cho kết quả hợp lý.
