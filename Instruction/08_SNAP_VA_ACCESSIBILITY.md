# Giai đoạn 08 — Snap và accessibility

## Mục tiêu

Tính thời gian đi bộ từ mỗi cell tới các dịch vụ gần nhất bằng hàm Dijkstra có sẵn.

## Cần có trước

- Walking graph từ giai đoạn 06.
- Cell và POI membership từ giai đoạn 07.
- Edge có `travel_time_s` hợp lệ.

## Khái niệm đơn giản

- **Snap**: tìm node đường gần nhất cho một POI hoặc cell.
- **Accessibility**: mức dễ tiếp cận dịch vụ.
- **Multi-source Dijkstra**: tính khoảng cách tới nguồn gần nhất trong một lần chạy.

## Luồng

```text
POI + representative point của cell
                ↓ snap
          node gần nhất
                ↓ Dijkstra theo category
       thời gian tới dịch vụ gần nhất
```

## Các bước thực hiện

1. Load walking graph từ GraphML.
2. Snap POI vào node gần nhất và lưu khoảng cách snap.
3. Snap representative point của cell vào node gần nhất.
4. Gom node POI theo từng category.
5. Gọi hàm multi-source Dijkstra của NetworkX.
6. Đổi giây sang phút.
7. Tạo cột dịch vụ trong phạm vi 5, 10 và 15 phút.
8. Đánh dấu cell không thể đi tới dịch vụ thay vì thay bằng 0.
9. Kiểm tra thủ công một số tuyến A–B trên bản đồ.

## File cần tạo hoặc sửa

```text
src/ady201/snap.py
src/ady201/accessibility.py
src/ady201/main.py
```

Snap output:

```text
object_type
object_id
region_id
node_id
snap_distance_m
status
```

Accessibility output:

```text
cell_id
nearest_hospital_min
nearest_pharmacy_min
nearest_school_min
nearest_supermarket_min
nearest_transit_min
hospital_within_15_min
school_within_15_min
unreachable_hospital
```

Lệnh mục tiêu:

```powershell
ady201 build-accessibility --region hanoi --snapshot <snapshot_id>
```

## Quy tắc

- Không tự viết Dijkstra từ đầu.
- Weight của Dijkstra là `travel_time_s`.
- Không chạy Dijkstra riêng cho từng cặp cell–POI.
- Nếu graph có hướng, kiểm tra chiều đi; có thể cần reversed graph khi POI là nguồn.
- Không thay giá trị unreachable bằng 0.
- Ghi lại snap distance để phát hiện điểm quá xa đường.

## Cần học trước

- Nearest node.
- Dijkstra và edge weight.
- Multi-source Dijkstra.
- Directed graph và reversed graph.
- Giá trị unreachable.

## Tìm hiểu thêm

- Từ khóa: `OSMnx nearest_nodes`.
- Từ khóa: `NetworkX multi_source_dijkstra_path_length`.
- Từ khóa: `directed graph reverse shortest path`.

## Phân công

### Thành

- Chốt schema accessibility và câu SQL kiểm tra missing/unreachable.
- Kiểm tra số cell cho từng category.

### Hiếu

- Viết snap và gọi multi-source Dijkstra.
- Kiểm tra chiều graph, weight và các điểm snap quá xa.

### Quang

- Vẽ các tuyến mẫu và điểm snap bất thường.
- Tạo bảng phân bố thời gian 5, 10 và 15 phút.

## Đầu ra

```text
data/processed/{snapshot_id}/{region_id}/snap/poi_snap.parquet
data/processed/{snapshot_id}/{region_id}/snap/cell_snap.parquet
data/processed/{snapshot_id}/{region_id}/accessibility/cell_accessibility.parquet
outputs/quality/{snapshot_id}/{region_id}/accessibility_summary.json
```

## Hoàn thành khi

- Kết quả tuyến mẫu phù hợp với đường trên bản đồ.
- Không có travel time âm.
- Cell unreachable được đánh dấu rõ.
- Chạy một lần cho mỗi category, không chạy cho từng POI.
