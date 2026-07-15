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

st.markdown("### EVALUASI AKURASI PREDIKSI")

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
###### 3. INISIALISASI SESSION STATE ######
# =====================================================
if "selected_sid_eval" not in st.session_state:
    st.session_state.selected_sid_eval = None

# =====================================================
###### 4. PENCARIAN & DROPDOWN – 1 BARIS (2 KOLOM) ######
# =====================================================
try:
    from streamlit_searchbox import st_searchbox
except ImportError:
    st.error("Package 'streamlit-searchbox' belum terinstall. Jalankan: pip install streamlit-searchbox")
    st.stop()

def search_sid_eval(searchterm: str) -> list[str]:
    if not searchterm:
        return []
    term = searchterm.upper()
    return [sid for sid in all_sids if term in sid.upper()]

col_search, col_drop = st.columns([1, 1], gap="small")

with col_search:
    search_value = st_searchbox(
        search_sid_eval,
        placeholder="🔍  Ketik ID Siklon (misal: 1992311...)",
        key="searchbox_eval",
        clear_on_submit=False,
        default=st.session_state.selected_sid_eval,
        label="Cari ID Siklon",
    )

with col_drop:
    default_index = 0
    if st.session_state.selected_sid_eval is not None and st.session_state.selected_sid_eval in all_sids:
        default_index = all_sids.index(st.session_state.selected_sid_eval)
    selected_sid_dropdown = st.selectbox(
        "Atau pilih dari daftar:",
        options=all_sids,
        index=default_index,
        key="selectbox_eval",
    )

# Sinkronisasi session state
if search_value is not None and search_value != st.session_state.selected_sid_eval:
    st.session_state.selected_sid_eval = search_value
    st.rerun()

if selected_sid_dropdown != st.session_state.selected_sid_eval:
    st.session_state.selected_sid_eval = selected_sid_dropdown
    st.rerun()

final_sid = st.session_state.selected_sid_eval

# =====================================================
###### 5. TAMPILKAN EVALUASI JIKA SID SUDAH DIPILIH ######
# =====================================================
if final_sid is None:
    st.info("Silakan pilih ID siklon melalui pencarian atau dropdown di atas.")
else:
    sid_data = pred_df[pred_df["SID"] == final_sid].copy().sort_values("ISO_TIME").reset_index(drop=True)

    if sid_data.empty:
        st.warning(f"Tidak ada data prediksi untuk SID `{final_sid}`.")
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

        mc1, mc2, mc3, mc4 = st.columns(4)
        for col_ui, label, value, color in [
            (mc1, "MAE (km)",  mae_km,  "#1E3A8A"),
            (mc2, "RMSE (km)", rmse_km, "#1E3A8A"),
            (mc3, "Min Error (km)", min_km, "#059669"),
            (mc4, "Max Error (km)", max_km, "#DC2626"),
        ]:
            col_ui.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{color};">{value:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ---------- 5c. Grafik Deviasi ----------
        st.markdown("""
        <div style="text-align:center; margin: 10px 0 6px 0; font-size:19px; font-weight:900;
                    color:#1E3A8A; letter-spacing:0.08em; text-transform:uppercase;
                    border-top:3px solid #1E3A8A; border-bottom:3px solid #1E3A8A;
                    padding:10px 0;">
            📉 GRAFIK DEVIASI PREDIKSI (km)
        </div>
        """, unsafe_allow_html=True)

        # Siapkan data grafik
        chart_data = sid_data[["ISO_TIME", "ERROR_KM"]].copy()
        chart_data["Waktu"] = chart_data["ISO_TIME"].dt.strftime("%d/%m %H:%M")
        chart_data = chart_data.set_index("Waktu")[["ERROR_KM"]]
        chart_data.columns = ["Deviasi (km)"]

        # Garis rata-rata
        mean_err = chart_data["Deviasi (km)"].mean()
        chart_data["Rata-rata (km)"] = mean_err

        st.markdown(f"""
        <div style="display:flex; gap:30px; align-items:center; margin:8px 0 4px 0;
                    font-size:15px; font-weight:700;">
            <span style="color:#1E3A8A;">■ Deviasi per-titik</span>
            <span style="color:#DC2626;">■ Rata-rata: {mean_err:.2f} km</span>
            <span style="color:#059669;">Min: {min_km:.2f} km</span>
            <span style="color:#92400E;">Max: {max_km:.2f} km</span>
        </div>
        """, unsafe_allow_html=True)

        st.line_chart(
            chart_data,
            color=["#1E3A8A", "#DC2626"],
            use_container_width=True,
            height=340,
        )

        st.markdown("---")

        # ---------- 5d. Tabel Perbandingan Koordinat ----------
        st.subheader("Tabel Perbandingan Koordinat")
        tabel_eval = sid_data[["ISO_TIME", "LAT_ACTUAL", "LON_ACTUAL", "LAT_PRED", "LON_PRED", "ERROR_KM"]].copy()
        tabel_eval["ISO_TIME"] = tabel_eval["ISO_TIME"].dt.strftime("%d/%m/%Y %H:%M")
        for col in ["LAT_ACTUAL", "LON_ACTUAL", "LAT_PRED", "LON_PRED"]:
            tabel_eval[col] = tabel_eval[col].apply(lambda x: f"{x:.4f}°")
        tabel_eval["ERROR_KM"] = tabel_eval["ERROR_KM"].apply(lambda x: f"{x:.2f}")
        tabel_eval.columns = ["Waktu", "LAT Aktual (°)", "LON Aktual (°)", "LAT Pred (°)", "LON Pred (°)", "Error (km)"]
        utils.render_custom_table(tabel_eval)

        # ---------- 5e. Narasi Evaluasi ----------
        st.markdown("""
        <div class="narrative-box">
            <h4>[ Ringkasan Evaluasi ]</h4>
            Halaman ini menampilkan tingkat akurasi model LSTM dengan membandingkan posisi aktual (data IBTrACS)
            dan posisi hasil prediksi pada setiap titik waktu. Tabel di atas menunjukkan selisih koordinat secara
            detail berikut besar error dalam kilometer per titik. Grafik deviasi menggambarkan fluktuasi kesalahan
            posisi sepanjang jalur pergerakan siklon, disertai garis rata-rata sebagai acuan performa keseluruhan.
        </div>
        """, unsafe_allow_html=True)

# =====================================================
###### 6. FOOTER ######
# =====================================================
utils.render_footer()