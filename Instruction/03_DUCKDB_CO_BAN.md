# 03 — DuckDB phụ trợ

## Vai trò

DuckDB không bắt buộc để chạy `ady201 grf`. Nó hiện được dùng cho hai việc:

- Downloader Overture truy vấn STAC database và ghi GeoParquet.
- Database cục bộ thử nghiệm tại `data/database/ady201.duckdb`.

## Khởi tạo database cục bộ

```powershell
ady201 init-db
```

Schema hiện chỉ có bảng `regions`:

```sql
CREATE TABLE IF NOT EXISTS regions (
    region_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    boundary_path VARCHAR NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);
```

## Kiểm tra trong Python

CLI `check-db` hiện gọi hàm nhưng chưa in dictionary trả về. Để xem kết quả:

```python
from ady201.database import check_database

print(check_database())
```

Output dạng:

```python
{"ready": True, "region_count": 0}
```

## Query trực tiếp GeoParquet

Không cần import dữ liệu vào bảng DuckDB:

```sql
SELECT
    count(*) AS cells,
    avg(food_and_drink_count_200m) AS avg_food
FROM read_parquet('data/processed/29_3/cell_features.parquet');
```

Ví dụ Python:

```python
import duckdb

result = duckdb.sql("""
    SELECT cell_id, food_and_drink_count_200m
    FROM read_parquet('data/processed/29_3/cell_features.parquet')
    ORDER BY food_and_drink_count_200m DESC
    LIMIT 10
""").df()
```

## Giới hạn hiện tại

- `create_feature_view()` đang hard-code `data/processed/hanoi/cell_features.parquet`, không phải `29_3`.
- Database không nằm trong luồng tạo feature hoặc Streamlit.
- Không cần chạy `init-db` trước `download-overture-poi` hoặc `grf`.
