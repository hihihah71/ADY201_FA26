# 02 — Cấu hình category và region

## `config/categories.json`

Đây là cấu hình POI đang được `poi.py` sử dụng trực tiếp.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `source` | Nguồn POI, hiện là `overture` |
| `category_column` | Category chi tiết trong GeoParquet |
| `group_column` | Hierarchy dùng để lấy group |
| `group_level` | Cấp hierarchy, hiện là `0` |
| `nearest_categories` | Category quan trọng cần khoảng cách gần nhất |
| `groups` | 13 group và toàn bộ category thuộc từng group |

Trạng thái hiện tại:

- 13 group.
- 22 category quan trọng cho nearest.
- 1.212 category Overture được liệt kê trong các group.

`poi.py` đọc cấu hình khi import:

```python
OVERTURE_GROUPS = list(CATEGORY_CONFIG["groups"])
NEAREST_CATEGORIES = list(CATEGORY_CONFIG["nearest_categories"])
```

Khi taxonomy Overture thay đổi, cập nhật JSON trước rồi mới chạy lại feature.

## `config/regions.json`

File này chứa danh sách 63 tỉnh/thành để tham khảo hoặc phục vụ batch trong tương lai. Pipeline hiện tại không đọc registry này; CLI nhận trực tiếp tên tỉnh:

```powershell
ady201 grf "Hà Nội" 29_3
```

Tên phải khớp với boundary trong OSM PBF. `region_id` chỉ là tên thư mục output và phải do người chạy chọn duy nhất.

## `config/project.json`

File chứa các tham số thử nghiệm cũ như tốc độ đi bộ và kích thước hexagon. Pipeline `grf` hiện không đọc file này.

Giá trị grid đang có hiệu lực nằm trực tiếp trong `regions.py`:

```python
cell_points = get_grid_cell(boundary, 200)
```

Không nên cho rằng sửa `hexagon_size` trong `project.json` sẽ đổi grid.

## Kiểm tra config

```powershell
python -c "import json; c=json.load(open('config/categories.json', encoding='utf-8')); print(len(c['groups']), len(c['nearest_categories']))"
```

Kết quả mong đợi:

```text
13 22
```
