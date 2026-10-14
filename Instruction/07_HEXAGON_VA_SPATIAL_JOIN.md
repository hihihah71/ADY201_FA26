# Giai đoạn 07 — Hexagon và gán dữ liệu theo vị trí

## Mục tiêu

Chia mỗi khu vực thành các cell thống nhất và xác định POI thuộc cell nào.

## Cần có trước

- Boundary hợp lệ từ giai đoạn 04.
- POI toàn quốc từ giai đoạn 05.
- Graph đường từ giai đoạn 06.

## Luồng

```text
analysis boundary
       ↓ tạo và cắt hexagon
     các cell
       ↓ tính diện tích + điểm đại diện
   cell phân tích

POI toàn quốc + cell
       ↓ spatial join
POI thuộc region/cell
```

## Các bước thực hiện

### Bước 1 — Cài và kiểm tra thư viện H3

- Thêm `h3` vào `pyproject.toml`, sau đó chạy `python -m pip install -e .`.
- Kiểm tra phiên bản đang cài vì tên hàm của H3 có thể khác giữa các phiên bản lớn.
- Chạy một ví dụ nhỏ: đổi một cặp latitude/longitude thành H3 cell rồi đổi cell lại thành polygon.
- Khi cả nhóm chạy ổn, cố định khoảng phiên bản để ba máy dùng cùng API.

Kết quả cần thấy: một tọa độ mẫu ở Hà Nội tạo được một `cell_id` H3 hợp lệ.

### Bước 2 — Chọn resolution từ config

- Đọc `hex_resolution` từ `project.json`; không đặt trực tiếp trong `hexagons.py`.
- Thử hai resolution trên một vùng nhỏ và ghi số cell, diện tích trung bình, thời gian xử lý.
- Chốt một resolution dùng chung nếu cần so sánh các tỉnh/thành.
- Tạo `grid_version` từ loại lưới và resolution, ví dụ `h3_r9`.

Kết quả cần thấy: đổi resolution chỉ cần sửa config và đầu ra cho biết rõ grid version.

### Bước 3 — Tạo các H3 cell phủ boundary

- Đọc analysis boundary ở EPSG:4326.
- Chuyển geometry sang dạng đầu vào mà H3 chấp nhận rồi gọi hàm phủ polygon, ví dụ `h3.geo_to_cells(...)` với H3 4.x.
- Với MultiPolygon, xử lý từng phần rồi hợp nhất tập `cell_id` để tránh cell trùng.
- Đổi từng `cell_id` về polygon và tạo GeoDataFrame có CRS EPSG:4326.

Kết quả cần thấy: các hexagon phủ kín khu vực và `cell_id` không trùng.

### Bước 4 — Xử lý các cell nằm ở biên

- Giữ các cell có giao với analysis boundary.
- Tạo geometry phân tích bằng phần giao giữa hexagon và boundary; cell giữa vùng giữ nguyên, cell biên có thể bị cắt.
- Không thay `cell_id` sau khi clip; ID vẫn đại diện cho H3 cell ban đầu.
- Loại geometry rỗng và sửa geometry không hợp lệ nếu có.

Kết quả cần thấy: không cell nào nằm hoàn toàn ngoài boundary và cell biên không cộng diện tích ngoài vùng.

### Bước 5 — Tính diện tích thật của cell

- Chuyển geometry đã clip sang CRS có đơn vị mét phù hợp với khu vực.
- Tính `area_km2 = area_m2 / 1_000_000`.
- Kiểm tra `area_km2 > 0`; cell biên sẽ có diện tích nhỏ hơn cell đầy đủ.
- Chuyển geometry về EPSG:4326 trước khi ghi GeoParquet nếu đó là CRS thống nhất của dự án.

Kết quả cần thấy: tổng `area_km2` của cell xấp xỉ diện tích analysis boundary.

### Bước 6 — Tạo điểm đại diện cho mỗi cell

- Dùng `representative_point()` trên geometry đã clip, không lấy trung bình latitude/longitude thủ công.
- Lưu điểm vào cột `representative_point` hoặc file riêng nếu định dạng GeoParquet chỉ cho một geometry chính.
- Xác nhận điểm nằm trong phần cell thuộc boundary.
- Điểm này sẽ được snap vào walking graph ở giai đoạn 08.

