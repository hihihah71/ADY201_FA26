# 12 — Chạy nhiều tỉnh/thành

## Trạng thái hiện tại

Project chưa có command `run-all` và chưa có hàm batch đọc `config/regions.json`.

CLI chỉ hỗ trợ một region mỗi lần:

```powershell
ady201 grf <province> <region_id>
```

Không sử dụng các lệnh batch được mô tả trong tài liệu cũ vì chúng chưa tồn tại trong `main.py`.

## Chạy tuần tự thủ công

Ví dụ nhỏ:

```powershell
ady201 grf "Hà Nội" 29_3
ady201 grf "Thanh Hóa" 38_1
```

Mỗi region tạo một file riêng:

```text
data/processed/29_3/cell_features.parquet
data/processed/38_1/cell_features.parquet
```

## Đọc nhiều output bằng DuckDB

Khi đã có nhiều file:

```sql
SELECT count(*)
FROM read_parquet(
    'data/processed/*/cell_features.parquet',
    union_by_name = true,
    filename = true
);
```

Không cần ghép thành một file vật lý nếu chỉ phân tích bằng DuckDB.

## Điều kiện trước khi triển khai batch

Một command batch tương lai cần:

- Mapping ổn định giữa province name và `region_id`.
- Không ghi đè output đã hoàn thành trừ khi có `--force`.
- Ghi trạng thái success/failure và thời gian từng region.
- Có thể tiếp tục từ lần chạy trước.
- Giới hạn chạy tuần tự vì road overlay dùng nhiều RAM.
- Không che mất traceback của region lỗi.

## Vì sao chưa nên chạy toàn quốc ngay

- Grid 200 m tạo số cell rất lớn.
- Road overlay là bước nặng.
- Tên boundary cần được xác minh theo OSM PBF.
- `regions.json` hiện chỉ là danh sách tham khảo và có thể khác tên boundary thực tế.
- Giao diện hiện chỉ hỗ trợ `29_3`.

## Khuyến nghị

Xác nhận pipeline trên một thành phố và một tỉnh có diện tích lớn trước. Chỉ thêm batch sau khi thời gian, RAM và chất lượng output đã được đo.
