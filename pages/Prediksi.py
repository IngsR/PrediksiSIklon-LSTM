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
    run_inference,
    WINDOW_SIZE,
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Prediksi Siklon",
    page_icon="🔮",
    layout="wide",
)

utils.inject_custom_css()
utils.render_sidebar_brand()

# =====================================================
# HEADER
# =====================================================

st.markdown("### PREDIKSI LINTASAN SIKLON (LSTM)")

st.markdown(
    """
<div class="info-card">
<h4>🧠 Prediksi Posisi Berbasis LSTM</h4>

Masukkan 8 observasi siklon
(LAT, LON, WMO_WIND, WMO_PRES).

Feature engineering dan prediksi
hanya dijalankan setelah tombol
Prediksi LSTM ditekan.

</div>
""",
    unsafe_allow_html=True,
)

# =====================================================
# DATA DEFAULT
# =====================================================

def create_empty_dataframe():

    return pd.DataFrame(
        {
            "LAT": [0.0] * WINDOW_SIZE,
            "LON": [0.0] * WINDOW_SIZE,
            "WMO_WIND": [25.0] * WINDOW_SIZE,
            "WMO_PRES": [1005.0] * WINDOW_SIZE,
        }
    )

# =====================================================
# SESSION STATE
# =====================================================

# Data yang sedang diedit
if "draft_data" not in st.session_state:
    st.session_state.draft_data = create_empty_dataframe()

# Snapshot saat tombol Prediksi ditekan
if "prediction_input" not in st.session_state:
    st.session_state.prediction_input = None

# Hasil prediksi
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

# Refresh editor jika tombol Bersihkan ditekan
if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0

# =====================================================
# FUNGSI RESET
# =====================================================

def clear_prediction():

    st.session_state.draft_data = create_empty_dataframe()

    st.session_state.prediction_input = None

    st.session_state.prediction_result = None

    st.session_state.editor_version += 1

# =====================================================
# LAYOUT
# =====================================================

left_col, right_col = st.columns([0.8, 1.4])

# =====================================================
# INPUT
# =====================================================

with left_col:

    with st.container(border=True):

        st.markdown("#### 📝 Input Observasi (8 Titik)")

        st.caption(
            "LAT dan LON dapat diisi dari tabel "
            "atau melalui klik pada peta."
        )

        # -------------------------------------

        date_col, time_col = st.columns(2)

        with date_col:

            start_date = st.date_input(
                "📅 Tanggal Awal",
                datetime.now(),
            )

        with time_col:

            start_time = st.time_input(
                "⏰ Jam Awal",
                datetime.now().time().replace(
                    hour=0,
                    minute=0,
                    second=0,
                ),
            )

        start_datetime = datetime.combine(
            start_date,
            start_time,
        )

        # -------------------------------------

        edited_df = st.data_editor(

            st.session_state.draft_data,

            key=f"prediction_editor_{st.session_state.editor_version}",

            num_rows="fixed",

            width="stretch",

            height=340,

            column_config={

                "LAT": st.column_config.NumberColumn(
                    "LAT (°)",
                    format="%.1f",
                ),

                "LON": st.column_config.NumberColumn(
                    "LON (°)",
                    format="%.1f",
                ),

                "WMO_WIND": st.column_config.NumberColumn(
                    "Wind (WMO)",
                    format="%.1f",
                ),

                "WMO_PRES": st.column_config.NumberColumn(
                    "Press (WMO)",
                    format="%.1f",
                ),

            },
        )

        # Selalu simpan hasil edit ke draft

        st.session_state.draft_data = edited_df.copy()

        # -------------------------------------

        col1, col2 = st.columns([2,1])

        with col1:

            predict_clicked = st.button(
                "🧠 Prediksi LSTM",
                type="primary",
                width="stretch",
            )

        with col2:

            st.button(
                "🗑️ Bersihkan",
                width="stretch",
                on_click=clear_prediction,
            )
            # =====================================================
