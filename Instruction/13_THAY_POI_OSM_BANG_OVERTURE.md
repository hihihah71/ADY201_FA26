# Giai đoạn 13 — Thay POI OSM bằng Overture

## Mục tiêu

Chỉ thay nguồn POI:

```text
POI cũ: OSM PBF
POI mới: data/raw/overture/vietnam_places.parquet
```

Các phần khác giữ nguyên:

- Boundary vẫn lấy từ OSM.
- Road vẫn lấy từ OSM.
- Grid cell vẫn là 200 m.
- Road feature vẫn ở 500 m và 1000 m.
- Output vẫn chỉ có một file:

```text
data/processed/{region_id}/cell_features.parquet
```

Không tạo file trung gian. Không mapping category Overture về amenity OSM.

## Luồng

```text
boundary OSM
    ↓
grid cell 200 m
    ↓
đọc POI Overture trong boundary
    ↓
category_group = category_hierarchy[0]
    ↓
gán POI vào cell
    ↓
count POI theo 6 bán kính
    ↓
nearest theo group và category quan trọng
    ↓
ghép road feature
    ↓
cell_features.parquet
```

## Những file cần sửa

Chỉ sửa:

```text
src/ady201/poi.py
src/ady201/regions.py
src/ady201/main.py
pyproject.toml
```

Giữ nguyên:

```text
src/ady201/network.py
src/ady201/analys.py
src/ady201/grid_cell.py
src/ady201/feature_process.py
```

`config/categories.json` đã chứa:

- 13 group Overture.
- Toàn bộ 1.212 category.
- Danh sách `nearest_categories` quan trọng.

## 1. Thêm SciPy

Trong `pyproject.toml`, thêm:

```toml
"scipy>=1.11",
```

SciPy được dùng để tính count theo bán kính và nearest bằng `cKDTree`. Cách này không tạo hàng trăm triệu dòng spatial join ở bán kính 5 km.

## 2. Sửa poi.py

Giữ các hàm đọc JSON/CSV cũ nếu vẫn cần. Chỉ thay phần `get_pois()` và `get_cell_pois()`.

### Import và cấu hình

Thêm các import:

```python
import json

import numpy as np
from scipy.spatial import cKDTree
```

Xóa import `OSM` và biến `pbf_path` khỏi `poi.py`. Boundary sẽ được truyền từ `regions.py`.

Thêm các đường dẫn và đọc config:

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]

OVERTURE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "overture"
    / "vietnam_places.parquet"
)

CATEGORIES_PATH = (
    PROJECT_ROOT
    / "config"
    / "categories.json"
)

with CATEGORIES_PATH.open(
    "r",
    encoding="utf-8",
) as file:
    CATEGORY_CONFIG = json.load(file)

OVERTURE_GROUPS = list(
    CATEGORY_CONFIG["groups"]
)

NEAREST_CATEGORIES = list(
    CATEGORY_CONFIG["nearest_categories"]
)

POI_RADII_M = (
    100,
    200,
    500,
    1000,
    2000,
    5000,
)
```

Xóa khai báo `PROJECT_ROOT` bị lặp trong `poi.py`, chỉ giữ một lần.

### Thay get_pois()

```python
def get_pois(boundary):
    boundary_wgs84 = boundary.to_crs(4326)

    minx, miny, maxx, maxy = (
        boundary_wgs84.total_bounds
    )

    pois = gpd.read_parquet(
        OVERTURE_PATH,
        filters=[
            ("longitude", ">=", minx),
            ("longitude", "<=", maxx),
            ("latitude", ">=", miny),
            ("latitude", "<=", maxy),
        ],
    )

    pois = pois.to_crs(
        boundary_wgs84.crs
    )
    pois = gpd.clip(
        pois,
        boundary_wgs84,
    ).reset_index(drop=True)

    pois = pois[
        pois["operating_status"]
        .fillna("")
        .ne("permanently_closed")
    ].copy()

    pois["category_group"] = (
        pois["category_hierarchy"]
        .str[0]
        .fillna("unclassified")
    )

    return pois.reset_index(drop=True)
```

`get_pois()` chỉ nhận boundary đã có sẵn. Hàm không mở PBF và không biết tên tỉnh.

Không còn dòng:

```python
osm.get_pois(
    custom_filter={"amenity": amenity}
)
```

### Tách get_cell_pois() thành các hàm nhỏ

Tất cả hàm dưới đây vẫn đặt trong `poi.py`. Không tạo file Python mới.

#### Chuyển Point thành tọa độ

```python
def _to_xy(geodataframe):
    return np.column_stack(
        [
            geodataframe.geometry.x,
            geodataframe.geometry.y,
        ]
    )
