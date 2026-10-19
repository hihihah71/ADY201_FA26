# Giai đoạn 01 — Chuẩn hóa project Python

Trạng thái: **đã hoàn thành**.

## Mục tiêu

Chuyển các script rời rạc thành package Python có thể cài và chạy từ terminal.

## Đầu vào

- Các script cũ trong `Code/`.
- JSON POI trong `RawData/`.

## Luồng

```text
RawData/*.json
      ↓ poi.py
POI hợp lệ
      ↓
CSV chuẩn hóa
```

## Các bước đã làm

### Bước 1 — Tạo file cài đặt project

- Mở `pyproject.toml` ở thư mục gốc.
- Khai báo tên package, phiên bản Python và dependency.
- Khai báo `ady201 = "ady201.main:main"` để tạo lệnh `ady201`.
- Chạy `python -m pip install -e .`; tùy chọn `-e` giúp code vừa sửa được dùng ngay mà không phải cài lại.

Kết quả cần thấy:

```powershell
ady201 --version
```

trả về phiên bản hiện tại của project.

### Bước 2 — Tạo package `src/ady201`

- `__init__.py` lưu `__version__`.
- `__main__.py` gọi hàm `main()` khi chạy `python -m ady201`.
- Không đặt code xử lý dữ liệu trực tiếp trong hai file này.

Kết quả cần thấy:

```powershell
python -c "import ady201"
```

chạy không báo lỗi.

### Bước 3 — Tạo điểm vào cho command line

- `main.py` tạo parser bằng `argparse`.
- Mỗi command có tên và tham số riêng.
- `main.py` chỉ đọc tham số rồi gọi hàm ở module khác; không xử lý dữ liệu dài trong file này.

Ví dụ luồng:

```text
ady201 normalize-poi input.json output.csv
        ↓
main.py đọc hai đường dẫn
        ↓
poi.py thực hiện chuẩn hóa
```

Kết quả cần thấy: `ady201 --help` hiển thị command và tham số mà không chạy xử lý dữ liệu.

### Bước 4 — Chia xử lý POI thành hàm nhỏ

- `clean_text()` xử lý chuỗi rỗng và khoảng trắng.
- `get_coordinates()` lấy tọa độ trực tiếp hoặc từ `center`.
- `create_poi()` biến một OSM element thành một POI hợp lệ.
- `read_pois()` đọc toàn bộ JSON.
- `save_pois()` ghi CSV.
- `normalize_poi_file()` nối các bước trên.

Khi một bản ghi sai, chỉ bỏ bản ghi đó; khi cấu trúc cả file sai, báo lỗi rõ ràng.

Kết quả cần thấy: file mẫu tạo được CSV sáu cột và hàm `normalize_poi_file()` trả về số POI đã ghi.

### Bước 5 — Chuẩn hóa đường dẫn

- Dùng `Path` thay cho chuỗi `D:\...` hoặc `G:\...`.
- Đường dẫn input/output nhận từ command line hoặc được tạo từ thư mục gốc project.
- Tạo thư mục output bằng `mkdir(parents=True, exist_ok=True)` trước khi ghi file.

Kết quả cần thấy: cùng câu lệnh chạy được trên máy khác nếu đứng ở thư mục project.

### Bước 6 — Giữ phần network ở mức tối thiểu

- `network.py` hiện chỉ là placeholder từ bước chuẩn hóa ban đầu.
- Chưa tải PBF và chưa xử lý road ở giai đoạn này.
- Giai đoạn 05 sẽ thay phần này bằng hàm lấy road lines; project không cần nodes hoặc graph.

Kết quả cần thấy: package vẫn import được; chưa đưa xử lý Pyrosm vào giai đoạn 01.

## Cấu trúc hiện tại

```text
src/ady201/
├── __init__.py
├── __main__.py
├── main.py
├── poi.py
└── network.py
```

- `main.py`: nhận lệnh từ terminal.
- `poi.py`: đọc, làm sạch và lưu POI.
- `network.py`: placeholder, sẽ được rút gọn thành xử lý road lines ở giai đoạn 05.
- `__init__.py`: đánh dấu package và lưu version.
- `__main__.py`: cho phép chạy `python -m ady201`.

`__pycache__` và `*.egg-info` là file tự sinh. Không cần đọc, sửa hoặc commit.

## Lỗi thường gặp

- `ady201` không được nhận diện: thường là project chưa được cài bằng đúng Python đang dùng; chạy `python -m pip install -e .`.
- Sửa file trong `__pycache__` hoặc `*.egg-info`: đây là file tự sinh và thay đổi sẽ bị ghi đè.
- Dùng đường dẫn tuyệt đối của một máy: thành viên khác sẽ không chạy được.
- Đặt xử lý POI trực tiếp trong `main.py`: lệnh chạy được nhưng khó dùng lại khi ghép pipeline.

## Cần học trước

- Hàm, tham số và giá trị trả về trong Python.
- `list`, `dict` và vòng lặp `for`.
- `pathlib.Path`.
- Type hint và `dataclass` ở mức cơ bản.
- Ý nghĩa của `if __name__ == "__main__"`.

## Tìm hiểu thêm

- Từ khóa: `Python package src layout`.
- Từ khóa: `pip editable install`.
- Từ khóa: `Python argparse tutorial`.

## Phân công

### Thành

- Chuẩn hóa hàm xử lý POI.
- Chốt sáu cột đầu ra của POI.

### Hiếu

- Kiểm tra cấu trúc road lines cần cho phép tính mật độ đường.
- Xác nhận project chạy được trên máy khác.

### Quang

- Viết README cài đặt và lệnh chạy.
- Kiểm tra cấu trúc thư mục và `.gitignore`.

## Đầu ra

CSV POI có các cột:

```text
osm_type,osm_id,lat,lon,amenity,name
```

## Hoàn thành khi

Ba thành viên đều chạy được:

```powershell
python -m pip install -e .
python -c "import ady201"
ady201 --help
ady201 normalize-poi RawData/Anuong_Taichinh_Dichvu.json data/interim/pois.csv
```

File `data/interim/pois.csv` phải được tạo mà không cần sửa source code.
