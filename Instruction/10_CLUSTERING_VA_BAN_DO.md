# Giai đoạn 10 — Khám phá dữ liệu và trực quan hóa bằng notebook

## Mục tiêu

Tạo notebook `notebook/10_kham_pha_cell_features.ipynb` để đọc kết quả của giai đoạn 09, kiểm tra dữ liệu, trả lời các câu hỏi thống kê và vẽ bản đồ. Notebook chỉ dùng dữ liệu đã xử lý; không sửa logic tạo grid, POI hoặc road feature.

Các phần dưới đây nên được đặt vào các cell riêng trong notebook để có thể chạy và xem kết quả từng bước.

## 1. Import thư viện và tìm thư mục project

Đoạn này chạy được khi Jupyter được mở từ thư mục gốc project hoặc từ thư mục `notebook/`:

```python
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def find_project_root(start=Path.cwd()):
    for path in (start, *start.parents):
        if (path / "pyproject.toml").exists():
            return path
    raise FileNotFoundError("Không tìm thấy thư mục gốc của project")


PROJECT_ROOT = find_project_root()
```

## 2. Đọc `cell_features.parquet`

Dùng `geopandas.read_parquet()` thay vì `pandas.read_parquet()` để giữ geometry và CRS:

```python
region_id = "thanh_hoa"  # thay bằng region_id cần xem

parquet_path = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / region_id
    / "cell_features.parquet"
)

if not parquet_path.exists():
    raise FileNotFoundError(f"Không tìm thấy: {parquet_path}")

features = gpd.read_parquet(parquet_path)
features = features.set_geometry("geometry")

print(f"Số cell: {len(features):,}")
print(f"CRS: {features.crs}")
```

## 3. Xem nhanh cấu trúc dữ liệu

Không hiển thị geometry trong bảng đầu tiên vì chuỗi geometry khá dài:

```python
display(
    features.drop(columns=["geometry", "points"], errors="ignore").head()
)

features.info()
```

Liệt kê các cột số có thể dùng để phân tích:

```python
numeric_columns = features.select_dtypes(include="number").columns.tolist()
numeric_columns
```

Xem thống kê mô tả của tất cả cột số:

```python
summary = features[numeric_columns].describe().T
display(summary)
```

Các cột trong bảng `summary` cho biết số giá trị hợp lệ, trung bình, độ lệch chuẩn, min, max và các phân vị.

## 4. Kiểm tra chất lượng dữ liệu

Kiểm tra khóa, geometry và số lượng giá trị thiếu:

```python
quality = pd.Series({
    "duplicate_cell_id": features["cell_id"].duplicated().sum(),
    "missing_cell_id": features["cell_id"].isna().sum(),
    "missing_geometry": features.geometry.isna().sum(),
    "empty_geometry": features.geometry.is_empty.sum(),
    "invalid_geometry": (~features.geometry.is_valid).sum(),
})

display(quality.to_frame("count"))
```

Chỉ hiển thị những cột có null:

```python
missing = features.isna().sum().sort_values(ascending=False)
display(missing[missing > 0].to_frame("missing_count"))
```

Null ở cột `nearest_*_m` có thể có nghĩa là toàn vùng không có POI thuộc loại đó. Không tự động đổi khoảng cách null thành `0`.

Kiểm tra các feature đáng lẽ không được âm:

```python
feature_columns = [
    column for column in numeric_columns
    if any(key in column for key in ("count", "nearest", "road_length", "road_density"))
]

negative_counts = (features[feature_columns] < 0).sum()
display(negative_counts[negative_counts > 0].to_frame("negative_count"))
```

## 5. Phân tích một cột

Chọn một cột để dùng cho các ví dụ tiếp theo:

```python
column = "hospital_count_1000m"

if column not in features.columns:
    raise KeyError(f"Không có cột {column}")
```

Tính các thống kê thường dùng:

```python
stats = features[column].agg([
    "count", "mean", "median", "std", "min", "max"
])
display(stats)
```

Đếm số cell không có bệnh viện trong bán kính 1.000 m:

```python
zero_cells = features[column].eq(0).sum()
zero_ratio = features[column].eq(0).mean()

print(f"Số cell bằng 0: {zero_cells:,}")
print(f"Tỷ lệ cell bằng 0: {zero_ratio:.1%}")
```

## 6. Tìm cell lớn nhất, nhỏ nhất và top-N

Tìm tất cả cell cùng đạt giá trị lớn nhất, thay vì chỉ lấy một dòng đầu tiên:

```python
max_value = features[column].max()

max_cells = features.loc[
    features[column].eq(max_value),
    ["cell_id", column, "geometry"],
]

display(max_cells.drop(columns="geometry"))
```

Xem 10 cell có giá trị cao nhất:

```python
top_10 = features.nlargest(10, column)[["cell_id", column]]
display(top_10)
```

Lấy các cell cao hơn mức trung bình:

```python
above_average = features.loc[
    features[column] > features[column].mean(),
    ["cell_id", column],
].sort_values(column, ascending=False)

display(above_average.head(10))
```

