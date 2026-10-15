# Giai đoạn 12 — Chạy toàn quốc

## Mục tiêu

Chạy `run-region` lần lượt cho mọi khu vực đang bật và tổng hợp kết quả toàn quốc từ cùng file `vietnam.osm.pbf`.

Giai đoạn này không tải PBF mới, không quản lý snapshot và không lập lịch cập nhật dữ liệu.

## Cần có trước

- `run-region` chạy ổn định cho ít nhất Hà Nội và Đà Nẵng.
- `--resume` đã được kiểm tra khi một step bị lỗi.
- Tất cả khu vực cần chạy đã có boundary và `enabled=true` trong `regions.json`.
- File `data/raw/osm/vietnam.osm.pbf` được giữ nguyên trong toàn bộ batch.

## Luồng

```text
regions.json với enabled=true
              ↓
kiểm tra một vietnam.osm.pbf cố định
              ↓
       lần lượt run-region
              ↓
 Parquet/GraphML theo từng region
              ↓
 ghép cell_features toàn quốc
              ↓
 model + bản đồ + báo cáo toàn quốc
```

## Các bước thực hiện

### Bước 1 — Lấy danh sách region cần chạy

- Đọc `regions.json` bằng loader của giai đoạn 02.
- Chỉ giữ region có `enabled=true`.
- Validate toàn bộ danh sách và boundary trước khi bắt đầu batch.
- Sắp xếp theo `region_id` để hai lần chạy có cùng thứ tự.

Kết quả cần thấy: batch hiển thị danh sách region cụ thể và không có tên tỉnh/thành hard-code trong `batch.py`.

### Bước 2 — Kiểm tra đầu vào dùng chung

- Gọi `get_osm_path()` một lần trước vòng lặp.
- Dừng toàn bộ batch nếu PBF thiếu, rỗng hoặc Pyrosm không mở được.
- Truyền cùng một `Path` cho mọi lần gọi `run_region()`.
- Không thay file PBF cho đến khi batch kết thúc.

Kết quả cần thấy: mọi region dùng đúng `data/raw/osm/vietnam.osm.pbf`.

### Bước 3 — Chạy tuần tự từng region

- Tạo một `batch_id` để nhóm biết các region thuộc cùng lần chạy.
- Gọi trực tiếp `run_region(region_id, resume=...)` trong vòng lặp.
- Bắt đầu với một region tại một thời điểm để dễ đo RAM và sửa lỗi.
- Ghi thời gian bắt đầu, kết thúc và `run_id` của từng region.

Kết quả cần thấy: thay danh sách `enabled` là thay được phạm vi batch mà không sửa code.

### Bước 4 — Cô lập lỗi theo region

- Bọc mỗi lần gọi `run_region()` bằng `try/except` riêng.
- Nếu một region lỗi, lưu region, step lỗi và message rồi tiếp tục region sau.
- Không bắt `KeyboardInterrupt` như lỗi thường; người dùng chủ động dừng thì batch phải dừng.
- Cuối batch trả trạng thái thất bại một phần nếu có region failed.

Kết quả cần thấy: một boundary bị lỗi không làm mất kết quả của các region đã chạy thành công.

### Bước 5 — Resume batch

- Region đã completed và còn đủ output hợp lệ được đánh dấu `skipped`.
- Region failed hoặc đang dở được gọi lại bằng `run_region(..., resume=True)`.
- Nếu output của một step bị mất, pipeline chạy lại từ step đó.
- Batch summary phải phân biệt `completed`, `failed`, `resumed` và `skipped`.

Kết quả cần thấy: chạy `run-all --resume` không tạo lại graph của region đã hoàn thành hợp lệ.

### Bước 6 — Không ghi DuckDB đồng thời

- Phiên bản đầu chạy tuần tự và cập nhật DuckDB sau từng region.
- Chỉ nghiên cứu worker song song sau khi đã đo RAM và thời gian.
- Nếu sau này có worker, worker chỉ ghi file của region; một process điều phối cập nhật DuckDB.
- Không chia sẻ một DuckDB connection cho nhiều process.

Kết quả cần thấy: batch không gặp lỗi lock database.

### Bước 7 — Ghép feature toàn quốc

