# Tổng quan dự án

## Kết quả cuối cùng

Người dùng nhập một tỉnh/thành:

```powershell
ady201 run-region --region hanoi
```

Python tự tạo một bảng, mỗi hàng là một cell trong tỉnh. Bảng có các nhóm cột:

- Số bệnh viện, trường học, siêu thị và điểm giao thông công cộng trong bán kính 500 m, 1.000 m và 2.000 m.
- Khoảng cách thẳng từ tâm cell tới dịch vụ gần nhất, đơn vị mét.
- Tổng chiều dài và mật độ đường trong bán kính 500 m và 1.000 m.
- Polygon của cell để vẽ bản đồ.

Khi một tỉnh chạy đúng, dùng:

```powershell
ady201 run-all
```

để chạy lần lượt cho toàn bộ tỉnh/thành đã khai báo.

## Luồng duy nhất của project

```text
vietnam.osm.pbf + boundary tỉnh
                ↓
       lấy POI và đường của tỉnh
                ↓
      chia tỉnh thành grid vuông
                ↓
   chọn một điểm đại diện cho mỗi cell
                ↓
 ┌──────────────────────────────────────────┐
 │ POI trong 500 m / 1.000 m / 2.000 m     │
 │ POI gần nhất theo khoảng cách thẳng      │
 │ đường trong 500 m / 1.000 m             │
 └──────────────────────────────────────────┘
                ↓
 cell_features.parquet + cell_features.csv
```

Không có bước gán mỗi POI cố định vào một cell. Các vùng tròn được phép chồng lên nhau; một POI có thể được tính cho nhiều cell gần nó.

## Những gì không làm

- Không dùng H3.
- Không tạo graph, node graph hoặc shortest path.
- Không dùng Dijkstra, NetworkX hoặc GraphML.
- Không tính khoảng cách đi bộ theo đường.
- Không tạo buffer bên ngoài tỉnh để lấy thêm network.
- Không đọc toàn bộ POI Việt Nam rồi mới chia theo tỉnh.
- Không mở pgAdmin và không import PBF vào database.

`nearest_*_m` là khoảng cách đường thẳng trên CRS mét, không phải khoảng cách đi bộ.

## Output chính

```text
data/processed/{region_id}/
├── pois.parquet
├── roads.parquet
├── cells.parquet
├── cell_features.parquet
└── cell_features.csv
```

Các cột quan trọng:

```text
region_id
cell_id
cell_area_km2
hospital_count_500m
hospital_count_1000m
hospital_count_2000m
school_count_500m
school_count_1000m
school_count_2000m
supermarket_count_500m
supermarket_count_1000m
supermarket_count_2000m
transit_count_500m
transit_count_1000m
transit_count_2000m
nearest_hospital_m
nearest_school_m
nearest_supermarket_m
nearest_transit_m
road_length_500m_km
road_density_500m_km_per_km2
road_length_1000m_km
road_density_1000m_km_per_km2
geometry
```

CSV bỏ cột `geometry`. GeoParquet giữ `geometry` để vẽ bản đồ.

## Thứ tự thực hiện

| Giai đoạn | Việc cần làm | Output |
|---|---|---|
| [01](01_CHUAN_HOA_PROJECT.md) | Chuẩn hóa package Python | Lệnh `ady201` |
| [02](02_CONFIG_VA_REGION_REGISTRY.md) | Khai báo tham số và tỉnh | JSON cấu hình |
| [03](03_DUCKDB_CO_BAN.md) | Kết nối DuckDB tối giản | Một file database, một view |
| [04](04_PBF_CO_DINH.md) | Chuẩn bị PBF | `vietnam.osm.pbf` |
| [05](05_LAY_POI_VA_DUONG_CUA_TINH.md) | Lấy POI và đường của tỉnh | `pois.parquet`, `roads.parquet` |
| [06](06_TAO_GRID_CELL.md) | Tạo grid và tâm cell | `cells.parquet` |
| [07](07_POI_QUANH_CELL_VA_NEAREST.md) | Đếm POI và tìm dịch vụ gần nhất | Feature POI |
| [08](08_MAT_DO_DUONG_QUANH_CELL.md) | Tính chiều dài và mật độ đường | Feature đường |
| [09](09_FEATURES_VA_CHI_SO.md) | Ghép và xuất bảng cuối | `cell_features.*` |
| [10](10_CLUSTERING_VA_BAN_DO.md) | Clustering và bản đồ, làm sau | Bản đồ, cluster |
| [11](11_TU_DONG_HOA_MOT_REGION.md) | Tự động hóa một tỉnh | `run-region` |
| [12](12_RUN_ALL_TOAN_QUOC.md) | Chạy toàn quốc | `run-all` |