```

#### Tính khoảng cách gần nhất

```python
def _nearest_distances(
    cell_xy,
    selected_pois,
):
    if selected_pois.empty:
        return np.full(
            len(cell_xy),
            np.nan,
        )

    tree = cKDTree(
        _to_xy(selected_pois)
    )
    distance, _ = tree.query(
        cell_xy,
        k=1,
        workers=-1,
    )
    return distance
```

Điều kiện `selected_pois.empty` là cần thiết vì một tỉnh có thể không có category đang tính.

#### Chuẩn bị polygon và tâm cell

```python
def prepare_cell_layers(cell_points):
    polygons = (
        cell_points[
            ["cell_id", "geometry"]
        ]
        .copy()
    )

    points = (
        cell_points
        .copy()
        .reset_index(drop=True)
        .set_geometry("points")
    )

    return polygons, points
```

#### Gán POI vào cell

```python
def assign_pois_to_cells(
    pois,
    polygons,
):
    assigned = gpd.sjoin_nearest(
        pois[
            [
                "overture_id",
                "category_group",
                "geometry",
            ]
        ],
        polygons,
        how="inner",
    )

    return (
        assigned
        .sort_values(
            ["overture_id", "cell_id"]
        )
        .drop_duplicates(
            "overture_id"
        )
    )
```

`sjoin_nearest()` gán cả POI nằm lệch khỏi biên cell một khoảng rất nhỏ do sai số phép chiếu. `drop_duplicates("overture_id")` xử lý trường hợp Point nằm đúng trên cạnh hai cell.

#### Count trực tiếp trong cell

```python
def build_direct_poi_features(
    points,
    assigned,
    categories,
):
    cell_ids = (
        points["cell_id"]
        .to_numpy()
    )

    total_counts = (
        assigned
        .groupby("cell_id")
        .size()
        .reindex(
            cell_ids,
            fill_value=0,
        )
        .to_numpy()
    )

    group_counts = pd.crosstab(
        assigned["cell_id"],
        assigned["category_group"],
    )
    group_counts = group_counts.reindex(
        index=cell_ids,
        columns=categories,
        fill_value=0,
    )
    group_counts.index.name = "cell_id"
    group_counts.columns = [
        f"{category}_count"
        for category in group_counts.columns
    ]

    result = (
        group_counts
        .reset_index()
    )
    result.insert(
        1,
        "poi_count",
        total_counts,
    )

    return result
```

#### Count bán kính và nearest theo group

```python
def build_group_radius_features(
    points,
    pois,
    categories,
):
    cell_xy = _to_xy(points)

    features = {
        "cell_id": (
            points["cell_id"]
            .to_numpy()
        )
    }

    for category in categories:
        selected = pois[
            pois["category_group"]
            == category
        ]

        features[
            f"nearest_{category}_m"
        ] = _nearest_distances(
            cell_xy,
            selected,
        )

        if selected.empty:
            for radius_m in POI_RADII_M:
                features[
                    f"{category}_count_{radius_m}m"
                ] = np.zeros(
                    len(points),
                    dtype="int64",
                )
            continue

        tree = cKDTree(
            _to_xy(selected)
        )

        for radius_m in POI_RADII_M:
            features[
                f"{category}_count_{radius_m}m"
            ] = tree.query_ball_point(
                cell_xy,
                r=radius_m,
                return_length=True,
                workers=-1,
            )

    return pd.DataFrame(features)
```

#### Nearest cho category quan trọng

```python
def build_important_nearest_features(
    points,
    pois,
):
    cell_xy = _to_xy(points)

    features = {
        "cell_id": (
            points["cell_id"]
            .to_numpy()
        )
    }

    for category in NEAREST_CATEGORIES:
        selected = pois[
            pois["category"] == category
        ]

        features[
            f"nearest_{category}_m"
        ] = _nearest_distances(
            cell_xy,
            selected,
        )

    return pd.DataFrame(features)
