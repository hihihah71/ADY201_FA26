# Giai đoạn 10 — Clustering và bản đồ

## Mục tiêu

Phân nhóm khu vực đô thị và trình bày kết quả bằng bản đồ/bảng dễ giải thích.

## Nhiệm vụ tổng quát

- Chuẩn bị feature cho model.
- Chạy within-region K-Means.
- Đánh giá số cluster.
- Profile và đặt tên cluster sau phân tích.
- Tạo bộ bản đồ thống nhất.
- Chuẩn bị thiết kế national model riêng.

## Luồng

```text
Raw feature matrix
    ↓ missing/outlier/scale
Model features
    ↓ K-Means k candidates
Metrics + cluster profiles
    ↓
Maps + summary tables
```

## Những thứ cần thay đổi

Tạo:

```text
src/ady201/models/within_region.py
src/ady201/models/national.py
src/ady201/visualization/maps.py
src/ady201/visualization/reports.py
config/clustering.yaml
```

Bản đồ bắt buộc:

- POI density.
- Service completeness.
- Accessibility đến nhóm thiết yếu.
- Road/intersection density.
- Main-road share.
- High-service/low-connectivity.
- Cluster.
- Composite index.

Quy tắc:

- Scale trước K-Means.
- Không đưa ID/tọa độ trực tiếp vào model baseline.
- Không chọn `k` chỉ dựa vào silhouette.
- Cluster nội tỉnh không so trực tiếp giữa tỉnh.
- National model dùng scaler/model chung và có version.

## Kiến thức cần học

### Bắt buộc

- StandardScaler/RobustScaler.
- K-Means và silhouette.
- Cluster profile.
- Choropleth/hex map.
- Color scale và legend.

### Tìm hiểu sâu bên ngoài

- PCA dùng để quan sát.
- Spatial autocorrelation.
- DBSCAN/HDBSCAN; chỉ phần mở rộng.
- Folium/GeoPandas explore/Plotly.

## Phân công

### Thành

- Review feature definitions và composite score.
- Kiểm tra cluster summary bằng DuckDB.

### Hiếu

- Review road/accessibility interpretation.
- Kiểm tra map route/network.

### Quang

- Owner scaling, K-Means, profiling, maps và report.
- Chuẩn hóa template bản đồ.

### Review

- Thành review dữ liệu.
- Hiếu review ý nghĩa không gian.
- Quang tích hợp feedback.

## Đầu ra

```text
models/within_region_model.*
models/model_metadata.json
maps/*.html
figures/*.png
tables/cluster_profile.csv
```

## Hoàn thành khi

- Cluster có mô tả dựa trên feature.
- Bản đồ có title, legend, unit, snapshot và nguồn.
- Kết luận không suy diễn quan hệ nhân quả.

