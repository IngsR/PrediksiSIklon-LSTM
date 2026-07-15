# ==========================================================
# predictor/inference.py
# Engine Inferensi Model LSTM
# ==========================================================

import numpy as np
import tensorflow as tf


# ==========================================================
# VALIDASI INPUT
# ==========================================================

def validate_sequence(sequence):

    if not isinstance(sequence, np.ndarray):
        raise TypeError("Sequence harus berupa numpy array.")

    if sequence.ndim != 3:
        raise ValueError(
            f"Dimensi sequence harus 3, diperoleh {sequence.ndim}"
        )

    if np.isnan(sequence).any():
        raise ValueError("Sequence mengandung NaN.")

    if np.isinf(sequence).any():
        raise ValueError("Sequence mengandung Infinity.")

    return True


# ==========================================================
# VALIDASI MODEL
# ==========================================================

def validate_model(model):

    if not isinstance(model, tf.keras.Model):
        raise TypeError("Model bukan tensorflow keras model.")

    return True


# ==========================================================
# PREDIKSI
# ==========================================================

def predict(model, sequence):

    validate_model(model)
    validate_sequence(sequence)

    prediction = model.predict(
        sequence,
        verbose=0
    )

    return prediction


# ==========================================================
# INVERSE TARGET
# ==========================================================

def inverse_target(prediction, scaler_y=None):

    if scaler_y is None:
        return prediction

    prediction = scaler_y.inverse_transform(prediction)

    return prediction


# ==========================================================
# KONVERSI OUTPUT
# ==========================================================

def prediction_to_coordinate(prediction):

    prediction = np.asarray(prediction)

    if prediction.ndim == 2:

        prediction = prediction[0]

    if len(prediction) != 2:

        raise ValueError(
            "Output model harus terdiri dari LAT dan LON."
        )

    return {

        "LAT": float(prediction[0]),
        "LON": float(prediction[1])

    }


# ==========================================================
# VALIDASI HASIL
# ==========================================================

def validate_coordinate(result):

    lat = result["LAT"]
    lon = result["LON"]

    if lat < -90 or lat > 90:
        raise ValueError(
            f"Latitude tidak valid : {lat}"
        )

    if lon < -180 or lon > 180:
        raise ValueError(
            f"Longitude tidak valid : {lon}"
        )

    return result


# ==========================================================
# PIPELINE INFERENSI
# ==========================================================

def run_inference(

    model,
    sequence,
    scaler_y=None

):

    raw_prediction = predict(
        model,
        sequence
    )

    prediction = inverse_target(
        raw_prediction,
        scaler_y
    )

    result = prediction_to_coordinate(
        prediction
    )

    result = validate_coordinate(
        result
    )

    return result