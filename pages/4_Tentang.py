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
        Selamat datang di halaman <strong>Evaluasi & Metrik Kinerja Model</strong>. Purwarupa sistem ini merupakan hasil penelitian yang berfokus pada 
        <strong>prediksi lintasan siklon tropis menggunakan arsitektur Deep Learning <em>Long Short-Term Memory</em> (LSTM)</strong>. 
        Penelitian ini dirancang khusus untuk meningkatkan sistem peringatan dini (<em>early warning system</em>) dan mitigasi risiko bencana 
        hidrometeorologi di wilayah <strong>Sumatera Barat</strong>.
    </p>
    <p>
        Siklon tropis memiliki karakteristik pergerakan temporal dan spasial yang sangat dinamis. Untuk menangkap karakteristik pergerakannya secara akurat, penelitian ini memanfaatkan 
        data historis lintasan siklon dari dataset internasional <strong>IBTrACS (1980–2025)</strong>. Model dilatih menggunakan variasi parameter untuk 
        menemukan konfigurasi terbaik dalam memprediksi koordinat lintasan (Latitude dan Longitude) pada langkah waktu berikutnya.
    </p>
    <h5>🧭 Bagaimana Memahami Halaman Ini?</h5>
    <p>
        Untuk membantu Anda menganalisis performa sistem secara menyeluruh, halaman ini menyajikan hasil evaluasi model yang disusun secara terstruktur:
    </p>
    <ol style="margin-left: 20px; padding-left: 0;">
        <li><strong>Skenario Wilayah (Samudra):</strong> Model dilatih pada tiga skenario cakupan wilayah, yaitu:
            <ul>
                <li><em>North Indian (NI):</em> Siklon di Samudra Hindia bagian Utara.</li>
                <li><em>South Indian (SI):</em> Siklon di Samudra Hindia bagian Selatan.</li>
                <li><em>Gabungan (GAB):</em> Dataset komprehensif yang menyatukan kedua wilayah (NI + SI). Skenario ini sangat krusial karena Sumatera Barat secara geografis berada dekat dengan khatulistiwa dan dipengaruhi oleh pola cuaca dari kedua belahan samudra tersebut.</li>
            </ul>
        </li>
        <li><strong>Ukuran Window (Sliding Window):</strong> Variasi <em>Window Size</em> (8, 16, 24, dan 32 timestep) merepresentasikan durasi historis (dalam kelipatan 3 jam) yang digunakan model sebagai referensi untuk memproyeksikan lintasan ke depan.</li>
        <li><strong>Metrik Evaluasi Utama:</strong>
            <ul>
                <li><strong>Mean Haversine Distance (km):</strong> Metrik jarak fisik sesungguhnya yang menghitung jarak melingkar bumi (dalam kilometer) antara koordinat prediksi dan koordinat observasi riil. Semakin kecil nilai Haversine, semakin presisi posisi prediksi model.</li>
                <li><strong>MAE & RMSE (Latitude/Longitude):</strong> Mengukur kesalahan rata-rata absolut dan deviasi kuadrat koordinat derajat secara terpisah.</li>
                <li><strong>R² Score (Koefisien Determinasi):</strong> Mengukur seberapa baik model dapat menjelaskan variansi data lintasan (nilai mendekati 1.0 menunjukkan kecocokan sangat tinggi).</li>
            </ul>
        </li>
    </ol>
    <p style="font-style: italic; margin-top: 15px; color: #4B5563;">
        Silakan pelajari grafik komparatif, tabel pemeringkatan kinerja, analisis overfitting, serta efisiensi komputasi di bawah ini untuk melihat bagaimana model operasional final dipilih berdasarkan pembuktian ilmiah.
    </p>
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
###### PROFIL EFISIENSI KOMPUTASI & KECEPATAN INFERENSI ######
# =====================================================
try:
    df_pred_summary = utils.load_prediction_summary()
    st.markdown("#### ⏱️ Profil Efisiensi Komputasi dan Kecepatan Inferensi Model")
    
    df_pred_disp = df_pred_summary.copy()
    
    # Format float prediction time to 4 decimals for precision
    if "Prediction Time (Second)" in df_pred_disp.columns:
        df_pred_disp["Prediction Time (Second)"] = df_pred_disp["Prediction Time (Second)"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "-")
        
    utils.render_custom_table(df_pred_disp)
    
    st.markdown("""
    <p style="font-size: 16px; margin-top: 10px; color: #4B5563; font-style: italic; line-height: 1.6;">
        <strong>Keterangan:</strong> Tabel di atas menyajikan profil kompleksitas data uji (<em>Test Samples</em>), dimensi luaran koordinat prediksi (<em>Prediction Shape</em>), dan efisiensi waktu komputasi yang dibutuhkan untuk proses inferensi (<em>Prediction Time</em>). Secara ilmiah, terdapat korelasi linier positif antara ukuran sampel uji dengan waktu inferensi. Skenario <strong>Gabungan (GAB-8)</strong> memproses data uji terbesar (11.564 sampel) hanya dalam waktu <strong>0,9730 detik</strong>, menunjukkan bahwa arsitektur Stacked LSTM yang dirancang sangat efisien untuk diimplementasikan secara real-time pada sistem operasional peringatan dini kebencanaan di Sumatera Barat tanpa terkendala masalah latensi komputasi.
    </p>
    """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Gagal memuat prediction_summary.csv: {e}")

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

# Default values for GAB-8 (consistent with model_ranking_arversine.csv)
gab8_mae = "0.0877"
gab8_rmse = "0.1247"
gab8_haversine = "14.923"
gab8_max_error = "280.349"
gab8_samples = "11.564"

# Dynamically extract GAB-8 values from loaded data for absolute precision
if not df_hav.empty:
    row_gab8 = df_hav[(df_hav["Scenario"] == "GAB") & (df_hav["Window"] == 8)]
    if not row_gab8.empty:
        try:
            gab8_mae = f"{row_gab8.iloc[0]['MAE']:.4f}"
            gab8_rmse = f"{row_gab8.iloc[0]['RMSE']:.4f}"
            gab8_haversine = f"{row_gab8.iloc[0]['Mean Haversine (km)']:.3f}"
            gab8_max_error = f"{row_gab8.iloc[0]['Max Haversine (km)']:.3f}"
            gab8_samples = f"{row_gab8.iloc[0]['Samples']:,}".replace(",", ".")
        except Exception:
            pass

# Info cards
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="info-card">
        <h4>🏆 Model Terpilih – GAB Window 8</h4>
        <p>
        MAE: <strong>{gab8_mae}</strong> &nbsp;|&nbsp; RMSE: <strong>{gab8_rmse}</strong><br>
        Mean Haversine: <strong>{gab8_haversine} km</strong><br>
        Max Error: <strong>{gab8_max_error} km</strong> (paling terkendali di antara skenario GAB)<br>
        Sampel pengujian: <strong>{gab8_samples}</strong> (paling representatif)
        </p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="info-card" style="border-left-color: #059669;">
        <h4>✅ Rasionalisasi Pemilihan GAB-8</h4>
        <p>
        Skenario GAB mencakup data gabungan dari <strong>seluruh wilayah</strong> (NI + SI). Hal ini memberikan pemahaman spasial yang menyeluruh dan sangat relevan bagi daerah regional Sumatera Barat.<br><br>
        Di antara skenario GAB, <strong>Window 8</strong> terbukti unggul mutlak pada seluruh metrik evaluasi: nilai MAE, RMSE, dan Mean Haversine terendah, serta Max Error terkecil.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.info("**📊 Kesimpulan Final:** Model **GAB Window 8** dipilih sebagai model operasional terbaik untuk diimplementasikan ke dalam sistem prediksi ini. Meskipun model dari skenario belahan bumi selatan (**SI-16** di peringkat 1 dengan **14.031 km** dan **SI-8** di peringkat 2 dengan **14.399 km**) memiliki nilai *Mean Haversine* sedikit lebih kecil secara numerik, cakupan latihnya terbatas hanya pada Samudra Hindia Selatan. Sebaliknya, skenario **GAB (Gabungan)** mencakup dinamika iklim dari kedua belahan samudra (**North Indian + South Indian**), menjadikannya model yang jauh lebih representatif, tangguh (robust), dan berdaya guna tinggi (generalizable) untuk mitigasi bencana siklon tropis yang dapat memengaruhi Sumatera Barat dari belahan bumi utara maupun selatan.")

# =====================================================
###### KONTRIBUSI & ARSITEKTUR ######
# =====================================================
col3, col4 = st.columns(2)
with col3:
    st.markdown("""
    <div class="info-card">
        <h4>🎯 Kontribusi Sistem</h4>
        Purwarupa ini diharapkan dapat berkontribusi membantu instansi penanggulangan bencana seperti BMKG dan BPBD dalam memantau serta memproyeksikan pergerakan siklon tropis secara objektif, presisi, dan real-time.
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="info-card">
        <h4>🔄 Arsitektur Model</h4>
        Stacked LSTM 2 Layers<br>
        Sliding Window 8 (24 jam histori aktivitas siklon)<br>
        Skenario Data: Gabungan NI + SI (GAB) untuk cakupan komprehensif
    </div>
    """, unsafe_allow_html=True)

# =====================================================
###### VISUALISASI TRAJECTORY MODEL TERBAIK (GAB-8) ######
# =====================================================
st.markdown("#### 🗺️ Visualisasi Trajectory Model Terbaik (GAB Window 8)")

trajectory_imgs = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", f"trajectory_best_model{i}.png")
    for i in range(1, 5)
]

