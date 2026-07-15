# ==========================================================
# predictor/postprocessing.py
# Trajectory Refinement Engine
# ==========================================================

import numpy as np


# ==========================================================
# LIMIT LATITUDE
# ==========================================================

def clamp_latitude(lat):

    return np.clip(lat, -90.0, 90.0)


# ==========================================================
# LIMIT LONGITUDE
# ==========================================================

def clamp_longitude(lon):

    while lon > 180:
        lon -= 360

    while lon < -180:
        lon += 360

    return lon


# ==========================================================
# MAXIMUM STEP
# ==========================================================

def limit_step(

    last_lat,
    last_lon,

    pred_lat,
    pred_lon,

    max_delta=2.0

):

    dlat = pred_lat - last_lat
    dlon = pred_lon - last_lon

    magnitude = np.sqrt(
        dlat**2 +
        dlon**2
    )

    if magnitude <= max_delta:

        return pred_lat, pred_lon

    scale = max_delta / magnitude

    pred_lat = last_lat + dlat * scale
    pred_lon = last_lon + dlon * scale

    return pred_lat, pred_lon


# ==========================================================
# MOMENTUM
# ==========================================================

def momentum(

    history,

    pred_lat,
    pred_lon,

    alpha=0.25

):

    if len(history) < 2:

        return pred_lat, pred_lon

    last = history.iloc[-1]

    prev = history.iloc[-2]

    vx = last["LAT"] - prev["LAT"]
    vy = last["LON"] - prev["LON"]

    pred_lat = (
        (1 - alpha) * pred_lat +
        alpha * (last["LAT"] + vx)
    )

    pred_lon = (
        (1 - alpha) * pred_lon +
        alpha * (last["LON"] + vy)
    )

    return pred_lat, pred_lon


# ==========================================================
# MOVING AVERAGE
# ==========================================================

def smooth(

    history,

    pred_lat,
    pred_lon,

    beta=0.30

):

    mean_lat = history["LAT"].tail(3).mean()
    mean_lon = history["LON"].tail(3).mean()

    pred_lat = (
        (1 - beta) * pred_lat +
        beta * mean_lat
    )

    pred_lon = (
        (1 - beta) * pred_lon +
        beta * mean_lon
    )

    return pred_lat, pred_lon


# ==========================================================
# BOUNDARY
# ==========================================================

def basin_boundary(

    lat,
    lon

):

    lat = np.clip(
        lat,
        -40,
        40
    )

    lon = np.clip(
        lon,
        40,
        130
    )

    return lat, lon


# ==========================================================
# PIPELINE
# ==========================================================

def refine(

    history,

    prediction

):

    last = history.iloc[-1]

    lat = prediction["LAT"]
    lon = prediction["LON"]

    lat, lon = limit_step(

        last["LAT"],
        last["LON"],

        lat,
        lon

    )

    lat, lon = momentum(

        history,

        lat,
        lon

    )

    lat, lon = smooth(

        history,

        lat,
        lon

    )

    lat, lon = basin_boundary(

        lat,
        lon

    )

    lat = clamp_latitude(lat)

    lon = clamp_longitude(lon)

    return {

        "LAT": float(lat),

        "LON": float(lon)

    }