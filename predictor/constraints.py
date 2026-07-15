# ==========================================================
# predictor/constraints.py
# Trajectory Constraint Engine
# ==========================================================

import numpy as np


# ==========================================================
# UTILITAS
# ==========================================================

def clip(value, minimum, maximum):

    return np.minimum(
        np.maximum(value, minimum),
        maximum
    )


# ==========================================================
# SPEED CONSTRAINT
# ==========================================================

def speed_constraint(

    history,

    prediction,

    max_ratio=1.35

):

    if len(history) < 2:

        return prediction

    last = history.iloc[-1]

    prev = history.iloc[-2]

    history_dx = last["LAT"] - prev["LAT"]
    history_dy = last["LON"] - prev["LON"]

    pred_dx = prediction["LAT"] - last["LAT"]
    pred_dy = prediction["LON"] - last["LON"]

    history_mag = np.sqrt(
        history_dx**2 +
        history_dy**2
    )

    pred_mag = np.sqrt(
        pred_dx**2 +
        pred_dy**2
    )

    if history_mag == 0:

        return prediction

    max_step = history_mag * max_ratio

    if pred_mag <= max_step:

        return prediction

    scale = max_step / pred_mag

    prediction["LAT"] = (
        last["LAT"] +
        pred_dx * scale
    )

    prediction["LON"] = (
        last["LON"] +
        pred_dy * scale
    )

    return prediction


# ==========================================================
# MOMENTUM CONSTRAINT
# ==========================================================

def momentum_constraint(

    history,

    prediction,

    alpha=0.25

):

    if len(history) < 2:

        return prediction

    last = history.iloc[-1]

    prev = history.iloc[-2]

    vx = last["LAT"] - prev["LAT"]
    vy = last["LON"] - prev["LON"]

    prediction["LAT"] = (

        (1-alpha) * prediction["LAT"] +

        alpha * (last["LAT"] + vx)

    )

    prediction["LON"] = (

        (1-alpha) * prediction["LON"] +

        alpha * (last["LON"] + vy)

    )

    return prediction


# ==========================================================
# LATITUDE CONSTRAINT
# ==========================================================

def latitude_constraint(

    prediction

):

    prediction["LAT"] = clip(

        prediction["LAT"],

        -40,

        40

    )

    return prediction


# ==========================================================
# LONGITUDE CONSTRAINT
# ==========================================================

def longitude_constraint(

    prediction

):

    prediction["LON"] = clip(

        prediction["LON"],

        40,

        130

    )

    return prediction


# ==========================================================
# TURN CONSTRAINT
# ==========================================================

def turn_constraint(

    history,

    prediction,

    max_turn_deg=35

):

    if len(history) < 3:

        return prediction

    p1 = history.iloc[-3]
    p2 = history.iloc[-2]
    p3 = history.iloc[-1]

    v1 = np.array([

        p2["LAT"]-p1["LAT"],

        p2["LON"]-p1["LON"]

    ])

    v2 = np.array([

        p3["LAT"]-p2["LAT"],

        p3["LON"]-p2["LON"]

    ])

    vp = np.array([

        prediction["LAT"]-p3["LAT"],

        prediction["LON"]-p3["LON"]

    ])

    if np.linalg.norm(v2)==0:

        return prediction

    cos_angle = np.dot(v2,vp)

    cos_angle /= (

        np.linalg.norm(v2) *

        np.linalg.norm(vp)

    )

    cos_angle=np.clip(cos_angle,-1,1)

    angle=np.degrees(np.arccos(cos_angle))

    if angle<=max_turn_deg:

        return prediction

    scale=max_turn_deg/angle

    prediction["LAT"]=p3["LAT"]+vp[0]*scale
    prediction["LON"]=p3["LON"]+vp[1]*scale

    return prediction


# ==========================================================
# APPLY
# ==========================================================

def apply_constraints(

    history,

    prediction

):

    prediction = speed_constraint(

        history,

        prediction

    )

    prediction = momentum_constraint(

        history,

        prediction

    )

    prediction = turn_constraint(

        history,

        prediction

    )

    prediction = latitude_constraint(

        prediction

    )

    prediction = longitude_constraint(

        prediction

    )

    return prediction