# PROSES PREDIKSI
# =====================================================

    if predict_clicked:

        df = st.session_state.draft_data.copy()

        # -----------------------------------------
        # VALIDASI
        # -----------------------------------------

        if df.isnull().values.any():

            st.error(
                "⚠️ Masih terdapat data kosong (NaN)."
            )

        elif (df["LAT"] == 0).any() or (df["LON"] == 0).any():

            st.error(
                "⚠️ Semua koordinat LAT dan LON harus diisi."
            )

        elif (df["WMO_WIND"] == 0).any():

            st.error(
                "⚠️ Nilai WMO_WIND tidak boleh 0."
            )

        elif (df["WMO_PRES"] == 0).any():

            st.error(
                "⚠️ Nilai WMO_PRES tidak boleh 0."
            )

        else:

            # -------------------------------------
            # SIMPAN SNAPSHOT
            # -------------------------------------

            st.session_state.prediction_input = df.copy()

            # -------------------------------------
            # JALANKAN MODEL
            # -------------------------------------

            try:

                with st.spinner(
                    "⏳ Sedang melakukan feature engineering dan prediksi..."
                ):

                    result = run_inference(
                        df_raw=st.session_state.prediction_input,
                        start_time=start_datetime,
                    )

                st.session_state.prediction_result = result

            except Exception as e:

                st.session_state.prediction_result = None

                st.error(
                    f"⚠️ Terjadi kesalahan:\n\n{e}"
                )

# =====================================================
# HASIL PREDIKSI
# =====================================================

    if st.session_state.prediction_result is not None:

        result = st.session_state.prediction_result

        pred_lat = result["pred_lat"]
        pred_lon = result["pred_lon"]

        next_time = (
            start_datetime
            + timedelta(hours=24)
        )

        with st.container(border=True):

            st.markdown(
                "#### 📍 Hasil Prediksi"
            )

            st.success(
                "Prediksi berhasil dijalankan."
            )

            c1, c2 = st.columns(2)

            with c1:

                st.metric(
                    "Latitude",
                    f"{pred_lat:.6f}°",
                )

            with c2:

                st.metric(
                    "Longitude",
                    f"{pred_lon:.6f}°",
                )

            st.info(
                f"""
Prediksi dilakukan untuk:

**{next_time.strftime('%d-%m-%Y %H:%M')}**
"""
            )
            # =====================================================
# PETA
# =====================================================

with right_col:

    with st.container(border=True):

        st.markdown("#### 🗺️ Peta Observasi")

        st.caption(
            "Klik peta untuk mengisi koordinat "
            "LAT dan LON."
        )

        map_df = st.session_state.draft_data.copy()

        valid_df = map_df[
            (map_df["LAT"] != 0)
            &
            (map_df["LON"] != 0)
        ]

        if len(valid_df):

            center_lat = valid_df.iloc[-1]["LAT"]
            center_lon = valid_df.iloc[-1]["LON"]

        else:

            center_lat = -10
            center_lon = 90

        m = folium.Map(

            location=[
                center_lat,
                center_lon,
            ],

            zoom_start=5,

            tiles="OpenStreetMap",

            control_scale=True,

            prefer_canvas=True,

        )

        Fullscreen().add_to(m)

        MiniMap().add_to(m)

        MeasureControl().add_to(m)

        folium.LatLngPopup().add_to(m)

        # =====================================
        # GARIS OBSERVASI
        # =====================================

        points = valid_df[
            ["LAT", "LON"]
        ].values.tolist()

        if len(points):

            folium.PolyLine(

                points,

                color="black",

                weight=3,

            ).add_to(m)

            for i, point in enumerate(points):

                folium.CircleMarker(

                    point,

                    radius=4,

                    color="black",

                    fill=True,

                    tooltip=f"Titik {i+1}",

                ).add_to(m)

        # =====================================
        # HASIL PREDIKSI
        # =====================================

        if (

            st.session_state.prediction_result
            is not None

            and

            len(points)

        ):

            pred_lat = st.session_state.prediction_result[
                "pred_lat"
            ]

            pred_lon = st.session_state.prediction_result[
                "pred_lon"
            ]

            AntPath(

                locations=[

                    points[-1],

                    [

                        pred_lat,

                        pred_lon,

                    ],

                ],

                color="red",

                weight=4,

            ).add_to(m)

            folium.Marker(

                [

                    pred_lat,

                    pred_lon,

                ],

                tooltip="Prediksi",

            ).add_to(m)

        map_data = st_folium(

            m,

            width="stretch",

            height=650,

        )

# =====================================================
# INPUT DARI PETA
# =====================================================

    if (

        map_data

        and

        map_data.get("last_clicked")

    ):

        lat = map_data["last_clicked"]["lat"]

        lon = map_data["last_clicked"]["lng"]

        df = st.session_state.draft_data.copy()

        empty = df.index[

            (df["LAT"] == 0)

            &

            (df["LON"] == 0)

        ]

        if len(empty):

            idx = empty[0]

            df.loc[idx, "LAT"] = lat

            df.loc[idx, "LON"] = lon

            st.session_state.draft_data = df

        else:

            st.toast(
                "Seluruh titik sudah terisi."
            )

utils.render_footer()
