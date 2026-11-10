import json
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

from ady201.evaluation import CRITERIA, SuitabilityModel


DATA_PATH = Path(__file__).parent / "data/processed/29_3/cell_features.parquet"
CENTRAL_BOUNDS = (565_000, 605_000, 2_305_000, 2_345_000)

LABELS = {
    "food": "Đồ ăn",
    "services": "Dịch vụ",
    "shopping": "Mua sắm",
    "school": "Trường học",
    "hospital": "Bệnh viện",
    "grocery": "Cửa hàng thực phẩm",
    "park": "Công viên",
    "transport": "Giao thông",
    "quietness": "Yên tĩnh",
    "student_activity": "Hoạt động sinh viên",
    "service_balance": "Cân bằng dịch vụ",
}

MODE_LABELS = {
    "more": "Nhiều hơn",
    "less": "Ít hơn",
    "target": "Trong khoảng",
    "near": "Gần hơn",
    "far": "Xa hơn",
}

DISTANCE_CRITERIA = {"school", "hospital", "grocery", "park"}
COUNT_CRITERIA = {"food", "services", "shopping", "transport"}

PROFILES = {
    "Sinh viên": {
        "food": {"weight": 5, "mode": "more", "limit": 10},
        "services": {"weight": 2, "mode": "more", "limit": 10},
        "shopping": {"weight": 3, "mode": "more", "limit": 10},
        "hospital": {"weight": 1, "mode": "near", "limit": 2000},
        "grocery": {"weight": 3, "mode": "near", "limit": 1000},
        "park": {"weight": 1, "mode": "near", "limit": 2000},
        "transport": {"weight": 5, "mode": "more", "limit": 15},
        "quietness": {"weight": 2, "mode": "less", "limit": 0.8},
        "student_activity": {"weight": 5, "mode": "more", "limit": 0.8},
        "service_balance": {"weight": 2, "mode": "more", "limit": 0.8},
    },
    "Người đi làm": {
        "food": {
            "weight": 3,
            "mode": "target",
            "min": 2,
            "max": 10,
        },
        "services": {"weight": 5, "mode": "more", "limit": 10},
        "shopping": {"weight": 3, "mode": "more", "limit": 10},
        "hospital": {"weight": 2, "mode": "near", "limit": 2000},
        "grocery": {"weight": 3, "mode": "near", "limit": 1000},
        "park": {"weight": 2, "mode": "near", "limit": 2000},
        "transport": {"weight": 5, "mode": "more", "limit": 15},
        "quietness": {"weight": 2, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 1, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 5, "mode": "more", "limit": 0.8},
    },
    "Gia đình có con": {
        "food": {
            "weight": 2,
            "mode": "target",
            "min": 1,
            "max": 8,
        },
        "services": {"weight": 4, "mode": "more", "limit": 10},
        "shopping": {"weight": 2, "mode": "more", "limit": 10},
        "school": {"weight": 5, "mode": "near", "limit": 1500},
        "hospital": {"weight": 4, "mode": "near", "limit": 2000},
        "grocery": {"weight": 5, "mode": "near", "limit": 1000},
        "park": {"weight": 4, "mode": "near", "limit": 2000},
        "transport": {"weight": 3, "mode": "more", "limit": 15},
        "quietness": {"weight": 5, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 3, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 4, "mode": "more", "limit": 0.8},
    },
    "Người cao tuổi": {
        "food": {
            "weight": 2,
            "mode": "target",
            "min": 1,
            "max": 6,
        },
        "services": {"weight": 5, "mode": "more", "limit": 10},
        "shopping": {"weight": 1, "mode": "more", "limit": 10},
        "hospital": {"weight": 5, "mode": "near", "limit": 1500},
        "grocery": {"weight": 5, "mode": "near", "limit": 800},
        "park": {"weight": 4, "mode": "near", "limit": 1000},
        "transport": {"weight": 2, "mode": "more", "limit": 15},
        "quietness": {"weight": 5, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 4, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 5, "mode": "more", "limit": 0.8},
    },
    "Làm việc tại nhà": {
        "food": {"weight": 3, "mode": "target", "min": 1, "max": 6},
        "services": {"weight": 4, "mode": "more", "limit": 8},
        "shopping": {"weight": 2, "mode": "target", "min": 1, "max": 6},
        "hospital": {"weight": 2, "mode": "near", "limit": 2000},
        "grocery": {"weight": 4, "mode": "near", "limit": 800},
        "park": {"weight": 4, "mode": "near", "limit": 1200},
        "transport": {"weight": 1, "mode": "more", "limit": 15},
        "quietness": {"weight": 5, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 4, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 4, "mode": "more", "limit": 0.8},
    },
    "Thích yên tĩnh": {
        "food": {"weight": 4, "mode": "target", "min": 0, "max": 4},
        "services": {"weight": 3, "mode": "target", "min": 1, "max": 6},
        "shopping": {"weight": 3, "mode": "less", "limit": 8},
        "hospital": {"weight": 2, "mode": "near", "limit": 2500},
        "grocery": {"weight": 4, "mode": "near", "limit": 1000},
        "park": {"weight": 5, "mode": "near", "limit": 1000},
        "transport": {"weight": 2, "mode": "target", "min": 4, "max": 12},
        "quietness": {"weight": 5, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 5, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 3, "mode": "more", "limit": 0.8},
    },
    "Thích sôi động": {
        "food": {"weight": 5, "mode": "more", "limit": 10},
        "services": {"weight": 5, "mode": "more", "limit": 10},
        "shopping": {"weight": 4, "mode": "more", "limit": 10},
        "grocery": {"weight": 2, "mode": "near", "limit": 1000},
        "park": {"weight": 1, "mode": "near", "limit": 2000},
        "transport": {"weight": 5, "mode": "more", "limit": 15},
        "quietness": {"weight": 5, "mode": "less", "limit": 0.8},
        "student_activity": {"weight": 3, "mode": "more", "limit": 0.8},
        "service_balance": {"weight": 4, "mode": "more", "limit": 0.8},
    },
    "Ưu tiên sức khỏe": {
        "food": {"weight": 2, "mode": "target", "min": 1, "max": 6},
        "services": {"weight": 4, "mode": "more", "limit": 8},
        "hospital": {"weight": 5, "mode": "near", "limit": 1000},
        "grocery": {"weight": 5, "mode": "near", "limit": 700},
        "park": {"weight": 5, "mode": "near", "limit": 800},
        "transport": {"weight": 2, "mode": "more", "limit": 15},
        "quietness": {"weight": 4, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 3, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 4, "mode": "more", "limit": 0.8},
    },
    "Yêu ẩm thực": {
        "food": {"weight": 5, "mode": "target", "min": 4, "max": 15},
        "services": {"weight": 2, "mode": "more", "limit": 10},
        "shopping": {"weight": 2, "mode": "more", "limit": 10},
        "hospital": {"weight": 1, "mode": "near", "limit": 2500},
        "grocery": {"weight": 3, "mode": "near", "limit": 1000},
        "transport": {"weight": 4, "mode": "more", "limit": 15},
        "quietness": {"weight": 2, "mode": "less", "limit": 0.8},
        "student_activity": {"weight": 2, "mode": "more", "limit": 0.8},
        "service_balance": {"weight": 3, "mode": "more", "limit": 0.8},
    },
    "Ưu tiên mua sắm": {
        "food": {"weight": 3, "mode": "more", "limit": 10},
        "services": {"weight": 4, "mode": "more", "limit": 10},
        "shopping": {"weight": 5, "mode": "more", "limit": 10},
        "hospital": {"weight": 1, "mode": "near", "limit": 2500},
        "grocery": {"weight": 3, "mode": "near", "limit": 800},
        "park": {"weight": 1, "mode": "near", "limit": 2000},
        "transport": {"weight": 5, "mode": "more", "limit": 15},
        "quietness": {"weight": 2, "mode": "less", "limit": 0.8},
        "student_activity": {"weight": 1, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 4, "mode": "more", "limit": 0.8},
    },
    "Ưu tiên công viên": {
        "food": {"weight": 2, "mode": "target", "min": 1, "max": 6},
        "services": {"weight": 3, "mode": "more", "limit": 8},
        "shopping": {"weight": 1, "mode": "more", "limit": 10},
        "hospital": {"weight": 2, "mode": "near", "limit": 2000},
        "grocery": {"weight": 4, "mode": "near", "limit": 800},
        "park": {"weight": 5, "mode": "near", "limit": 600},
        "transport": {"weight": 2, "mode": "more", "limit": 15},
        "quietness": {"weight": 5, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 3, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 3, "mode": "more", "limit": 0.8},
    },
    "Tiện nghi cân bằng": {
        "food": {"weight": 4, "mode": "target", "min": 2, "max": 10},
        "services": {"weight": 4, "mode": "target", "min": 2, "max": 10},
        "shopping": {"weight": 4, "mode": "target", "min": 2, "max": 10},
        "school": {"weight": 2, "mode": "near", "limit": 2000},
        "hospital": {"weight": 3, "mode": "near", "limit": 2000},
        "grocery": {"weight": 4, "mode": "near", "limit": 1000},
        "park": {"weight": 3, "mode": "near", "limit": 1500},
        "transport": {"weight": 4, "mode": "target", "min": 6, "max": 18},
        "quietness": {"weight": 3, "mode": "more", "limit": 0.8},
        "student_activity": {"weight": 2, "mode": "less", "limit": 0.8},
        "service_balance": {"weight": 5, "mode": "more", "limit": 0.8},
    },
}


