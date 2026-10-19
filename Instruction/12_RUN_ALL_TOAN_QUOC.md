# Giai đoạn 12 — Chạy tất cả tỉnh/thành

## Nhiệm vụ tổng quát

Đọc danh sách tỉnh có `enabled=true`, gọi `run_region()` lần lượt và ghép các bảng feature thành kết quả toàn quốc.

## Luồng

```text
regions.json
    ↓ lọc enabled=true
for mỗi region_id: run_region(region_id)
    ↓
feature Parquet theo tỉnh
    ↓ DuckDB read_parquet hoặc pandas concat
cell_features_vietnam.parquet
```

## Những thứ cần thay đổi

- Thêm `run_all()` vào `pipeline.py`.
- Thêm subcommand `run-all` vào `main.py`.
- Chạy tuần tự ở phiên bản đầu để dễ tìm lỗi và tránh hết RAM.
- Không tải PBF lại trong vòng lặp; mọi tỉnh dùng cùng file hiện tại.

## Các bước thực hiện

### Bước 1 — Lấy danh sách tỉnh

```python
def get_enabled_region_ids():
    regions = read_json("config/regions.json")
    return [
        region_id
        for region_id, region in regions.items()
        if region.get("enabled", False)
    ]
```

Muốn thử ít tỉnh, đặt `enabled=false` cho các tỉnh chưa chạy.

### Bước 2 — Chạy tuần tự và giữ kết quả lỗi

```python
def run_all():
    summary = []

    for region_id in get_enabled_region_ids():
        try:
            run_region(region_id)
            summary.append({"region_id": region_id, "status": "success", "error": ""})
        except Exception as error:
            summary.append({"region_id": region_id, "status": "failed", "error": str(error)})

    return summary
```

Một tỉnh lỗi không làm mất output của các tỉnh đã chạy xong.

### Bước 3 — Lưu bảng tổng kết

```text
data/processed/run_all_summary.csv
```

Cột tối thiểu:

```text
region_id,status,error
```

### Bước 4 — Ghép output toàn quốc

Sau khi các tỉnh thành công, dùng DuckDB đọc các file:

```sql
COPY (
    SELECT *
    FROM read_parquet(
        'data/processed/*/cell_features.parquet',
        union_by_name = true
    )
)
TO 'data/processed/national/cell_features_vietnam.parquet'
(FORMAT PARQUET);
```

Nếu cần giữ geometry đúng dạng GeoParquet, dùng GeoPandas `concat` và `to_parquet()` thay cho `COPY`.

### Bước 5 — Thêm câu lệnh

```powershell
ady201 run-all
```

Không chạy toàn quốc trước khi ít nhất hai tỉnh đã chạy đúng bằng `run-region`.

## Kiểm tra kết quả

- Mỗi region enabled xuất hiện một lần trong summary.
- Tổng số hàng toàn quốc bằng tổng số hàng của các file tỉnh thành công.
- Khóa ghép toàn quốc là cặp `region_id`, `cell_id`.
- Tỉnh lỗi có thông báo trong summary và có thể chạy lại riêng.

## Kiến thức cần học

- Vòng lặp, `try/except` và danh sách kết quả.
- Ghép nhiều Parquet có cùng schema.
- Khóa ghép gồm hai cột.
- Vì sao xử lý tuần tự đơn giản hơn multiprocessing ở bản đầu.

Từ khóa tìm thêm: `DuckDB read multiple parquet files`, `pandas concat GeoDataFrame`.

## Phân công

### Thành — trung bình/khó

- Viết `run_all()`, lệnh `run-all` và cách chạy lại tỉnh lỗi.

### Hiếu — trung bình/khó

- Ghép Parquet toàn quốc và kiểm tra tổng số hàng/khóa trùng.

### Quang — dễ/trung bình

- Hoàn thiện `regions.json`, theo dõi summary và lập danh sách tỉnh cần chạy lại.

Review chéo: Hiếu cố tình làm một tỉnh lỗi; Thành và Quang kiểm tra batch vẫn chạy tỉnh tiếp theo và summary ghi đúng.

## Hoàn thành khi

- Một lệnh chạy được tất cả region enabled.
- Có summary thành công/thất bại.
- Có thể ghép các tỉnh thành công thành một bảng feature toàn quốc.