# Tampilkan dalam grid 2x2
col_img1, col_img2 = st.columns(2)
with col_img1:
    if os.path.exists(trajectory_imgs[0]):
        st.image(trajectory_imgs[0], caption="Trajectory Contoh 1 (SID: 2008033S11083 - Mean Haversine: 12.93 km)", use_container_width=True)
    else:
        st.warning("Gambar trajectory 1 tidak ditemukan.")

with col_img2:
    if os.path.exists(trajectory_imgs[1]):
        st.image(trajectory_imgs[1], caption="Trajectory Contoh 2 (SID: 1994086S08092 - Mean Haversine: 12.49 km)", use_container_width=True)
    else:
        st.warning("Gambar trajectory 2 tidak ditemukan.")

col_img3, col_img4 = st.columns(2)
with col_img3:
    if os.path.exists(trajectory_imgs[2]):
        st.image(trajectory_imgs[2], caption="Trajectory Contoh 3 (SID: 1980056S15059 - Mean Haversine: 16.36 km)", use_container_width=True)
    else:
        st.warning("Gambar trajectory 3 tidak ditemukan.")

with col_img4:
    if os.path.exists(trajectory_imgs[3]):
        st.image(trajectory_imgs[3], caption="Trajectory Contoh 4 (SID: 2013305N07141 - Mean Haversine: 15.61 km)", use_container_width=True)
    else:
        st.warning("Gambar trajectory 4 tidak ditemukan.")

utils.render_footer()