Vì mỗi dòng là một grid cell, “vùng lớn nhất” ở đây nghĩa là cell có giá trị feature lớn nhất, không nhất thiết là một quận hoặc huyện hành chính.

## 7. Xem phân phối của một cột

Histogram giúp phát hiện dữ liệu lệch, có nhiều số `0` hoặc có outlier:

```python
ax = features[column].plot.hist(bins=30, figsize=(8, 4))
ax.set(title=f"Phân phối {column}", xlabel=column, ylabel="Số cell")
plt.show()
```

Boxplot giúp xem trung vị và các giá trị bất thường:

```python
ax = features[[column]].plot.box(figsize=(5, 5))
ax.set_title(f"Boxplot của {column}")
plt.show()
```

## 8. Vẽ bản đồ cho một cột

Đây là spatial heatmap dạng choropleth: màu của mỗi cell biểu diễn độ lớn của feature.

```python
fig, ax = plt.subplots(figsize=(10, 10))

features.plot(
    ax=ax,
    column=column,
    legend=True,
    cmap="YlOrRd",
    edgecolor="grey",
    linewidth=0.15,
    missing_kwds={"color": "lightgrey", "label": "Thiếu dữ liệu"},
)

ax.set_title("Số bệnh viện trong bán kính 1.000 m")
ax.set_axis_off()
plt.show()
```

Đánh dấu các cell có giá trị lớn nhất trên bản đồ:

```python
fig, ax = plt.subplots(figsize=(10, 10))

features.plot(ax=ax, column=column, cmap="YlOrRd", legend=True)
max_cells.boundary.plot(ax=ax, color="cyan", linewidth=2)

ax.set_title(f"{column} — viền xanh là cell lớn nhất")
ax.set_axis_off()
plt.show()
```

Không so sánh màu giữa hai bản đồ nếu chúng dùng thang màu hoặc khoảng giá trị khác nhau.

## 9. Vẽ nhiều cột cạnh nhau

Chỉ những cột thực sự tồn tại mới được đưa vào hình:

```python
requested_columns = [
    "hospital_count_1000m",
    "school_count_1000m",
    "nearest_hospital_m",
    "road_density_1000m_km_per_km2",
]
map_columns = [c for c in requested_columns if c in features.columns]

fig, axes = plt.subplots(2, 2, figsize=(16, 14))
axes = axes.ravel()

for ax, map_column in zip(axes, map_columns):
    features.plot(
        ax=ax,
        column=map_column,
        legend=True,
        cmap="YlOrRd",
        linewidth=0,
    )
    ax.set_title(map_column)
    ax.set_axis_off()

for ax in axes[len(map_columns):]:
    ax.set_visible(False)

plt.tight_layout()
plt.show()
```

Nên so sánh các bản đồ theo câu hỏi cụ thể, ví dụ:

- Nơi có mật độ đường cao có nhiều dịch vụ hơn không?
- Cell có nhiều bệnh viện có đồng thời nhiều trường học không?
- Khu vực xa bệnh viện tập trung ở phần nào của tỉnh?

## 10. Heatmap tương quan giữa nhiều cột

Heatmap này không phải bản đồ địa lý. Nó cho biết hai feature có xu hướng tăng hoặc giảm cùng nhau hay không.

```python
requested_columns = [
    "hospital_count_1000m",
    "school_count_1000m",
    "supermarket_count_1000m",
    "nearest_hospital_m",
    "road_density_1000m_km_per_km2",
]
corr_columns = [c for c in requested_columns if c in features.columns]
corr = features[corr_columns].corr()

fig, ax = plt.subplots(figsize=(8, 6))
image = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)

ax.set_xticks(range(len(corr_columns)), corr_columns, rotation=45, ha="right")
ax.set_yticks(range(len(corr_columns)), corr_columns)

for row in range(len(corr_columns)):
    for col in range(len(corr_columns)):
        ax.text(col, row, f"{corr.iloc[row, col]:.2f}", ha="center", va="center")

fig.colorbar(image, ax=ax, label="Correlation")
ax.set_title("Tương quan giữa các feature")
plt.tight_layout()
plt.show()
```

Correlation gần `1` hoặc `-1` cho thấy liên hệ tuyến tính mạnh, nhưng không chứng minh quan hệ nhân quả.

## 11. Xem quan hệ giữa hai cột

Scatter plot giúp kiểm tra chi tiết hơn một cặp feature:

```python
x_column = "road_density_1000m_km_per_km2"
y_column = "hospital_count_1000m"

ax = features.plot(
    kind="scatter",
    x=x_column,
    y=y_column,
    alpha=0.4,
    figsize=(7, 5),
)
ax.set_title(f"{x_column} và {y_column}")
plt.show()
```

## 12. Tạo heatmap từ nhiều chỉ số

Có thể tạo một score khám phá bằng cách chuẩn hóa các feature về khoảng `0–1` rồi lấy trung bình. Với cột `nearest_*`, khoảng cách thấp hơn được coi là tiếp cận tốt hơn nên thang điểm được đảo lại.

