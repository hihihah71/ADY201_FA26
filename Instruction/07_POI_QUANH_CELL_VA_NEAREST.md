# 07 — POI quanh cell và khoảng cách gần nhất

## Nguồn và cấu hình

- Nguồn: `data/raw/overture/vietnam_places.parquet`.
- Group/category: `config/categories.json`.
- 13 group Overture.
- 22 category quan trọng.
- Bán kính: 100, 200, 500, 1000, 2000, 5000 m.

## Hàm điều phối

```python
poi_features = get_cell_pois(
    boundary,
    OVERTURE_GROUPS,
    cell_points,
)
```

`get_cell_pois()` chỉ điều phối các bước nhỏ trong `poi.py`.

## 1. Đọc POI trong boundary

`get_pois()` dùng bbox filter khi đọc Parquet, sau đó clip chính xác và loại địa điểm đóng vĩnh viễn.

## 2. Gán POI vào cell

`assign_pois_to_cells()` dùng `gpd.sjoin_nearest()` giữa POI và polygon. Sau join, mỗi `overture_id` chỉ giữ một cell để tránh đếm trùng ở ranh giới.

Các feature trực tiếp:

```text
poi_count
arts_and_entertainment_count
...
travel_and_transportation_count
```

## 3. Count theo bán kính

Với mỗi group, code tạo `scipy.spatial.cKDTree` và đếm POI quanh representative point:

```text
food_and_drink_count_100m
food_and_drink_count_200m
food_and_drink_count_500m
food_and_drink_count_1000m
food_and_drink_count_2000m
food_and_drink_count_5000m
```

Mẫu này áp dụng cho cả 13 group.

## 4. Nearest theo group

```text
nearest_food_and_drink_m
nearest_health_care_m
nearest_education_m
...
```

## 5. Nearest category quan trọng

22 category gồm hospital, pharmacy, school, restaurant, grocery store, bus station, ATM, bank, police station, park và các category liên quan.

Ví dụ:

```text
nearest_hospital_m
nearest_school_m
nearest_college_university_m
nearest_grocery_store_m
nearest_park_m
```

## Khi không có POI

- Count được trả về 0.
- Nearest được trả về `NaN`.
- `feature_process()` chỉ fill các cột count/road, không biến nearest thiếu thành 0.

Khoảng cách 0 có nghĩa là POI ở ngay representative point; không được dùng 0 để biểu diễn “không có POI”.

## Kiểm tra

```python
assert poi_features["cell_id"].is_unique
assert poi_features.filter(like="_count").ge(0).all().all()
```

## Feature dùng trong evaluation

Model hiện dùng count 200 m cho food, services, shopping và education; nearest cho trường, bệnh viện, thực phẩm, công viên; road density dùng 1000 m.