Kết quả cần thấy: mỗi cell có đúng một điểm đại diện không rỗng.

### Bước 7 — Gán POI vào region và cell

- Lọc POI toàn quốc theo extraction boundary trước để giảm dữ liệu cần join.
- Dùng `geopandas.sjoin()` giữa point POI và polygon cell với predicate phù hợp.
- Xử lý riêng POI nằm đúng đường biên để mỗi POI density chỉ nhận một `cell_id`; quy tắc chọn phải cố định, ví dụ lấy `cell_id` nhỏ nhất sau khi sắp xếp.
- Kiểm tra số POI trước join, số được gán, số chưa gán và số bị gán nhiều lần.

Kết quả cần thấy: mỗi POI nằm trong analysis boundary có đúng một `cell_id`.

### Bước 8 — Phân biệt POI phân tích và POI hỗ trợ routing

- Gắn `membership_scope = analysis` cho POI nằm trong boundary gốc; các POI này dùng cho count và density.
- Gắn `membership_scope = buffer` cho POI chỉ nằm trong vùng buffer; các POI này chỉ làm đích accessibility.
- Không cộng POI buffer vào số dịch vụ của cell trong vùng.
- Ghi chung một file membership hoặc hai file, nhưng schema phải thể hiện rõ scope.

Kết quả cần thấy: một bệnh viện ngay ngoài biên có thể dùng để tính thời gian tiếp cận nhưng không làm tăng POI count của khu vực.

## File cần tạo hoặc sửa

```text
src/ady201/hexagons.py
src/ady201/spatial_join.py
src/ady201/main.py
sql/030_region_views.sql
pyproject.toml
```

Schema cell:

```text
snapshot_id
region_id
grid_version
cell_id
area_km2
geometry
representative_point
```

Lệnh mục tiêu:

```powershell
ady201 build-grid --region hanoi --snapshot <snapshot_id>
```

## Quy tắc

- Dùng cùng H3 resolution nếu muốn so sánh giữa các khu vực.
- Cell biên dùng diện tích sau khi clip.
- POI trong boundary gốc dùng tính count và density.
- POI trong vùng buffer chỉ bổ sung cho tính accessibility.
- POI nằm đúng đường biên chỉ được gán một lần theo quy tắc cố định.
- Không dùng tọa độ độ để tính diện tích km².

## Lỗi thường gặp

- Đảo latitude và longitude khi gọi H3, làm cell xuất hiện sai châu lục.
- Tính diện tích trên EPSG:4326 nên đơn vị không phải km².
- Giữ nguyên toàn bộ diện tích hexagon ở biên, khiến tổng diện tích lớn hơn boundary.
- Dùng `intersects` rồi không xử lý POI trên biên, dẫn đến một POI thuộc nhiều cell.

## Cần học trước

- Point, polygon và spatial join.
- `within`, `covers` và `intersects`.
- Clip/overlay geometry.
- CRS theo mét và cách tính diện tích.

## Tìm hiểu thêm

- Từ khóa: `H3 Python polygon to cells`.
- Từ khóa: `GeoPandas sjoin`.
- Từ khóa: `GeoPandas overlay clip`.

## Phân công

### Thành

- Viết phần gán POI vào region/cell.
- Kiểm tra POI bị gán trùng và số lượng trước/sau join.

### Hiếu

- Kiểm tra CRS, cell biên và representative point.
- Kiểm tra điểm đại diện có thể snap vào graph.

### Quang

- Tạo hexagon và bản đồ xem nhanh.
- So sánh hai resolution trên một khu vực nhỏ.

## Đầu ra

```text
data/processed/{snapshot_id}/{region_id}/grid/hexagons.parquet
data/processed/{snapshot_id}/{region_id}/poi/region_membership.parquet
outputs/quality/{snapshot_id}/{region_id}/grid_summary.json
```

## Hoàn thành khi

- Không có cell nằm hoàn toàn ngoài boundary.
- Tổng diện tích cell gần bằng diện tích boundary.
- Mỗi POI dùng cho density chỉ thuộc một cell.
- Bản đồ cell phủ đúng khu vực.