@st.cache_resource(show_spinner="Đang tải dữ liệu khu vực...")
def load_model():
    return SuitabilityModel.from_parquet(DATA_PATH)


def profile_choice(profile, name):
    _, default_mode, default_limit = CRITERIA[name]
    return PROFILES[profile].get(
        name,
        {"weight": 0, "mode": default_mode, "limit": default_limit},
    )


def limit_slider(name, default, key):
    if name in DISTANCE_CRITERIA:
        return st.slider(
            "Khoảng cách tham chiếu (m)",
            100,
            5000,
            int(default),
            100,
            key=key,
        )
    if name in COUNT_CRITERIA:
        return st.slider(
            "Ngưỡng đủ tốt",
            1,
            50,
            int(default),
            key=key,
        )
    return st.slider(
        "Ngưỡng đủ tốt",
        0.1,
        1.0,
        float(default),
        0.05,
        key=key,
    )


def preference_controls(profile):
    preferences = {}

    for name in CRITERIA:
        default = profile_choice(profile, name)
        modes = (
            ["near", "far"]
            if name in DISTANCE_CRITERIA
            else ["more", "less", "target"]
            if name in COUNT_CRITERIA
            else ["more", "less"]
        )

        with st.sidebar.expander(LABELS[name]):
            weight = st.slider(
                "Mức quan trọng",
                0,
                5,
                int(default["weight"]),
                key=f"{profile}-{name}-weight",
            )
            mode = st.selectbox(
                "Mong muốn",
                modes,
                index=modes.index(default["mode"]),
                format_func=MODE_LABELS.get,
                key=f"{profile}-{name}-mode",
            )

            choice = {"weight": weight, "mode": mode}
            if mode == "target":
                low = int(default.get("min", 1))
                high = int(default.get("max", 10))
                choice["min"], choice["max"] = st.slider(
                    "Khoảng mong muốn",
                    0,
                    50,
                    (low, high),
                    key=f"{profile}-{name}-target",
                )
            else:
                choice["limit"] = limit_slider(
                    name,
                    default.get("limit", CRITERIA[name][2]),
                    f"{profile}-{name}-limit",
                )

            preferences[name] = choice

    return preferences


