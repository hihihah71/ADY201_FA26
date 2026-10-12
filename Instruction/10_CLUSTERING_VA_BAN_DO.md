# Giai đoạn 10 — Clustering và bản đồ

## Mục tiêu

Phân nhóm các cell có đặc điểm đô thị giống nhau và trình bày kết quả bằng bản đồ dễ hiểu.

## Cần có trước

- `cell_features.parquet` từ giai đoạn 09.
- Data dictionary cho toàn bộ feature.

## Khái niệm đơn giản

- **Scaling**: đưa các feature về thang đo gần nhau.
- **K-Means**: chia các hàng dữ liệu thành `k` nhóm.
- **Silhouette score**: một chỉ số tham khảo để đánh giá cách chia nhóm.
- **Cluster profile**: giá trị trung bình của từng feature trong mỗi nhóm.

## Luồng

```text
cell features
     ↓ xử lý missing + scaling
model features
     ↓ K-Means với vài giá trị k
cluster + profile
     ↓
bản đồ + bảng tóm tắt
```

## Các bước thực hiện

1. Chọn danh sách feature dùng cho clustering trong config.
2. Xử lý missing theo quy tắc đã ghi rõ.
3. Scale feature trước khi chạy K-Means.
4. Chạy một số giá trị `k` nhỏ và lưu metric.
5. Chọn `k` bằng metric kết hợp với khả năng giải thích.
6. Tạo cluster profile rồi mới đặt tên nhóm.
7. Ghép cluster về geometry cell.
8. Tạo bản đồ HTML và ảnh PNG.
9. Viết bảng tóm tắt kết quả, không suy diễn quan hệ nhân quả.

## File cần tạo hoặc sửa

```text
src/ady201/clustering.py
src/ady201/maps.py
src/ady201/reports.py
src/ady201/main.py
config/clustering.json
pyproject.toml
```

Bản đồ cần có:

- Mật độ POI.
- Mức đầy đủ dịch vụ.
- Accessibility tới dịch vụ thiết yếu.
- Mật độ đường và giao lộ.
- Khu vực dịch vụ cao nhưng kết nối đường thấp.
- Cluster.
- Các score tổng hợp.

Lệnh mục tiêu:

```powershell
ady201 build-analysis --region hanoi --snapshot <snapshot_id>
```

## Quy tắc

- Không đưa `cell_id`, tên vùng hoặc tọa độ trực tiếp vào K-Means cơ bản.
- Luôn scale feature trước K-Means.
- Không chọn `k` chỉ vì silhouette cao nhất.
- Cluster được huấn luyện riêng trong một tỉnh không so số nhãn trực tiếp với tỉnh khác.
- Bản đồ phải có title, legend, đơn vị, snapshot và nguồn dữ liệu.

## Cần học trước

- StandardScaler hoặc RobustScaler.
- K-Means.
- Silhouette score.
- Đọc cluster profile.
- Choropleth/hexagon map.

## Tìm hiểu thêm

- Từ khóa: `scikit-learn KMeans StandardScaler`.
- Từ khóa: `silhouette score interpretation`.
- Từ khóa: `GeoPandas explore map`.
- Từ khóa: `PCA visualization`; chỉ dùng để quan sát nếu cần.

## Phân công

### Thành

- Kiểm tra feature đầu vào và score tổng hợp.
- Viết bảng thống kê cluster bằng DuckDB.

### Hiếu

- Kiểm tra cách diễn giải feature đường và accessibility.
- Xác nhận bản đồ không gian khớp graph/boundary.

### Quang

- Chạy scaling, K-Means và tạo cluster profile.
- Tạo bản đồ và report theo template thống nhất.

## Đầu ra

```text
data/models/{snapshot_id}/{region_id}/within_region_model.joblib
data/models/{snapshot_id}/{region_id}/model_metadata.json
outputs/{snapshot_id}/{region_id}/maps/*.html
outputs/{snapshot_id}/{region_id}/figures/*.png
outputs/{snapshot_id}/{region_id}/tables/cluster_profile.csv
```

## Hoàn thành khi

- Mỗi cluster có mô tả dựa trên feature thật.
- Bản đồ có đầy đủ title, legend và đơn vị.
- Chạy lại cùng config và random seed cho cùng kết quả.
- Kết luận chỉ mô tả mối liên hệ, không khẳng định nguyên nhân.
