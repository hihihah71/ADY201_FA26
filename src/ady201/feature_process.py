def feature_process(feature):
    df  = feature.copy()
    for col in df:
        if "count" in col or "road_length" in col or "road_density" in col:
            df[col] = df[col].fillna(0)

    return df
