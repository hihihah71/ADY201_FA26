# Giai đoạn 05 — Lấy POI và đường của một tỉnh

## Nhiệm vụ tổng quát

Đọc boundary của tỉnh, lấy đúng POI và các đoạn đường từ PBF, rồi lưu hai file GeoParquet.

Chỉ xử lý một tỉnh trong mỗi lần chạy để code dễ hiểu và không tốn RAM cho toàn quốc.

## Luồng

```text
region_id
    ↓ đọc boundary và lấy bbox
Pyrosm đọc vietnam.osm.pbf trong bbox
    ├── POI → phân loại → Point → clip theo tỉnh
    └── road edges → clip theo tỉnh
                ↓
       pois.parquet + roads.parquet
```

## Những thứ cần thay đổi

- `poi.py`: thêm hàm lấy và phân loại POI của một tỉnh.
- `network.py`: chỉ lấy road edges; không lấy nodes và không tạo graph.
- Không tạo POI toàn quốc.
- Không dùng boundary buffer. Bbox chỉ giúp Pyrosm đọc ít dữ liệu hơn; `clip()` mới quyết định đối tượng thuộc tỉnh.

## Các bước thực hiện

### Bước 1 — Đọc boundary

```python
import geopandas as gpd


def read_boundary(boundary_path):
    boundary = gpd.read_file(boundary_path).to_crs(4326)
    return boundary.dissolve()
```

`dissolve()` gộp các mảnh của cùng một tỉnh thành một geometry dùng chung.

### Bước 2 — Tạo Pyrosm reader theo bbox

```python
from pyrosm import OSM


def create_osm_reader(pbf_path, boundary):
    bbox = boundary.total_bounds
    return OSM(str(pbf_path), bounding_box=bbox)
```

Thứ tự bbox là `minx, miny, maxx, maxy`.

### Bước 3 — Lấy và chuẩn hóa POI

- Gọi `get_pois()` với các tag trong `categories.json`.
- Đổi từng record thành một trong bốn category.
- Giữ các cột: `osm_type`, `id`, `name`, `category`, `geometry`.
- Polygon POI được đổi thành một Point nằm trong polygon bằng `representative_point()`.
- Clip Point theo boundary tỉnh.

Khung hàm:

```python
def prepare_pois(raw_pois, boundary):
    pois = raw_pois.copy()
    pois["category"] = pois.apply(classify_poi, axis=1)
    pois = pois.dropna(subset=["category", "geometry"])
    pois["geometry"] = pois.geometry.representative_point()
    return pois.clip(boundary)
```

`classify_poi()` đọc tag trên một hàng và trả `hospital`, `school`, `supermarket`, `transit` hoặc `None`.

### Bước 4 — Lấy đường

```python
def prepare_roads(osm, boundary, network_type):
    roads = osm.get_network(network_type=network_type, nodes=False)
    roads = roads[["id", "highway", "geometry"]]
    roads = roads.dropna(subset=["geometry"])
    return roads.clip(boundary)
```

Tên cột Pyrosm có thể khác theo phiên bản. In `roads.columns` một lần và sửa danh sách cột cho đúng dữ liệu thực tế.

Giữ `nodes=False`: project cần geometry đường để đo chiều dài, không cần chia way thành các edge nhỏ phục vụ graph.

### Bước 5 — Đổi sang CRS mét

```python
metric_crs = boundary.estimate_utm_crs()
boundary_metric = boundary.to_crs(metric_crs)
pois_metric = pois.to_crs(metric_crs)
roads_metric = roads.to_crs(metric_crs)
```

Từ đây trở đi dùng các layer `_metric` để tính buffer, distance, area và length.

### Bước 6 — Lưu output

```text
data/processed/{region_id}/pois.parquet
data/processed/{region_id}/roads.parquet
```

GeoParquet giữ cả CRS và geometry.

## Kiểm tra kết quả

- `pois.geometry.geom_type` chỉ còn `Point`.
- `roads.geometry.geom_type` là `LineString` hoặc `MultiLineString`.
- POI chỉ có bốn category đã chốt.
- CRS của hai output giống nhau và có đơn vị mét.
- Hai file có dữ liệu và mở lại được bằng `gpd.read_parquet()`.

## Kiến thức cần học

- Boundary, bbox và sự khác nhau giữa bbox với polygon thật.
- `get_pois()`, `get_network()` và OSM tag.
- `representative_point()`, `clip()` và CRS.

Từ khóa tìm thêm: `Pyrosm get_pois custom filter`, `GeoPandas clip projected CRS`.

## Phân công

### Thành — trung bình/khó

- Viết phần đọc boundary, Pyrosm reader và lấy POI.

### Hiếu — trung bình/khó

- Viết phần lấy road, chọn cột và kiểm tra geometry/CRS.

### Quang — dễ/trung bình

- Kiểm tra thủ công số record, category, geometry và mở lại hai file output.

Review chéo: Thành review road; Hiếu review POI; Quang giải thích vì sao vẫn phải clip sau khi đã dùng bbox.

## Hoàn thành khi

- Một lệnh/hàm tạo được `pois.parquet` và `roads.parquet` cho một tỉnh.
- Không có nodes, graph, POI toàn quốc hoặc PBF riêng theo tỉnh.
