import tensorflow as tf
import numpy as np
import pandas as pd
import joblib
import streamlit as st
from pathlib import Path
import time

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
# LOAD MODEL & SCALER (CACHED)
# ==========================================
@st.cache_resource(show_spinner=False)
def load_resources():
    """Memuat model dan scaler sekali saja dan menyimpannya di memori."""
    print("\n[INIT] Loading Heavy Resources (TensorFlow Model & Scalers)...")
    start_load = time.time()
    
    model = tf.keras.models.load_model(
        MODEL_DIR / "gab_window8.keras"
    )

    feature_scaler = joblib.load(
        MODEL_DIR / "feature_scaler_gab.pkl"
    )

    target_scaler = joblib.load(
        MODEL_DIR / "target_scaler_gab.pkl"
    )
    
    end_load = time.time()
    print(f"[INIT] Resources loaded successfully in {end_load - start_load:.2f} seconds.\n")
    return model, feature_scaler, target_scaler


# ==========================================
# INFERENCE
# ==========================================
def run_inference(df_raw: pd.DataFrame, start_time=None, resources=None):
    """
    Melakukan satu langkah prediksi.
    resources: tuple (model, feature_scaler, target_scaler) opsional untuk menghindari pemanggilan cache berulang.
    """
    if len(df_raw) != WINDOW_SIZE:
        raise ValueError(
            f"Data harus berisi tepat {WINDOW_SIZE} baris."
        )

    if start_time is None:
        start_time = pd.Timestamp("2024-01-01 00:00")
    else:
        start_time = pd.to_datetime(start_time)

    df = df_raw.copy()

    # ======================================
    # FEATURE ENGINEERING
    # ======================================
    prev_lat = df["LAT"].shift(1)
    prev_lon = df["LON"].shift(1)
    prev_time = df["ISO_TIME"] if "ISO_TIME" in df.columns else pd.date_range(start=start_time, periods=WINDOW_SIZE, freq="3h")
    
    if "ISO_TIME" not in df.columns:
        df["ISO_TIME"] = prev_time

    prev_time_shift = df["ISO_TIME"].shift(1)
    delta_hour = (
        (df["ISO_TIME"] - prev_time_shift)
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
    # LOAD RESOURCE (FROM CACHE OR ARGUMENT)
    # ======================================
    if resources is None:
        model, feature_scaler, target_scaler = load_resources()
    else:
        model, feature_scaler, target_scaler = resources

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
    
    return {
        "pred_lat": float(prediction[0, 0]),
        "pred_lon": float(prediction[0, 1]),
    }

# ==========================================
# RECURSIVE INFERENCE
# ==========================================
def run_recursive_inference(df_raw: pd.DataFrame, start_time, steps=1):
    """
    Melakukan prediksi secara rekursif dengan log terminal yang detail.
    Setiap prediksi baru ditambahkan ke window dan window bergeser.
    """
    print("\n" + "="*60)
    print("MEMULAI PROSES PREDIKSI REKURSIF (LSTM)")
    print("="*60)
    print(f"* Horizon Prediksi : {steps * 3} Jam ({steps} Langkah)")
    print(f"* Waktu Awal       : {start_time}")
    print(f"* Model Terpilih   : GAB_WINDOW_8 (Stacked LSTM)")
    print("-" * 60)

    overall_start = time.time()
    
    # Muat resources sekali di awal rekursi
    resources = load_resources()
    
    current_df = df_raw.copy()
    start_dt = pd.to_datetime(start_time)
    
    # Data 8 titik observasi historis dimulai dari start_time (Titik 1 = start_time, Titik 8 = start_time + 21 jam)
    current_df["ISO_TIME"] = pd.date_range(
        start=start_dt,
        periods=WINDOW_SIZE,
        freq="3h"
    )
    current_time = current_df["ISO_TIME"].iloc[-1]
    
    predictions = []
    
    for i in range(steps):
        step_start = time.time()
        step_num = i + 1
        target_time = current_time + pd.Timedelta(hours=3)
        
        print(f"> LANGKAH {step_num}/{steps} | Target: {target_time.strftime('%Y-%m-%d %H:%M')}")
        
        # 1. Prediksi untuk step saat ini
        result = run_inference(current_df, start_time=current_time, resources=resources)
        
        # 2. Simpan hasil
        prediction_point = {
            "pred_lat": result["pred_lat"],
            "pred_lon": result["pred_lon"],
            "time": target_time
        }
        predictions.append(prediction_point)
        
        step_end = time.time()
        print(f"  -> Hasil: LAT {result['pred_lat']:.4f}, LON {result['pred_lon']:.4f} | Durasi: {step_end - step_start:.4f}s")
        
        # 3. Update window untuk step berikutnya
        new_row = {
            "LAT": result["pred_lat"],
            "LON": result["pred_lon"],
            "WMO_WIND": current_df["WMO_WIND"].iloc[-1],
            "WMO_PRES": current_df["WMO_PRES"].iloc[-1],
            "ISO_TIME": target_time
        }
        
        current_df = current_df.iloc[1:].copy()
        current_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
        current_time = target_time
        
    overall_end = time.time()
    print("-" * 60)
    print(f"PREDIKSI SELESAI!")
    print(f"* Total Waktu Eksekusi: {overall_end - overall_start:.4f} detik")
    print(f"* Rata-rata per Langkah: {(overall_end - overall_start)/steps:.4f} detik")
    print("="*60 + "\n")
        
    return predictions