```

#### get_cell_pois() chỉ điều phối

```python
def get_cell_pois(
    boundary,
    amenity,
    cell_points,
):
    categories = list(amenity)

    pois = get_pois(boundary)

    polygons, points = (
        prepare_cell_layers(
            cell_points
        )
    )

    target_crs = points.crs
    pois = pois.to_crs(target_crs)
    polygons = polygons.to_crs(
        target_crs
    )

    assigned = assign_pois_to_cells(
        pois,
        polygons,
    )

    direct_features = (
        build_direct_poi_features(
            points,
            assigned,
            categories,
        )
    )

    radius_features = (
        build_group_radius_features(
            points,
            pois,
            categories,
        )
    )

    nearest_features = (
        build_important_nearest_features(
            points,
            pois,
        )
    )

    result = direct_features.merge(
        radius_features,
        on="cell_id",
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        nearest_features,
        on="cell_id",
        how="left",
        validate="one_to_one",
    )

    return result
```

`get_cell_pois()` giờ chỉ thể hiện đúng thứ tự xử lý:

```text
đọc POI
→ chuẩn bị cell
→ đổi CRS
→ gán POI vào cell
→ tạo direct feature
→ tạo radius feature
→ tạo nearest feature
→ merge
```

Không thêm logger, `try/except` hoặc file trung gian.

## 3. Sửa main.py

Sửa import:

```python
from ady201.poi import (
    OVERTURE_GROUPS,
    normalize_poi_file,
)
```

Thay toàn bộ danh sách `amenity` trong nhánh `grf` bằng:

```python
if options.command == "grf":
    get_region_features(
        options.region_id,
        options.province,
        "walking",
        OVERTURE_GROUPS,
    )
```

Trong `regions.py`, chỉ sửa lời gọi `get_cell_pois()` để truyền boundary đã đọc ở đầu hàm:

```python
poi_features = get_cell_pois(
    boundary,
    amenity,
    cell_points,
)
```

`get_region_features()` vẫn nhận danh sách category ở vị trí cũ. Cách merge và ghi Parquet không đổi.

## 4. Feature POI trong file cuối

File cuối có count trực tiếp trong cell:

```text
poi_count
food_and_drink_count
education_count
health_care_count
...
```

Mỗi group có count theo sáu bán kính:

```text
food_and_drink_count_100m
food_and_drink_count_200m
food_and_drink_count_500m
food_and_drink_count_1000m
food_and_drink_count_2000m
food_and_drink_count_5000m
```

Mỗi group có nearest:

```text
nearest_food_and_drink_m
nearest_education_m
nearest_health_care_m
...
```

Các category quan trọng có nearest riêng:

```text
nearest_hospital_m
nearest_pharmacy_m
nearest_doctors_office_m
nearest_dental_clinic_m
nearest_school_m
nearest_elementary_school_m
nearest_preschool_m
nearest_college_university_m
nearest_language_school_m
nearest_restaurant_m
nearest_coffee_shop_m
nearest_cafe_m
nearest_fast_food_restaurant_m
nearest_grocery_store_m
nearest_convenience_store_m
nearest_bus_station_m
nearest_parking_m
nearest_gas_station_m
nearest_atm_m
nearest_bank_or_credit_union_m
nearest_police_station_m
nearest_park_m
```

## 5. Feature đường giữ nguyên

Không sửa `network.py`.

`get_road_features()` tiếp tục tạo:

```text
road_length_500m_km
road_density_500m_km_per_km2
road_length_1000m_km
road_density_1000m_km_per_km2
```

`regions.py` tiếp tục merge:

```python
features = build_cell_features(
    cell_points,
    poi_features,
    road_features,
)
```

## 6. Chỉ ghi một file

Giữ nguyên đoạn cuối trong `regions.py`:

```python
features = feature_process(features)

assert len(features) == len(cell_points)
assert features["cell_id"].is_unique
assert features["cell_id"].notna().all()

features.to_parquet(output_path)
```

Không ghi `pois`, `assigned` hoặc `poi_features` ra file riêng.

## 7. Chạy

```powershell
pip install -e .
ady201 grf "Hà Nội" 29_2
```

Output:

```text
data/processed/29_2/cell_features.parquet
```

## Hoàn thành khi

- `poi.py` không còn gọi `osm.get_pois()` trong luồng `grf`.
- POI chỉ đọc từ `vietnam_places.parquet`.
- Category sử dụng taxonomy Overture.
- Có count trực tiếp trong cell.
- Có count tại 100, 200, 500, 1000, 2000 và 5000 m.
- Có nearest theo 13 group.
- Có nearest cho category quan trọng.
- Có feature đường tại 500 m và 1000 m.
- Chỉ tạo `cell_features.parquet`.
- `regions.py` chỉ đổi một lời gọi hàm; `network.py` giữ nguyên.
