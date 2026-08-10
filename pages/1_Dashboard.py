import streamlit as st
import utils
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Dashboard Prediksi",
    page_icon="🗺️",
    layout="wide"
)

utils.inject_custom_css()
utils.render_sidebar()

st.markdown("### DASHBOARD PREDIKSI SIKLON")

# =====================================================
# LOAD DATA
# =====================================================
try:
    pred_df = utils.load_prediction_data()
    test_df = utils.load_test_data()
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

if pred_df.empty or test_df.empty:
    st.warning("Data prediksi atau observasi kosong.")
    st.stop()

PADANG_LAT = -0.94
PADANG_LON = 100.32

if "DIST_TO_PADANG" not in pred_df.columns:
    pred_df["DIST_TO_PADANG"] = utils.haversine_km(
        pred_df["LAT_ACTUAL"].values,
        pred_df["LON_ACTUAL"].values,
        np.full(len(pred_df), PADANG_LAT),
        np.full(len(pred_df), PADANG_LON),
    )

# =====================================================
# FILTER RADIUS
# =====================================================
radius_km = st.slider(
    "🎯 Radius dari Sumatera (km)",
    500,
    4000,
    1500,
    250
)

sumatra_mask = pred_df["DIST_TO_PADANG"] <= radius_km
sumatra_sids = pred_df[sumatra_mask]["SID"].unique()

if len(sumatra_sids) > 0:
    sid_list_filtered = sumatra_sids.tolist()
else:
    sid_list_filtered = pred_df["SID"].unique().tolist()

# =====================================================
# INITIALIZE SELECTED SID IN SESSION STATE
# =====================================================
if "selected_sid_dashboard" not in st.session_state:
    st.session_state["selected_sid_dashboard"] = sid_list_filtered[0] if sid_list_filtered else None

# Jika selected_sid saat ini tidak ada di dalam daftar yang difilter (misal setelah ganti radius),
# reset ke item pertama yang tersedia.
if st.session_state["selected_sid_dashboard"] not in sid_list_filtered:
    st.session_state["selected_sid_dashboard"] = sid_list_filtered[0] if sid_list_filtered else None

# =====================================================
# FILTER & SELEKSI SIKLON
# =====================================================
col_info, col_select = st.columns([1, 4], gap="large")

with col_info:
    warna = "#E8F0FE" if len(sid_list_filtered) > 0 else "#FEE2E2"
    teks = "#1E3A8A" if len(sid_list_filtered) > 0 else "#991B1B"

    # Margin-top disesuaikan agar lencana sejajar tengah dengan selectbox
    st.markdown(
        f"""
        <div style="
            background:{warna};
            padding:10px;
            border-radius:10px;
            text-align:center;
            font-weight:700;
            color:{teks};
            margin-top: 26px;
            border: 1px solid #BFDBFE;
            font-size: 0.9rem;
        ">
            🌀 {len(sid_list_filtered)} Siklon
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_select:
    try:
        default_index = sid_list_filtered.index(st.session_state["selected_sid_dashboard"])
    except ValueError:
        default_index = 0

    selectbox_val = st.selectbox(
        "🆔 Pilih ID Siklon (Gunakan pencarian teks di bawah)",
        options=sid_list_filtered,
        index=default_index,
        key="sid_selectbox",
        help="Anda dapat mengetik langsung ID siklon untuk mencari dengan cepat."
    )

    if selectbox_val and selectbox_val != st.session_state["selected_sid_dashboard"]:
        st.session_state["selected_sid_dashboard"] = selectbox_val
        st.rerun()

selected_sid = st.session_state["selected_sid_dashboard"]

if selected_sid is None:
    st.info("Silakan pilih ID siklon dari daftar untuk melanjutkan.")
    st.stop()

# =====================================================
# MERGE DATA
# =====================================================
pred_sid = (
    pred_df[pred_df["SID"] == selected_sid]
    .sort_values("ISO_TIME")
    .reset_index(drop=True)
)

test_sid = (
    test_df[test_df["SID"] == selected_sid]
    .sort_values("ISO_TIME")
    .reset_index(drop=True)
)

merged = pd.merge(
    test_sid[["SID", "ISO_TIME", "LAT", "LON"]],
    pred_sid[["SID", "ISO_TIME", "LAT_PRED", "LON_PRED", "ERROR_KM"]],
    on=["SID", "ISO_TIME"],
    how="inner",
)

if merged.empty:
    st.warning("Data prediksi tidak ditemukan.")
    st.stop()

# =====================================================
# INFORMASI SIKLON
# =====================================================
with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
**🆔 ID Siklon** : `{selected_sid}`  
**🏷️ Nama** : `{test_sid["NAME"].iloc[0]}`  
**⏱️ Interval** : `3 Jam`
""")

    with col2:
        awal = merged["ISO_TIME"].min().strftime("%d/%m/%Y")
        akhir = merged["ISO_TIME"].max().strftime("%d/%m/%Y")

        durasi = (
            merged["ISO_TIME"].max()
            - merged["ISO_TIME"].min()
        ).total_seconds() / 3600

        st.markdown(f"""
**📅 Periode** : `{awal} – {akhir}`  
**⏳ Durasi** : `{int(durasi)} jam`  
**📌 Jumlah titik** : `{len(merged)}`
""")

