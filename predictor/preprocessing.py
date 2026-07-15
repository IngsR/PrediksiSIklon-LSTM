# ==========================================================
# predictor/preprocessing.py
# Preprocessing untuk inferensi model LSTM
# ==========================================================

import numpy as np
import pandas as pd


# ==========================================================
# KONSTANTA
# ==========================================================

EARTH_RADIUS_KM = 6371.0


# ==========================================================
# VALIDASI INPUT
# ==========================================================

REQUIRED_COLUMNS = [
    "LAT",
    "LON",
    "WMO_WIND",
    "WMO_PRES"
]


def validate_input(df: pd.DataFrame):

    missing = []

    for col in REQUIRED_COLUMNS:

        if col not in df.columns:
            missing.append(col)

    if len(missing) > 0:

        raise ValueError(
            f"Kolom tidak ditemukan : {missing}"
        )

    if len(df) < 8:

        raise ValueError(
            "Minimal diperlukan 8 observasi."
        )

    return True


# ==========================================================
# HAVERSINE
# ==========================================================

def haversine(lat1, lon1, lat2, lon2):

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(a))

    return EARTH_RADIUS_KM * c


# ==========================================================
# BEARING
# ==========================================================

def bearing(lat1, lon1, lat2, lon2):

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)

    dlon = np.radians(lon2 - lon1)

    y = np.sin(dlon) * np.cos(lat2)

    x = (
        np.cos(lat1) * np.sin(lat2)
        - np.sin(lat1)
        * np.cos(lat2)
        * np.cos(dlon)
    )

    angle = np.degrees(np.arctan2(y, x))

    return (angle + 360) % 360


# ==========================================================
# FEATURE ENGINEERING
# ==========================================================

def build_features(df: pd.DataFrame):

    data = df.copy()

    data["delta_lat"] = data["LAT"].diff()

    data["delta_lon"] = data["LON"].diff()

    data["dist_km"] = haversine(
        data["LAT"].shift(1),
        data["LON"].shift(1),
        data["LAT"],
        data["LON"]
    )

    data["speed_kmh"] = data["dist_km"] / 3.0

    data["bearing"] = bearing(
        data["LAT"].shift(1),
        data["LON"].shift(1),
        data["LAT"],
        data["LON"]
    )

    data["turn_angle"] = (
        data["bearing"].diff()
    )

    data["turn_angle"] = (
        (data["turn_angle"] + 180) % 360
    ) - 180

    data.fillna(0.0, inplace=True)

    return data


# ==========================================================
# URUTKAN FEATURE
# ==========================================================

def arrange_features(
    feature_df,
    feature_columns
):

    missing = []

    for col in feature_columns:

        if col not in feature_df.columns:

            missing.append(col)

    if len(missing) > 0:

        raise ValueError(
            f"Feature hilang : {missing}"
        )

    return feature_df[
        feature_columns
    ].copy()


# ==========================================================
# SCALING
# ==========================================================

def scale_features(
    feature_df,
    scaler
):

    scaled = scaler.transform(feature_df)

    return scaled


# ==========================================================
# BENTUK INPUT LSTM
# ==========================================================

def make_sequence(
    scaled_feature,
    window_size=8
):

    if len(scaled_feature) < window_size:

        raise ValueError(
            "Data kurang dari window."
        )

    sequence = scaled_feature[
        -window_size:
    ]

    sequence = np.expand_dims(
        sequence,
        axis=0
    )

    return sequence.astype(
        np.float32
    )


# ==========================================================
# PIPELINE
# ==========================================================

def prepare_input(
    df,
    feature_columns,
    scaler,
    window_size=8
):

    validate_input(df)

    feature_df = build_features(df)

    feature_df = arrange_features(
        feature_df,
        feature_columns
    )

    scaled = scale_features(
        feature_df,
        scaler
    )

    sequence = make_sequence(
        scaled,
        window_size
    )

    return sequence