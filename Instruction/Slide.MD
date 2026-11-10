# Slide 1 — Hệ thống đánh giá khu vực phù hợp

## Từ dữ liệu bản đồ mở đến bản đồ gợi ý theo nhu cầu

- Môn học: ADY201
- Dữ liệu minh họa: Hà Nội (`29_3`)
- 85.249 cell, 135 cột feature
- OpenStreetMap + Overture Places + GeoPandas + Streamlit

> Gợi ý trình bày: thêm tên nhóm, thành viên và một ảnh heatmap làm nền.

> Thuyết trình: Dự án chia thành phố thành các khu vực nhỏ, mô tả đặc điểm của từng khu vực và đề xuất nơi phù hợp với nhu cầu của người dùng.

---

# Slide 2 — Bài toán

## Mỗi người có một tiêu chí chọn nơi ở khác nhau

- Sinh viên muốn gần đồ ăn, trường học và giao thông.
- Người đi làm cần dịch vụ và khả năng kết nối tốt.
- Gia đình cần trường học, bệnh viện, thực phẩm và công viên.
- Người cao tuổi ưu tiên y tế, tiện ích và sự yên tĩnh.
- Việc so sánh thủ công hàng chục nghìn khu vực là rất khó.

## Mục tiêu

> Chuyển dữ liệu bản đồ thành điểm đánh giá và heatmap phù hợp với lựa chọn của từng người dùng.

```text
Nhu cầu người dùng → Chấm điểm từng khu vực → Heatmap → Khu vực đề xuất
```

> Thuyết trình: Hệ thống không tìm một khu vực tốt nhất cho tất cả mọi người mà tìm khu vực phù hợp nhất với từng loại nhu cầu.

---

# Slide 3 — Luồng tổng thể của dự án

```text
OpenStreetMap PBF
├── Boundary tỉnh/thành
└── Mạng đường
         │
         ▼
    Grid cell 200 m
         ▲
         │
Overture Places
└── POI trong khu vực
         │
         ▼
Tính POI features + road features
         │
         ▼
cell_features.parquet
         │
         ▼
SuitabilityModel
         │
         ▼
Streamlit heatmap + Top khu vực
```

## Nguyên tắc chính

- OSM dùng cho boundary và mạng đường.
- Overture là nguồn POI duy nhất.
- Toàn bộ feature được ghép theo `cell_id`.
- Pipeline chỉ xuất một file GeoParquet cuối.

> Gợi ý trình bày: dùng một màu riêng cho OSM, Overture, Parquet, Model và giao diện.

---

# Slide 4 — Nguồn dữ liệu

## OpenStreetMap

```text
data/raw/osm/vietnam-261014.osm.pbf
```

Dùng để lấy:

- Boundary tỉnh/thành.
- Mạng đường đi bộ.
- Không sử dụng POI từ OSM.

## Overture Places

```text
data/raw/overture/vietnam_places.parquet
```

Dùng để lấy:

- Ăn uống, dịch vụ và mua sắm.
- Giáo dục và y tế.
- Công viên, thực phẩm và các POI quan trọng khác.

> Điểm cần nhấn mạnh: dự án không merge, matching hoặc deduplicate POI giữa OSM và Overture.

---

# Slide 5 — Tạo grid cell 200 m

```text
Tên tỉnh/thành
→ Đọc boundary từ OSM
→ Chuyển sang hệ tọa độ theo mét
→ Tạo lưới vuông 200 × 200 m
→ Giữ các cell thuộc boundary
→ Gán cell_id
```

## Mỗi cell chứa

- `cell_id`: khóa duy nhất.
- `geometry`: polygon của cell.
- Tọa độ đại diện của cell.

## Vì sao dùng grid?

- Tạo đơn vị không gian thống nhất để so sánh.
- Có thể tổng hợp POI và mạng đường theo cùng một khóa.
- Phù hợp để vẽ heatmap và xếp hạng khu vực.

> Gợi ý hình: boundary Hà Nội với các ô vuông phủ bên trong.

---

# Slide 6 — Tính POI feature

```text
Overture Places
→ Lọc POI trong boundary
→ Chia POI thành 13 nhóm
→ Gán POI vào cell
→ Đếm POI theo bán kính
→ Tính khoảng cách tới POI gần nhất
```

## Các bán kính

```text
100 m · 200 m · 500 m · 1 km · 2 km · 5 km
```

## Ví dụ feature

```text
food_and_drink_count_200m
services_and_business_count_200m
shopping_count_200m
nearest_hospital_m
nearest_school_m
nearest_park_m
nearest_grocery_store_m
```

Model chủ yếu dùng POI trong bán kính 200 m để thể hiện tiện ích có thể tiếp cận gần nơi ở.

---

# Slide 7 — Tính feature mạng đường

```text
Mạng đường OSM
→ Tạo buffer quanh cell
→ Lấy đoạn đường trong buffer
→ Tính tổng chiều dài đường
→ Tính mật độ đường
```

## Bán kính chính

- 500 m.
- 1.000 m.

## Ví dụ feature

```text
road_length_500m_km
road_density_500m_km_per_km2
road_length_1000m_km
road_density_1000m_km_per_km2
```

Mật độ đường được dùng như một chỉ báo cho khả năng kết nối và mức độ đô thị hóa.

---

# Slide 8 — Tạo `cell_features.parquet`

```text
Grid cell
   + POI features
   + Road features
→ Merge theo cell_id
→ Xử lý missing
→ Kiểm tra cell_id
→ cell_features.parquet
```

## File đầu ra

```text
data/processed/{region_id}/cell_features.parquet
```

