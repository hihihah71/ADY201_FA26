from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ACTIVITY_COLUMNS = [
    "food_and_drink_count_500m",
    "shopping_count_500m",
    "arts_and_entertainment_count_500m",
    "sports_and_recreation_count_500m",
    "travel_and_transportation_count_500m",
]

# name: source column, default mode, default limit
CRITERIA = {
    "food": ("food_and_drink_count_200m", "more", 6),
    "services": ("services_and_business_count_200m", "more", 8),
    "shopping": ("shopping_count_200m", "more", 10),
    "school": ("nearest_school_m", "near", 1500),
    "university": ("nearest_college_university_m", "near", 1500),
    "hospital": ("nearest_hospital_m", "near", 2000),
    "pharmacy": ("nearest_pharmacy_m", "near", 1000),
    "grocery": ("nearest_grocery_store_m", "near", 1000),
    "park": ("nearest_park_m", "near", 2000),
    "transport": ("road_density_1000m_km_per_km2", "more", 15),
    "quietness": (None, "more", 1),
}


def _number(values):
    return pd.to_numeric(values, errors="coerce").fillna(0).clip(lower=0)


def _more(values, limit):
    return (_number(values) / limit).clip(upper=1)


def _near(values, distance):
    return np.exp(-np.log(2) * _number(values) / distance)


def _quantile_scale(values, quantile=0.95):
    values = _number(values)
    limit = values.quantile(quantile)
    return (values / limit).clip(upper=1) if limit > 0 else values


def _quietness(features):
    activity = features[ACTIVITY_COLUMNS].apply(_number).sum(axis=1)
    activity_level = _quantile_scale(activity)
    road_level = _quantile_scale(features["road_density_500m_km_per_km2"])
    return np.sqrt((1 - activity_level) * (1 - road_level))


def _score(values, mode, limit, options):
    if mode in {"more", "less"}:
        score = _more(values, limit)
        return score if mode == "more" else 1 - score

    if mode in {"near", "far"}:
        score = _near(values, limit)
        return score if mode == "near" else 1 - score

    if mode == "target":
        low, high = options["min"], options["max"]
        values = _number(values)
        score = pd.Series(1.0, index=values.index)
        score[values < low] = values[values < low] / low
        score[values > high] = high / values[values > high]
        return score

    raise ValueError(f"Unknown mode: {mode}")


class SuitabilityModel:
    def __init__(self, features):
        self.features = features
        self.values = pd.DataFrame(
            {
                name: _number(features[column])
                for name, (column, _, _) in CRITERIA.items()
                if column
            }
        )
        self.values["quietness"] = _quietness(features)

    @classmethod
    def from_parquet(cls, path: str | Path):
        path = Path(path)
        if not path.is_absolute() and not path.exists():
            path = Path(__file__).resolve().parents[2] / path
        return cls(gpd.read_parquet(path))

    def evaluate(self, preferences, top_quantile=0.9):
        result = self.features.copy()
        weighted_log = pd.Series(0.0, index=result.index)
        total_weight = 0.0

        for name, choice in preferences.items():
            _, default_mode, default_limit = CRITERIA[name]
            is_config = isinstance(choice, dict)
            options = choice if is_config else {}
            weight = float(options.get("weight", 1) if is_config else choice)
            if weight <= 0:
                continue

            mode = options.get("mode", default_mode)
            limit = options.get("limit", default_limit)
            score = _score(self.values[name], mode, limit, options).clip(0, 1)

            result[f"score_{name}"] = score
            weighted_log += weight * np.log(score.clip(lower=1e-6))
            total_weight += weight

        if total_weight == 0:
            result["suitability_score"] = 0.0
            result["recommended"] = False
            return result

        result["suitability_score"] = np.exp(weighted_log / total_weight)
        threshold = result["suitability_score"].quantile(top_quantile)
        result["recommended"] = result["suitability_score"] >= threshold
        return result

    def top_cells(self, preferences, limit=20):
        return self.evaluate(preferences).nlargest(limit, "suitability_score")

    def select_candidates(self, preferences, limit=10, minimum_distance_m=2000):
        result = self.evaluate(preferences)
        candidates = result[result["recommended"]].sort_values(
            "suitability_score",
            ascending=False,
        )
        if candidates.empty:
            return candidates

        points = gpd.GeoSeries(
            candidates.geometry.representative_point(),
            index=candidates.index,
            crs=candidates.crs,
        ).to_crs(candidates.estimate_utm_crs())

        selected, coordinates = [], []
        for index, point in points.items():
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