Chỉ làm giai đoạn 10 sau khi giai đoạn 05–09 chạy đúng cho một tỉnh nhỏ.

## File Python cần có

Giữ số file ít và trách nhiệm rõ:

| File | Dùng để làm gì |
|---|---|
| `settings.py` | Đọc cấu hình chung |
| `regions.py` | Lấy cấu hình một tỉnh |
| `osm_input.py` | Trả về đường dẫn PBF |
| `poi.py` | Lấy và phân loại POI |
| `network.py` | Lấy các đoạn đường |
| `analysis.py` | Tạo cell, buffer và các feature |
| `database.py` | Mở DuckDB và tạo view |
| `pipeline.py` | Gọi các bước theo đúng thứ tự |
| `main.py` | Nhận câu lệnh từ terminal |

Không tạo một file Python mới cho mỗi phép tính.

## Kiến thức cần học

Học theo đúng thứ tự:

1. `Path`, hàm, `dict`, đọc JSON và DataFrame.
2. Point, LineString, Polygon và GeoDataFrame.
3. CRS 4326 và CRS mét; `to_crs()` và `estimate_utm_crs()`.
4. `clip()`, `buffer()`, `sjoin()`, `sjoin_nearest()` và `overlay()`.
5. `groupby()`, `pivot_table()`, `merge()` và `fillna()`.
6. Pyrosm: `OSM`, `get_pois()` và `get_network()`.
7. Parquet/GeoParquet và truy vấn DuckDB cơ bản.
8. Sau cùng mới học scaling, K-Means và bản đồ.

## Phân công tổng quát

### Thành — mức trung bình/khó

- Phụ trách config, đọc PBF, pipeline và chạy toàn quốc.
- Review công thức POI và mật độ đường.

### Hiếu — mức trung bình/khó

- Phụ trách grid, buffer, POI feature, nearest và road feature.
- Review dữ liệu Pyrosm và bảng đầu ra.

### Quang — mức dễ/trung bình

- Chuẩn bị boundary/config, kiểm tra file đầu ra, data dictionary và bản đồ.
- Chạy thử bằng câu lệnh và ghi lại lỗi tái hiện được.

## Cách để cả ba người đều hiểu project

- Mỗi pull request phải được một người khác review.
- Người review phải chạy được bước đó trên cùng một tỉnh mẫu.
- Cuối mỗi giai đoạn, người không viết code giải thích lại input, hàm chính và output.
- Cả nhóm dùng cùng tên cột, bán kính và cấu trúc thư mục trong tài liệu này.

## Điều kiện hoàn thành toàn project

- `run-region` tạo đủ output cho Hà Nội hoặc Đà Nẵng bằng một lệnh.
- Mỗi `cell_id` chỉ có một hàng trong bảng cuối.
- Count không âm; cell không có POI nhận count bằng `0`.
- Khoảng cách và chiều dài có đơn vị mét/km đúng vì được tính trong CRS mét.
- `road_density = road_length_km / buffer_area_km2`.
- `run-all` tiếp tục sang tỉnh sau nếu một tỉnh lỗi và tạo bảng tổng kết.