def select_candidates(result, limit, minimum_distance_m):
    candidates = result[result["recommended"]].sort_values(
        "suitability_score",
        ascending=False,
    )
    if candidates.empty:
        return candidates

    selected = []
    coordinates = []
    for index, point in candidates.geometry.representative_point().items():
        current = np.array([point.x, point.y])
        if coordinates and np.any(
            np.linalg.norm(np.asarray(coordinates) - current, axis=1)
            < minimum_distance_m
        ):
            continue
        selected.append(index)
        coordinates.append(current)
        if len(selected) == limit:
            break

    return candidates.loc[selected]


def score_color(score):
    red, green, blue, _ = mpl.colormaps["YlOrRd"](float(score))
    return [int(red * 255), int(green * 255), int(blue * 255), 190]


def map_deck(result, candidates, scope, score_columns):
    columns = ["cell_id", "suitability_score", *score_columns, "geometry"]
    cells = result[result["recommended"]][columns].copy().to_crs(4326)
    cells["fill_color"] = cells["suitability_score"].map(score_color)

    def tooltip(row):
        details = "".join(
            f"<br>{LABELS[column.removeprefix('score_')]}: {row[column]:.3f}"
            for column in score_columns
        )
        return (
            f"<b>{row['cell_id']}</b>"
            f"<br>Điểm tổng: {row['suitability_score']:.3f}"
            f"{details}"
        )

    cells["tooltip"] = cells.apply(tooltip, axis=1)
    geojson = json.loads(cells.to_json(drop_id=True))

    layers = [
        pdk.Layer(
            "GeoJsonLayer",
            id="recommended-cells",
            data=geojson,
            filled=True,
            stroked=False,
            get_fill_color="properties.fill_color",
            pickable=True,
            auto_highlight=True,
        )
    ]

    if not candidates.empty:
        candidate_points = candidates[["cell_id", "suitability_score", "geometry"]].copy()
        candidate_points = candidate_points.to_crs(4326)
        centers = candidate_points.geometry.representative_point()
        candidate_data = pd.DataFrame(
            {
                "cell_id": candidate_points["cell_id"],
                "score": candidate_points["suitability_score"].round(3),
                "longitude": centers.x,
                "latitude": centers.y,
            }
        )
        candidate_data["tooltip"] = (
            "<b>Ứng viên "
            + candidate_data["cell_id"].astype(str)
            + "</b><br>Điểm: "
            + candidate_data["score"].astype(str)
        )
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                id="candidate-points",
                data=candidate_data,
                get_position="[longitude, latitude]",
                get_fill_color=[20, 90, 230, 230],
                get_line_color=[255, 255, 255, 255],
                get_radius=450,
                line_width_min_pixels=2,
                stroked=True,
                pickable=True,
            )
        )

    if scope == "Trung tâm Hà Nội":
        view = pdk.ViewState(
            latitude=21.0285,
            longitude=105.8542,
            zoom=10.4,
            pitch=0,
        )
    else:
        bounds = result.to_crs(4326).total_bounds
        view = pdk.ViewState(
            latitude=(bounds[1] + bounds[3]) / 2,
            longitude=(bounds[0] + bounds[2]) / 2,
            zoom=8.5,
            pitch=0,
        )

    return pdk.Deck(
        map_style=None,
        initial_view_state=view,
        layers=layers,
        tooltip={"html": "{tooltip}"},
    )


