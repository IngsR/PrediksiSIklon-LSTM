"""Prediksi lintasan satu langkah berbasis kinematika geodesik.

Modul ini sengaja tidak bergantung pada TensorFlow/Keras.  Perpindahan
diproyeksikan dari kecepatan dan arah beberapa observasi terakhir, lalu
dibatasi oleh batas fisik yang konservatif untuk interval tiga jam.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


EARTH_RADIUS_KM = 6371.0
DEFAULT_INTERVAL_HOURS = 3.0
# Kecepatan translasi siklon umumnya jauh lebih rendah dari nilai ini. Batas
# ini adalah pagar pengaman terhadap titik input yang salah/terlompat.
MAX_TRANSLATION_SPEED_KMH = 60.0


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Arah lintasan geodesik dalam derajat (0=utara, 90=timur)."""
    delta_lon = math.radians(lon2 - lon1)
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Jarak lingkaran besar dalam kilometer."""
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, (lat1, lon1, lat2, lon2))
    delta_lat, delta_lon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def destination(lat: float, lon: float, bearing: float, distance_km: float) -> tuple[float, float]:
    """Titik tujuan setelah bergerak ``distance_km`` pada arah ``bearing``."""
    lat1, lon1, direction = map(math.radians, (lat, lon, bearing))
    angular_distance = distance_km / EARTH_RADIUS_KM
    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance)
        + math.cos(lat1) * math.sin(angular_distance) * math.cos(direction)
    )
    lon2 = lon1 + math.atan2(
        math.sin(direction) * math.sin(angular_distance) * math.cos(lat1),
        math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
    )
    lon2 = (math.degrees(lon2) + 540.0) % 360.0 - 180.0
    return math.degrees(lat2), lon2


def _valid_history(df: pd.DataFrame) -> pd.DataFrame:
    required = {"LAT", "LON"}
    if not required.issubset(df.columns):
        raise ValueError("Data harus memiliki kolom LAT dan LON.")

    history = df[["LAT", "LON"]].apply(pd.to_numeric, errors="coerce").dropna()
    history = history[(history["LAT"].between(-90, 90)) & (history["LON"].between(-180, 180))]
    if len(history) < 2:
        raise ValueError("Minimal dua koordinat valid diperlukan.")
    return history.reset_index(drop=True)


def predict_next_position(
    df: pd.DataFrame,
    interval_hours: float = DEFAULT_INTERVAL_HOURS,
    forecast_hours: float = DEFAULT_INTERVAL_HOURS,
    max_speed_kmh: float = MAX_TRANSLATION_SPEED_KMH,
) -> dict[str, float]:
    """Prediksi posisi berikutnya dari gerak 3 jam terakhir yang robust.

    Median tiga segmen terakhir menahan satu klik koordinat yang salah agar
    tidak menghasilkan lonjakan ribuan kilometer pada prediksi berikutnya.
    """
    if interval_hours <= 0 or forecast_hours <= 0 or max_speed_kmh <= 0:
        raise ValueError("Interval, horizon, dan batas kecepatan harus lebih besar dari nol.")

    history = _valid_history(df)
    recent = history.iloc[-4:].to_numpy(dtype=float)
    distances, bearings = [], []
    for (lat1, lon1), (lat2, lon2) in zip(recent[:-1], recent[1:]):
        distance = haversine_km(lat1, lon1, lat2, lon2)
        distances.append(distance)
        bearings.append(calculate_bearing(lat1, lon1, lat2, lon2))

    speeds = np.asarray(distances, dtype=float) / interval_hours
    # Median menjadikan estimasi tahan terhadap satu outlier pada riwayat.
    raw_speed = float(np.median(speeds))
    speed = min(raw_speed, max_speed_kmh)

    # Arah dari segmen terbaru yang masih berada dalam batas fisik. Jika semua
    # outlier, pertahankan arah segmen terakhir tetapi tetap batasi jaraknya.
    plausible = [i for i, value in enumerate(speeds) if value <= max_speed_kmh]
    direction_index = plausible[-1] if plausible else len(bearings) - 1
    bearing = bearings[direction_index]
    distance_forecast = speed * forecast_hours
    last_lat, last_lon = recent[-1]
    pred_lat, pred_lon = destination(last_lat, last_lon, bearing, distance_forecast)

    return {
        "lat": pred_lat,
        "lon": pred_lon,
        "bearing": bearing,
        "raw_speed_kmh": raw_speed,
        "speed_kmh": speed,
        "distance_km": distance_forecast,
        "max_distance_km": max_speed_kmh * forecast_hours,
    }