# =====================================================
# PETA
# =====================================================
st.markdown("#### Visualisasi Peta")

try:
    center_lat = merged["LAT"].mean()
    center_lon = merged["LON"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6
    )

    folium.PolyLine(
        list(zip(merged["LAT"], merged["LON"])),
        color="black",
        weight=3,
        tooltip="Aktual",
    ).add_to(m)

    folium.PolyLine(
        list(zip(merged["LAT_PRED"], merged["LON_PRED"])),
        color="#1E3A8A",
        weight=3,
        dash_array="6,6",
        tooltip="Prediksi",
    ).add_to(m)

    for _, row in merged.iterrows():
        folium.CircleMarker(
            [row["LAT"], row["LON"]],
            radius=4,
            color="black",
            fill=True,
            fill_color="white",
        ).add_to(m)

        folium.CircleMarker(
        [row["LAT_PRED"], row["LON_PRED"]],
        radius=4,
        color="#1E3A8A",
        fill=True,
        fill_color="white",
    ).add_to(m)

    folium.CircleMarker(
        [merged["LAT"].iloc[0], merged["LON"].iloc[0]],
        radius=8,
        color="green",
        fill=True,
        fill_color="green",
    ).add_to(m)

    folium.CircleMarker(
        [merged["LAT"].iloc[-1], merged["LON"].iloc[-1]],
        radius=8,
        color="#1E3A8A",
        fill=True,
        fill_color="#1E3A8A",
    ).add_to(m)

    legend = """
    <div style="
    position:absolute;
    bottom:60px;
    left:50px;
    z-index:9999;
    background:white;
    padding:12px;
    border-radius:8px;
    border:2px solid #999;
    ">
    <b>Legenda</b><br>
    <span style="display:inline-block;width:24px;height:3px;background:black;"></span>
    Aktual<br>

    <span style="display:inline-block;border-top:3px dashed #1E3A8A;width:24px;"></span>
    Prediksi<br>

    <span style="display:inline-block;width:15px;height:15px;border-radius:50%;background:green;"></span>
    Start<br>

    <span style="display:inline-block;width:15px;height:15px;border-radius:50%;background:#1E3A8A;"></span>
    End
    </div>
    """

    m.get_root().html.add_child(
        folium.Element(legend)
    )

    st_folium(
        m,
        width="100%",
        height=550,
        returned_objects=[],
    )

except Exception as e:
    st.error(e)

# =====================================================
# METRIK
# =====================================================
st.markdown("---")
st.markdown("#### Metrik Akurasi")

rmse = np.sqrt(np.mean(merged["ERROR_KM"] ** 2))
mae = merged["ERROR_KM"].mean()

c1, c2 = st.columns(2)

with c1:
    st.markdown(
        f"""
<div class="metric-card">
<div class="metric-label">RMSE (km)</div>
<div class="metric-value">{rmse:.2f}</div>
</div>
""",
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
<div class="metric-card">
<div class="metric-label">MAE (km)</div>
<div class="metric-value">{mae:.2f}</div>
</div>
""",
        unsafe_allow_html=True,
    )

# =====================================================
# TABEL
# =====================================================
st.markdown("#### Tabel Perbandingan Koordinat")

tabel = merged.copy()
tabel["ISO_TIME"] = tabel["ISO_TIME"].dt.strftime("%d/%m/%Y %H:%M")
tabel["LAT"] = tabel["LAT"].map(lambda x: f"{x:.4f}°")
tabel["LON"] = tabel["LON"].map(lambda x: f"{x:.4f}°")
tabel["LAT_PRED"] = tabel["LAT_PRED"].map(lambda x: f"{x:.4f}°")
tabel["LON_PRED"] = tabel["LON_PRED"].map(lambda x: f"{x:.4f}°")
tabel["ERROR_KM"] = tabel["ERROR_KM"].map(lambda x: f"{x:.2f}")

tabel = tabel[["ISO_TIME", "LAT", "LON", "LAT_PRED", "LON_PRED", "ERROR_KM"]]
tabel.columns = [
    "Waktu",
    "LAT Aktual",
    "LON Aktual",
    "LAT Prediksi",
    "LON Prediksi",
    "Error (km)",
]

utils.render_custom_table(tabel)

utils.render_footer()