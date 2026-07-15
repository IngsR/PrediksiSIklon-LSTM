import streamlit as st
import utils
import os
import pandas as pd

st.set_page_config(page_title="Tentang Model", page_icon="ℹ️", layout="wide")
utils.inject_custom_css()
utils.render_sidebar_brand()

st.markdown("### TENTANG PENELITIAN & MODEL")

st.markdown("""
<div class="narrative-box" style="margin-top:0;">
    <h4>[ Ringkasan Penelitian ]</h4>
    Penelitian ini bertujuan mengembangkan sistem prediksi lintasan siklon tropis untuk mitigasi risiko bencana di wilayah Sumatera Barat menggunakan Long Short-Term Memory (LSTM). Model dilatih dan dievaluasi pada data IBTrACS (1980–2025) dengan skenario North Indian (NI), South Indian (SI), dan gabungan (GAB), serta variasi sliding window 8, 16, 24, dan 32 timestep.
</div>
""", unsafe_allow_html=True)

# =====================================================
###### PERBANDINGAN SELURUH MODEL (GRAFIK) ######
# =====================================================
PERBANDINGAN_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "perbandingan_model.png")

st.markdown("#### 📊 Perbandingan Mean Haversine Distance Seluruh Model")
if os.path.exists(PERBANDINGAN_IMG):
    st.image(PERBANDINGAN_IMG, caption="Perbandingan Mean Haversine Distance (km) seluruh skenario dan window size", use_container_width=True)
else:
    st.warning("Gambar perbandingan model tidak ditemukan.")

# =====================================================
###### TABEL RANKING LENGKAP (HAVERSINE) ######
# =====================================================
try:
    df_hav = utils.load_model_ranking_haversine()
    st.markdown("#### 🏅 Ranking Seluruh Model – Berdasarkan Mean Haversine Distance")

    df_hav_disp = df_hav.copy()

    # Format kolom float 4 desimal
    float_4d = ["MAE LAT", "MAE LON", "RMSE LAT", "RMSE LON", "MAE", "RMSE"]
    for col in float_4d:
        if col in df_hav_disp.columns:
            df_hav_disp[col] = df_hav_disp[col].map(lambda x: f"{x:.4f}" if pd.notna(x) else "-")

    # Format kolom Haversine 3 desimal
    float_hav = ["Mean Haversine (km)", "Min Haversine (km)", "Max Haversine (km)"]
    for col in float_hav:
        if col in df_hav_disp.columns:
            df_hav_disp[col] = df_hav_disp[col].map(lambda x: f"{x:.3f}" if pd.notna(x) else "-")

    # Buat label Model = Scenario-Window
    if "Scenario" in df_hav_disp.columns and "Window" in df_hav_disp.columns:
        df_hav_disp.insert(1, "Model", df_hav_disp["Scenario"].astype(str) + "-" + df_hav_disp["Window"].astype(str))

    utils.render_custom_table(df_hav_disp)

except Exception as e:
    st.error(f"Gagal memuat model_ranking_arversine.csv: {e}")
    df_hav = pd.DataFrame()

# =====================================================
###### TABEL R² KINERJA MODEL ######
# =====================================================
try:
    df_ranking = utils.load_model_ranking()
    st.markdown("#### Kinerja Model Berdasarkan R² Score")

    df_ranking_disp = df_ranking.copy()
    float_cols = ["R² Latitude", "R² Longitude", "R² Mean"]
    for col in float_cols:
        if col in df_ranking_disp.columns:
            df_ranking_disp[col] = df_ranking_disp[col].map(lambda x: f"{x:.6f}" if pd.notna(x) else "-")

    utils.render_custom_table(df_ranking_disp)
except Exception as e:
    st.error(f"Gagal memuat model_ranking.csv: {e}")
    df_ranking = pd.DataFrame()

# =====================================================
###### OVERFITTING SUMMARY ######
# =====================================================
try:
    df_overfit = utils.load_overfitting_summary()
    st.markdown("#### Ringkasan Evaluasi Overfitting")
    df_overfit_disp = df_overfit.copy()
    float_cols_4d = ["Train Loss", "Validation Loss", "Gap"]
    for col in float_cols_4d:
        if col in df_overfit_disp.columns:
            df_overfit_disp[col] = df_overfit_disp[col].map(lambda x: f"{x:.4f}" if pd.notna(x) else "-")
    utils.render_custom_table(df_overfit_disp)
