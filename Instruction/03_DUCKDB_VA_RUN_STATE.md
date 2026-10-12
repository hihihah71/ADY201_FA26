# Giai đoạn 03 — DuckDB và trạng thái chạy

## Mục tiêu

Python tự tạo và sử dụng một file DuckDB; không cần pgAdmin hoặc import thủ công.

## Cần có trước

- Đọc được config và khu vực ở giai đoạn 02.
- Biết SQL cơ bản: `CREATE TABLE`, `SELECT`, `INSERT` và `UPDATE`.

## Luồng

```text
main.py
   ↓ gọi database.py
sql/001_schema.sql
   ↓ tự chạy
data/database/ady201.duckdb
```

## Các bước thực hiện

1. Tạo file SQL chứa toàn bộ bảng ban đầu.
2. Viết `connect_database()` để mở DuckDB.
3. Viết `initialize_database()` để tự chạy file SQL.
4. Đồng bộ dữ liệu từ `regions.json` vào bảng `regions`.
5. Viết các hàm bắt đầu và kết thúc một lần chạy.
6. Dùng transaction để lỗi giữa chừng không ghi dữ liệu dở dang.
7. Thêm lệnh `db-init` và `db-check` vào `main.py`.

## File cần tạo hoặc sửa

```text
sql/001_schema.sql
src/ady201/database.py
src/ady201/run_state.py
src/ady201/main.py
data/database/ady201.duckdb
```

Bảng tối thiểu:

```text
regions
snapshots
pipeline_runs
pipeline_steps
artifacts
```

Trạng thái dùng thống nhất:

```text
pending
running
completed
failed
```

## Quy tắc

- Python luôn tự chạy SQL cần thiết.
- Không commit file `.duckdb`.
- Mỗi thời điểm chỉ có một process ghi vào DuckDB.
- File dữ liệu lớn lưu bằng Parquet; DuckDB lưu metadata và bảng tổng hợp.
- Lỗi được lưu vào cột `error_message`, không cần hệ thống logging riêng.

## Cần học trước

- DuckDB Python API.
- SQL DDL và CRUD cơ bản.
- Transaction, `commit` và `rollback`.
- Khóa chính và giá trị unique.

## Tìm hiểu thêm

- Từ khóa: `DuckDB Python connect execute`.
- Từ khóa: `database transaction rollback`.
- Từ khóa: `DuckDB read parquet`.

## Phân công

### Thành

- Thiết kế bảng và file `001_schema.sql`.
- Viết hàm mở database và khởi tạo schema.

### Hiếu

- Thiết kế bảng `artifacts` và `pipeline_steps`.
- Kiểm tra rollback khi cố ý tạo lỗi.

### Quang

- Thêm lệnh `db-init`, `db-check`.
- Viết câu lệnh hiển thị số bảng và trạng thái gần nhất.

## Đầu ra

- DuckDB được tạo tự động.
- Có thể lưu khu vực, snapshot và trạng thái chạy.
- Có thể xóa database rồi dựng lại bằng một lệnh.

## Hoàn thành khi

```powershell
ady201 db-init
ady201 db-check
```

chạy được trên máy mới mà không mở ứng dụng database nào.