```python
score_columns = [
    "hospital_count_1000m",
    "school_count_1000m",
    "supermarket_count_1000m",
    "nearest_hospital_m",
    "road_density_1000m_km_per_km2",
]
score_columns = [c for c in score_columns if c in features.columns]

normalized = pd.DataFrame(index=features.index)

for score_column in score_columns:
    values = features[score_column]
    value_range = values.max() - values.min()
    scaled = (values - values.min()) / value_range if value_range else 0.0

    if score_column.startswith("nearest_"):
        scaled = 1 - scaled

    normalized[score_column] = pd.Series(scaled, index=features.index).fillna(0)

features["exploratory_score"] = normalized.mean(axis=1)
```

Vẽ score tổng hợp:

```python
fig, ax = plt.subplots(figsize=(10, 10))

features.plot(
    ax=ax,
    column="exploratory_score",
    legend=True,
    cmap="viridis",
)

ax.set_title("Heatmap chỉ số tiếp cận dịch vụ — bản khám phá")
ax.set_axis_off()
plt.show()
```

`exploratory_score` chỉ dùng để khám phá. Trước khi dùng làm kết luận chính thức, cần giải thích việc chọn feature, chiều tốt/xấu và trọng số của từng feature.

## 13. Clustering tùy chọn

Clustering dùng nhiều feature để nhóm các cell có đặc điểm tương tự. Cần cài `scikit-learn` trong môi trường chạy notebook.

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

model_columns = [
    "hospital_count_1000m",
    "school_count_1000m",
    "supermarket_count_1000m",
    "road_density_1000m_km_per_km2",
]
model_columns = [c for c in model_columns if c in features.columns]

X = features[model_columns].fillna(0)
X_scaled = StandardScaler().fit_transform(X)

model = KMeans(n_clusters=4, random_state=42, n_init=10)
features["cluster"] = model.fit_predict(X_scaled)
```

Xem số cell và trung bình feature trong từng cluster:

```python
cluster_sizes = features["cluster"].value_counts().sort_index()
cluster_profile = features.groupby("cluster")[model_columns].mean().round(2)

display(cluster_sizes.to_frame("cell_count"))
display(cluster_profile)
```

Vẽ bản đồ cluster:

```python
fig, ax = plt.subplots(figsize=(10, 10))

features.plot(
    ax=ax,
    column="cluster",
    categorical=True,
    legend=True,
    cmap="tab10",
)

ax.set_title("Nhóm cell theo đặc điểm dịch vụ và đường")
ax.set_axis_off()
plt.show()
```

Số cluster chỉ là mã nhóm, không phải thứ hạng tốt–xấu. Phải xem `cluster_profile` trước khi mô tả ý nghĩa từng nhóm.

## 14. Lưu hình và kết quả tùy chọn

Tạo thư mục report:

```python
report_dir = PROJECT_ROOT / "reports" / region_id
report_dir.mkdir(parents=True, exist_ok=True)
```

Khi cần lưu một biểu đồ, gọi `savefig()` trước `show()`:

```python
fig.savefig(
    report_dir / "hospital_count_1000m.png",
    dpi=200,
    bbox_inches="tight",
)
plt.show()
```

Nếu đã chạy clustering, lưu sang file mới và không ghi đè `cell_features.parquet`:

```python
cluster_path = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / region_id
    / "cell_clusters.parquet"
)

features.to_parquet(cluster_path, index=False)
```

## Câu hỏi nên trả lời trong notebook

- Mỗi feature có trung bình, trung vị, min và max bằng bao nhiêu?
- Bao nhiêu phần trăm cell có count bằng `0`?
- Cell nào có giá trị cao nhất và các cell đó nằm ở đâu?
- Phân phối có bị lệch hoặc có outlier không?
- Khu vực nào có khả năng tiếp cận bệnh viện thấp?
- Mật độ đường có liên hệ với số lượng dịch vụ không?
- Các loại dịch vụ có tập trung tại cùng khu vực không?
- Các cluster khác nhau như thế nào theo giá trị trung bình?

## Output đề xuất

```text
notebook/10_kham_pha_cell_features.ipynb
reports/{region_id}/hospital_count_1000m.png
reports/{region_id}/road_density_1000m.png
reports/{region_id}/exploratory_score.png
reports/{region_id}/clusters.png
data/processed/{region_id}/cell_clusters.parquet
```

## Hoàn thành khi

- Notebook chạy tuần tự từ đầu đến cuối mà không phụ thuộc biến được tạo thủ công ở cell khác.
- Đã kiểm tra khóa, geometry, CRS, null và giá trị âm.
- Có thống kê mô tả và danh sách cell cực trị cho ít nhất một feature.
- Có histogram hoặc boxplot để xem phân phối.
- Có bản đồ cho một feature gốc và bản đồ so sánh nhiều feature.
- Có nhận xét bằng số liệu, không chỉ dựa vào màu trên bản đồ.
- Nếu dùng score hoặc clustering, đã ghi rõ đây là kết quả khám phá và giải thích cách tạo.