except Exception as e:
    st.error(f"Gagal memuat overfitting_summary.csv: {e}")

# =====================================================
###### PEMILIHAN MODEL OPERASIONAL (GAB-8) ######
# =====================================================
st.markdown("### 📌 Pemilihan Model Operasional")

# Ambil data GAB dari ranking haversine untuk perbandingan
if not df_hav.empty and "Scenario" in df_hav.columns:
    df_gab = df_hav[df_hav["Scenario"] == "GAB"].copy().reset_index(drop=True)

    if not df_gab.empty:
        df_gab_disp = df_gab.copy()
        df_gab_disp.insert(0, "Model", "GAB-" + df_gab_disp["Window"].astype(str))

        # Tandai model terpilih
        df_gab_disp["Model"] = df_gab_disp["Model"].apply(
            lambda x: f"✅ {x} (Terpilih)" if x == "GAB-8" else x
        )

        for col in ["MAE LAT", "MAE LON", "RMSE LAT", "RMSE LON", "MAE", "RMSE"]:
            if col in df_gab_disp.columns:
                df_gab_disp[col] = df_gab_disp[col].map(lambda x: f"{x:.4f}" if pd.notna(x) else "-")
        for col in ["Mean Haversine (km)", "Min Haversine (km)", "Max Haversine (km)"]:
            if col in df_gab_disp.columns:
                df_gab_disp[col] = df_gab_disp[col].map(lambda x: f"{x:.3f}" if pd.notna(x) else "-")

        # Tampilkan kolom pilihan saja agar ringkas
        cols_show = [c for c in ["Model", "Rank", "Window", "Samples", "MAE", "RMSE",
                                  "Mean Haversine (km)", "Min Haversine (km)", "Max Haversine (km)"]
                     if c in df_gab_disp.columns]
        utils.render_custom_table(df_gab_disp[cols_show])

# Info cards
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="info-card">
        <h4>🏆 Model Terpilih – GAB Window 8</h4>
        <p>
        MAE: <strong>0.0886</strong> &nbsp;|&nbsp; RMSE: <strong>0.1230</strong><br>
        Mean Haversine: <strong>15.058 km</strong><br>
        Max Error: <strong>232.14 km</strong> (paling terkendali di antara GAB)<br>
        Sampel pelatihan: <strong>11.564</strong> (terbanyak)
        </p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="info-card" style="border-left-color: #059669;">
        <h4>✅ Rasionalisasi Pemilihan GAB-8</h4>
        <p>
        Model GAB mencakup <strong>seluruh wilayah</strong> (NI + SI) sehingga lebih relevan untuk prediksi regional Sumatera Barat.<br><br>
        Di antara skenario GAB, <strong>Window 8</strong> unggul pada seluruh metrik:
        MAE, RMSE, dan Mean Haversine terendah, serta Max Error paling stabil.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.info("**📊 Kesimpulan:** Model GAB Window 8 dipilih sebagai model operasional final. Meskipun SI-8 memiliki Haversine sedikit lebih kecil secara angka, skenario GAB mencakup kedua samudra (NI + SI) sehingga jauh lebih representatif dan generalisable untuk wilayah Sumatera Barat.")

# =====================================================
###### KONTRIBUSI & ARSITEKTUR ######
# =====================================================
col3, col4 = st.columns(2)
with col3:
    st.markdown("""
    <div class="info-card">
        <h4>🎯 Kontribusi Sistem</h4>
        Purwarupa ini diharapkan membantu BMKG dan BPBD dalam pemantauan pergerakan siklon tropis secara objektif, sehingga peringatan dini lebih presisi dan tepat sasaran.
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="info-card">
        <h4>🔄 Arsitektur Model</h4>
        Stacked LSTM 2 Layers<br>
        Sliding Window 8 (24 jam histori)<br>
        Skenario Data: Gabungan NI + SI (GAB)
    </div>
    """, unsafe_allow_html=True)

# Gambar trajectory model terbaik
if os.path.exists(utils.TRAJECTORY_IMG_PATH):
    st.image(utils.TRAJECTORY_IMG_PATH, caption="Visualisasi Trajectory Model Terbaik (GAB Window 8)", use_container_width=True)

utils.render_footer()