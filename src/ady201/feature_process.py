def build_cell_features(cells, poi_features, road_features):
    features = cells.merge(poi_features, on="cell_id", how="left")
    features = features.merge(road_features, on="cell_id", how="left")
    return features

def feature_process(features):
    df  = features.copy()
    for col in df:
        if "count" in col or "road_length" in col or "road_density" in col:
            df[col] = df[col].fillna(0)

    return df