## Kết quả hiện tại của `29_3`

- 85.249 cell.
- 135 cột.
- Có geometry và CRS, đọc trực tiếp bằng GeoPandas.
- Một file dùng chung cho notebook, model và giao diện.

## Nhóm cột

| Nhóm               | Nội dung                          |
| ------------------- | ---------------------------------- |
| Cell                | ID, tọa độ, geometry            |
| POI trực tiếp     | Số POI nằm trong cell            |
| POI theo bán kính | Count từ 100 m đến 5 km         |
| Nearest             | Khoảng cách tới POI quan trọng |
| Road                | Chiều dài và mật độ đường |

---

# Slide 9 — Model đánh giá khu vực

## Tiêu chí trực tiếp

- Đồ ăn.
- Dịch vụ.
- Mua sắm.
- Trường học.
- Bệnh viện.
- Cửa hàng thực phẩm.
- Công viên.
- Giao thông.

## Chỉ số được suy ra

### Yên tĩnh — `quietness`

Nghịch đảo của mức độ tập trung POI, giáo dục và mật độ đường.

### Hoạt động sinh viên — `student_activity`

Kết hợp khoảng cách tới đại học, trường ngoại ngữ và POI giáo dục.

### Cân bằng dịch vụ — `service_balance`

Kết hợp số lượng dịch vụ và tỷ lệ dịch vụ trong tổng POI địa phương.

> Điểm cần nói rõ: đây là mô hình chấm điểm theo luật và trọng số, chưa phải machine learning.

---

# Slide 10 — Cách tính điểm từng tiêu chí

| Mode       | Ý nghĩa                              |
| ---------- | -------------------------------------- |
| `more`   | Càng nhiều càng tốt                |
| `less`   | Càng ít càng tốt                   |
| `near`   | Càng gần càng tốt                  |
| `far`    | Càng xa càng tốt                    |
| `target` | Tốt nhất khi nằm trong một khoảng |

## Công thức cơ bản

```text
more = min(value / limit, 1)
less = 1 - more

near = 2 ^ (-distance / limit)
far  = 1 - near
```

Với `near`, khoảng cách bằng `limit` nhận 0,5 điểm.

## Mode `target`

```text
Trong khoảng min–max → 1 điểm
Nhỏ hơn min          → giảm điểm
Lớn hơn max          → giảm điểm
```

Ví dụ: người dùng muốn có đồ ăn xung quanh nhưng không muốn khu vực quá tập trung quán ăn.

---

# Slide 11 — Điểm tổng và khu vực đề xuất

## Ghép điểm

```text
Suitability score
= trung bình nhân có trọng số của các điểm thành phần
```

Một tiêu chí quan trọng có điểm rất thấp sẽ kéo điểm tổng xuống mạnh. Vì vậy, một lợi thế duy nhất không thể bù hoàn toàn cho các nhược điểm khác.

## Chọn khu vực

```text
Tính suitability_score cho tất cả cell
→ Xếp hạng từ cao xuống thấp
→ Lấy top 5–30%
→ Đánh dấu recommended
→ Chọn ứng viên cách nhau tối thiểu
→ Hiển thị heatmap
```

Ví dụ mặc định:

- Top 10% cell.
- 10 khu vực đề xuất.
- Khoảng cách tối thiểu 2 km giữa các ứng viên.

> Gợi ý hình: đặt hai heatmap “Sinh viên” và “Thích yên tĩnh” cạnh nhau để cho thấy cùng dữ liệu nhưng nhu cầu khác nhau tạo ra kết quả khác nhau.

---

# Slide 12 — Giao diện, kết quả và hướng phát triển

## Giao diện Streamlit

- 12 hồ sơ mặc định.
- Trọng số từ 0 đến 5.
- Các mode `more`, `less`, `target`, `near`, `far`.
- Thay đổi top phần trăm và số ứng viên.
- Điều chỉnh khoảng cách giữa các ứng viên.
- Xem trung tâm Hà Nội hoặc toàn khu vực.
- Tooltip hiển thị điểm tổng và điểm thành phần.

## Giá trị của dự án

> Biến dữ liệu bản đồ thô thành hệ thống hỗ trợ lựa chọn khu vực theo nhu cầu cá nhân.

## Giới hạn hiện tại

- Chưa có giá thuê nhà và dữ liệu dân cư.
- Chưa tính thời gian di chuyển theo mạng đường.
- `quietness` là chỉ số đại diện, không phải dữ liệu tiếng ồn thực tế.
- Model chưa học từ phản hồi người dùng.
- Giao diện hiện đọc cố định dữ liệu `29_3`.

## Hướng phát triển

- Bổ sung giá thuê và dữ liệu dân số.
- Tính thời gian đi bộ hoặc đi xe thực tế.
- Cho phép chọn tỉnh/thành trên giao diện.
- Thu thập phản hồi để điều chỉnh hoặc học trọng số.

---

# Gợi ý thời lượng thuyết trình

| Phần                               | Thời lượng |
| ----------------------------------- | ------------: |
| Bài toán và mục tiêu           |       1 phút |
| Nguồn dữ liệu                    |       1 phút |
| Pipeline tạo Parquet               |       3 phút |
| Model đánh giá                   |    2–3 phút |
| Giao diện và kết quả            |       2 phút |
| Giới hạn và hướng phát triển |       1 phút |

Tổng thời lượng phù hợp: khoảng 8–10 phút.

Các slide nên tập trung trình bày kỹ: 3, 8, 9, 10 và 11. Không nên đưa nhiều code lên slide; chỉ giữ luồng dữ liệu, tên feature quan trọng và công thức chính.
