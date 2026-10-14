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

### Bước 1 — Tạo các feature số lượng và mật độ dịch vụ

- Chỉ dùng POI có `membership_scope = analysis`.
- Group theo `cell_id` và `category` để đếm POI, sau đó pivot thành các cột như `hospital_count`.
- Tính mật độ bằng `count / area_km2`; giữ cả count và density vì chúng trả lời hai câu hỏi khác nhau.
- Left join kết quả vào danh sách cell đầy đủ rồi điền count bằng `0` cho cell không có POI.

Kết quả cần thấy: mỗi cell đều xuất hiện, kể cả cell không có dịch vụ.

### Bước 2 — Đo mức đầy đủ và đa dạng dịch vụ

- Tạo cột boolean cho biết cell có hay không có từng category thiết yếu.
- `service_category_count` là số category có count lớn hơn 0.
- Nếu dùng chỉ số đa dạng nâng cao, lưu công thức và không thay thế cột count dễ hiểu.
- Danh sách category thiết yếu phải nằm trong config hoặc data dictionary, không rải trong nhiều hàm.

Kết quả cần thấy: có thể phân biệt cell nhiều POI cùng loại với cell có nhiều loại dịch vụ khác nhau.

### Bước 3 — Ghép feature accessibility

- Đọc `cell_accessibility.parquet` của cùng snapshot và region.
- Left join theo `cell_id` vào danh sách cell chuẩn.
- Giữ cả thời gian gần nhất, các cột `within_<n>_min` và trạng thái unreachable.
- Kiểm tra số hàng không tăng sau join; tăng hàng nghĩa là bảng accessibility bị trùng `cell_id`.

Kết quả cần thấy: một hàng cell có cả thông tin dịch vụ tại chỗ và dịch vụ có thể đi bộ tới.

### Bước 4 — Tạo feature chiều dài và mật độ đường

- Spatial join hoặc clip edge với cell để biết phần đường nằm trong từng cell.
- Với edge hai chiều được lưu thành hai hướng, tạo khóa đoạn đường vật lý để không cộng cùng geometry hai lần.
- Tính `road_length_km`, sau đó `road_density_km_per_km2 = road_length_km / area_km2`.
- Ghi rõ loại đường nào được đưa vào tổng chiều dài.

Kết quả cần thấy: tổng chiều dài theo cell không bị nhân đôi chỉ vì graph có hai hướng.

### Bước 5 — Tạo feature kết nối mạng đường

- Tính degree trên graph phù hợp, nhưng hiểu rõ MultiDiGraph có in-degree/out-degree và edge song song.
- Định nghĩa giao lộ theo số nhánh đường vật lý, không chỉ đếm số edge có hướng; lưu ngưỡng định nghĩa trong data dictionary.
- Tính `intersection_density_km2`, `average_node_degree` và `dead_end_ratio`.
- Nhóm `highway` thành đường chính/khác rồi tính `main_road_share` trên chiều dài, không trên số dòng edge.

Kết quả cần thấy: feature phản ánh cấu trúc đường thay vì cách dữ liệu được biểu diễn hai chiều.

### Bước 6 — Ghép thành một feature matrix

- Bắt đầu từ bảng cell chuẩn có một hàng cho mỗi `cell_id`.
- Left join lần lượt service features, accessibility và road features.
- Sau mỗi join, kiểm tra số hàng và số `cell_id` duy nhất không thay đổi.
- Thêm `snapshot_id`, `region_id`, `grid_version` để truy nguồn dữ liệu.

Kết quả cần thấy: `cell_features.parquet` có đúng một hàng cho mỗi cell.

### Bước 7 — Quy định rõ `0`, `null` và `unreachable`

- `0`: đã đo và không có đối tượng, ví dụ `hospital_count = 0`.
- `null`: chưa tính được hoặc dữ liệu đầu vào thiếu; phải có cột trạng thái hoặc ghi chú giải thích.
- `unreachable = true`: cell và dịch vụ tồn tại nhưng graph không có đường đi phù hợp.
- Không dùng một giá trị số lớn tùy ý thay cho unreachable trong file dữ liệu gốc.

Kết quả cần thấy: không cần đoán ý nghĩa của giá trị thiếu khi đọc feature matrix.

### Bước 8 — Tạo chỉ số tổng hợp có thể giải thích

- Trong `config/scores.json`, khai báo feature, chiều tốt/xấu và trọng số của từng score.
- Chuẩn hóa các feature về thang chung; feature thời gian cần đảo chiều vì thời gian thấp là tốt.
- Kiểm tra tổng trọng số của mỗi score bằng `1` hoặc chuẩn hóa trọng số trước khi tính.
- Lưu cả feature thành phần và score cuối, không chỉ giữ một điểm tổng hợp.

Kết quả cần thấy: thay trọng số chỉ cần sửa config và có thể giải thích score được tạo từ đâu.

### Bước 9 — Viết data dictionary cùng lúc với code

- Mỗi cột cần có: tên, ý nghĩa, kiểu dữ liệu, đơn vị, công thức, nguồn và cách xử lý missing.
- Với ratio/score, ghi miền giá trị dự kiến và chiều diễn giải cao là tốt hay xấu.
- Với giao lộ và đường chính, ghi chính xác quy tắc phân loại.
- Cập nhật file ngay khi thêm hoặc đổi feature, không đợi cuối dự án.

Kết quả cần thấy: một thành viên không viết feature vẫn đọc và kiểm tra được cột đó.

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

## Lỗi thường gặp

- Inner join làm biến mất các cell không có POI hoặc không có đường.
- Cộng cả hai edge ngược chiều thành hai đoạn đường vật lý.
- Điền mọi giá trị thiếu bằng `0` rồi mất thông tin lỗi/unreachable.
- Cộng các feature khác đơn vị vào score trước khi chuẩn hóa.

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
