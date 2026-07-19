import numpy as np
import pandas as pd
from prediction.inference import haversine, bearing

def calculate_analytics(history_df, pred_lat, pred_lon):
    """
    Menghitung metrik informatif berdasarkan data historis dan titik prediksi.
    """
    # Ambil titik terakhir dari data historis
    last_point = history_df.iloc[-1]

    # 1. Kecepatan (km/h) - Asumsi interval 3 jam
    dist = haversine(last_point["LAT"], last_point["LON"], pred_lat, pred_lon)
    speed = dist / 3.0

    # 2. Arah (Bearing)
    brng = bearing(last_point["LAT"], last_point["LON"], pred_lat, pred_lon)

    # 3. Klasifikasi Kategori (Berdasarkan WMO/NOAA Wind Speed dalam knot)
    wind = last_point["WMO_WIND"]

    if wind >= 108:
        category = "Siklon Tropis Kategori 5 (Ekstrem)"
    elif wind >= 86:
        category = "Siklon Tropis Kategori 4 (Sangat Parah)"
    elif wind >= 64:
        category = "Siklon Tropis Kategori 3 (Parah)"
    elif wind >= 48:
        category = "Siklon Tropis Kategori 2 (Sedang)"
    elif wind >= 34:
        category = "Siklon Tropis Kategori 1 (Lemah)"
    else:
        category = "Sistem Tekanan Rendah Tropis"

    return {
        "speed_kmh": round(speed, 2),
        "bearing": round(brng, 1),
        "category": category
    }
