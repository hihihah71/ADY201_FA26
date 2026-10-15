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

## Các bước thực hiện chi tiết

### Bước 1 — Chốt cấu trúc ba file JSON

Tạo và phân biệt rõ trách nhiệm:

- `project.json`: tham số dùng chung cho cả project.
- `categories.json`: mapping OSM tag sang nhóm dịch vụ.
- `regions.json`: danh sách khu vực có thể chạy.

Tên tham số phải kèm đơn vị để tránh hiểu nhầm:

```json
{
  "walking_speed_mps": 1.4,
  "accessibility_minutes": [5, 10, 15],
  "hex_resolution": 9
}
```

Không dùng tên mơ hồ như `walking_speed: 5000` vì người đọc không biết đơn vị là mét/giây hay mét/giờ.

`categories.json` nên lưu rule có cả tên tag, thay vì giả định tất cả dịch vụ đều nằm trong `amenity`:

```json
{
  "rules": [
    {
      "tag": "amenity",
      "values": ["hospital", "clinic", "pharmacy"],
      "category": "healthcare",
      "subcategory": "medical"
    },
    {
      "tag": "shop",
      "values": ["supermarket"],
      "category": "shopping",
      "subcategory": "supermarket"
    }
  ]
}
```

Kết quả cần thấy: đọc từng file JSON bằng Python không lỗi và mỗi file chỉ chứa đúng loại cấu hình của nó.

### Bước 2 — Viết hàm đọc config trong `settings.py`

- Viết `load_json(path)` để đọc một file JSON và trả về `dict` hoặc `list`.
- Viết `load_project_settings()` và `load_categories()` gọi lại `load_json()`.
- Dùng UTF-8 để đọc được tên tiếng Việt.
- Nếu file không tồn tại hoặc JSON sai cú pháp, để Python báo lỗi kèm đúng đường dẫn file.

Kết quả cần thấy:

```powershell
python -c "from ady201.settings import load_project_settings; print(load_project_settings())"
```

### Bước 3 — Chuẩn hóa `regions.json`

Mỗi region dùng cùng năm trường tối thiểu:

```json
{
  "region_id": "hanoi",
  "name": "Hà Nội",
  "boundary_path": "data/boundaries/v1/hanoi.geojson",
  "network_bbox": [105.70, 20.85, 106.05, 21.25],
  "enabled": true
}
```

- `region_id` viết thường, không dấu và không đổi sau khi đã có dữ liệu.
- `name` chỉ dùng để hiển thị.
- `boundary_path` là đường dẫn tương đối dùng cho hexagon và phân tích không gian từ giai đoạn 07.
- `network_bbox` có thứ tự `[min_lon, min_lat, max_lon, max_lat]` và được Pyrosm dùng để lấy mạng đường.
- `enabled=false` nghĩa là tạm thời không chạy region đó.

Kết quả cần thấy: Hà Nội và Đà Nẵng có `region_id`, boundary và network bbox riêng.

### Bước 4 — Viết hàm tìm region trong `regions.py`

- `load_regions()` trả toàn bộ danh sách.
- `get_region(region_id)` trả đúng một region.
- Nếu không tìm thấy, báo lỗi có danh sách ID hợp lệ.
- Nominatim/get-bbox có thể hỗ trợ lấy `network_bbox`; boundary trong registry vẫn là đầu vào cho phân tích hexagon.

Kết quả cần thấy: `get_region("hanoi")` trả đúng cấu hình Hà Nội, còn ID sai tạo thông báo có danh sách ID hợp lệ.

### Bước 5 — Kiểm tra dữ liệu config

Kiểm tra ngay sau khi đọc:

- Không có hai region cùng `region_id`.
- Các trường bắt buộc không rỗng.
- `walking_speed_mps` lớn hơn 0.
- Các ngưỡng phút là số dương và tăng dần.
- `network_bbox` có đúng bốn số và `min` nhỏ hơn `max`.

Không đợi tới giai đoạn graph mới báo config sai.

Kết quả cần thấy: cố tình tạo `walking_speed_mps = 0` hoặc lặp `region_id` thì loader dừng và chỉ rõ trường sai.

### Bước 6 — Thêm lệnh xem region

Thêm `list-regions` vào `main.py`. Lệnh chỉ đọc config và hiển thị:

```text
region_id | name    | enabled
hanoi     | Hà Nội  | true
danang    | Đà Nẵng | true
```

Sau đó thêm Đà Nẵng vào `regions.json` và chạy lại. Nếu danh sách thay đổi mà không sửa file Python thì bước này đạt.

Kết quả cần thấy: `ady201 list-regions` hiển thị dữ liệu mới ngay sau khi chỉ sửa JSON.

## Lỗi thường gặp

- Giữ các key cũ như `walking_speed`, `hexagon_size` nhưng không ghi đơn vị.
- Để `regions.json` rỗng rồi các bước sau phải hard-code Hà Nội.
- Chỉ lưu bounding box từ Nominatim và coi đó là boundary thật; bounding box là hình chữ nhật, không phải ranh giới hành chính.
- Đổi `region_id` sau khi đã có output, làm đường dẫn và khóa dữ liệu cũ không còn khớp.

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

`categories.json` lưu mapping tag OSM sang nhóm như bệnh viện, trường học và siêu thị.

`regions.json` lưu:

- `region_id` không dấu, ví dụ `hanoi`.
- Tên hiển thị.
- Đường dẫn boundary.
- Bounding box dùng để đọc mạng đường.
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

- Chốt `network_bbox`, boundary và loại mạng đường.
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
