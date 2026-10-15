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

### Bước 1 — Load và kiểm tra walking graph

- Thêm `osmnx` vào `pyproject.toml` nếu dùng hàm `nearest_nodes`, rồi chạy lại `python -m pip install -e .`.
- Mở `walk.graphml` của đúng `region_id`.
- Chuyển `length_m` và `travel_time_s` về kiểu số nếu GraphML đọc chúng thành chuỗi.
- Kiểm tra graph có node/edge và mọi weight dùng cho routing đều hữu hạn, không âm.
- Dùng walking graph, không dùng driving graph cho chỉ số thời gian đi bộ.

Kết quả cần thấy: một lệnh shortest path mẫu chạy được với weight `travel_time_s`.

### Bước 2 — Snap POI vào node gần nhất

- Chỉ lấy POI thuộc `analysis` hoặc `buffer` của region hiện tại.
- Gửi toàn bộ longitude/latitude theo mảng vào hàm nearest-node thay vì lặp từng hàng; nếu dùng OSMnx thì `X` là longitude và `Y` là latitude.
- Lưu `node_id`, `snap_distance_m` và `status` bên cạnh khóa POI.
- Đặt ngưỡng cảnh báo snap quá xa trong config; không tự xóa hàng mà chưa xem trên bản đồ.

Kết quả cần thấy: mỗi POI hợp lệ có node gần nhất và biết nó cách mạng đường bao nhiêu mét.

### Bước 3 — Snap điểm đại diện của cell

- Làm tương tự bước 2 với `representative_point` của cell.
- Giữ `cell_id` làm khóa, không dùng số thứ tự dòng.
- Cell không snap được cần có `status` riêng để phân biệt với cell snap được nhưng không tới được dịch vụ.
- So sánh phân bố snap distance của POI và cell để tìm boundary hoặc graph bị lệch.

Kết quả cần thấy: mỗi cell có `node_id` đầu hành trình hoặc một lý do lỗi rõ ràng.

### Bước 4 — Tạo tập node đích cho từng category

- Group POI đã snap theo `category`.
- Với mỗi category, lấy tập `node_id` duy nhất; nhiều POI cùng snap vào một node chỉ cần một source cho Dijkstra.
- Vẫn giữ số POI riêng để báo cáo, không nhầm số source node với số dịch vụ.
- Nếu một category không có POI trong cả analysis và buffer, đánh dấu `no_source`, không gọi Dijkstra với tập rỗng.

Kết quả cần thấy: có dictionary dạng `category -> set(node_id)` để đưa vào thuật toán.

### Bước 5 — Chạy multi-source Dijkstra đúng chiều

- Mục tiêu là thời gian từ cell tới POI gần nhất.
- Vì graph có hướng nhưng các POI đang được dùng làm nhiều source, chạy `multi_source_dijkstra_path_length()` trên reversed graph để kết quả tương ứng chiều `cell -> POI` của graph gốc.
- Dùng `travel_time_s` làm `weight` và chạy đúng một lần cho mỗi category.
- Kết quả trả về là khoảng cách từ các source tới mọi node đi tới được; tra kết quả theo `node_id` của cell.

Kết quả cần thấy: số lần chạy Dijkstra bằng số category, không bằng số POI hoặc số cell.

### Bước 6 — Đổi kết quả sang phút

- Với node có kết quả, tính `nearest_<category>_min = seconds / 60`.
- Giữ đủ độ chính xác trong file dữ liệu; chỉ làm tròn khi hiển thị báo cáo.
- Thời gian bằng `0` chỉ hợp lệ khi cell node cũng là một source node.
- Không cộng snap distance vào thời gian cho phiên bản đầu; ghi giới hạn này trong data dictionary.

Kết quả cần thấy: mọi thời gian hợp lệ lớn hơn hoặc bằng 0 và có đơn vị phút rõ ràng.

### Bước 7 — Tạo các cột theo ngưỡng thời gian

- Đọc danh sách `[5, 10, 15]` từ `accessibility_minutes` trong `project.json`.
- Với mỗi category và ngưỡng, tạo cột boolean như `hospital_within_15_min`.
- Chỉ gán `true` khi có thời gian và thời gian nhỏ hơn hoặc bằng ngưỡng.
- Dùng quy tắc đặt tên thống nhất để giai đoạn 09 có thể chọn cột tự động.

Kết quả cần thấy: có thể đếm ngay bao nhiêu cell tiếp cận từng dịch vụ trong từng ngưỡng.

### Bước 8 — Phân biệt dữ liệu thiếu và không thể đi tới

- `snap_failed`: cell hoặc POI không gắn được vào graph.
- `no_source`: region không có POI thuộc category đó trong phạm vi cho phép.
- `unreachable`: có source và cell đã snap nhưng không tồn tại đường đi trong graph.
- Giữ thời gian là null cho các trường hợp trên và thêm cột trạng thái; tuyệt đối không thay bằng `0`.

Kết quả cần thấy: người đọc biết vì sao một giá trị thời gian bị thiếu.

### Bước 9 — Kiểm tra tuyến mẫu trên bản đồ

- Chọn ít nhất năm cell ở trung tâm, ngoại vi, gần biên và gần khu vực graph đứt.
- Tìm category gần nhất theo kết quả, chạy shortest path để lấy danh sách node của tuyến cụ thể.
- Vẽ tuyến, điểm cell và POI trên bản đồ; so sánh thời gian với độ dài tuyến.
- Nếu tuyến đi ngược chiều hoặc đi vòng vô lý, quay lại kiểm tra bước 06 và chiều reversed graph.

Kết quả cần thấy: các tuyến mẫu bám theo mạng đường và thời gian có độ lớn hợp lý.

## File cần tạo hoặc sửa

```text
src/ady201/snap.py
src/ady201/accessibility.py
src/ady201/main.py
pyproject.toml
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
ady201 build-accessibility --region hanoi
```

## Quy tắc

- Không tự viết Dijkstra từ đầu.
- Weight của Dijkstra là `travel_time_s`.
- Không chạy Dijkstra riêng cho từng cặp cell–POI.
- Nếu graph có hướng, kiểm tra chiều đi; có thể cần reversed graph khi POI là nguồn.
- Không thay giá trị unreachable bằng 0.
- Ghi lại snap distance để phát hiện điểm quá xa đường.

## Lỗi thường gặp

- Truyền latitude vào `X` và longitude vào `Y` khi tìm nearest node.
- Chạy từ POI trên graph gốc rồi hiểu nhầm đó là chiều cell đi tới POI.
- Chạy Dijkstra cho từng POI hoặc từng cell, khiến thời gian xử lý tăng rất lớn.
- Thay unreachable bằng `0`, làm cell kém tiếp cận trông giống cell tốt nhất.

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
data/processed/{region_id}/snap/poi_snap.parquet
data/processed/{region_id}/snap/cell_snap.parquet
data/processed/{region_id}/accessibility/cell_accessibility.parquet
outputs/quality/{region_id}/accessibility_summary.json
```

## Hoàn thành khi

- Kết quả tuyến mẫu phù hợp với đường trên bản đồ.
- Không có travel time âm.
- Cell unreachable được đánh dấu rõ.
- Chạy một lần cho mỗi category, không chạy cho từng POI.
