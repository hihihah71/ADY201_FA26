# Giai đoạn 12 — Chạy toàn quốc và cập nhật dữ liệu

## Mục tiêu

Chạy `run-region` cho mọi khu vực đang bật và tổng hợp kết quả toàn quốc.

## Cần có trước

- `run-region` chạy ổn định cho ít nhất Hà Nội và Đà Nẵng.
- `--resume` đã được kiểm tra khi một step bị lỗi.
- Tất cả khu vực cần chạy đã có trong `regions.json`.

## Luồng chạy toàn quốc

```text
regions.json với enabled=true
              ↓ lần lượt từng khu vực
          run-region
              ↓
  Parquet/GraphML theo khu vực
              ↓ một bước ghi DuckDB
      bảng tổng hợp toàn quốc
              ↓
      model + bản đồ + báo cáo
```

## Luồng cập nhật snapshot

```text
kiểm tra file Geofabrik mới
              ↓ nếu checksum thay đổi
đăng ký snapshot mới
              ↓
POI toàn quốc → run-all → aggregate-national
```

## Các bước thực hiện

1. Đọc tất cả khu vực có `enabled=true` từ `regions.json`.
2. Gọi `run-region` lần lượt cho từng khu vực.
3. Một khu vực lỗi thì ghi failed và tiếp tục khu vực sau.
4. Hỗ trợ `--resume` để chỉ chạy khu vực hoặc step còn thiếu.
5. Sau khi các worker kết thúc, dùng một process cập nhật DuckDB.
6. Ghép Parquet của các khu vực thành national feature dataset.
7. Huấn luyện national scaler/model riêng có version.
8. Tạo báo cáo completed, failed và skipped.
9. Chỉ thêm lịch chạy tự động sau khi run-all thủ công ổn định.

## File cần tạo hoặc sửa

```text
src/ady201/batch.py
src/ady201/aggregation.py
src/ady201/national_model.py
src/ady201/main.py
```

Lệnh mục tiêu:

```powershell
ady201 run-all --resume
ady201 run-all --snapshot <snapshot_id> --resume
ady201 batch-status --snapshot <snapshot_id>
ady201 aggregate-national --snapshot <snapshot_id>
ady201 check-update
```

## Quy tắc

- Bắt đầu với một khu vực tại một thời điểm.
- Chỉ tăng số worker sau khi đo RAM và thời gian.
- Không cho nhiều process ghi cùng file DuckDB.
- Một khu vực lỗi không làm dừng toàn bộ batch.
- Không hard-code số lượng hoặc tên tỉnh/thành.
- Không ghi đè model và snapshot cũ.
- National model phải dùng một scaler và model chung cho toàn bộ cell.

## Cần học trước

- Vòng lặp batch và xử lý lỗi riêng từng phần tử.
- Chạy tuần tự và chạy song song khác nhau thế nào.
- Ghép nhiều file Parquet bằng DuckDB.
- Version cho snapshot, config và model.
- Giới hạn RAM khi xử lý dữ liệu lớn.

## Tìm hiểu thêm

- Từ khóa: `Python concurrent futures`; chỉ dùng sau bản tuần tự.
- Từ khóa: `DuckDB parquet glob hive partitioning`.
- Từ khóa: `batch failure isolation`.
- Từ khóa: `Windows Task Scheduler Python`; chỉ học ở bước cuối.

## Phân công

### Thành

- Viết aggregation và national DuckDB views.
- Kiểm tra duplicate, coverage và khóa dữ liệu.

### Hiếu

- Đo RAM/thời gian và quyết định số worker an toàn.
- Kiểm tra graph artifact được dùng lại thay vì tạo lại sai.

### Quang

- Viết `run-all`, `batch-status` và bảng tổng kết.
- Tạo national clustering, bản đồ và report.

## Đầu ra

```text
outputs/{snapshot_id}/batch_summary.csv
data/processed/{snapshot_id}/national/cell_features.parquet
data/models/{snapshot_id}/national/model_metadata.json
outputs/{snapshot_id}/national/maps/
outputs/{snapshot_id}/national/report/
```

## Hoàn thành khi

- Batch tiếp tục khi cố ý làm một khu vực bị lỗi.
- `--resume` chỉ chạy phần thiếu hoặc failed.
- POI trong buffer không bị tính hai lần ở tổng hợp toàn quốc.
- Mọi kết quả truy được snapshot, config và model version.
- Chạy snapshot mới không ghi đè kết quả snapshot cũ.
