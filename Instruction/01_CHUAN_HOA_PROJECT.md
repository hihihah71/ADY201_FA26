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

1. Tạo `pyproject.toml` để cài project bằng `pip install -e .`.
2. Tạo package `src/ady201`.
3. Đưa lệnh terminal vào `main.py`.
4. Tách xử lý POI vào các hàm nhỏ trong `poi.py`.
5. Dùng `pathlib.Path` thay cho đường dẫn cố định theo máy.
6. Giữ `network.py` làm điểm bắt đầu cho phần mạng đường.

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
- `network.py`: khai báo file node và edge sẽ dùng sau.
- `__init__.py`: đánh dấu package và lưu version.
- `__main__.py`: cho phép chạy `python -m ady201`.

`__pycache__` và `*.egg-info` là file tự sinh. Không cần đọc, sửa hoặc commit.

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

- Kiểm tra cấu trúc `nodes` và `edges` cần cho mạng đường.
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
pip install -e .
python -c "import ady201"
ady201 --help
ady201 normalize-poi RawData/Anuong_Taichinh_Dichvu.json data/interim/pois.csv
```

File `data/interim/pois.csv` phải được tạo mà không cần sửa source code.
