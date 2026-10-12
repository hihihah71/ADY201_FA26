# Giai đoạn 02 — Config và region registry

## Mục tiêu

Loại bỏ mọi giả định Hà Nội khỏi source code và quản lý tỉnh/thành bằng configuration.

## Nhiệm vụ tổng quát

- Tạo config chung cho pipeline.
- Tạo mapping category OSM.
- Tạo registry region.
- Tạo `RunContext` truyền vào mọi module.
- Validate config trước khi xử lý dữ liệu.

## Luồng

```text
project.yaml + categories.yaml + regions.yaml
                    ↓
              Config loader
                    ↓
               RunContext
                    ↓
             Pipeline modules
```

## Những thứ cần thay đổi

Tạo:

```text
config/project.yaml
config/categories.yaml
config/regions.yaml
src/ady201/config.py
src/ady201/context.py
src/ady201/registry/regions.py
```

`project.yaml` chứa:

- Walking speed.
- Accessibility thresholds.
- Hex resolution.
- Extraction buffer.
- Network types.
- Main-road types.
- Runtime settings.

`regions.yaml` chứa:

- `region_id`, slug, tên.
- Boundary path.
- OSM relation ID nếu có.
- Override buffer nếu cần.
- Trạng thái enabled.

Không để trong source:

- Bounding box Hà Nội.
- Tên file Hà Nội.
- CRS hoặc output path cố định.
- Danh sách amenity viết lặp lại.

## Kiến thức cần học

### Bắt buộc

- YAML.
- Dataclass/config validation.
- Stable ID/slug.
- Separation of configuration and code.

### Tìm hiểu sâu bên ngoài

- Pydantic Settings nếu cần validation mạnh.
- OSM administrative boundary và `admin_level`.
- Configuration hash.

## Phân công

### Thành

- Thiết kế `categories.yaml`.
- Định nghĩa mapping tag → category/subcategory.

### Hiếu

- Định nghĩa config cho walking/driving network, buffer và graph.
- Kiểm tra các tham số bắt buộc của region.

### Quang

- Tạo `regions.yaml`, config loader và validation report.
- Viết lệnh liệt kê region.

### Review

- Thành review category.
- Hiếu review boundary/network fields.
- Quang smoke test Hà Nội và Đà Nẵng.

## Đầu ra

- Config parse được thành `RunContext`.
- Thêm region không cần sửa source.

## Hoàn thành khi

- Test thiếu field bắt buộc phải báo lỗi rõ.
- Tìm trong `src/` không còn tọa độ bounding box Hà Nội.
- Tạo được context cho ít nhất Hà Nội và Đà Nẵng.

