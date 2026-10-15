# Tổng quan lộ trình dự án

## Mục tiêu cuối

Người dùng chỉ cần nhập khu vực cần phân tích:

```powershell
ady201 run-region --region hanoi
ady201 run-region --region danang
ady201 run-all --resume
```

Python tự đọc dữ liệu, gọi DuckDB, xử lý mạng đường và tạo kết quả. Không cần mở pgAdmin hoặc import dữ liệu thủ công.

## Cách dùng bộ Instruction

1. Làm lần lượt từ giai đoạn 01 đến 12.
2. Đọc mục **Cần học trước** của giai đoạn đang làm.
3. Mỗi người hoàn thành nhiệm vụ của mình rồi đổi phần để review chéo.
4. Chỉ sang giai đoạn tiếp theo khi tất cả mục **Hoàn thành khi** đã đạt.
5. Nếu gặp thuật ngữ lạ, dùng các từ khóa trong mục **Tìm hiểu thêm** để tự học.

Không cần học toàn bộ công nghệ ngay từ đầu.

Trong mỗi bước, đọc theo bốn câu hỏi:

1. **Mở hoặc tạo file nào?** Xem mục “File cần tạo hoặc sửa”.
2. **Phải làm gì?** Làm lần lượt các bullet trong bước, không làm tắt sang bước sau.
3. **Kết quả nằm ở đâu?** Xem dòng “Kết quả cần thấy” và mục “Đầu ra”.
4. **Biết đúng hay sai bằng cách nào?** Chạy lệnh được ghi trong file và đối chiếu mục “Hoàn thành khi”.

Nếu một bước chưa có “Kết quả cần thấy”, chưa nên giao output đó cho người tiếp theo.

## Trạng thái hiện tại và việc cần làm tiếp

| Giai đoạn | Trạng thái | Việc tiếp theo |
|---|---|---|
| 01 | Đã hoàn thành | Giữ cấu trúc hiện tại |
| 02 | Chưa hoàn thành | Sửa ba file config, viết loader và `list-regions` |
| 03 | Hoàn thành một phần | Đồng bộ `regions.json` vào DuckDB |
| 04–12 | Kế hoạch | Chưa tạo code trước khi giai đoạn phụ thuộc hoàn thành |

Vì vậy, việc nên làm ngay là hoàn thành giai đoạn 02 rồi hoàn tất bước đồng bộ region của giai đoạn 03. Không bắt đầu tải và xử lý PBF trước khi hai giai đoạn này chạy ổn.

## Python và DuckDB dùng để làm gì

| Công cụ | Trách nhiệm |
|---|---|
| Python | Dùng Pyrosm đọc PBF, gọi từng bước, xử lý bản đồ, graph, Dijkstra và clustering |
| DuckDB | Chạy SQL, lưu metadata/trạng thái, tổng hợp bảng và kiểm tra dữ liệu |
| Parquet/GeoParquet | Lưu bảng lớn và dữ liệu có geometry |
| GraphML | Lưu graph đường để dùng lại |

SQL được Python tự chạy. Người dùng không phải mở công cụ quản trị database.

## Cấu trúc code thống nhất

Giữ module dạng phẳng để dễ tìm:

```text
src/ady201/
├── __init__.py
├── __main__.py
├── main.py
├── poi.py
├── network.py
├── settings.py
├── regions.py
├── database.py
├── osm_input.py
├── boundaries.py
├── hexagons.py
├── snap.py
├── accessibility.py
├── feature_matrix.py
├── clustering.py
├── pipeline.py
└── batch.py
```

Không cần tạo đủ các file trên ngay. Mỗi giai đoạn chỉ thêm file mà giai đoạn đó sử dụng.

## Luồng dữ liệu tổng thể

```text
Vietnam OSM PBF + ranh giới khu vực
                ↓
        POI + mạng đường
                ↓
       hexagon cho từng vùng
                ↓
       snap POI/cell vào đường
                ↓
 Dijkstra + đặc trưng dịch vụ/đường
                ↓
      chỉ số + clustering
                ↓
        bản đồ + báo cáo
```

## Danh sách giai đoạn

