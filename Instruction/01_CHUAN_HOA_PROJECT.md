# Giai đoạn 01 — Chuẩn hóa project Python

## Mục tiêu

Chuyển các script rời rạc thành package Python có thể import, test và gọi từ command line.

## Nhiệm vụ tổng quát

- Tạo `pyproject.toml` và môi trường dependency thống nhất.
- Tạo package `src/ady201`.
- Tách logic khỏi notebook và script chạy trực tiếp.
- Chuẩn hóa path, logging, exception và test fixtures.
- Giữ code cũ cho đến khi module mới chạy tương đương.

## Luồng

```text
Code/*.py hiện tại
    ↓ tách hàm dùng lại
src/ady201/*
    ↓
pytest + CLI mẫu
```

## Những thứ cần thay đổi

Tạo:

```text
pyproject.toml
src/ady201/__init__.py
src/ady201/config.py
src/ady201/context.py
src/ady201/logging.py
tests/fixtures/
tests/test_imports.py
```

Loại bỏ dần:

- `from nt import write`.
- Đường dẫn tương đối phụ thuộc thư mục chạy.
- Code thực thi ngay khi import.
- `print` dùng thay logging.
- Biến toàn cục cho tọa độ/input/output.

Dependency ban đầu cần đánh giá:

```text
duckdb
pandas
geopandas
pyarrow
shapely
pyproj
pyyaml
typer
pytest
```

Dependency graph/OSM bổ sung ở giai đoạn sau.

## Kiến thức cần học

### Bắt buộc

- Python package và `src` layout.
- `pathlib.Path`.
- `if __name__ == "__main__"`.
- Type hints và dataclass.
- Logging và exception cơ bản.
- Pytest fixture.

### Tìm hiểu sâu bên ngoài

- `pyproject.toml` dependency management.
- Editable install: `pip install -e .`.
- Typer command-line application.

## Phân công

### Thành

- Refactor hàm normalize POI đầu tiên.
- Định nghĩa input/output contract cho module POI.

### Hiếu

- Tạo module placeholder cho `network`.
- Kiểm tra cài các package native trên Windows/WSL.

### Quang

- Tạo cấu trúc package, `pyproject.toml` và test import.
- Viết README ngắn về cài môi trường.

### Review

- Thành review cấu trúc dữ liệu.
- Hiếu review dependency OSM/graph.
- Cả nhóm chạy trên máy của mình.

## Đầu ra

- Package `ady201` import được.
- `pytest` chạy được.
- Không còn path ổ `D:`/`G:` trong module mới.

## Hoàn thành khi

```powershell
pip install -e .
pytest
python -c "import ady201"
```

đều chạy thành công trên máy của ba thành viên.

