# Giai đoạn 05 — POI toàn quốc

## Mục tiêu

Tạo một bộ POI chuẩn hóa cho toàn Việt Nam từ file `vietnam.osm.pbf`, thay cho nhiều script riêng theo loại dịch vụ.

## Cần có trước

- PBF cố định đã được kiểm tra ở giai đoạn 04.
- `categories.json` đã có mapping POI.
- Hiểu các hàm đang có trong `poi.py`.

## Luồng

```text
Vietnam PBF + categories.json
              ↓ lọc OSM tags
            POI thô
              ↓ làm sạch + làm giàu
       POI GeoParquet toàn quốc
              ↓
          DuckDB view
```

## Các bước thực hiện

### Bước 1 — Cài thư viện của giai đoạn

- Giữ `geopandas` từ giai đoạn 04, sau đó thêm `pyrosm` và `pyarrow` vào `pyproject.toml`.
- Chạy lại `python -m pip install -e .` trong môi trường Python đang dùng.
- Kiểm tra import từng thư viện bằng một lệnh Python ngắn trước khi viết extraction.
- Ghi cố định khoảng phiên bản sau khi nhóm đã chạy ổn để ba máy không dùng API quá khác nhau.

Kết quả cần thấy: cả ba thành viên đều import được thư viện từ đúng Python đang chạy lệnh `ady201`.

### Bước 2 — Chỉ đọc các POI và cột cần thiết

- Tạo `poi_extract.py` và một hàm nhận `pbf_path`, cấu hình category và `output_path`.
- Từ `categories.json`, lấy các tag cần lọc như `amenity`, `shop`, `highway` và `public_transport`.
- Giữ các trường định danh OSM, tag cần phân loại, thông tin mô tả và geometry; bỏ sớm các cột chắc chắn không dùng.
- Thử trước trên một PBF khu vực nhỏ để đo RAM và kiểm tra mapping, sau đó mới chạy toàn quốc.

Kết quả cần thấy: bảng POI thô nhỏ hơn dữ liệu OSM gốc và vẫn còn đủ tag để kiểm tra lại.

### Bước 3 — Chuẩn hóa dữ liệu bằng các hàm trong `poi.py`

- Chuẩn hóa tên cột về một kiểu duy nhất.
- Đổi chuỗi rỗng thành giá trị thiếu và bỏ khoảng trắng thừa.
- Kiểm tra latitude trong `[-90, 90]`, longitude trong `[-180, 180]` nếu dữ liệu có hai cột này.
- Không xóa POI chỉ vì `name` bị thiếu; OSM có nhiều đối tượng hợp lệ không có tên riêng.

Kết quả cần thấy: mọi batch POI đi qua cùng một bộ quy tắc thay vì mỗi người làm sạch một kiểu.

### Bước 4 — Ánh xạ OSM tag sang nhóm dịch vụ

- Mỗi rule trong `categories.json` cần chỉ rõ tag, giá trị tag, `category` và `subcategory` đích.
- Viết một hàm áp rule theo thứ tự cố định để cùng một POI luôn nhận cùng kết quả.
- Nếu một POI khớp nhiều rule, lưu lại cờ chất lượng hoặc danh sách rule khớp để nhóm xem xét.
- POI chưa có mapping không nên bị mất ngay; gắn `quality_flags = unmapped_category` và thống kê riêng.

Kết quả cần thấy: các tên category có tập giá trị hữu hạn, ví dụ `healthcare`, `education`, `shopping`, `transit`.

### Bước 5 — Gom các trường làm giàu có sẵn trong OSM

- Tạo `poi_enrich.py` để ghép các tag địa chỉ thành một trường `address` dễ dùng.
- Giữ `operator`, `brand`, `opening_hours`, `phone` và `website` khi OSM có dữ liệu.
- Chỉ chuẩn hóa định dạng cơ bản; không đoán giá trị còn thiếu.
- Không gọi API geocoding công cộng cho toàn bộ POI vì chậm, khó chạy lại và có giới hạn sử dụng.

Kết quả cần thấy: một hàng POI chứa đủ thông tin phục vụ mô tả nhưng nguồn vẫn truy ngược được về OSM.

### Bước 6 — Tạo điểm đại diện cho POI dạng vùng