- Chỉ lấy `cell_features.parquet` từ các region completed và cùng `grid_version`.
- Dùng DuckDB đọc các file Parquet rồi ghi `data/processed/national/cell_features.parquet`.
- Kiểm tra khóa `(region_id, cell_id)` không trùng.
- Kiểm tra số hàng national bằng tổng số cell của các region được ghép.

Kết quả cần thấy: có một feature matrix toàn quốc và vẫn truy được mỗi cell thuộc region nào.

### Bước 8 — Tạo model và báo cáo toàn quốc

- Dùng một danh sách feature và một quy tắc missing chung cho mọi region.
- Fit một scaler và một model chung trên national dataset.
- Lưu feature list, scaler, random seed, số cluster và cấu hình model.
- Tạo bản đồ, cluster profile và báo cáo coverage toàn quốc.

Kết quả cần thấy: cluster có cùng ý nghĩa giữa các region vì chúng đến từ cùng một model.

### Bước 9 — Tạo báo cáo trạng thái batch

- Ghi `batch_summary.csv` với một hàng cho mỗi region.
- Mỗi hàng có trạng thái, thời gian, `run_id`, step lỗi và output chính.
- `batch-status` hiển thị số completed, failed, skipped và danh sách cần chạy lại.
- Không che region lỗi bằng cách chỉ xuất các region thành công.

Kết quả cần thấy: đọc một file là biết batch đã chạy đến đâu và region nào cần sửa.

## File cần tạo hoặc sửa

```text
src/ady201/batch.py
src/ady201/aggregation.py
src/ady201/national_model.py
src/ady201/main.py
```

Lệnh mục tiêu:

```powershell
ady201 run-all
ady201 run-all --resume
ady201 batch-status
ady201 aggregate-national
```

Không tạo lệnh `check-update` và không nhận tham số `--snapshot`.

## Quy tắc

- Mọi region dùng cùng một file `vietnam.osm.pbf`.
- Bắt đầu bằng chạy tuần tự.
- Không cho nhiều process ghi cùng file DuckDB.
- Một region lỗi không làm dừng toàn bộ batch.
- Không hard-code số lượng hoặc tên tỉnh/thành.
- National model dùng một scaler và model chung cho toàn bộ cell.

## Lỗi thường gặp

- Thay PBF khi batch vẫn đang chạy.
- Chạy song song quá sớm làm hết RAM hoặc khóa DuckDB.
- Ghép file bằng wildcard nhưng không kiểm tra `grid_version`.
- So sánh trực tiếp nhãn cluster từ các model riêng của từng tỉnh.
- Bỏ qua region lỗi trong báo cáo và hiểu nhầm coverage đã đủ.

## Cần học trước

- Vòng lặp batch và `try/except` theo từng phần tử.
- Chạy tuần tự và chạy song song khác nhau thế nào.
- Ghép nhiều file Parquet bằng DuckDB.
- Khóa ghép `(region_id, cell_id)`.
- Giới hạn RAM khi xử lý dữ liệu lớn.

## Tìm hiểu thêm

- Từ khóa: `DuckDB read multiple parquet files`.
- Từ khóa: `batch failure isolation`.
- Từ khóa: `Python concurrent futures`; chỉ học sau khi bản tuần tự ổn định.

## Phân công

### Thành

- Viết aggregation và DuckDB query ghép feature toàn quốc.
- Kiểm tra duplicate, số cell và coverage.

### Hiếu

- Đo RAM/thời gian của từng region.
- Kiểm tra graph được dùng lại đúng khi chạy `--resume`.

### Quang

- Viết `run-all`, `batch-status` và `batch_summary.csv`.
- Tạo national clustering, bản đồ và report theo template.

## Đầu ra

```text
outputs/batch_summary.csv
data/processed/national/cell_features.parquet
data/models/national/model_metadata.json
outputs/national/maps/
outputs/national/report/
```

## Hoàn thành khi

- Batch tiếp tục khi cố ý làm một region bị lỗi.
- `--resume` chỉ chạy phần thiếu hoặc failed.
- POI có scope `network` không bị tính vào mật độ dịch vụ của region.
- Khóa `(region_id, cell_id)` không trùng.
- Mọi region trong batch dùng cùng một file PBF cố định.
