import numpy as np
import pandas as pd
from prediction.inference import haversine, bearing

def format_lat_indo(lat, precision=1):
    direction = "LS" if lat < 0 else "LU"
    return f"{abs(lat):.{precision}f}° {direction}"

def format_lon_indo(lon, precision=1):
    direction = "BB" if lon < 0 else "BT"
    return f"{abs(lon):.{precision}f}° {direction}"

def get_reliability_metrics(step):
    """
    Mengembalikan estimasi reliabilitas dan ketidakpastian (confidence) berdasarkan langkah prediksi (step)
    untuk mengakomodasi akumulasi kesalahan (error accumulation) pada model LSTM.
    """
    if step == 1:
        return {
            "reliability": "Tinggi",
            "confidence_pct": 92,
            "uncertainty_km": "±15-25 km",
            "text": "Tinggi (92%)",
            "color": "green"
        }
    elif step == 2:
        return {
            "reliability": "Sedang",
            "confidence_pct": 78,
            "uncertainty_km": "±35-55 km",
            "text": "Sedang (78%)",
            "color": "orange"
        }
    else:
        return {
            "reliability": "Rendah (Perlu Kewaspadaan)",
            "confidence_pct": 61,
            "uncertainty_km": "±60-90 km",
            "text": "Rendah (61%)",
            "color": "red"
        }

def calculate_analytics(history_df, pred_lat, pred_lon, prev_lat=None, prev_lon=None, wind_val=None):
    """
    Menghitung metrik informatif berdasarkan titik sebelumnya dan titik prediksi saat ini.
    Jika prev_lat & prev_lon tidak diberikan, gunakan titik terakhir dari history_df.
    """
    if prev_lat is None or prev_lon is None:
        last_point = history_df.iloc[-1]
        p_lat = float(last_point["LAT"])
        p_lon = float(last_point["LON"])
        wind = float(last_point["WMO_WIND"]) if wind_val is None else float(wind_val)
    else:
        p_lat = float(prev_lat)
        p_lon = float(prev_lon)
        wind = float(history_df.iloc[-1]["WMO_WIND"]) if wind_val is None else float(wind_val)

    # 1. Kecepatan (km/h) - Asumsi interval 3 jam
    dist = haversine(p_lat, p_lon, pred_lat, pred_lon)
    speed = dist / 3.0

    # 2. Arah (Bearing)
    brng = bearing(p_lat, p_lon, pred_lat, pred_lon)

    # 3. Klasifikasi Kategori (Berdasarkan WMO/NOAA Wind Speed dalam knot)
    if wind >= 137:
        category = "Siklon Tropis Kategori 5"
        description = "Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak sangat ekstrem apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis."

    elif wind >= 113:
        category = "Siklon Tropis Kategori 4"
        description = "Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak berat apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis."

    elif wind >= 96:
        category = "Siklon Tropis Kategori 3"
        description = "Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak berat pada wilayah pesisir apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis."

    elif wind >= 83:
        category = "Siklon Tropis Kategori 2"
        description = "Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak sedang hingga berat apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis."

    elif wind >= 64:
        category = "Siklon Tropis Kategori 1"
        description = "Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak ringan hingga sedang apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis."

    elif wind >= 34:
        category = "Badai Tropis"
        description = "Sistem berpotensi meningkatkan kecepatan angin dan memicu gelombang tinggi di sekitar lintasan apabila kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis."

    else:
        category = "Depresi Tropis"
        description = "Sistem tekanan rendah dengan potensi berkembang menjadi badai tropis apabila kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis."

    return {
        "speed_kmh": round(speed, 2),
        "bearing": round(brng, 1),
        "category": category,
        "description": description
    }
