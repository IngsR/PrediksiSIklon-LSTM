# predictor/loader.py

from pathlib import Path
import tensorflow as tf
import joblib


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"

SCALER_DIR = BASE_DIR / "normalized_dataset"


MODEL_PATHS = {

    "gab": MODEL_DIR / "gab_window8.keras",

    "ni": MODEL_DIR / "ni_window8.keras",

    "si": MODEL_DIR / "si_window8.keras"

}


FEATURE_SCALER = {

    "gab": SCALER_DIR / "feature_scaler_gab.pkl",

    "ni": SCALER_DIR / "feature_scaler_ni.pkl",

    "si": SCALER_DIR / "feature_scaler_si.pkl"

}


TARGET_SCALER = {

    "gab": SCALER_DIR / "target_scaler_gab.pkl",

    "ni": SCALER_DIR / "target_scaler_ni.pkl",

    "si": SCALER_DIR / "target_scaler_si.pkl"

}


_cache = {}


def load_pipeline(dataset="gab"):

    dataset = dataset.lower()

    if dataset in _cache:

        return _cache[dataset]

    model = tf.keras.models.load_model(

        MODEL_PATHS[dataset],

        compile=False

    )

    feature_scaler = joblib.load(

        FEATURE_SCALER[dataset]

    )

    target_scaler = joblib.load(

        TARGET_SCALER[dataset]

    )

    pipeline = {

        "model": model,

        "feature_scaler": feature_scaler,

        "target_scaler": target_scaler

    }

    _cache[dataset] = pipeline

    return pipeline