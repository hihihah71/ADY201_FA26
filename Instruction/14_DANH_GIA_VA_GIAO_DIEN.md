# 14 — Đánh giá khu vực và giao diện Streamlit

## Mục tiêu

Biến `cell_features.parquet` thành bản đồ gợi ý theo nhu cầu người dùng mà không cần train model học máy.

Model là hệ thống chấm điểm đa tiêu chí có trọng số.

## Tiêu chí

| Tên | Feature nguồn | Mặc định |
|---|---|---|
| `food` | `food_and_drink_count_200m` | more, limit 10 |
| `services` | `services_and_business_count_200m` | more, limit 10 |
| `shopping` | `shopping_count_200m` | more, limit 10 |
| `school` | `nearest_school_m` | near, 1500 m |
| `hospital` | `nearest_hospital_m` | near, 2000 m |
| `grocery` | `nearest_grocery_store_m` | near, 1000 m |
| `park` | `nearest_park_m` | near, 2000 m |
| `transport` | `road_density_1000m_km_per_km2` | more, limit 15 |
| `quietness` | derived | more |
| `student_activity` | derived proxy | less |
| `service_balance` | derived | more |

POI dịch vụ dùng bán kính 200 m để phản ánh khu vực đi bộ gần cell, thay vì làm mọi vùng trung tâm giống nhau ở bán kính lớn.

## Mode

| Mode | Ý nghĩa |
|---|---|
| `more` | Giá trị tăng đến `limit`, sau đó không cộng thêm |
| `less` | Giá trị thấp được điểm cao |
| `target` | Tốt nhất trong `[min, max]`, quá thấp hoặc quá cao đều giảm |
| `near` | Khoảng cách càng gần càng tốt |
| `far` | Khoảng cách càng xa càng tốt |

Điểm `more` bão hòa tại `limit`, nên trung tâm không tiếp tục được thưởng chỉ vì có hàng trăm POI.

## Chỉ số derived

### Quietness

Nghịch đảo của cường độ đô thị, được ước lượng từ food, services, shopping, education trong 200 m và road density 1000 m.

### Student activity

Proxy từ:

- Khoảng cách tới college/university.
- Khoảng cách tới language school.
- Education count 200 m.

Đây không phải dữ liệu nhân khẩu học thực tế.

### Service balance

Kết hợp số lượng services với tỷ trọng services trong nhóm food/services/shopping. Mục tiêu là tìm khu đủ dịch vụ nhưng không nhất thiết là trung tâm POI lớn nhất.

## Ghép điểm

Model dùng weighted geometric mean:

```text
score = exp(sum(weight_i * log(score_i)) / sum(weight_i))
```

Cách này hạn chế một tiêu chí rất cao bù hoàn toàn cho tiêu chí rất thấp.

## Dùng trong Python

```python
from ady201.evaluation import SuitabilityModel

model = SuitabilityModel.from_parquet(
    "data/processed/29_3/cell_features.parquet"
)

preferences = {
    "food": {
        "mode": "target",
        "weight": 3,
        "min": 1,
        "max": 10,
    },
    "services": {
        "mode": "more",
        "weight": 5,
        "limit": 10,
    },
    "hospital": {
        "mode": "near",
        "weight": 5,
        "limit": 2000,
    },
    "quietness": 4,
    "student_activity": 4,
}

result = model.evaluate(preferences, top_quantile=0.9)
```

Output thêm:

```text
score_{criterion}
suitability_score
recommended
```

## Chọn ứng viên tách biệt

```python
candidates = model.select_candidates(
    preferences,
    limit=10,
    minimum_distance_m=2000,
)
```

Sau khi chọn cell tốt nhất, model bỏ qua các cell nằm trong khoảng cách tối thiểu rồi chọn cell tiếp theo. Kết quả không bị dồn thành nhiều ô liền nhau.

## Giao diện Streamlit

```powershell
streamlit run app.py
```

Giao diện hiện có:

- Bốn profile: Sinh viên, Người đi làm, Gia đình có con, Người cao tuổi.
- Điều chỉnh weight, mode và limit/range.
- Top 5–30% cell.
- 5–20 ứng viên.
- Khoảng cách ứng viên 500–5000 m.
- Bản đồ PyDeck với tooltip.
- Chế độ Trung tâm Hà Nội hoặc Toàn khu vực.

Model được cache bằng `st.cache_resource`, nên thay slider không đọc lại Parquet.

## Dữ liệu giao diện

`app.py` hiện cố định:

```text
data/processed/29_3/cell_features.parquet
```

Bbox trung tâm trong CRS EPSG:32648:

```text
x: 565000 -> 605000
y: 2305000 -> 2345000
```

## Chạy kiểm tra

```powershell
python -m compileall -q app.py src/ady201/evaluation.py
streamlit run app.py --server.headless true
```

## Giới hạn

- Profile là preset thiết kế thủ công, chưa học từ lịch sử người dùng.
- Chưa có giá thuê, ngập lụt, chất lượng không khí, độ ồn thật hoặc nhân khẩu học.
- Map chỉ render cell `recommended` để giảm tải trình duyệt.
- Giao diện chưa cho chọn region khác `29_3`.
