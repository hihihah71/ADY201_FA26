# Giai đoạn 11 — Tự động hóa một tỉnh

## Nhiệm vụ tổng quát

Gom các hàm đã chạy đúng thành một hàm `run_region(region_id)`. Người dùng chỉ nhập tên tỉnh và không mở notebook, DuckDB hay pgAdmin.

## Luồng

```text
ady201 run-region --region hanoi
                ↓
          đọc config + boundary
                ↓
          lấy POI và đường
                ↓
       tạo cell và điểm đại diện
                ↓
      POI features + road features
                ↓
       ghép và lưu bảng cuối
```

## Những thứ cần thay đổi

- Tạo `pipeline.py` chứa `run_region()`.
- `main.py` chỉ nhận tham số rồi gọi pipeline.
- Phiên bản đầu chạy tuần tự, chưa cần resume, worker hoặc bảng trạng thái phức tạp.

## Các bước thực hiện

### Bước 1 — Chốt các hàm đầu vào

Pipeline cần gọi được các hàm sau:

```text
get_project_config()
get_categories()
get_region(region_id)
get_osm_path()
extract_region_data(...)
create_cells(...)
create_cell_points(...)
build_poi_features(...)
build_road_features(...)
build_cell_features(...)
```

Mỗi hàm nhận input rõ ràng và trả dữ liệu hoặc đường dẫn rõ ràng. Không phụ thuộc vào biến trong notebook.

### Bước 2 — Viết pipeline tuần tự

```python
def run_region(region_id):
    config = get_project_config()
    region = get_region(region_id)
    boundary, pois, roads = extract_region_data(region, config)

    cells = create_cells(boundary, config["cell_size_m"])
    cell_points = create_cell_points(cells)

    poi_features = build_poi_features(
        cell_points,
        pois,
        boundary,
        config["poi_radii_m"],
    )
    road_features = build_road_features(
        cell_points,
        roads,
        boundary,
        config["road_radii_m"],
    )

    features = build_cell_features(cells, poi_features, road_features)
    save_region_outputs(region_id, pois, roads, cells, features)
    return features
```

Đây là khung luồng; tên hàm có thể điều chỉnh nhưng thứ tự không đổi.

### Bước 3 — Thêm câu lệnh terminal

Trong `main.py`, thêm subcommand:

```powershell
ady201 run-region --region hanoi
```

Nếu chưa cài lệnh `ady201`, có thể chạy:

```powershell
python -m ady201 run-region --region hanoi
```

### Bước 4 — Xử lý lỗi đơn giản

Dừng tỉnh hiện tại với thông báo rõ khi:

- Không tìm thấy region hoặc boundary.
- Thiếu PBF.
- Pyrosm không trả về POI/road.
- Output không có cell hoặc bị trùng `cell_id`.

Không bắt lỗi rồi bỏ qua im lặng.

### Bước 5 — Chạy thử theo thứ tự

1. Một tỉnh nhỏ.
2. Hà Nội hoặc Đà Nẵng.
3. Chạy lại cùng tỉnh và kiểm tra output được tạo nhất quán.

## Kiểm tra kết quả

- Một câu lệnh tạo đủ năm output trong thư mục của tỉnh.
- Không phải sửa tên tỉnh trong source code.
- Không cần mở notebook hoặc database thủ công.
- Số cell trong `cells.parquet` bằng số hàng trong bảng cuối.

## Kiến thức cần học

- Hàm điều phối pipeline.
- `argparse` subcommand và command-line arguments.
- `try/except` ở mức gọi lệnh, không bọc mọi dòng code.
- Tạo đường dẫn output bằng `Path`.

Từ khóa tìm thêm: `Python argparse subparsers`, `Python data pipeline functions`.

## Phân công

### Thành — trung bình/khó

- Viết `run_region()` và nối vào `main.py`.

### Hiếu — trung bình/khó

- Kiểm tra input/output giữa từng hàm và các điều kiện lỗi.

### Quang — dễ/trung bình

- Chạy lệnh từ một thư mục mới, ghi hướng dẫn và bảng kết quả mong đợi.

Review chéo: Quang chỉ dùng tài liệu để chạy; lỗi nào phải hỏi miệng thì bổ sung lại tài liệu.

## Hoàn thành khi

- `ady201 run-region --region hanoi` chạy hết luồng bằng một lệnh.
- Pipeline không chứa H3, graph hoặc bước import thủ công.
