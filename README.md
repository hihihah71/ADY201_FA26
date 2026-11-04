# ADY201_FA26

Dự án xây dựng lưới không gian 200 m cho một tỉnh/thành tại Việt Nam, tổng hợp POI từ Overture Maps và mạng đường từ OpenStreetMap, sau đó chấm điểm khu vực theo nhu cầu của người dùng.

Thành viên: Thành, Hiếu và Quang.

## Luồng hiện tại

```text
OSM PBF ──> boundary + road network ──┐
                                      ├─> grid 200 m ─> cell_features.parquet
Overture Places ──> POI trong vùng ───┘                        │
                                                               ├─> notebook
                                                               └─> evaluation + Streamlit
```

- OSM chỉ cung cấp ranh giới và đường.
- Overture là nguồn POI duy nhất.
- Mỗi lần chạy một vùng chỉ tạo một output chính.
- Model đánh giá dùng trọng số và hướng lựa chọn của người dùng, không phải model học máy có giám sát.

## Yêu cầu

- Python 3.11 trở lên.
- File OSM PBF tại `data/raw/osm/vietnam-261014.osm.pbf`.
- POI Overture tại `data/raw/overture/vietnam_places.parquet`.
- Đủ RAM và dung lượng đĩa để xử lý dữ liệu không gian cấp tỉnh.

## Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

Kiểm tra CLI:

```powershell
ady201 --help
```

## Chuẩn bị POI Overture

Tải Places mới nhất của Việt Nam:

```powershell
ady201 download-overture-poi
```

Ghi đè file hiện có:

```powershell
ady201 download-overture-poi --force
```

Output mặc định:

```text
data/raw/overture/vietnam_places.parquet
```

## Tạo feature cho một vùng

Ví dụ tạo dữ liệu Hà Nội với mã output `29_3`:

```powershell
ady201 grf "Hà Nội" 29_3
```

Output:

```text
data/processed/29_3/cell_features.parquet
```

Luồng này tạo grid 200 m, POI feature, road feature và ghi một GeoParquet cuối. Bước mạng đường có thể chạy lâu và CLI hiện chưa hiển thị tiến độ chi tiết.

## Chạy giao diện đánh giá

```powershell
streamlit run app.py
```

Mở `http://localhost:8501`. Giao diện có 12 hồ sơ mặc định:

- Sinh viên.
- Người đi làm.
- Gia đình có con.
- Người cao tuổi.
- Làm việc tại nhà.
- Thích yên tĩnh.
- Thích sôi động.
- Ưu tiên sức khỏe.
- Yêu ẩm thực.
- Ưu tiên mua sắm.
- Ưu tiên công viên.
- Tiện nghi cân bằng.

Người dùng có thể đổi trọng số, chọn `more`, `less`, `target`, `near`, `far`, thay đổi top phần trăm và khoảng cách giữa các đề xuất.

Phiên bản giao diện hiện đọc cố định:

```text
data/processed/29_3/cell_features.parquet
```

## Dùng model trong Python

```python
from ady201.evaluation import SuitabilityModel

model = SuitabilityModel.from_parquet(
    "data/processed/29_3/cell_features.parquet"
)

preferences = {
    "food": {
        "mode": "target",
        "weight": 3,
        "min": 1,
        "max": 10,
    },
    "services": {
        "mode": "more",
        "weight": 5,
        "limit": 10,
    },
    "hospital": {
        "mode": "near",
        "weight": 5,
        "limit": 2000,
    },
    "quietness": 4,
}

result = model.evaluate(preferences)
candidates = model.select_candidates(
    preferences,
    limit=10,
    minimum_distance_m=2000,
)
```

## Dữ liệu đầu ra

`cell_features.parquet` chứa:

- Cell: `cell_id`, diện tích, polygon và điểm đại diện.
- POI trực tiếp trong cell theo 13 group Overture.
- POI theo bán kính 100, 200, 500, 1000, 2000 và 5000 m.
- Khoảng cách tới 13 group và 22 category quan trọng.
- Chiều dài và mật độ đường trong 500 m và 1000 m.

File `29_3` hiện có 85.249 cell và 135 cột.

## Cấu trúc chính

```text
ADY201_FA26/
├── app.py
├── config/
│   ├── categories.json
│   ├── project.json
│   └── regions.json
├── data/
│   ├── raw/osm/
│   ├── raw/overture/
│   └── processed/{region_id}/
├── Instruction/
├── notebook/
├── sql/
└── src/ady201/
    ├── main.py
    ├── overture.py
    ├── poi.py
    ├── grid_cell.py
    ├── network.py
    ├── feature_process.py
    ├── regions.py
    └── evaluation.py
```

## CLI hiện có

| Lệnh                                 | Công dụng                                                                           |
| ------------------------------------- | ------------------------------------------------------------------------------------- |
| `ady201 download-overture-poi`      | Tải POI Overture của Việt Nam                                                      |
| `ady201 grf <province> <region_id>` | Tạo `cell_features.parquet` cho một vùng                                         |
| `ady201 init-db`                    | Khởi tạo DuckDB phụ trợ                                                           |
| `ady201 check-db`                   | Gọi kiểm tra DuckDB; CLI chưa in kết quả                                         |
| `ady201 check-osm`                  | Tiện ích kiểm tra PBF đang chưa hoàn thiện, không dùng trong pipeline chính |

## Tài liệu

- Bắt đầu tại [tổng quan dự án](Instruction/00_TONG_QUAN.md).
- Xem [khám phá dữ liệu bằng notebook](Instruction/10_CLUSTERING_VA_BAN_DO.md).
- Xem [chạy pipeline một region](Instruction/11_TU_DONG_HOA_MOT_REGION.md).
- Xem [model đánh giá và giao diện](Instruction/14_DANH_GIA_VA_GIAO_DIEN.md).

Các file trong `Instruction/` được sắp theo thứ tự từ thiết lập dữ liệu đến đánh giá và giao diện.

## Giới hạn hiện tại

- Tên file OSM PBF đang được cố định trong code.
- Chưa có CLI chạy tự động toàn bộ 63 tỉnh/thành.
- `app.py` đang cố định vào region `29_3` và bbox trung tâm Hà Nội.
- `student_activity` là chỉ số proxy từ POI, không phải dữ liệu dân số sinh viên thực tế.
- `database.py`, `analys.py`, `project.json` và `regions.json` là tiện ích/phần tham khảo, không nằm trên luồng `grf` chính.
