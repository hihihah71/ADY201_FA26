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

### Bước 1 — Chốt feature dùng cho clustering

- Khai báo danh sách cột trong `config/clustering.json` thay vì chọn tự động mọi cột số.
- Chỉ chọn các feature có ý nghĩa đô thị và đã được giải thích trong data dictionary.
- Không đưa `cell_id`, `region_id`, tọa độ, geometry hoặc score được tạo từ chính các feature đã chọn nếu việc đó làm lặp thông tin.
- Ghi một câu lý do cho từng feature được giữ hoặc loại.

Kết quả cần thấy: có một danh sách đầu vào cố định và người khác biết vì sao mỗi cột có mặt.

### Bước 2 — Xử lý missing trước khi đưa vào model

- Thống kê số null theo từng cột và theo nguyên nhân từ giai đoạn 09.
- Count bằng null do left join có thể đổi thành `0` sau khi xác minh; unreachable không được tự động đổi thành `0` phút.
- Chọn quy tắc loại hàng hoặc điền giá trị cho từng feature trong config/metadata.
- Lưu cờ missing nếu bản thân việc thiếu dữ liệu có ý nghĩa.

Kết quả cần thấy: ma trận đưa vào model không còn NaN và không làm sai nghĩa accessibility.

### Bước 3 — Scale các feature

- Tách `cell_id` và metadata khỏi ma trận số trước khi scale.
- Dùng `StandardScaler` khi phân bố tương đối ổn; cân nhắc `RobustScaler` khi có nhiều outlier.
- Gọi `fit_transform()` trên tập cell dùng để huấn luyện và lưu scaler cùng model.
- Kiểm tra trung bình/độ phân tán sau scale để phát hiện cột hằng hoặc cột lỗi.

Kết quả cần thấy: feature có đơn vị lớn không tự động chi phối khoảng cách của K-Means.

### Bước 4 — Chạy thử nhiều giá trị `k`

- Chọn dải nhỏ, ví dụ `k = 2..6`, và bảo đảm số cell lớn hơn `k`.
- Với mỗi `k`, chạy K-Means với cùng `random_state` và khai báo `n_init` rõ ràng.
- Lưu inertia, silhouette score, số cell mỗi cluster và thời gian chạy.
- Không ghi đè kết quả giữa các `k`; lưu vào một bảng so sánh.

Kết quả cần thấy: có đủ bằng chứng để so sánh vài cách chia nhóm thay vì chọn `k` tùy ý.

### Bước 5 — Chọn `k` có thể giải thích

- Xem silhouette score và xu hướng inertia, nhưng không dùng một metric làm quyết định duy nhất.
- Loại phương án tạo cluster quá nhỏ hoặc không có ý nghĩa thực tế.
- Vẽ bản đồ nháp để xem cluster có phải chỉ phản ánh lỗi dữ liệu hoặc vùng biên hay không.
- Ghi lý do chọn `k` trong `model_metadata.json`.

Kết quả cần thấy: một người khác có thể lặp lại quyết định chọn số cluster.

### Bước 6 — Lập profile rồi đặt tên cluster

- Ghép nhãn cluster với feature chưa scale để số liệu còn đơn vị dễ hiểu.
- Tính trung bình, trung vị và số cell theo cluster.
- So sánh mỗi cluster với toàn vùng, sau đó mới đặt tên mô tả như “dịch vụ cao, kết nối thấp”.
- Giữ cả nhãn số vì tên mô tả có thể thay đổi khi nhóm chỉnh cách diễn giải.

Kết quả cần thấy: tên cluster dựa trên số liệu, không dựa vào màu hoặc vị trí nhìn trên bản đồ.

### Bước 7 — Ghép kết quả về geometry

- Kết quả model chỉ cần `cell_id`, `cluster_id` và các giá trị hỗ trợ.
- Left join vào file hexagon bằng `cell_id` và kiểm tra mỗi cell nhận tối đa một nhãn.
- Giữ cell không được model xử lý với trạng thái rõ ràng, không xóa khỏi bản đồ.
- Ghi `model_version` và `snapshot_id` vào kết quả.

Kết quả cần thấy: số geometry sau join bằng số cell ban đầu.

### Bước 8 — Tạo bộ bản đồ thống nhất

- Tạo từng bản đồ trong danh sách ở phần dưới bằng cùng boundary, màu nền và cách ghi nguồn.
- HTML dùng để xem tương tác; PNG dùng để chèn báo cáo và thuyết trình.
- Mỗi bản đồ phải có title, legend, đơn vị, snapshot, region và nguồn OSM.
- Với accessibility, thể hiện riêng unreachable thay vì tô như thời gian bằng 0.

Kết quả cần thấy: người xem không cần mở code vẫn hiểu màu sắc và thời điểm dữ liệu.

### Bước 9 — Viết phần kết quả và giới hạn

- Tóm tắt số cell, phân bố cluster và các vùng nổi bật bằng con số cụ thể.
- Nêu các phát hiện như khu vực thiếu dịch vụ hoặc dịch vụ cao nhưng mạng đường kém kết nối.
- Ghi giới hạn: chất lượng OSM, tốc độ đi bộ giả định, POI chưa đầy đủ và đường đi chưa xét địa hình.
- Dùng từ “liên quan”, “cùng xuất hiện” thay cho khẳng định nguyên nhân nếu phân tích không chứng minh nhân quả.

Kết quả cần thấy: report liên kết trực tiếp tới bảng và bản đồ đã tạo.

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

## Lỗi thường gặp

- Đưa cột ID hoặc tọa độ vào K-Means và nhận cluster theo vị trí/định danh ngoài ý muốn.
- Không scale nên feature có số lớn nhất quyết định gần như toàn bộ cluster.
- So sánh `cluster 0` giữa hai model riêng và cho rằng chúng là cùng một nhóm.
- Chọn `k` chỉ vì silhouette lớn nhất dù tạo nhóm quá nhỏ hoặc khó giải thích.

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
