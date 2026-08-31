"""
Script konversi model Keras → ONNX + ekstrak scaler params ke JSON.
Jalankan SEKALI dari direktori streamlit_app/:
    python web/scripts/convert_model.py
"""

import sys
import os
import json
import numpy as np
import joblib
import tensorflow as tf

# Pastikan path benar relatif ke streamlit_app/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")          # streamlit_app/
MODEL_DIR = os.path.join(ROOT_DIR, "prediction", "models")
OUT_DIR   = os.path.join(BASE_DIR, "..", "public", "models")

os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 60)
print("KONVERSI MODEL: Keras -> ONNX")
print("=" * 60)

# ─────────────────────────────────────────────
# 1. Konversi .keras → .onnx via tf2onnx
# ─────────────────────────────────────────────
try:
    import tf2onnx
    import onnx
except ImportError:
    print("ERROR: Install tf2onnx & onnx dulu:")
    print("  pip install tf2onnx onnx")
    sys.exit(1)

keras_path = os.path.join(MODEL_DIR, "gab_window8.keras")
onnx_path  = os.path.join(OUT_DIR, "model.onnx")

print(f"\n[1/3] Load model dari: {keras_path}")
model = tf.keras.models.load_model(keras_path)

# Input shape: (batch, window_size=8, features=11)
input_signature = [tf.TensorSpec([1, 8, 11], tf.float32, name="input")]

print(f"[2/3] Konversi ke ONNX...")
@tf.function
def run_model(x):
    return model(x)

onnx_model, _ = tf2onnx.convert.from_function(
    run_model,
    input_signature=input_signature,
    opset=13,
    output_path=onnx_path
)
print(f"      Tersimpan: {onnx_path}")

# Tampilkan ukuran
size_kb = os.path.getsize(onnx_path) / 1024
print(f"      Ukuran ONNX: {size_kb:.1f} KB")

# ─────────────────────────────────────────────
# 2. Ekstrak feature_scaler params → JSON
# ─────────────────────────────────────────────
print(f"\n[3/3] Ekstrak scaler params...")

feat_scaler = joblib.load(os.path.join(MODEL_DIR, "feature_scaler_gab.pkl"))
tgt_scaler  = joblib.load(os.path.join(MODEL_DIR, "target_scaler_gab.pkl"))

def scaler_to_dict(scaler):
    return {
        "scaler_type": type(scaler).__name__,
        "feature_names": list(scaler.feature_names_in_) if hasattr(scaler, "feature_names_in_") else [],
        "mean_":         scaler.mean_.tolist() if hasattr(scaler, "mean_") else [],
        "scale_":        scaler.scale_.tolist() if hasattr(scaler, "scale_") else [],
        "var_":          scaler.var_.tolist() if hasattr(scaler, "var_") else [],
    }

feat_json_path = os.path.join(OUT_DIR, "feature_scaler.json")
tgt_json_path  = os.path.join(OUT_DIR, "target_scaler.json")

with open(feat_json_path, "w") as f:
    json.dump(scaler_to_dict(feat_scaler), f, indent=2)

with open(tgt_json_path, "w") as f:
    json.dump(scaler_to_dict(tgt_scaler), f, indent=2)

print(f"      feature_scaler.json -> {feat_json_path}")
print(f"      target_scaler.json  -> {tgt_json_path}")

print("\n" + "=" * 60)
print("KONVERSI SELESAI!")
print("File output:")
for fn in ["model.onnx", "feature_scaler.json", "target_scaler.json"]:
    fp = os.path.join(OUT_DIR, fn)
    size = os.path.getsize(fp) / 1024
    print(f"  {fn:30s} {size:8.1f} KB")
print("=" * 60)
