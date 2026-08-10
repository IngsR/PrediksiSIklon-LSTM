import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium
from folium.plugins import (
    AntPath,
    Fullscreen,
    MeasureControl,
    MiniMap,
)

from datetime import datetime, timedelta

import utils

from prediction.inference import (
    run_recursive_inference,
    load_resources,
    WINDOW_SIZE,
)
from prediction.analytics import calculate_analytics, format_lat_indo, format_lon_indo, get_reliability_metrics
from prediction.pdf_report import generate_pdf_report

# =====================================================
# SESSION STATE
# =====================================================

st.set_page_config(
    page_title="Prediksi Siklon",
    page_icon="🔮",
    layout="wide",
)

utils.inject_custom_css()
utils.render_sidebar_brand()

# Pre-load resources di latar belakang untuk mempercepat eksekusi pertama
load_resources()

# =====================================================
# HEADER
# =====================================================

st.markdown("### PREDIKSI LINTASAN SIKLON (LSTM)")

# =====================================================
# SESSION STATE
# =====================================================

def create_empty_dataframe():
    return pd.DataFrame(
        {
            "LAT": [0.0] * WINDOW_SIZE,
            "LON": [0.0] * WINDOW_SIZE,
            "WMO_WIND": [115.0] * WINDOW_SIZE,
            "WMO_PRES": [1005.0] * WINDOW_SIZE,
        }
    )

if "draft_data" not in st.session_state:
    st.session_state.draft_data = create_empty_dataframe()

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

# =====================================================
# FUNGSI RESET
# =====================================================

def clear_prediction():
    st.session_state.draft_data = create_empty_dataframe()
    st.session_state.prediction_result = None

# =====================================================
# LAYOUT
# =====================================================

left_col, right_col = st.columns([0.9, 1.3])

# =====================================================
# INPUT
# =====================================================

