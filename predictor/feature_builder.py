# ==========================================================
# predictor/feature_builder.py
# Feature Engineering
# ==========================================================

import numpy as np
import pandas as pd


EARTH_RADIUS = 6371.0


def haversine(lat1, lon1, lat2, lon2):

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat/2)**2
        +
        np.cos(lat1)
        *
        np.cos(lat2)
        *
        np.sin(dlon/2)**2
    )

    return 2 * EARTH_RADIUS * np.arcsin(np.sqrt(a))


def bearing(lat1, lon1, lat2, lon2):

    dlon = np.radians(lon2-lon1)

    lat1=np.radians(lat1)
    lat2=np.radians(lat2)

    y=np.sin(dlon)*np.cos(lat2)

    x=(
        np.cos(lat1)
        *
        np.sin(lat2)
        -
        np.sin(lat1)
        *
        np.cos(lat2)
        *
        np.cos(dlon)
    )

    angle=np.degrees(np.arctan2(y,x))

    return (angle+360)%360


def build(df):

    df=df.copy()

    df["delta_lat"]=df["LAT"].diff()

    df["delta_lon"]=df["LON"].diff()

    df["dist_km"]=haversine(

        df["LAT"].shift(),

        df["LON"].shift(),

        df["LAT"],

        df["LON"]

    )

    df["speed_kmh"]=df["dist_km"]/3

    df["bearing"]=bearing(

        df["LAT"].shift(),

        df["LON"].shift(),

        df["LAT"],

        df["LON"]

    )

    df["turn_angle"]=df["bearing"].diff()

    df["turn_angle"]=(
        (df["turn_angle"]+180)%360
    )-180

    df=df.fillna(0)

    return df