# Giai đoạn 03 — DuckDB cơ bản

## Mục tiêu

Python tự tạo và kết nối tới DuckDB mà không cần pgAdmin.

## Luồng

```text
ady201 db-init
      ↓
database.py đọc 001_schema.sql
      ↓
data/database/ady201.duckdb
      ↓
bảng regions
```

## Vì sao hiện tại chỉ có một bảng

Giai đoạn này mới cần lưu danh sách khu vực, nên chỉ tạo bảng `regions`.

- `pipeline_runs` và `pipeline_steps` được thêm ở giai đoạn 11 khi pipeline đã tồn tại.
- Chưa cần bảng `artifacts`; output được tìm theo cấu trúc thư mục cố định.

## Trạng thái hiện tại

- Phần connect, initialize và check đã có.
- Phần đồng bộ `regions.json` vào DuckDB chưa làm.

## Các bước thực hiện chi tiết

### Bước 1 — Tạo schema tối thiểu

Mở `sql/001_schema.sql` và chỉ tạo bảng đang dùng:

```sql
CREATE TABLE IF NOT EXISTS regions (
    region_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    boundary_path VARCHAR NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);
```

Ý nghĩa:

- `IF NOT EXISTS`: chạy `db-init` nhiều lần không báo bảng đã tồn tại.
- `PRIMARY KEY`: không cho hai dòng dùng cùng `region_id`.
- `NOT NULL`: không cho thiếu dữ liệu bắt buộc.
- `DEFAULT TRUE`: region mới mặc định được bật.

Kết quả cần thấy: chạy file SQL lần đầu và lần thứ hai đều thành công, bảng vẫn chỉ có bốn cột đã định nghĩa.

### Bước 2 — Viết `connect_database()`

- Xác định đường dẫn `data/database/ady201.duckdb` từ thư mục project.
- Tạo thư mục cha nếu chưa tồn tại.
- Gọi `duckdb.connect()` với đường dẫn file.
- Trả connection; không chạy SQL trong hàm này.

Connection tới đường dẫn file tạo database lưu trên đĩa, khác với database `:memory:` sẽ mất khi chương trình kết thúc.

Kết quả cần thấy: sau khi đóng connection, file `data/database/ady201.duckdb` vẫn tồn tại.

### Bước 3 — Viết `initialize_database()`

- Đọc toàn bộ `001_schema.sql` bằng UTF-8.
- Mở connection bằng `connect_database()`.
- Gọi `connection.execute(schema_sql)`.
- Luôn đóng connection trong `finally`.

Không đưa nội dung `CREATE TABLE` trực tiếp vào Python; schema thuộc file SQL.

Kết quả cần thấy: gọi `initialize_database()` tạo được bảng `regions` và gọi lại không phát sinh lỗi.

### Bước 4 — Viết `check_database()`

- Nếu file DuckDB chưa tồn tại, trả `ready=false`.
- Đọc `information_schema.tables` để xem bảng `regions` có tồn tại không.
- Nếu có bảng, chạy `SELECT COUNT(*) FROM regions`.
- Trả một `dict` ngắn gồm `ready` và `region_count`.

Hàm này mở database ở chế độ `read_only=True` để không thay đổi dữ liệu.

Kết quả cần thấy: database chưa khởi tạo trả `ready=false`; database hợp lệ trả `ready=true`.

### Bước 5 — Nối hai lệnh vào `main.py`

- `db-init` gọi `initialize_database()` và không cần tham số.
- `db-check` gọi `check_database()` rồi hiển thị kết quả.

Chạy theo thứ tự:

```powershell
ady201 db-init
ady201 db-check
```

Kết quả ban đầu hợp lệ:

```json
{
  "ready": true,
  "region_count": 0
}
```

Kết quả cần thấy: hai command chạy trực tiếp từ terminal, không cần mở giao diện quản trị database.

### Bước 6 — Đồng bộ region vào bảng

- Đọc danh sách bằng `load_regions()` của giai đoạn 02.
- Với mỗi region, dùng câu `INSERT ... ON CONFLICT DO UPDATE`.
- Truyền giá trị bằng parameter `?`, không ghép SQL bằng f-string.
- Chạy lại đồng bộ không được tạo dòng trùng.
- Tạo hàm `sync_regions()` trong `database.py` và để lệnh `db-init` gọi hàm này sau khi tạo schema.

Sau khi đồng bộ Hà Nội và Đà Nẵng, `region_count` phải bằng `2`.

Kết quả cần thấy: chạy `db-init` lần nữa vẫn có đúng hai hàng và các thay đổi trong JSON được cập nhật.

## File cần tạo hoặc sửa

```text
sql/001_schema.sql
src/ady201/database.py
src/ady201/main.py
```

## Bốn hàm cần hiểu

- `connect_database()`: mở file DuckDB và trả connection.
- `initialize_database()`: đọc SQL và tạo bảng.
- `check_database()`: kiểm tra bảng `regions` và đếm số dòng.
- `sync_regions()`: chép cấu hình region hiện tại vào bảng và cập nhật hàng đã tồn tại.

## Lỗi thường gặp

- Mở pgAdmin để import: DuckDB là file riêng và toàn bộ schema phải được Python tạo.
- Ghép giá trị region vào câu SQL bằng f-string: dễ lỗi dấu nháy và không an toàn.
- Dùng database `:memory:` rồi mất toàn bộ bảng khi chương trình kết thúc.
- Quên đóng connection khiến lần chạy sau khó ghi vào file trên Windows.

## Cần học trước

- `duckdb.connect()`.
- `connection.execute()`.
- SQL `CREATE TABLE IF NOT EXISTS`.
- `PRIMARY KEY`, `NOT NULL` và `DEFAULT`.
- `try/finally` để luôn đóng connection.

## Phân công

### Thành

- Viết `001_schema.sql`, `database.py` và hàm `sync_regions()`.

### Hiếu

- Kiểm tra chạy `db-init` nhiều lần không làm mất dữ liệu.

### Quang

- Thêm `db-init`, `db-check` vào `main.py`.
- Viết hướng dẫn chạy hai lệnh.

## Hoàn thành khi

```powershell
ady201 db-init
ady201 db-check
```

Kết quả `db-check` có `ready: true`. Chạy `db-init` lần thứ hai vẫn thành công.
