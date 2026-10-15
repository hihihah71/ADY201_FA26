# Giai đoạn 11 — Tự động hóa một khu vực

## Mục tiêu

Nhập một `region_id` và để Python tự chạy toàn bộ các bước theo đúng thứ tự.

## Cần có trước

- Từng lệnh từ giai đoạn 04 đến 10 chạy độc lập thành công.
- DuckDB lưu được trạng thái step.
- Hà Nội đã chạy đủ luồng bằng cách gọi từng lệnh.

## Luồng

```text
region_id + vietnam.osm.pbf
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

### Bước 1 — Biến mỗi công đoạn thành một hàm gọi được

- Mỗi step từ giai đoạn 04 đến 10 cần có một hàm Python công khai, không phụ thuộc vào biến global thay đổi ngầm.
- Dùng đầu vào thống nhất như `region_id`, config, PBF cố định và các đường dẫn cần thiết.
- Hàm trả về đường dẫn artifact hoặc một dictionary kết quả nhỏ; không chỉ tạo file rồi trả về `None`.
- Chạy riêng từng hàm/lệnh thành công trước khi nối vào pipeline.

Kết quả cần thấy: có thể gọi và kiểm tra từng step độc lập khi xảy ra lỗi.

### Bước 2 — Khai báo thứ tự và phụ thuộc của step

- Trong `pipeline.py`, tạo một danh sách có thứ tự đúng như phần “Thứ tự step” bên dưới.
- Mỗi phần tử cần có tên step, hàm cần gọi, input bắt buộc và output dự kiến.
- Mọi đường dẫn output phải được tạo từ `region_id`; PBF luôn lấy qua `get_osm_path()`.
- Pipeline duyệt danh sách tuần tự trong phiên bản đầu.

Kết quả cần thấy: đọc một cấu trúc duy nhất là biết pipeline chạy bước nào trước và bước nào sau.

### Bước 3 — Kiểm tra đầu vào trước khi chạy step

- Xác nhận region tồn tại và `enabled=true`.
- Xác nhận `data/raw/osm/vietnam.osm.pbf` tồn tại và không rỗng.
- Trước từng step, kiểm tra file/bảng phụ thuộc tồn tại, không rỗng và thuộc đúng region.
- Báo thiếu input bằng tên step và đường dẫn cụ thể, không để thư viện sâu bên trong báo lỗi khó hiểu.

Kết quả cần thấy: pipeline dừng sớm với lỗi dễ sửa nếu thiếu boundary, graph hoặc Parquet.

### Bước 4 — Tạo bảng trạng thái chạy

- Tạo `sql/030_run_state.sql` ở giai đoạn này.
- `pipeline_runs` lưu một lần chạy: `run_id`, `region_id`, trạng thái, thời gian bắt đầu/kết thúc.
- `pipeline_steps` lưu từng bước: `run_id`, `step_name`, trạng thái, `output_path`, thời gian và `error_message`.
- Khi tạo run mới, thêm các step với trạng thái `pending`; trước khi gọi hàm đổi thành `running`, sau khi thành công đổi thành `completed`.

Kết quả cần thấy: DuckDB cho biết lần chạy nào đang dở và bước cuối cùng đã thành công.

### Bước 5 — Xử lý lỗi tại đúng step

- Bọc lời gọi từng step bằng `try/except`, không bọc toàn pipeline bằng một thông báo lỗi chung.
- Khi lỗi, cập nhật step thành `failed`, lưu loại lỗi và nội dung ngắn gọn rồi cập nhật run thành `failed`.
- Dừng các step còn lại của region vì đầu vào tiếp theo có thể không hợp lệ.
- Ném lỗi trở lại CLI để tiến trình trả exit code khác 0.

Kết quả cần thấy: `run-status` chỉ ra chính xác step lỗi và nguyên nhân gần nhất.

### Bước 6 — Cài đặt `--resume` an toàn

- Chỉ skip khi trạng thái là `completed` và output path vẫn tồn tại.
- Kiểm tra thêm file không rỗng, schema đúng và config liên quan chưa thay đổi.
- Nếu output mất hoặc config đầu vào đổi, chạy lại step đó và tất cả step phụ thuộc phía sau.
- Step phải idempotent: chạy lại sẽ thay đúng artifact của region, không nối thêm duplicate.

Kết quả cần thấy: xóa output của một step rồi chạy `--resume` sẽ tạo lại từ step đó, không bỏ qua sai.

### Bước 7 — Dùng một PBF chung trong toàn bộ run

- Pipeline gọi `get_osm_path()` đúng một lần khi bắt đầu.
- Truyền `Path` này cho bước tạo POI và bước Pyrosm tạo network; không tìm PBF ở thư mục khác.
- Không nhận tham số `--snapshot` và không truy vấn active snapshot trong DuckDB.
- Không thay `vietnam.osm.pbf` cho tới khi `run-region` hoặc `run-all` kết thúc.

Kết quả cần thấy: mọi artifact trong một lần chạy đều bắt nguồn từ cùng file `vietnam.osm.pbf`.

### Bước 8 — Thêm CLI cho người dùng cuối

- `run-region` nhận `--region` và tùy chọn `--resume`.
- `run-status` nhận region hoặc run ID và hiển thị từng step theo đúng thứ tự.
- `main.py` chỉ đọc tham số rồi gọi hàm trong `pipeline.py`; không đặt logic xử lý dữ liệu ở CLI.
- Cuối run, ghi `run_summary.json` gồm trạng thái, region, thời gian và đường dẫn output chính.

Kết quả cần thấy: Hà Nội hoặc Đà Nẵng chạy bằng một lệnh, không cần mở Python hay DuckDB thủ công.

## File cần tạo hoặc sửa

```text
src/ady201/pipeline.py
src/ady201/run_state.py
src/ady201/main.py
sql/030_run_state.sql
```

Thứ tự step:

```text
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
ady201 run-region --region danang
ady201 run-region --region hanoi --resume
ady201 run-status --region hanoi
```

## Quy tắc

- `main.py` chỉ nhận tham số; logic pipeline nằm trong `pipeline.py`.
- Chạy tuần tự trước, chưa chạy song song.
- Step chạy lại không được tạo duplicate.
- Chỉ bỏ qua step khi trạng thái completed và output vẫn tồn tại.
- Không tạo `cli.py`, `context.py` hoặc hệ thống logging riêng.
- Tạo hai bảng `pipeline_runs` và `pipeline_steps` ở giai đoạn này.
- Trạng thái, lỗi và đường dẫn output nằm trong `pipeline_steps`.
- Kết quả cuối có `run_summary.json`.

## Lỗi thường gặp

- Thấy trạng thái `completed` là skip ngay dù file output đã bị xóa hoặc config đã đổi.
- Thay `vietnam.osm.pbf` khi pipeline đang chạy, khiến các artifact không còn cùng nguồn.
- Bắt lỗi nhưng không trả exit code lỗi, làm batch hiểu nhầm region đã thành công.
- Đặt toàn bộ logic vào `main.py`, khiến khó gọi lại và khó xác định step lỗi.

## Cần học trước

- Gọi hàm theo thứ tự.
- Exception và `try/except`.
- Idempotent: chạy lại không làm sai dữ liệu.
- Cách kiểm tra output tồn tại, không rỗng và đúng schema.
- Resume pipeline.

## Tìm hiểu thêm

- Từ khóa: `Python pipeline steps pattern`.
- Từ khóa: `idempotent data pipeline`.
- Từ khóa: `pipeline output validation`.

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
outputs/{region_id}/run_summary.json
```

Cùng toàn bộ artifact của các giai đoạn 04 đến 10.

## Hoàn thành khi

- Hà Nội chạy hết bằng một lệnh.
- Đà Nẵng chạy bằng cách chỉ đổi `region_id`.
- Lỗi ở clustering không làm graph chạy lại khi dùng `--resume`.
- Có thể xem step nào completed hoặc failed trong DuckDB.
