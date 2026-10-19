# Giai đoạn 10 — Clustering và bản đồ (tùy chọn)

## Nhiệm vụ tổng quát

Dùng bảng feature đã hoàn thành để phân nhóm cell và vẽ bản đồ. Đây là phần sau cùng, không được làm trước khi pipeline dữ liệu chạy đúng.

## Luồng

```text
cell_features.parquet
        ├── chọn feature → scale → K-Means → cluster
        └── chọn một cột → vẽ choropleth/heatmap
```

## Những thứ cần thay đổi

- Không sửa cách tạo POI/road feature.
- Có thể viết notebook riêng để thử trước.
- Chỉ chuyển code ổn định vào `analysis.py` hoặc một file `reporting.py`.

## Phần A — Bản đồ trước

Vẽ từng cột dễ giải thích:

- `hospital_count_1000m`.
- `nearest_hospital_m`.
- `road_density_1000m_km_per_km2`.

Ví dụ:

```python
features.plot(
    column="hospital_count_1000m",
    legend=True,
    cmap="YlOrRd",
)
```

Kiểm tra cell giá trị cao/thấp có hợp lý khi đối chiếu với bản đồ nền.

## Phần B — Clustering cơ bản

Chọn ít cột, tránh đưa nhiều feature gần như trùng nhau vào lần đầu:

```python
model_columns = [
    "hospital_count_1000m",
    "school_count_1000m",
    "supermarket_count_1000m",
    "transit_count_1000m",
    "road_density_1000m_km_per_km2",
]
```

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

X = features[model_columns].fillna(0)
X_scaled = StandardScaler().fit_transform(X)
features["cluster"] = KMeans(n_clusters=4, random_state=42).fit_predict(X_scaled)
```

Sau đó tính trung bình feature theo cluster để đặt tên mô tả, ví dụ “dịch vụ cao, đường cao”. Không coi số cluster tự có ý nghĩa xếp hạng.

## Output

```text
data/processed/{region_id}/cell_clusters.parquet
reports/{region_id}/hospital_1000m.png
reports/{region_id}/road_density_1000m.png
reports/{region_id}/clusters.png
```

## Kiểm tra kết quả

- Không đưa `cell_id`, `region_id` hoặc geometry vào mô hình.
- Feature được scale trước K-Means.
- Dùng `random_state` để chạy lại có cùng kết quả.
- Mỗi cluster có bảng trung bình feature để giải thích.

## Kiến thức cần học

- Choropleth map và color scale.
- StandardScaler, K-Means và cluster profile.
- Vì sao clustering là mô tả nhóm, không tự chứng minh quan hệ nhân quả.

Từ khóa tìm thêm: `GeoPandas choropleth`, `scikit-learn StandardScaler KMeans`.

## Phân công

### Thành — trung bình

- Ghép output cluster trở lại cell và kiểm tra có mất hàng không.

### Hiếu — trung bình/khó

- Chọn feature, scale, chạy K-Means và lập cluster profile.

### Quang — dễ/trung bình

- Vẽ ba bản đồ, chú giải màu và ghi nhận xét dễ hiểu.

Review chéo: mỗi người giải thích một cluster bằng các con số, không chỉ nhìn màu bản đồ.

## Hoàn thành khi

- Có bản đồ cho feature gốc trước khi có bản đồ cluster.
- Mỗi cell có một cluster và mỗi cluster có mô tả bằng giá trị trung bình.
