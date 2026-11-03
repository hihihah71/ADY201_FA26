# 00 — Tổng quan dự án

## Mục tiêu

Dự án trả lời hai nhóm câu hỏi:

1. Mỗi cell có bao nhiêu POI, gần loại tiện ích nào và có mật độ đường ra sao?
2. Với nhu cầu cụ thể của người dùng, cell nào phù hợp nhất?

## Kiến trúc dữ liệu

```text
data/raw/osm/vietnam-261014.osm.pbf
    ├── boundary
    └── walking road network

data/raw/overture/vietnam_places.parquet
    └── Places POI

boundary ─> grid vuông 200 m ────────────────┐
POI ─> count + radius + nearest ─────────────┼─> cell_features.parquet
roads ─> length + density 500/1000 m ────────┘
                                                     │
                                                     ├─> notebook
                                                     └─> evaluation + app.py
```

## Nguồn dữ liệu

| Thành phần | Nguồn | Vai trò |
|---|---|---|
| Ranh giới | OSM PBF | Lọc vùng và cắt grid/buffer |
| Mạng đường | OSM PBF | Road length và road density |
| POI | Overture Places | Toàn bộ POI feature |

Không dùng amenity OSM để tạo POI feature và không ghép POI OSM với Overture.

## Output chính

Mỗi `region_id` có một file duy nhất:

```text
data/processed/{region_id}/cell_features.parquet
```

Không tạo CSV hoặc các file POI/road trung gian trong luồng `grf`.

## Chạy nhanh

```powershell
pip install -e .
ady201 download-overture-poi
ady201 grf "Hà Nội" 29_3
streamlit run app.py
```

## Các giai đoạn tài liệu

| File | Nội dung |
|---|---|
| [01](01_CHUAN_HOA_PROJECT.md) | Cài đặt và cấu trúc package |
| [02](02_CONFIG_VA_REGION_REGISTRY.md) | Cấu hình category và region |
| [03](03_DUCKDB_CO_BAN.md) | DuckDB phụ trợ |
| [04](04_PBF_CO_DINH.md) | Input OSM PBF |
| [05](05_LAY_POI_VA_DUONG_CUA_TINH.md) | Đọc dữ liệu theo vùng |
| [06](06_TAO_GRID_CELL.md) | Grid 200 m |
| [07](07_POI_QUANH_CELL_VA_NEAREST.md) | POI feature |
| [08](08_MAT_DO_DUONG_QUANH_CELL.md) | Road feature |
| [09](09_FEATURES_VA_CHI_SO.md) | File feature cuối |
| [10](10_CLUSTERING_VA_BAN_DO.md) | Khám phá bằng notebook |
| [11](11_TU_DONG_HOA_MOT_REGION.md) | Chạy một vùng bằng CLI |
| [12](12_RUN_ALL_TOAN_QUOC.md) | Trạng thái chạy nhiều vùng |
| [13](13_THAY_POI_OSM_BANG_OVERTURE.md) | Thiết kế Overture-only |
| [14](14_DANH_GIA_VA_GIAO_DIEN.md) | Suitability model và Streamlit |

## Trạng thái triển khai

Đã có:

- Downloader Overture toàn Việt Nam.
- Pipeline tạo feature một tỉnh/thành.
- Grid 200 m.
- POI radius/nearest và road density.
- Model đánh giá đa tiêu chí.
- Giao diện Streamlit cho dữ liệu `29_3`.

Chưa có:

- CLI batch toàn bộ tỉnh/thành.
- Theo dõi tiến độ chi tiết của `grf`.
- Giao diện tự chọn region.
- Dữ liệu nhân khẩu học thực tế cho chỉ số sinh viên hoặc độ ồn.

## Quy tắc đồng bộ

- Code trong `src/ady201/` là nguồn sự thật cho pipeline.
- `config/categories.json` là nguồn sự thật cho taxonomy POI.
- Không đưa lại lệnh `normalize-poi`, POI OSM, grid 1 km hoặc CSV output vào tài liệu nếu code chưa hỗ trợ.
