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

### Bước 1 — Lấy danh sách region cần chạy

- Đọc `regions.json` bằng loader của giai đoạn 02 và chỉ giữ region có `enabled=true`.
- Validate toàn bộ danh sách trước khi bắt đầu để không chạy nửa batch mới phát hiện config sai.
- Sắp xếp theo `region_id` để thứ tự ổn định và dễ so sánh hai lần chạy.
- Đồng bộ bảng `regions` trong DuckDB nhưng vẫn coi file JSON là nơi nhóm chỉnh cấu hình.

Kết quả cần thấy: lệnh batch in được danh sách region cụ thể, không hard-code tên tỉnh/thành trong `batch.py`.

### Bước 2 — Chạy tuần tự phiên bản đầu

- Tạo một `batch_id` và chọn snapshot một lần trước vòng lặp.
- Với từng region, gọi trực tiếp hàm `run_region()` thay vì mở một terminal mới.
- Truyền cùng `snapshot_id` và cờ `resume` cho mọi region.
- Bắt đầu với một region tại một thời điểm để dễ đo RAM và tìm lỗi.

Kết quả cần thấy: đổi danh sách `enabled` là thay đổi được phạm vi batch mà không sửa code.

### Bước 3 — Cô lập lỗi theo region

- Bọc mỗi lần gọi `run_region()` bằng `try/except` riêng.
- Nếu lỗi, thêm một hàng failed gồm region, step lỗi và message rồi tiếp tục region sau.
- Không bắt `KeyboardInterrupt` như lỗi thông thường; người dùng chủ động dừng thì batch phải dừng.
- Cuối batch trả trạng thái thất bại một phần nếu có ít nhất một region failed.

Kết quả cần thấy: một boundary bị lỗi không làm mất kết quả của các region khác.

### Bước 4 — Resume ở hai cấp

- Ở cấp batch, bỏ qua region đã completed cho cùng snapshot và cùng config version.
- Với region failed hoặc đang dở, gọi `run_region(..., resume=True)` để tiếp tục từ step hợp lệ gần nhất.
- Region có config thay đổi phải chạy lại các step bị ảnh hưởng dù lần cũ completed.
- Ghi rõ `completed`, `failed`, `resumed` hoặc `skipped` trong batch summary.

Kết quả cần thấy: chạy lại batch không tạo lại graph của region đã hoàn thành hợp lệ.

### Bước 5 — Tránh nhiều tiến trình cùng ghi DuckDB

- Phiên bản tuần tự có thể cập nhật DuckDB sau mỗi region.
- Nếu sau này thêm worker song song, mỗi worker chỉ ghi artifact/summary riêng của region.
- Một process điều phối đọc các summary và cập nhật DuckDB sau khi worker kết thúc.
- Không truyền chung một DuckDB connection cho nhiều process.

Kết quả cần thấy: batch không gặp lỗi lock hoặc database hỏng do ghi đồng thời.

### Bước 6 — Tạo national feature dataset

- Chỉ lấy `cell_features.parquet` từ region completed của đúng snapshot/grid version.
- Dùng DuckDB đọc nhiều file Parquet, thêm/kiểm tra `region_id`, rồi ghi một file national Parquet.
- Kiểm tra khóa `(snapshot_id, region_id, cell_id)` không trùng.
- POI buffer không được cộng lại vì national dataset ghép feature cell đã tính trong analysis boundary.

Kết quả cần thấy: số hàng national bằng tổng số cell của các region đã đưa vào.

### Bước 7 — Huấn luyện model so sánh toàn quốc

- Dùng cùng danh sách feature cho toàn bộ cell và xử lý missing theo một quy tắc chung.
- Fit một scaler và một model trên national dataset; không ghép nhãn từ các model tỉnh riêng.
- Lưu `model_version`, feature list, scaler, random seed, `k`, snapshot và config version.
- Tạo profile theo region để biết một cluster phân bố ở đâu nhưng không dùng tên region làm feature.

Kết quả cần thấy: nhãn cluster có cùng ý nghĩa trên mọi region trong cùng national model.

### Bước 8 — Tạo báo cáo batch

- Ghi `batch_summary.csv` với một hàng mỗi region: trạng thái, thời gian, run ID, step lỗi và output chính.
- `batch-status` tổng hợp số completed, failed, skipped và danh sách cần chạy lại.
- Tạo báo cáo coverage: số region dự kiến, số đã có boundary, số hoàn tất và số cell.
- Không che lỗi bằng cách chỉ xuất các region thành công.

Kết quả cần thấy: nhìn một file là biết batch đã xử lý đến đâu và cần sửa vùng nào.

### Bước 9 — Chỉ lập lịch sau khi chạy tay ổn định

- Trước tiên chạy `check-update` thủ công để so checksum/timestamp với snapshot active.
- Chỉ khi có snapshot mới mới thực hiện: đăng ký snapshot → build POI toàn quốc → run-all → aggregate-national.
- Tạo script/lệnh duy nhất có exit code rõ ràng rồi mới đưa vào Windows Task Scheduler hoặc hệ thống khác.
- Giữ output theo snapshot; không ghi đè kết quả cũ khi lịch chạy kích hoạt.

Kết quả cần thấy: lần chạy tự động có thể kiểm tra lại bằng batch summary và không cần mở pgAdmin.

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

## Lỗi thường gặp

- Mỗi region tự chọn active snapshot tại thời điểm khác nhau, làm national dataset trộn ngày dữ liệu.
- Chạy song song quá sớm và để nhiều process ghi cùng DuckDB.
- Ghép mọi file theo wildcard mà không lọc snapshot/grid version.
- So sánh trực tiếp nhãn cluster từ các model riêng của từng tỉnh.

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