st.set_page_config(
    page_title="Đánh giá khu vực Hà Nội",
    page_icon="🗺️",
    layout="wide",
)

st.title("Đánh giá khu vực phù hợp")
st.caption(
    "Chọn một hồ sơ có sẵn, sau đó điều chỉnh nhu cầu để tìm các khu vực phù hợp nhất."
)

model = load_model()

st.sidebar.header("Lựa chọn của người dùng")
profile = st.sidebar.selectbox("Hồ sơ mặc định", list(PROFILES))
scope = st.sidebar.radio(
    "Phạm vi bản đồ",
    ["Trung tâm Hà Nội", "Toàn khu vực"],
)
top_percent = st.sidebar.slider("Tỷ lệ khu vực nổi bật (%)", 5, 30, 10, 5)
candidate_limit = st.sidebar.slider("Số khu vực đề xuất", 5, 20, 10)
minimum_distance = st.sidebar.slider(
    "Khoảng cách giữa đề xuất (m)",
    500,
    5000,
    2000,
    500,
)

st.sidebar.subheader("Điều chỉnh tiêu chí")
preferences = preference_controls(profile)

result = model.evaluate(
    preferences,
    top_quantile=1 - top_percent / 100,
)

if scope == "Trung tâm Hà Nội":
    xmin, xmax, ymin, ymax = CENTRAL_BOUNDS
    visible_result = result.cx[xmin:xmax, ymin:ymax]
else:
    visible_result = result

candidates = select_candidates(
    visible_result,
    candidate_limit,
    minimum_distance,
)
recommended_count = int(visible_result["recommended"].sum())
best_score = float(visible_result["suitability_score"].max())

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Hồ sơ", profile)
metric_2.metric("Cell đang hiển thị", f"{len(visible_result):,}")
metric_3.metric("Cell phù hợp", f"{recommended_count:,}")
metric_4.metric("Điểm cao nhất", f"{best_score:.3f}")

score_columns = [
    f"score_{name}"
    for name, choice in preferences.items()
    if choice["weight"] > 0
]

if recommended_count:
    deck = map_deck(visible_result, candidates, scope, score_columns)
    st.pydeck_chart(
        deck,
        width="stretch",
        height=680,
    )
else:
    st.warning("Không có khu vực phù hợp với lựa chọn hiện tại.")

st.subheader("Các khu vực đề xuất")
table_columns = ["cell_id", "suitability_score", *score_columns]
table = candidates[table_columns].copy()
table = table.rename(
    columns={
        "cell_id": "Cell",
        "suitability_score": "Điểm tổng",
        **{
            column: LABELS[column.removeprefix("score_")]
            for column in score_columns
        },
    }
)
numeric_columns = table.select_dtypes(include="number").columns
table[numeric_columns] = table[numeric_columns].round(3)
st.dataframe(table, width="stretch", hide_index=True)
