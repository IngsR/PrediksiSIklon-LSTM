import streamlit as st
import utils
import os
import pandas as pd

st.set_page_config(page_title="Tentang Model", page_icon="ℹ️", layout="wide")
utils.inject_custom_css()
utils.render_sidebar_brand()

st.markdown("### ℹ️ TENTANG PENELITIAN & EVALUASI MODEL")

# =====================================================
###### KATA PENGANTAR / PENDAHULUAN ######
# =====================================================
st.markdown("""
<div class="narrative-box" style="margin-bottom: 25px;">
    <h4>👋 Pengantar Penelitian & Sistem Prediksi</h4>
    <p>
        Selamat datang di halaman <strong>Tentang</strong>. Purwarupa aplikasi ini merupakan implementasi hasil penelitian mengenai
        <strong>prediksi lintasan siklon tropis menggunakan arsitektur <em>Deep Learning Long Short-Term Memory</em> (LSTM)</strong>.
        Aplikasi ini menyediakan visualisasi hasil prediksi, data observasi, serta evaluasi kinerja model untuk mendukung analisis
        terhadap performa prediksi lintasan siklon tropis di <strong>Samudra Hindia</strong>.
    </p>
    <p>
        Siklon tropis memiliki karakteristik pergerakan temporal dan spasial yang sangat dinamis. Untuk menangkap karakteristik pergerakannya secara akurat, penelitian ini memanfaatkan
        data historis lintasan siklon dari dataset internasional <strong>IBTrACS (1980–2025)</strong>. Model dilatih menggunakan variasi parameter untuk
        menemukan konfigurasi terbaik dalam memprediksi koordinat lintasan (Latitude dan Longitude) pada langkah waktu berikutnya.
    </p>
</div>
""", unsafe_allow_html=True)

# =====================================================
###### PERBANDINGAN SELURUH MODEL (GRAFIK KOMPARATIF) ######
# =====================================================
st.markdown("#### 📊 Perbandingan Kinerja Haversine Seluruh Model")
try:
    df_hav_rank = utils.load_model_ranking_haversine()
    if not df_hav_rank.empty:
        comp_df = df_hav_rank.copy()
        comp_df["Model"] = comp_df["Scenario"] + "-" + comp_df["Window"].astype(str)

        # Konversi Window ke numerik agar urutan 8 < 16 < 24 < 32 benar
        comp_df["Window"] = pd.to_numeric(comp_df["Window"])
        comp_df["Scenario"] = pd.Categorical(comp_df["Scenario"], categories=["GAB", "NI", "SI"], ordered=True)

        # Urutkan berdasarkan kategori Scenario dan nilai numerik Window
        comp_df = comp_df.sort_values(by=["Scenario", "Window"])

        st.bar_chart(comp_df.set_index("Model")[["Mean Haversine (km)"]], color="#1E3A8A", use_container_width=True, height=300)
        st.caption("Mean Haversine Distance (km) - Semakin rendah menunjukkan akurasi spasial yang lebih baik pada data uji.")
except Exception as e:
    st.error(f"Gagal memuat grafik komparatif: {e}")

# =====================================================
###### TABEL RANKING LENGKAP (HAVERSINE) ######
# =====================================================
try:
    df_hav = utils.load_model_ranking_haversine()
    st.markdown("#### 🏅 Ranking Seluruh Model – Berdasarkan Mean Haversine Distance")

    df_hav_disp = df_hav.copy()
    for col in ["MAE LAT", "MAE LON", "RMSE LAT", "RMSE LON", "MAE", "RMSE"]:
        if col in df_hav_disp.columns:
            df_hav_disp[col] = df_hav_disp[col].map(lambda x: f"{x:.4f}" if pd.notna(x) else "-")
    for col in ["Mean Haversine (km)", "Min Haversine (km)", "Max Haversine (km)"]:
        if col in df_hav_disp.columns:
            df_hav_disp[col] = df_hav_disp[col].map(lambda x: f"{x:.3f}" if pd.notna(x) else "-")

    if "Scenario" in df_hav_disp.columns and "Window" in df_hav_disp.columns:
        df_hav_disp.insert(1, "Model", df_hav_disp["Scenario"].astype(str) + "-" + df_hav_disp["Window"].astype(str))

    utils.render_custom_table(df_hav_disp)
except Exception as e:
    st.error(f"Gagal memuat ranking haversine: {e}")

# =====================================================
###### TABEL R² KINERJA MODEL ######
# =====================================================
try:
    df_ranking = utils.load_model_ranking()
    st.markdown("#### 📈 Kinerja Model Berdasarkan R² Score")
    df_ranking_disp = df_ranking.copy()
    for col in ["R² Latitude", "R² Longitude", "R² Mean"]:
        if col in df_ranking_disp.columns:
            df_ranking_disp[col] = df_ranking_disp[col].map(lambda x: f"{x:.6f}" if pd.notna(x) else "-")
    utils.render_custom_table(df_ranking_disp)
