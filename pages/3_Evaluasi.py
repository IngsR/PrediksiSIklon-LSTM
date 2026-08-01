import streamlit as st
import numpy as np
import pandas as pd
import utils

# =====================================================
###### 1. KONFIGURASI HALAMAN ######
# =====================================================
st.set_page_config(page_title="Evaluasi Akurasi", page_icon="📈", layout="wide")
utils.inject_custom_css()
utils.render_sidebar_brand()

st.markdown("### 📈 EVALUASI AKURASI PER KASUS SIKLON")

# =====================================================
###### 2. LOAD DATA PREDIKSI ######
# =====================================================
try:
    pred_df = utils.load_prediction_data()
except Exception as e:
    st.error(f"Gagal memuat prediksi: {e}")
    st.stop()

if pred_df.empty:
    st.warning("Data prediksi kosong.")
    st.stop()

all_sids = sorted(pred_df["SID"].unique().tolist())

# =====================================================
###### 3. INISIALISASI SESSION STATE & NAVIGASI ######
# =====================================================
if "selected_sid_eval" not in st.session_state:
    st.session_state.selected_sid_eval = all_sids[0] if all_sids else None

# =====================================================
###### 4. FITUR PENCARIAN & DROPDOWN – FIX SYNC BUG ######
# =====================================================
try:
    from streamlit_searchbox import st_searchbox
except ImportError:
    st.error("Package 'streamlit-searchbox' belum terinstall.")
    st.stop()

def search_sid_eval(searchterm: str) -> list[str]:
    if not searchterm:
        return []
    term = searchterm.upper()
    return [sid for sid in all_sids if term in sid.upper()]

col_search, col_drop = st.columns([1, 1], gap="medium")

with col_search:
    st.markdown("🔍 **Cari ID Siklon**")
    # Gunakan key dinamis berbasis state untuk memaksa update widget jika state berubah dari widget lain
    search_value = st_searchbox(
        search_sid_eval,
        placeholder="Ketik ID Siklon...",
        key=f"searchbox_eval_{st.session_state.selected_sid_eval}",
        clear_on_submit=False,
        default=st.session_state.selected_sid_eval,
    )
    if search_value and search_value != st.session_state.selected_sid_eval:
        st.session_state.selected_sid_eval = search_value
        st.rerun()

with col_drop:
    st.markdown("📂 **Atau Pilih dari Daftar**")
    try:
        default_idx = all_sids.index(st.session_state.selected_sid_eval)
    except ValueError:
        default_idx = 0

    selected_sid_dropdown = st.selectbox(
        "Pilih ID Siklon",
        options=all_sids,
        index=default_idx,
        key="selectbox_eval",
        label_visibility="collapsed"
    )
    if selected_sid_dropdown != st.session_state.selected_sid_eval:
        st.session_state.selected_sid_eval = selected_sid_dropdown
        st.rerun()

final_sid = st.session_state.selected_sid_eval

# =====================================================
###### 5. TAMPILKAN KONTEN EVALUASI ######
# =====================================================
if final_sid is None:
    st.info("Silakan pilih ID siklon untuk melihat hasil evaluasi.")
