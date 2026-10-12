# ADY201_FA26

Dự án phân tích mức độ tập trung dịch vụ, khả năng tiếp cận và hạ tầng giao thông tại Việt Nam.

Thành viên: Thành, Hiếu và Quang.

## Cài đặt

Yêu cầu Python 3.11 trở lên.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

## Chạy chương trình

```powershell
ady201 --help
ady201 normalize-poi RawData/Anuong_Taichinh_Dichvu.json data/interim/pois.csv
```

File CSV đầu ra có sáu cột:

```text
osm_type,osm_id,lat,lon,amenity,name
```

## Các file Python hiện tại

```text
src/ady201/
├── __init__.py
├── __main__.py
├── main.py
├── poi.py
└── network.py
```

- `main.py`: nhận lệnh từ terminal và gọi hàm xử lý phù hợp.
- `poi.py`: đọc JSON, kiểm tra POI và ghi CSV chuẩn hóa.
- `network.py`: định nghĩa hai file `nodes` và `edges` sẽ dùng cho mạng đường.
- `__init__.py`: đánh dấu `ady201` là một package Python và lưu phiên bản dự án. File này rất ngắn và ít khi phải sửa.
- `__main__.py`: cho phép chạy `python -m ady201`. File này chỉ chuyển việc xử lý sang `main.py`.

## Các file tự sinh

- `__pycache__/`: Python tự tạo để lần chạy sau nhanh hơn. Không cần đọc, sửa hoặc đưa lên Git. Có thể xóa nhưng Python sẽ tạo lại.
- `*.pyc`: file nằm trong `__pycache__`, chứa mã Python đã được biên dịch tạm thời.
- `*.egg-info/`: `pip install -e .` tự tạo để lưu thông tin package. Không cần sửa hoặc đưa lên Git.

Các file trên đã được khai báo trong `.gitignore`, nên không được commit.

## Cấu trúc dự án

- `src/ady201/`: code mới đang sử dụng.
- `Instruction/`: kế hoạch và hướng dẫn theo từng giai đoạn.
- `Code/`: script cũ, giữ lại để đối chiếu.
- `RawData/`: dữ liệu JSON hiện có.
- `Flatten/`: dữ liệu CSV hiện có.

## Tài liệu

- Bắt đầu tại `Instruction/00_TONG_QUAN.md` để xem toàn bộ lộ trình.
- Giai đoạn 01 trong `Instruction/01_CHUAN_HOA_PROJECT.md` đã hoàn thành.
- Tiếp tục với `Instruction/02_CONFIG_VA_REGION_REGISTRY.md`.
