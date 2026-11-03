# 10 — Khám phá dữ liệu bằng notebook

## Mục tiêu

Notebook chỉ đọc `cell_features.parquet`; không chạy lại OSM, Overture, grid hoặc road overlay.

## 1. Tìm project root và đọc dữ liệu

Đoạn sau chạy được cả từ project root và thư mục `notebook/`:

```python
from pathlib import Path
import geopandas as gpd

current = Path.cwd().resolve()
project_root = (
    current.parent
    if current.name.lower() == "notebook"
    else current
)

feature_path = (
    project_root
    / "data"
    / "processed"
    / "29_3"
    / "cell_features.parquet"
)

features = gpd.read_parquet(feature_path)
print(features.shape)
print(features.crs)
features.head()
```

Kết quả hiện tại của `29_3` là `(85249, 135)`.

## 2. Kiểm tra chất lượng

```python
assert features["cell_id"].is_unique
assert features["cell_id"].notna().all()
assert features.geometry.notna().all()

features.isna().sum().sort_values(ascending=False).head(20)
```

Nearest có thể thiếu nếu vùng không có category tương ứng. Count và road feature phải không âm:

```python
numeric_counts = [
    column
    for column in features.columns
    if "count" in column
    or "road_length" in column
    or "road_density" in column
]

assert features[numeric_counts].ge(0).all().all()
```

## 3. Thống kê một cột

```python
column = "food_and_drink_count_200m"

features[column].describe(
    percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]
)
```

Trung bình và trung vị:

```python
features[column].agg(["mean", "median", "min", "max"])
```

## 4. Tìm vùng cao nhất

```python
top_food = features.nlargest(
    20,
    "food_and_drink_count_200m",
)[
    [
        "cell_id",
        "food_and_drink_count_200m",
        "geometry",
    ]
]

top_food
```

## 5. Vẽ heatmap một cột

```python
features.plot(
    column="food_and_drink_count_200m",
    cmap="YlOrRd",
    legend=True,
    figsize=(12, 12),
    edgecolor="none",
)
```

Zoom trung tâm Hà Nội trong CRS UTM 48N:

```python
ax = features.plot(
    column="food_and_drink_count_200m",
    cmap="YlOrRd",
    legend=True,
    figsize=(12, 12),
    edgecolor="none",
)

ax.set_xlim(565_000, 605_000)
ax.set_ylim(2_305_000, 2_345_000)
ax.set_axis_off()
```

Hoặc lọc trước khi vẽ:

```python
central = features.cx[
    565_000:605_000,
    2_305_000:2_345_000,
]
```

## 6. So sánh nhiều feature

```python
columns = [
    "food_and_drink_count_200m",
    "services_and_business_count_200m",
    "shopping_count_200m",
    "road_density_1000m_km_per_km2",
]

features[columns].corr()
```

Vẽ correlation heatmap:

```python
import matplotlib.pyplot as plt

correlation = features[columns].corr()

fig, ax = plt.subplots(figsize=(8, 6))
image = ax.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(columns)), columns, rotation=45, ha="right")
ax.set_yticks(range(len(columns)), columns)
fig.colorbar(image, ax=ax)
plt.tight_layout()
```

## 7. Phân phối lệch

POI count có phân phối lệch mạnh. Khi vẽ histogram nên dùng `log1p` hoặc giới hạn percentile:

```python
import numpy as np

np.log1p(features[column]).hist(bins=50)
```

Không dùng min-max trực tiếp khi một số cell trung tâm có giá trị cực lớn.

## 8. Đánh giá khu vực

```python
from ady201.evaluation import SuitabilityModel

model = SuitabilityModel(features)

preferences = {
    "food": {
        "mode": "target",
        "weight": 3,
        "min": 1,
        "max": 10,
    },
    "services": 5,
    "hospital": 5,
    "quietness": 4,
    "student_activity": 4,
}

result = model.evaluate(preferences)
```

Chỉ vẽ các cell được khuyến nghị:

```python
result[result["recommended"]].plot(
    column="suitability_score",
    cmap="YlOrRd",
    legend=True,
    figsize=(12, 12),
)
```

## 9. Clustering tùy chọn

Clustering không nằm trong pipeline chính. Nếu thử nghiệm, chỉ dùng trên các cột đã chuẩn hóa và lưu sang file mới, không ghi đè `cell_features.parquet`.

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

X = features[columns].fillna(0)
X_scaled = StandardScaler().fit_transform(X)

features["cluster"] = KMeans(
    n_clusters=5,
    random_state=42,
    n_init="auto",
).fit_predict(X_scaled)
```

`scikit-learn` không nằm trong dependency mặc định; chỉ cài khi thực sự dùng phần này.

## Hoàn thành khi

- Đọc được GeoParquet mà không chạy lại pipeline.
- Giải thích được phân phối và missing của feature được chọn.
- Xác định được top cell và vẽ được bản đồ.
- Không sửa hoặc ghi đè dữ liệu nguồn.