except Exception as e:
    st.error(f"Gagal memuat R2 score: {e}")

# =====================================================
###### ANALISIS OVERFITTING & EFISIENSI ######
# =====================================================
st.markdown("#### ⚖️ Analisis Overfitting & Efisiensi Komputasi")

try:
    df_overfit = utils.load_overfitting_summary()
    st.markdown("**🔍 Ringkasan Evaluasi Overfitting (Gap Train vs Val Loss)**")
    df_overfit_disp = df_overfit.copy()
    for col in ["Train Loss", "Validation Loss", "Gap"]:
        if col in df_overfit_disp.columns:
            df_overfit_disp[col] = df_overfit_disp[col].map(lambda x: f"{x:.5f}" if pd.notna(x) else "-")
    if "Gap (%)" in df_overfit_disp.columns:
        df_overfit_disp["Gap (%)"] = df_overfit_disp["Gap (%)"].map(lambda x: f"{x:.2f}%")
    utils.render_custom_table(df_overfit_disp)
except Exception as e:
    st.error(e)

st.markdown("<br>", unsafe_allow_html=True)

try:
    df_inf = utils.load_prediction_summary()
    st.markdown("**⏱️ Kecepatan Inferensi Model (Detik)**")
    df_inf["Model"] = df_inf["Scenario"] + "-" + df_inf["Window"].astype(str)

    # Konversi Window ke numerik agar urutan 8 < 16 < 24 < 32 benar
    df_inf["Window"] = pd.to_numeric(df_inf["Window"])
    df_inf["Scenario"] = pd.Categorical(df_inf["Scenario"], categories=["GAB", "NI", "SI"], ordered=True)

    # Urutkan berdasarkan kategori Scenario dan nilai numerik Window
    df_inf = df_inf.sort_values(by=["Scenario", "Window"])

    st.bar_chart(
        df_inf.set_index("Model")[["Prediction Time (Second)"]],
        color="#1E3A8A",
        use_container_width=True,
        height=320
    )
    st.caption("Waktu inferensi (detik) diukur berdasarkan pemrosesan seluruh data pengujian untuk masing-masing konfigurasi model.")
except Exception as e:
    st.error(e)

# =====================================================
###### DETAIL PELATIHAN (TRAINING SUMMARY) ######
# =====================================================
try:
    df_train = utils.load_training_summary()
    st.markdown("#### ⏱️ Detail Statistik Pelatihan Model")
    df_train_disp = df_train.copy()
    cols_show = ["Scenario", "Window", "Train Samples", "Validation Samples", "Epoch", "Best Train Loss", "Best Validation Loss", "Training Time (Second)"]
    df_train_disp = df_train_disp[[c for c in cols_show if c in df_train_disp.columns]]

    if "Training Time (Second)" in df_train_disp.columns:
        df_train_disp["Waktu Training (s)"] = df_train_disp["Training Time (Second)"].map(lambda x: f"{x:.1f}")
        df_train_disp = df_train_disp.drop(columns=["Training Time (Second)"])

    utils.render_custom_table(df_train_disp)
except Exception as e:
    st.error(e)

# =====================================================
###### PEMILIHAN MODEL OPERASIONAL (GAB-8) ######
# =====================================================
st.markdown("### 📌 Pemilihan Model Operasional")
st.info("Berdasarkan seluruh metrik evaluasi di atas, model **GAB Window 8** dipilih sebagai model operasional terbaik. Model ini mencakup dinamika iklim dari kedua belahan samudra (North Indian + South Indian) dengan kestabilan overfitting yang sangat baik (Gap 7.07%) dan akurasi spasial yang tangguh (Mean Haversine 14.923 km).")

# =====================================================
###### VISUALISASI TRAJECTORY MODEL TERBAIK (GAB-8) ######
# =====================================================
st.markdown("#### 🗺️ Visualisasi Trajectory Model Terbaik (GAB Window 8)")
trajectory_imgs = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", f"trajectory_best_model{i}.png") for i in range(1, 5)]

ci1, ci2 = st.columns(2)
with ci1:
    if os.path.exists(trajectory_imgs[0]): st.image(trajectory_imgs[0], caption="Trajectory Contoh 1 (Excellent Accuracy)", use_container_width=True)
with ci2:
    if os.path.exists(trajectory_imgs[1]): st.image(trajectory_imgs[1], caption="Trajectory Contoh 2 (High Precision)", use_container_width=True)

ci3, ci4 = st.columns(2)
with ci3:
    if os.path.exists(trajectory_imgs[2]): st.image(trajectory_imgs[2], caption="Trajectory Contoh 3 (Good Fit)", use_container_width=True)
with ci4:
    if os.path.exists(trajectory_imgs[3]): st.image(trajectory_imgs[3], caption="Trajectory Contoh 4 (Consistent)", use_container_width=True)

utils.render_footer()
