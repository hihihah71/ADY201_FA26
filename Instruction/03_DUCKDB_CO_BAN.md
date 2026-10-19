# Giai đoạn 03 — DuckDB tối giản

## Nhiệm vụ tổng quát

Để Python tự mở DuckDB và dùng DuckDB đọc bảng feature sau này. Không import PBF, không mở pgAdmin và chưa cần tạo nhiều bảng.

GeoPandas thực hiện các phép tính không gian. DuckDB chỉ giúp xem, lọc và tổng hợp file kết quả.

## Luồng

```text
Python gọi connect_database()
             ↓
data/database/ady201.duckdb
             ↓
view đọc cell_features.parquet
```

## Những thứ cần thay đổi

- Giữ `src/ady201/database.py` thật ngắn.
- Có thể bỏ schema nhiều bảng cũ nếu chúng chưa được dùng.
- Chỉ cần một view `cell_features` sau khi đã có file Parquet.

## Các bước thực hiện

### Bước 1 — Viết hàm kết nối

```python
from pathlib import Path
import duckdb


DATABASE_PATH = Path("data/database/ady201.duckdb")


def connect_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DATABASE_PATH))
```

Ý nghĩa:

- Tạo thư mục nếu chưa có.
- DuckDB tự tạo file database ở lần kết nối đầu.
- Hàm trả về connection để chạy SQL.

### Bước 2 — Kiểm tra kết nối

```python
from ady201.database import connect_database

connection = connect_database()
result = connection.execute("SELECT 1 AS ok").fetchone()
connection.close()
print(result)
```

Kết quả cần thấy: `(1,)`.

### Bước 3 — Tạo view khi đã có output

Thực hiện ở giai đoạn 09 hoặc 12:

```python
def create_feature_view(connection):
    connection.execute("""
        CREATE OR REPLACE VIEW cell_features AS
        SELECT *
        FROM read_parquet(
            'data/processed/*/cell_features.parquet',
            union_by_name = true
        )
    """)
```

View chỉ đọc các file đang có. Không sao chép dữ liệu vào nhiều bảng.

### Bước 4 — Truy vấn thử

```sql
SELECT region_id, COUNT(*) AS cell_count
FROM cell_features
GROUP BY region_id
ORDER BY region_id;
```

## Khi nào mới cần bảng thật

Chỉ thêm bảng khi nhóm có nhu cầu rõ ràng, ví dụ lưu lịch sử chạy. Phiên bản đầu không cần `regions`, `pipeline_steps`, `artifacts` hoặc bảng POI/road trong DuckDB.

## Kiến thức cần học

- Connection, `execute()`, `fetchone()` và `fetchdf()`.
- Khác nhau giữa table và view.
- `read_parquet()` và `GROUP BY`.

Từ khóa tìm thêm: `DuckDB Python connection`, `DuckDB read_parquet view`.

## Phân công

### Thành — trung bình

- Rút gọn `database.py` và viết `create_feature_view()`.

### Hiếu — trung bình

- Viết ba truy vấn kiểm tra count, null và `cell_id` trùng.

### Quang — dễ

- Chạy `SELECT 1`, mở database bằng Python và ghi lại câu lệnh sử dụng.

Review chéo: Hiếu giải thích vì sao project dùng view thay vì import Parquet thành nhiều bảng.

## Hoàn thành khi

- Python tự tạo/kết nối được file `.duckdb`.
- Không cần pgAdmin.
- Không import PBF, POI hoặc road vào DuckDB.
- Khi có Parquet, view đọc được feature của các tỉnh.
