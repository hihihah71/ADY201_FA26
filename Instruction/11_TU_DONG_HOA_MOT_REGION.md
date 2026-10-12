# Giai đoạn 11 — Tự động hóa một khu vực

## Mục tiêu

Nhập một `region_id` và để Python tự chạy toàn bộ các bước theo đúng thứ tự.

## Cần có trước

- Từng lệnh từ giai đoạn 04 đến 10 chạy độc lập thành công.
- DuckDB lưu được trạng thái step.
- Hà Nội đã chạy đủ luồng bằng cách gọi từng lệnh.

## Luồng

```text
region_id + snapshot_id tùy chọn
              ↓
      kiểm tra đầu vào
              ↓
 chạy lần lượt từng step
              ↓
 artifact + trạng thái DuckDB
              ↓
       bản đồ và báo cáo
```

## Các bước thực hiện

1. Viết một hàm Python cho mỗi step.
2. Tạo danh sách thứ tự step trong `pipeline.py`.
3. Trước mỗi step, kiểm tra input bắt buộc đã tồn tại.
4. Sau mỗi step, lưu trạng thái và đường dẫn output vào DuckDB.
5. Nếu step lỗi, lưu `error_message` rồi dừng khu vực đó.
6. Với `--resume`, bỏ qua step đã hoàn thành và output vẫn hợp lệ.
7. Nếu không truyền snapshot, dùng snapshot đang được đánh dấu active.
8. Thêm `run-region` và `run-status` vào `main.py`.

## File cần tạo hoặc sửa

```text
src/ady201/pipeline.py
src/ady201/artifacts.py
src/ady201/run_state.py
src/ady201/main.py
```

Thứ tự step:

```text
prepare_boundary
extract_region_pbf
build_network
build_grid
select_region_pois
snap_pois_and_cells
calculate_accessibility
calculate_service_features
calculate_road_features
build_feature_matrix
calculate_scores
run_clustering
render_maps_and_report
```

Lệnh mục tiêu:

```powershell
ady201 run-region --region hanoi
ady201 run-region --region danang --snapshot <snapshot_id>
ady201 run-region --region hanoi --resume
ady201 run-status --region hanoi
```

## Quy tắc

- `main.py` chỉ nhận tham số; logic pipeline nằm trong `pipeline.py`.
- Chạy tuần tự trước, chưa chạy song song.
- Step chạy lại không được tạo duplicate.
- Chỉ bỏ qua step khi trạng thái completed và output vẫn tồn tại.
- Không tạo `cli.py`, `context.py` hoặc hệ thống logging riêng.
- Trạng thái và lỗi nằm trong DuckDB; kết quả cuối có `run_summary.json`.

## Cần học trước

- Gọi hàm theo thứ tự.
- Exception và `try/except`.
- Idempotent: chạy lại không làm sai dữ liệu.
- Checksum và cách xác định output còn hợp lệ.
- Resume pipeline.

## Tìm hiểu thêm

- Từ khóa: `Python pipeline steps pattern`.
- Từ khóa: `idempotent data pipeline`.
- Từ khóa: `checksum cache invalidation`.

## Phân công

### Thành

- Nối trạng thái step với DuckDB và transaction.
- Kiểm tra SQL được gọi đúng bước.

### Hiếu

- Chốt dependency giữa graph, snap và accessibility.
- Mô phỏng lỗi giữa bước nặng rồi kiểm tra `--resume`.

### Quang

- Thêm lệnh `run-region`, `run-status` vào `main.py`.
- Tạo `run_summary.json` dễ đọc.

## Đầu ra

```text
outputs/{snapshot_id}/{region_id}/run_summary.json
```

Cùng toàn bộ artifact của các giai đoạn 04 đến 10.

## Hoàn thành khi

- Hà Nội chạy hết bằng một lệnh.
- Đà Nẵng chạy bằng cách chỉ đổi `region_id`.
- Lỗi ở clustering không làm graph chạy lại khi dùng `--resume`.
- Có thể xem step nào completed hoặc failed trong DuckDB.