| Giai đoạn | Việc chính | Kết quả |
|---|---|---|
| [01](01_CHUAN_HOA_PROJECT.md) | Chuẩn hóa project | Package và CLI cơ bản |
| [02](02_CONFIG_VA_REGION_REGISTRY.md) | Tách tham số khỏi code | Thêm tỉnh/thành không sửa source |
| [03](03_DUCKDB_CO_BAN.md) | Tạo DuckDB cơ bản | Connection và bảng region |
| [04](04_PBF_CO_DINH.md) | Chuẩn bị PBF | Một file OSM cố định cho toàn dự án |
| [05](05_POI_TOAN_QUOC.md) | Chuẩn hóa POI toàn quốc | Một bộ POI dùng chung |
| [06](06_PYROSM_VA_ROAD_GRAPH.md) | Pyrosm tạo graph đường | Walking/driving graph |
| [07](07_HEXAGON_VA_SPATIAL_JOIN.md) | Tạo ô phân tích | POI được gán vào từng ô |
| [08](08_SNAP_VA_ACCESSIBILITY.md) | Tính đường đi | Thời gian tới dịch vụ gần nhất |
| [09](09_FEATURES_VA_CHI_SO.md) | Tạo đặc trưng và chỉ số | Một hàng dữ liệu cho mỗi ô |
| [10](10_CLUSTERING_VA_BAN_DO.md) | Phân nhóm và trực quan hóa | Cluster, heatmap và báo cáo |
| [11](11_TU_DONG_HOA_MOT_REGION.md) | Ghép thành một lệnh | `run-region` |
| [12](12_RUN_ALL_TOAN_QUOC.md) | Chạy toàn quốc | `run-all` với một PBF cố định |

## Từ điển ngắn

- **POI**: địa điểm dịch vụ như trường học, bệnh viện, siêu thị.
- **CLI**: lệnh chạy chương trình từ terminal, ví dụ `ady201 --help`.
- **DuckDB**: database chạy trực tiếp trong Python và lưu thành một file.
- **Region**: một khu vực cần phân tích, thường là một tỉnh hoặc thành phố.
- **PBF**: file OpenStreetMap đã nén, chứa node, way và relation.
- **Pyrosm**: thư viện Python đọc PBF và chuyển mạng đường thành node/edge/graph.
- **Node**: một điểm trong mạng đường.
- **Edge**: đoạn đường nối hai node.
- **Graph**: tập hợp node và edge.
- **Snap**: gán một địa điểm vào node đường gần nhất.
- **Dijkstra**: thuật toán tìm đường có tổng trọng số nhỏ nhất.
- **CRS**: hệ tọa độ dùng để đặt và đo geometry.
- **Geometry**: hình học không gian dạng điểm, đường hoặc vùng.
- **Hexagon/cell**: ô không gian dùng làm đơn vị phân tích.
- **Representative point**: một điểm đại diện nằm bên trong polygon.
- **Spatial join**: ghép dữ liệu dựa trên vị trí thay vì dựa trên ID.
- **GeoParquet**: file Parquet có thêm cột geometry.
- **GraphML**: định dạng file dùng để lưu graph.
- **Schema**: danh sách cột, kiểu dữ liệu và quy tắc của một bảng.
- **Metadata**: thông tin mô tả dữ liệu như nguồn, phiên bản và đường dẫn.
- **Feature**: một cột số mô tả cell, ví dụ mật độ POI.
- **Artifact**: file kết quả của một bước để bước sau sử dụng.
- **Resume**: chạy tiếp từ phần chưa hoàn thành.

## Phân công tổng quát

### Thành — trung bình đến khó

- POI, DuckDB, SQL, dữ liệu dịch vụ và kiểm tra chất lượng.

### Hiếu — trung bình đến khó

- PBF, ranh giới, graph, snap, Dijkstra và dữ liệu đường.

### Quang — dễ đến trung bình

- Config, kiểm tra đầu ra, clustering, bản đồ và báo cáo.

## Quy tắc chung

1. Không viết riêng logic cho Hà Nội hoặc Đà Nẵng trong source.
2. Không dùng đường dẫn tuyệt đối như `D:\...`.
3. Không commit PBF, GraphML, DuckDB và Parquet lớn.
4. Không chạy SQL thủ công; Python phải tự chạy SQL cần thiết.
5. Không tự viết Dijkstra nếu thư viện đã có hàm phù hợp.
6. Không tạo thư mục `tests`; kiểm tra bằng lệnh và dữ liệu mẫu của từng giai đoạn.
7. Không thêm logging hoặc comment vào code; dùng tên hàm và biến rõ nghĩa.
8. Mỗi người phải giải thích được phần mình làm và một phần do người khác làm.

## Cách review chéo để cả ba người hiểu dự án

Sau mỗi giai đoạn:

1. Người làm chính chạy demo từ đầu, không mở sẵn file kết quả.
2. Người review chọn một input khác hoặc cố tình tạo một lỗi đơn giản.
3. Người làm chính giải thích đầu vào, hàm chính, output và cách phát hiện lỗi.
4. Người review ghi xác nhận vào pull request hoặc biên bản nhóm rồi mới chuyển giai đoạn.

Luân phiên review: Thành review phần của Quang, Hiếu review phần của Thành, Quang review phần của Hiếu. Cách này giúp mỗi người luôn biết ít nhất hai mảng của dự án.

## Thứ tự triển khai an toàn

```text
Dữ liệu mẫu nhỏ
    → Hà Nội chạy đủ luồng
    → Đà Nẵng chạy mà không sửa code
    → chạy tiếp bằng --resume
    → chạy tuần tự toàn quốc
    → chỉ tăng số worker khi đã đo RAM và thời gian
```
