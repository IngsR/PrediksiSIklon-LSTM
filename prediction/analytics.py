import numpy as np
import pandas as pd
from prediction.inference import haversine, bearing

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
        description = "Intensitas sangat ekstrem dengan potensi kerusakan yang sangat besar. Masyarakat perlu mengikuti seluruh peringatan resmi dan menghindari aktivitas di wilayah terdampak."

    elif wind >= 113:
        category = "Siklon Tropis Kategori 4"
        description = "Intensitas sangat kuat dengan potensi kerusakan berat pada bangunan, pepohonan, dan jaringan listrik."

    elif wind >= 96:
        category = "Siklon Tropis Kategori 3"
        description = "Termasuk siklon mayor dengan potensi kerusakan berat serta gelombang tinggi yang dapat membahayakan wilayah pesisir."

    elif wind >= 83:
        category = "Siklon Tropis Kategori 2"
        description = "Siklon kuat yang dapat menyebabkan kerusakan sedang hingga berat serta meningkatkan risiko gelombang tinggi."

    elif wind >= 64:
        category = "Siklon Tropis Kategori 1"
        description = "Siklon tropis dengan potensi kerusakan ringan hingga sedang. Masyarakat disarankan memantau informasi cuaca secara berkala."

    elif wind >= 34:
        category = "Badai Tropis"
        description = "Belum termasuk siklon tropis kategori 1, tetapi sudah memiliki angin kencang dan berpotensi menimbulkan hujan lebat serta gelombang tinggi."

    else:
        category = "Depresi Tropis"
        description = "Sistem tekanan rendah dengan potensi berkembang menjadi badai tropis apabila kondisi atmosfer mendukung."

    return {
        "speed_kmh": round(speed, 2),
        "bearing": round(brng, 1),
        "category": category,
        "description": description
    }