- POI dạng node đã là Point nên giữ nguyên vị trí.
- POI dạng way/relation có thể là Polygon hoặc MultiPolygon; dùng `representative_point()` để lấy một điểm nằm trong vùng.
- Giữ geometry gốc nếu cần vẽ bản đồ, đồng thời tạo cột point riêng dùng cho snap vào mạng đường.
- Không dùng centroid nếu chưa kiểm tra vì centroid có thể nằm ngoài polygon lõm.

Kết quả cần thấy: mỗi POI dùng cho routing có đúng một point không rỗng.

### Bước 7 — Phát hiện và xử lý bản ghi trùng

- Tạo khóa `(osm_type, osm_id)`; chỉ `osm_id` là chưa đủ vì node và way có thể trùng số.
- Thống kê khóa trùng và xem nguyên nhân trước khi xóa.
- Nếu cùng một đối tượng xuất hiện do nhiều filter, gộp thông tin và giữ một hàng.
- Sau khi xử lý, kiểm tra số hàng bằng số khóa duy nhất.

Kết quả cần thấy: không còn duplicate key nhưng không làm mất POI chỉ vì trùng tên hoặc trùng tọa độ.

### Bước 8 — Lưu GeoParquet và tạo view trong DuckDB

- Ghi đầu ra vào `data/processed/national/poi.parquet`.
- Đọc lại file vừa ghi để xác nhận schema, CRS, số hàng và geometry.
- Trong `sql/010_poi_views.sql`, tạo view dùng `read_parquet(...)`; view chỉ trỏ tới file, không sao chép toàn bộ POI vào DuckDB.
- Chạy một truy vấn `GROUP BY category` để xác nhận DuckDB đọc được kết quả.

Kết quả cần thấy: Python và DuckDB cùng đọc được một file POI chuẩn hóa duy nhất.

## File cần tạo hoặc sửa

```text
src/ady201/poi.py
src/ady201/poi_extract.py
src/ady201/poi_enrich.py
src/ady201/main.py
sql/010_poi_views.sql
pyproject.toml
```

Schema tối thiểu:

```text
osm_type
osm_id
category
subcategory
name
address
operator
brand
opening_hours
phone
website
geometry
quality_flags
```

Lệnh mục tiêu:

```powershell
ady201 build-national-poi
```

## Quy tắc

- Khóa duy nhất là `(osm_type, osm_id)`.
- Không xóa POI chỉ vì thiếu tên.
- Đọc cả tag `amenity`, `shop`, `highway` và `public_transport` khi cần.
- Giữ dữ liệu gốc đủ để kiểm tra lại mapping.
- Không reverse-geocode hàng loạt bằng API công cộng.
- Dữ liệu có geometry lưu GeoParquet, không dùng CSV làm nguồn chính.

## Lỗi thường gặp

- Chỉ dùng `osm_id` làm khóa và vô tình gộp node với way.
- Đảo longitude/latitude khiến POI xuất hiện ngoài Việt Nam.
- Xóa toàn bộ hàng thiếu `name`, làm mất nhiều dịch vụ hợp lệ.
- Lưu geometry vào CSV rồi phải tự ghép lại tọa độ ở các giai đoạn sau.

## Cần học trước

- OSM `node`, `way`, `relation` và tags.
- GeoDataFrame và geometry.
- Parquet/GeoParquet.
- Missing value và duplicate.

## Tìm hiểu thêm

- Từ khóa: `Pyrosm custom filter POI`.
- Từ khóa: `OpenStreetMap taginfo amenity shop`.
- Từ khóa: `GeoPandas representative_point`.

## Phân công

### Thành

- Viết extraction, normalize và enrich POI.
- Chốt schema, mapping category và kiểm tra duplicate.

### Hiếu

- Kiểm tra cách Pyrosm đọc node/way/relation.
- Đo RAM và thời gian trên một phần PBF nhỏ trước.

### Quang

- So sánh số lượng trước và sau chuẩn hóa.
- Tạo bảng số POI theo category và `quality_flags`.

## Đầu ra

```text
data/processed/national/poi.parquet
outputs/quality/poi_summary.csv
```

## Hoàn thành khi

- Một lệnh xử lý được mọi category.
- Không trùng khóa `(osm_type, osm_id)`.
- Geometry không rỗng và nằm trong phạm vi Việt Nam.
- DuckDB đọc được trực tiếp file Parquet đầu ra.