with left_col:
    with st.container(border=True):
        st.markdown("#### 📝 Editor Observasi")

        # 1. Pilih Baris (1-8)
        row_idx = st.selectbox(
            "Pilih Nomor Titik untuk Diedit:",
            range(1, WINDOW_SIZE + 1),
            index=0
        )

        # Ambil data saat ini untuk baris terpilih
        current_row_data = st.session_state.draft_data.iloc[row_idx - 1]

        # 2. Form Input untuk Baris Terpilih (Batch Update)
        with st.form(key=f"row_editor_form_{row_idx}"):
            c1, c2 = st.columns(2)
            with c1:
                new_lat = st.number_input("Latitude (°)", value=float(current_row_data["LAT"]), format="%.1f")
                new_wind = st.number_input("WMO Wind", value=float(current_row_data["WMO_WIND"]), format="%.1f")
            with c2:
                new_lon = st.number_input("Longitude (°)", value=float(current_row_data["LON"]), format="%.1f")
                new_pres = st.number_input("WMO Pres", value=float(current_row_data["WMO_PRES"]), format="%.1f")

            submit_row = st.form_submit_button("Simpan Titik", use_container_width=True)

            if submit_row:
                st.session_state.draft_data.loc[row_idx - 1, "LAT"] = new_lat
                st.session_state.draft_data.loc[row_idx - 1, "LON"] = new_lon
                st.session_state.draft_data.loc[row_idx - 1, "WMO_WIND"] = new_wind
                st.session_state.draft_data.loc[row_idx - 1, "WMO_PRES"] = new_pres
                st.rerun()

        st.divider()

        # 3. Konfigurasi Prediksi
        if "start_datetime" not in st.session_state:
            st.session_state.start_datetime = datetime.combine(datetime.now().date(), datetime.now().time().replace(hour=0, minute=0, second=0))

        with st.expander("Konfigurasi Prediksi", expanded=True):
            d_col, t_col = st.columns(2)
            start_date = d_col.date_input("Tanggal Awal (Titik 1)", st.session_state.start_datetime.date())
            start_time = t_col.time_input("Jam Awal (Titik 1)", st.session_state.start_datetime.time())
            st.session_state.start_datetime = datetime.combine(start_date, start_time)

            horizon = st.selectbox("Horizon Prediksi (Jam):", [3, 6, 9])
            num_steps = horizon // 3

            st.divider()

            # 4. Tampilkan Tabel Data Observasi Historis
            display_df = st.session_state.draft_data.copy()
            display_df.insert(0, "Titik", range(1, WINDOW_SIZE + 1))
            waktu_list = [
            (st.session_state.start_datetime + timedelta(hours=i * 3)).strftime("%d-%m-%Y %H:%M")
            for i in range(WINDOW_SIZE)
            ]
            display_df.insert(1, "Waktu (WIB)", waktu_list)

            # Format Koordinat
            display_df["LAT"] = display_df["LAT"].apply(lambda x: format_lat_indo(x, precision=1))
            display_df["LON"] = display_df["LON"].apply(lambda x: format_lon_indo(x, precision=1))

            # Rename Columns
            display_df = display_df.rename(columns={
            "LAT": "Lintang",
            "LON": "Bujur",
            "WMO_WIND": "Kec. Angin (Knot)",
            "WMO_PRES": "Tekanan (hPa)"
            })
            utils.render_custom_table(display_df, classes="custom-table prediksi-table")

        btn_col_print, btn_col_pred, btn_col_reset = st.columns([1, 1, 1])
        with btn_col_print:
            if st.session_state.prediction_result:
                try:
                    pdf_buffer = generate_pdf_report(
                        draft_data=st.session_state.draft_data,
                        prediction_result=st.session_state.prediction_result,
                        start_datetime=st.session_state.start_datetime,
                        horizon_hours=len(st.session_state.prediction_result) * 3,
                        num_steps=len(st.session_state.prediction_result),
                    )
                    st.download_button(
                        label="📄 Print Laporan",
                        data=pdf_buffer,
                        file_name=f"Laporan_Prediksi_Siklon_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.button("📄 Print Laporan", disabled=True, use_container_width=True)
                    st.toast(f"Gagal membuat PDF: {e}")
            else:
                st.button("📄 Print Laporan", disabled=True, use_container_width=True)
        with btn_col_pred:
            predict_clicked = st.button("🧠 Prediksi LSTM", type="primary", use_container_width=True)
        with btn_col_reset:
            st.button("🗑️ Bersihkan", on_click=clear_prediction, use_container_width=True)

    # PROSES PREDIKSI
    if predict_clicked:
        df = st.session_state.draft_data.copy()
        if (df["LAT"] == 0).any() or (df["LON"] == 0).any():
            st.error("⚠️ Semua koordinat LAT dan LON harus diisi.")
        else:
            try:
                with st.spinner("⏳ Memproses Prediksi Rekursif..."):
                    results = run_recursive_inference(df_raw=df, start_time=st.session_state.start_datetime, steps=num_steps)
                st.session_state.prediction_result = results
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan: {e}")

# =====================================================
# PETA & HASIL
# =====================================================

with right_col:
    with st.container(border=True):
        st.markdown("#### 🗺️ Visualisasi Jalur")

        map_df = st.session_state.draft_data
        valid_points = map_df[(map_df["LAT"] != 0) & (map_df["LON"] != 0)]

        center = [valid_points.iloc[-1]["LAT"], valid_points.iloc[-1]["LON"]] if not valid_points.empty else [-10, 90]
        m = folium.Map(location=center, zoom_start=5, control_scale=True)

        Fullscreen().add_to(m)
        MiniMap().add_to(m)
        MeasureControl().add_to(m)
        folium.LatLngPopup().add_to(m)

        # Draw History
        pts = valid_points[["LAT", "LON"]].values.tolist()
        if pts:
            folium.PolyLine(pts, color="blue", weight=4, opacity=0.7).add_to(m)
            for i, p in enumerate(pts):
                folium.CircleMarker(p, radius=5, color="blue", fill=True, tooltip=f"Titik {i+1}").add_to(m)

        # Draw Predictions
        if st.session_state.prediction_result:
            results = st.session_state.prediction_result
            last_pt = pts[-1]
            for res in results:
                pred_pt = [res['pred_lat'], res['pred_lon']]
                AntPath(locations=[last_pt, pred_pt], color="red", weight=5, dash_array=[10, 20]).add_to(m)
                folium.Marker(pred_pt, tooltip=f"Pred: {res['time'].strftime('%H:%M')}", icon=folium.Icon(color="red", icon="star")).add_to(m)
                last_pt = pred_pt

        map_data = st_folium(m, use_container_width=True, height=600)

    # HASIL PREDIKSI (DI BAWAH PETA)
    if st.session_state.prediction_result:
        results = st.session_state.prediction_result
        with st.container(border=True):
            st.markdown("#### 📍 Hasil Prediksi")

            prev_lat = st.session_state.draft_data.iloc[-1]["LAT"]
            prev_lon = st.session_state.draft_data.iloc[-1]["LON"]

            for i, res in enumerate(results):
                st.markdown(f"**Step {i+1} ({res['time'].strftime('%d-%m-%Y %H:%M')})**")
                c1, c2, c3 = st.columns(3)

                # Format Koordinat
                c1.metric("Lintang", format_lat_indo(res['pred_lat'], precision=1))
                c2.metric("Bujur", format_lon_indo(res['pred_lon'], precision=1))

                # Analytics
                analytics = calculate_analytics(
                    st.session_state.draft_data,
                    res['pred_lat'],
                    res['pred_lon'],
                    prev_lat=prev_lat,
                    prev_lon=prev_lon
                )

                c3.metric("Kecepatan", f"{analytics['speed_kmh']} km/h")

                st.caption(f"Status: {analytics['category']} | Arah: {analytics['bearing']}°")

                prev_lat = res['pred_lat']
                prev_lon = res['pred_lon']

            st.warning(
                "**Catatan Ilmiah:** Prediksi bersifat *data-driven* dan bersifat probabilistik sesuai karakteristik umum siklon tropis. "
                "Peningkatan *horizon* waktu (6-9 jam) secara inheren meningkatkan akumulasi ketidakpastian "
                "dan penurunan akurasi model. Hasil ini sebagai pendukung informasi."
            )

    # Update Data dari Klik Peta
    if map_data and map_data.get("last_clicked"):
        lat = round(map_data["last_clicked"]["lat"], 1)
        lon = round(map_data["last_clicked"]["lng"], 1)
        df = st.session_state.draft_data.copy()
        empty_indices = df.index[(df["LAT"] == 0) & (df["LON"] == 0)]
        if len(empty_indices) > 0:
            df.loc[empty_indices[0], ["LAT", "LON"]] = [lat, lon]
            st.session_state.draft_data = df
            st.rerun()
        else:
            st.toast("Semua titik sudah terisi.")

utils.render_footer()
