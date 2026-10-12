# Giai đoạn 02 — Cấu hình và danh sách khu vực

## Mục tiêu

Cho phép thêm Hà Nội, Đà Nẵng hoặc khu vực khác bằng file JSON, không sửa code Python.

## Cần có trước

- Giai đoạn 01 đã hoàn thành.
- Biết đọc `dict` và JSON trong Python.

## Đầu vào

- Tham số chung như tốc độ đi bộ và ngưỡng thời gian.
- Danh sách nhóm POI.
- Danh sách tỉnh/thành cần chạy.

## Luồng

```text
project.json + categories.json + regions.json
                    ↓ settings.py / regions.py
             dữ liệu đã kiểm tra
                    ↓
              các module phía sau
```

## Các bước thực hiện

1. Tạo ba file JSON trong `config/`.
2. Viết hàm đọc JSON trong `settings.py`.
3. Viết hàm lấy một khu vực theo `region_id` trong `regions.py`.
4. Kiểm tra các trường bắt buộc và báo lỗi dễ hiểu nếu thiếu.
5. Thêm lệnh `ady201 list-regions` vào `main.py`.
6. Thử thêm Đà Nẵng chỉ bằng cách sửa `regions.json`.

## File cần tạo hoặc sửa

```text
config/project.json
config/categories.json
config/regions.json
src/ady201/settings.py
src/ady201/regions.py
src/ady201/main.py
```

`project.json` lưu:

- Tốc độ đi bộ.
- Các mốc 5, 10 và 15 phút.
- Kích thước hexagon.
- Khoảng buffer khi cắt mạng đường.

`categories.json` lưu mapping tag OSM sang nhóm như bệnh viện, trường học và siêu thị.

`regions.json` lưu:

- `region_id` không dấu, ví dụ `hanoi`.
- Tên hiển thị.
- Đường dẫn boundary.
- Trạng thái `enabled`.

## Quy tắc

- Dùng JSON vì Python đọc được bằng thư viện có sẵn.
- Không lưu bounding box hoặc tên Hà Nội trong source.
- Hàm cần khu vực nào thì nhận `region` qua tham số.
- Chưa cần tạo `context.py` hoặc framework config phức tạp.

## Cần học trước

- Cấu trúc JSON.
- `json.load`.
- Kiểm tra key trong `dict`.
- Giá trị mặc định và thông báo lỗi.

## Tìm hiểu thêm

- Từ khóa: `Python read JSON file`.
- Từ khóa: `configuration versus source code`.
- Từ khóa: `stable slug identifier`.

## Phân công

### Thành

- Thiết kế `categories.json`.
- Chốt mapping OSM tag sang category.

### Hiếu

- Chốt các trường liên quan boundary, buffer và loại mạng đường.
- Kiểm tra dữ liệu Hà Nội và Đà Nẵng.

### Quang

- Viết hàm đọc JSON và lệnh `list-regions`.
- Viết bảng báo trường nào còn thiếu.

## Đầu ra

- Ba file config dễ đọc.
- Danh sách khu vực có thể mở rộng.
- Các module sau không cần hard-code tên tỉnh/thành.

## Hoàn thành khi

```powershell
ady201 list-regions
```

hiển thị được Hà Nội và Đà Nẵng, đồng thời thêm một khu vực mới không cần sửa file Python.