else:
    sid_data = pred_df[pred_df["SID"] == final_sid].copy().sort_values("ISO_TIME").reset_index(drop=True)

    if sid_data.empty:
        st.warning(f"Data tidak ditemukan untuk SID `{final_sid}`.")
    else:
        # ---------- 5a. Informasi Ringkas Siklon ----------
        with st.container(border=True):
            ci1, ci2 = st.columns(2)
            with ci1:
                name_val = sid_data["NAME"].iloc[0] if "NAME" in sid_data.columns else "UNNAMED"
                st.markdown(f"""
                **🆔 ID Siklon** : `{final_sid}`
                **🏷️ Nama** : `{name_val}`
                **⏱️ Interval** : `3 Jam`
                """)
            with ci2:
                periode_mulai  = sid_data["ISO_TIME"].min().strftime("%d/%m/%Y")
                periode_selesai = sid_data["ISO_TIME"].max().strftime("%d/%m/%Y")
                durasi_jam = (sid_data["ISO_TIME"].max() - sid_data["ISO_TIME"].min()).total_seconds() / 3600
                st.markdown(f"""
                **📅 Periode** : `{periode_mulai} – {periode_selesai}`
                **⏳ Durasi** : `{int(durasi_jam)} jam`
                **📌 Jumlah titik** : `{len(sid_data)}`
                """)

        # ---------- 5b. Metrik Akurasi ----------
        rmse_km = float(np.sqrt(np.mean(sid_data["ERROR_KM"] ** 2)))
        mae_km  = float(sid_data["ERROR_KM"].mean())
        max_km  = float(sid_data["ERROR_KM"].max())
        min_km  = float(sid_data["ERROR_KM"].min())

        # Deskripsi Metrik
        st.markdown(f"""
        <div class="info-card">
            <h4>📊 Penjelasan Metrik Evaluasi</h4>
            <p>Berikut adalah parameter yang digunakan untuk mengukur keakuratan model dalam memprediksi koordinat siklon (selisih jarak dalam <b>Kilometer</b>):</p>
            <ul style="margin-bottom: 0;">
                <li><b>MAE (Mean Absolute Error):</b> Rata-rata kesalahan absolut. Menunjukkan seberapa besar penyimpangan rata-rata prediksi model dari posisi sebenarnya.</li>
                <li><b>RMSE (Root Mean Square Error):</b> Akar rata-rata kuadrat kesalahan. Metrik ini memberikan bobot lebih besar pada kesalahan yang signifikan, sehingga semakin kecil nilainya, semakin stabil model tersebut.</li>
                <li><b>Min Error:</b> Jarak penyimpangan terkecil yang tercatat (titik koordinat dengan prediksi paling akurat).</li>
                <li><b>Max Error:</b> Jarak penyimpangan terbesar yang tercatat (titik koordinat dengan prediksi paling meleset).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Kategori Kualitas Prediksi
        if mae_km < 15.0:
            qual_label, qual_color = "ERROR SANGAT RENDAH", "#059669"   # Hijau
        elif mae_km < 30.0:
            qual_label, qual_color = "ERROR RENDAH", "#1E3A8A"          # Biru
        elif mae_km < 60.0:
            qual_label, qual_color = "ERROR SEDANG", "#D97706"          # Oranye
        else:
            qual_label, qual_color = "ERROR TINGGI", "#DC2626"          # Merah

        mc1, mc2, mc3, mc4 = st.columns(4)
        for col_ui, label, value, color in [
            (mc1, "MAE (km)",  mae_km,  "#1E3A8A"),
            (mc2, "RMSE (km)", rmse_km, "#1E3A8A"),
            (mc3, "Min Error (km)", min_km, "#059669"),
            (mc4, "Max Error (km)", max_km, "#DC2626"),
        ]:
            col_ui.markdown(f"""
            <div class="metric-card" style="padding: 16px 10px;">
                <div class="metric-label" style="font-size: 15px;">{label}</div>
                <div class="metric-value" style="color:{color}; font-size: 40px;">{value:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background-color: #F3F4F6; border: 2.5px solid {qual_color}; border-radius: 10px; padding: 12px 20px; margin-top: 15px; text-align: center;">
            <span style="font-size: 14px; font-weight: bold; color: #4B5563; text-transform: uppercase;">Predikat Akurasi:</span>
            <span style="font-size: 18px; font-weight: 900; color: {qual_color}; margin-left: 10px;">{qual_label}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ---------- 5c. Grafik Analisis Berdampingan ----------
        col_chart1, col_chart2 = st.columns([1.1, 0.9])
        with col_chart1:
            st.markdown("##### 📉 Grafik Deviasi Jarak Per Waktu (Km)")
            chart_data = sid_data[["ISO_TIME", "ERROR_KM"]].copy()
            chart_data["Waktu"] = chart_data["ISO_TIME"].dt.strftime("%d/%m %H:%M")
            chart_data = chart_data.set_index("Waktu")[["ERROR_KM"]]
            chart_data.columns = ["Deviasi (km)"]
            st.line_chart(chart_data, color="#1E3A8A", use_container_width=True, height=280)

        with col_chart2:
            st.markdown("##### 📊 Distribusi Frekuensi Error")
            bins = [0, 10, 25, 50, float('inf')]
            labels = ["0-10km", "10-25km", "25-50km", ">50km"]
            sid_data["Error_Range"] = pd.cut(sid_data["ERROR_KM"], bins=bins, labels=labels, right=False)
            freq_pct = (sid_data["Error_Range"].value_counts().reindex(labels).fillna(0) / len(sid_data)) * 100
            st.bar_chart(pd.DataFrame({"Persentase (%)": freq_pct}), color="#059669", use_container_width=True, height=280)

        st.markdown("---")

        # ---------- 5d. Grafik Dekomposisi LAT vs LON ----------
        st.markdown("##### 📐 Grafik Dekomposisi Deviasi Koordinat (Mutlak Latitude vs Longitude)")
        decomp_data = sid_data[["ISO_TIME", "LAT_ACTUAL", "LON_ACTUAL", "LAT_PRED", "LON_PRED"]].copy()
        decomp_data["Waktu"] = decomp_data["ISO_TIME"].dt.strftime("%d/%m %H:%M")
        decomp_data["Deviasi LAT (°)"] = np.abs(decomp_data["LAT_ACTUAL"] - decomp_data["LAT_PRED"])
        decomp_data["Deviasi LON (°)"] = np.abs(decomp_data["LON_ACTUAL"] - decomp_data["LON_PRED"])
        decomp_data = decomp_data.set_index("Waktu")[["Deviasi LAT (°)", "Deviasi LON (°)"]]
        st.line_chart(decomp_data, color=["#2563EB", "#D97706"], use_container_width=True, height=260)

        st.markdown("---")

        # ---------- 5e. Tabel & Download ----------
        col_t, col_d = st.columns([3, 1])
        with col_t: st.subheader("Tabel Perbandingan Koordinat")
        with col_d:
            csv = sid_data[["ISO_TIME", "LAT_ACTUAL", "LON_ACTUAL", "LAT_PRED", "LON_PRED", "ERROR_KM"]].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh CSV", csv, f"eval_{final_sid}.csv", "text/csv", use_container_width=True)

        tabel_eval = sid_data[["ISO_TIME", "LAT_ACTUAL", "LON_ACTUAL", "LAT_PRED", "LON_PRED", "ERROR_KM"]].copy()
        tabel_eval["ISO_TIME"] = tabel_eval["ISO_TIME"].dt.strftime("%d/%m/%Y %H:%M")
        for col in ["LAT_ACTUAL", "LON_ACTUAL", "LAT_PRED", "LON_PRED"]:
            tabel_eval[col] = tabel_eval[col].apply(lambda x: f"{x:.4f}°")
        tabel_eval["ERROR_KM"] = tabel_eval["ERROR_KM"].apply(lambda x: f"{x:.2f}")
        tabel_eval.columns = ["Waktu", "LAT Aktual (°)", "LON Aktual (°)", "LAT Pred (°)", "LON Pred (°)", "Error (km)"]
        utils.render_custom_table(tabel_eval)

        # ---------- 5f. Narasi ----------
        st.markdown("""
        <div class="narrative-box">
            <h4>[ Ringkasan Evaluasi Spasial ]</h4>
            Halaman ini menampilkan tingkat akurasi model LSTM dengan membandingkan posisi aktual (data IBTrACS)
            dan posisi hasil prediksi pada setiap titik waktu. Statistik MAE dan RMSE memberikan gambaran kesalahan
            rata-rata dalam kilometer. Grafik dekomposisi membantu mengidentifikasi apakah model memiliki bias
            khusus pada sumbu Lintang (Utara-Selatan) atau Bujur (Barat-Timur).
        </div>
        """, unsafe_allow_html=True)

# =====================================================
###### 6. FOOTER ######
# =====================================================
utils.render_footer()
