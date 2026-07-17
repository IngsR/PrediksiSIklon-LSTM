import tensorflow as tf
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

# ==========================================
# KONSTANTA & KONFIGURASI
# ==========================================
WINDOW_SIZE = 8

MODEL_FEATURES = [
    "LAT",
    "LON",
    "WMO_WIND",
    "WMO_PRES",
    "delta_lat",
    "delta_lon",
    "speed_kmh",
    "bearing_rate",
    "acceleration",
    "sin_month",
    "cos_month",
]

FEATURES_TO_SCALE = [
    "WMO_WIND",
    "WMO_PRES",
    "delta_lat",
    "delta_lon",
    "speed_kmh",
    "bearing_rate",
    "acceleration",
    "sin_month",
    "cos_month",
]

# ==========================================
# PATH
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

# ==========================================
# UTILITAS GEOMETRI
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def bearing(lat1, lon1, lat2, lon2):
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlon = lon2 - lon1

    x = np.sin(dlon) * np.cos(lat2)

    y = (
        np.cos(lat1) * np.sin(lat2)
        - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    )

    angle = np.degrees(np.arctan2(x, y))

    return (angle + 360) % 360


def angle_diff(series):
    diff = series.diff()
    diff = (diff + 180) % 360 - 180
    return diff.abs()


# ==========================================
# LOAD MODEL & SCALER
# ==========================================
def load_resources():
    model = tf.keras.models.load_model(
        MODEL_DIR / "gab_window8.keras"
    )

    feature_scaler = joblib.load(
        MODEL_DIR / "feature_scaler_gab.pkl"
    )

    target_scaler = joblib.load(
        MODEL_DIR / "target_scaler_gab.pkl"
    )

    return model, feature_scaler, target_scaler


# ==========================================
# INFERENCE
# ==========================================
def run_inference(df_raw: pd.DataFrame, start_time=None):

    if len(df_raw) != WINDOW_SIZE:
        raise ValueError(
            f"Data harus berisi tepat {WINDOW_SIZE} baris."
        )

    if start_time is None:
        start_time = pd.Timestamp("2024-01-01 00:00")
    else:
        start_time = pd.to_datetime(start_time)

    df = df_raw.copy()

    df["ISO_TIME"] = pd.date_range(
        start=start_time,
        periods=WINDOW_SIZE,
        freq="3h",
    )

    # ======================================
    # FEATURE ENGINEERING
    # ======================================

    prev_lat = df["LAT"].shift(1)
    prev_lon = df["LON"].shift(1)
    prev_time = df["ISO_TIME"].shift(1)

    delta_hour = (
        (df["ISO_TIME"] - prev_time)
        .dt.total_seconds()
        .div(3600)
    )

    df["delta_lat"] = df["LAT"] - prev_lat
    df["delta_lon"] = df["LON"] - prev_lon

    distance = haversine(
        prev_lat,
        prev_lon,
        df["LAT"],
        df["LON"],
    )

    df["speed_kmh"] = np.where(
        delta_hour > 0,
        distance / delta_hour,
        np.nan,
    )

    df["bearing"] = bearing(
        prev_lat,
        prev_lon,
        df["LAT"],
        df["LON"],
    )

    df["bearing_rate"] = angle_diff(df["bearing"])

    prev_speed = df["speed_kmh"].shift(1)

    df["acceleration"] = np.where(
        delta_hour > 0,
        (df["speed_kmh"] - prev_speed) / delta_hour,
        np.nan,
    )

    month = df["ISO_TIME"].dt.month

    df["sin_month"] = np.sin(
        2 * np.pi * month / 12
    )

    df["cos_month"] = np.cos(
        2 * np.pi * month / 12
    )

    df[
        [
            "delta_lat",
            "delta_lon",
            "speed_kmh",
            "bearing_rate",
            "acceleration",
        ]
    ] = df[
        [
            "delta_lat",
            "delta_lon",
            "speed_kmh",
            "bearing_rate",
            "acceleration",
        ]
    ].fillna(0)

    df.drop(columns=["bearing"], inplace=True)

    # ======================================
    # LOAD RESOURCE
    # ======================================

    model, feature_scaler, target_scaler = load_resources()

    # Validasi agar nama fitur sama persis
    expected = list(feature_scaler.feature_names_in_)

    if expected != FEATURES_TO_SCALE:
        raise ValueError(
            f"Feature scaler mengharapkan {expected}, "
            f"namun inference menggunakan {FEATURES_TO_SCALE}."
        )

    scaled_features = feature_scaler.transform(
        df[FEATURES_TO_SCALE]
    )

    scaled_df = pd.DataFrame(
        scaled_features,
        columns=FEATURES_TO_SCALE,
        index=df.index,
    )

    # ======================================
    # PREPARE INPUT (X)
    # ======================================
    # Pastikan urutan kolom sesuai MODEL_FEATURES
    # LAT dan LON menggunakan nilai asli (tidak di-scale) sesuai PDF
    # Feature lainnya menggunakan nilai yang sudah di-scale
    
    final_df = pd.DataFrame(index=df.index)
    final_df["LAT"] = df["LAT"].values
    final_df["LON"] = df["LON"].values
    
    for col in FEATURES_TO_SCALE:
        final_df[col] = scaled_df[col].values

    X = (
        final_df[MODEL_FEATURES]
        .astype(np.float32)
        .to_numpy()
        .reshape(
            1,
            WINDOW_SIZE,
            len(MODEL_FEATURES),
        )
    )

    # ======================================
    # PREDIKSI
    # ======================================
    prediction = model.predict(
        X,
        verbose=0,
    )

    # Model ini memprediksi LAT dan LON secara langsung (unscaled)
    # Meskipun ada target_scaler, berdasarkan analisis PDF, 
    # output model (y_pred_scaled) sudah merupakan koordinat asli.
    
    return {
        "pred_lat": float(prediction[0, 0]),
        "pred_lon": float(prediction[0, 1]),
    }
