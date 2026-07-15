import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath, Fullscreen, MeasureControl, MiniMap
from datetime import datetime, timedelta
import utils
from predictor.physics import (
    DEFAULT_INTERVAL_HOURS,
    MAX_TRANSLATION_SPEED_KMH,
    calculate_bearing,
    destination,
    haversine_km,
    predict_next_position,
)

# --- UI STREAMLIT ---
st.set_page_config(page_title="Prediksi Siklon", page_icon="🔮", layout="wide")

utils.inject_custom_css()
utils.render_sidebar_brand()

st.markdown("### PREDIKSI LINTASAN SIKLON")
st.markdown(
    """
    <style>
    .prediction-result-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-top: 10px;
    }
    .prediction-result-item {
        min-width: 0;
        background: #F8FAFC;
        border: 1.5px solid #CBD5E1;
        border-radius: 8px;
        padding: 10px 12px;
    }
    .prediction-result-item.wide { grid-column: 1 / -1; }
    .prediction-result-label {
        display: block;
        color: #475569;
        font-size: 0.74rem !important;
        font-weight: 800;
        letter-spacing: .06em;
        text-transform: uppercase;
        margin-bottom: 3px;
    }
    .prediction-result-value {
        display: block;
        color: #1E3A8A;
        font-size: 1.05rem !important;
        font-weight: 900;
        overflow-wrap: anywhere;
    }
    .prediction-metric-card {
        min-width: 0;
        background: #FFFFFF;
        border: 2px solid #94A3B8;
        border-radius: 10px;
        padding: 15px 10px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(15, 23, 42, .08);
    }
    .prediction-metric-label {
        color: #475569;
        font-size: .7rem !important;
        font-weight: 900;
        letter-spacing: .07em;
        text-transform: uppercase;
    }
    .prediction-metric-value {
        color: #1E3A8A;
        font-size: 2.15rem !important;
        font-weight: 900;
        line-height: 1.15;
        margin: 7px 0 2px;
        overflow-wrap: anywhere;
    }
    .prediction-metric-unit { color: #475569; font-size: .82rem !important; }
    .prediction-method {
        background: #F8FAFC;
        border-left: 5px solid #1E3A8A;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 14px;
    }
    .prediction-method h5 {
        color: #1E3A8A !important;
        font-size: 1rem !important;
        margin: 0 0 8px !important;
        font-weight: 900 !important;
    }
    .prediction-method p, .prediction-method li {
        font-size: .88rem !important;
        line-height: 1.55;
        margin-bottom: 5px;
    }
    .prediction-method ol { margin: 8px 0 0; padding-left: 22px; }
    @media (max-width: 800px) {
        .prediction-metric-value { font-size: 1.75rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="info-card">
        <h4>🔮 Prediksi Posisi 3 Jam Berikutnya</h4>
        Masukkan delapan posisi siklon secara berurutan, dari observasi paling lama ke yang terbaru.
        Sistem menghitung proyeksi geodesik berbasis fisika dengan interval observasi tiga jam.
    </div>
    """,
    unsafe_allow_html=True,
)

def empty_coordinate_input():
    """Bentuk data awal yang dipakai oleh editor koordinat."""
    return pd.DataFrame({"LAT": [0.0] * 8, "LON": [0.0] * 8})


def clear_prediction_input():
    """Reset data dan ganti key editor agar state widget lama tidak digunakan."""
    st.session_state.input_data = empty_coordinate_input()
    st.session_state.results = None
    st.session_state.prediction_editor_version += 1


def add_estimated_motion_animation(map_object, points):
    """Tambahkan animasi aliran arah gerak dari dua observasi terakhir.

    Ini merupakan indikator arah gerak yang diturunkan dari koordinat input,
    bukan data angin/cuaca real-time.
    """
    if len(points) < 2:
        return

    previous_lat, previous_lon = points[-2]
    current_lat, current_lon = points[-1]
    bearing = calculate_bearing(previous_lat, previous_lon, current_lat, current_lon)
    stream_group = folium.FeatureGroup(name="Animasi arah gerak (estimasi)", show=True)

    # Tiga garis animasi paralel memperjelas arah pergerakan tanpa menyiratkan
    # bahwa aplikasi memiliki data medan angin observasi.
    for lateral_distance in (-55, 0, 55):
        offset_bearing = (bearing + 90) % 360 if lateral_distance >= 0 else (bearing - 90) % 360
        stream_lat, stream_lon = destination(
            current_lat,
            current_lon,
            offset_bearing,
            abs(lateral_distance),
        )
        start_lat, start_lon = destination(stream_lat, stream_lon, (bearing + 180) % 360, 145)
        end_lat, end_lon = destination(stream_lat, stream_lon, bearing, 180)
        AntPath(
            locations=[(start_lat, start_lon), (end_lat, end_lon)],
            color="#38BDF8",
            pulse_color="#E0F2FE",
            weight=3,
            opacity=0.9,
            delay=750,
            dash_array=[12, 24],
        ).add_to(stream_group)

    stream_group.add_to(map_object)


if 'input_data' not in st.session_state:
    st.session_state.input_data = empty_coordinate_input()
if 'results' not in st.session_state:
    st.session_state.results = None
if 'prediction_editor_version' not in st.session_state:
    st.session_state.prediction_editor_version = 0
# Hindari kegagalan bila browser masih menyimpan format hasil versi lama.
if st.session_state.results is not None and not isinstance(st.session_state.results, dict):
    st.session_state.results = None

col1, col2 = st.columns([0.8, 1.4])

with col1:
    with st.container(border=True):
        st.markdown("#### 📝 Input Koordinat")
        st.caption("Urutkan dari titik paling lama ke paling baru. Interval tiap titik adalah 3 jam; proyeksi dibatasi maksimal 180 km per 3 jam.")

        sim_date = st.date_input("📅 Tanggal awal observasi", value=datetime.now())

        edited_df = st.data_editor(
            st.session_state.input_data,
            key=f"prediction_coordinate_editor_{st.session_state.prediction_editor_version}",
            num_rows="fixed",
            width="stretch",
            height=330,
            column_config={
                "LAT": st.column_config.NumberColumn("LAT (°)", format="%.4f"),
                "LON": st.column_config.NumberColumn("LON (°)", format="%.4f"),
            },
        )
        st.session_state.input_data = edited_df

        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            predict_clicked = st.button("🚀 Prediksi 3 Jam", type="primary", use_container_width=True)
        with col_btn2:
            st.button(
                "🗑️ Bersihkan",
                type="secondary",
                use_container_width=True,
                on_click=clear_prediction_input,
            )

    if predict_clicked:
        coordinates = edited_df[["LAT", "LON"]].apply(pd.to_numeric, errors="coerce")
        has_empty_coordinate = coordinates.isna().any().any() or ((coordinates["LAT"] == 0.0) & (coordinates["LON"] == 0.0)).any()
        has_invalid_coordinate = (~coordinates["LAT"].between(-90, 90) | ~coordinates["LON"].between(-180, 180)).any()
        if has_empty_coordinate:
            st.error("⚠️ Masih ada koordinat LAT/LON yang kosong. Klik peta untuk mengisinya.")
        elif has_invalid_coordinate:
            st.error("⚠️ Koordinat tidak valid. LAT harus -90 s.d. 90 dan LON harus -180 s.d. 180.")
        else:
            try:
                forecast = predict_next_position(edited_df)
            except ValueError as error:
                st.error(f"⚠️ {error}")
            else:
                # Delapan observasi 3-jam berada pada jam 00 s.d. 21; langkah
                # berikutnya benar-benar jam 24, bukan jam 27.
                next_t = datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=24)
                final_result = [{
                    "Waktu": next_t.strftime("%Y-%m-%d %H:%M"),
                    "LAT": round(forecast["lat"], 4),
                    "LON": round(forecast["lon"], 4)
                }]

                st.session_state.results = {"position": final_result, "forecast": forecast}
                st.rerun()

    if st.session_state.results is not None:
        with st.container(border=True):
            st.markdown("#### 📍 Hasil Prediksi")
            st.success("Prediksi 3 jam ke depan berhasil dihitung.")
            predicted_position = st.session_state.results["position"][0]
            st.markdown(
                f"""
                <div class="prediction-result-grid">
                    <div class="prediction-result-item wide">
                        <span class="prediction-result-label">Waktu Prediksi</span>
                        <span class="prediction-result-value">{predicted_position['Waktu']}</span>
                    </div>
                    <div class="prediction-result-item">
                        <span class="prediction-result-label">Latitude</span>
                        <span class="prediction-result-value">{predicted_position['LAT']:.4f}°</span>
                    </div>
                    <div class="prediction-result-item">
                        <span class="prediction-result-label">Longitude</span>
                        <span class="prediction-result-value">{predicted_position['LON']:.4f}°</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.container(border=True):
            st.markdown("#### 📊 Detail Perhitungan")
            valid = edited_df[(edited_df['LAT'] != 0.0) & (edited_df['LON'] != 0.0)]
            if len(valid) >= 2:
                forecast = st.session_state.results["forecast"]
                total_dist = sum(
                    haversine_km(a.LAT, a.LON, b.LAT, b.LON)
                    for a, b in zip(valid.iloc[:-1].itertuples(), valid.iloc[1:].itertuples())
                )

                metric_1, metric_2 = st.columns(2)
                with metric_1:
                    st.markdown(
                        f"""
                        <div class="prediction-metric-card">
                            <div class="prediction-metric-label">Proyeksi 3 Jam</div>
                            <div class="prediction-metric-value">{forecast['distance_km']:.1f}</div>
                            <div class="prediction-metric-unit">kilometer</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with metric_2:
                    st.markdown(
                        f"""
                        <div class="prediction-metric-card">
                            <div class="prediction-metric-label">Kecepatan Digunakan</div>
                            <div class="prediction-metric-value">{forecast['speed_kmh']:.1f}</div>
                            <div class="prediction-metric-unit">km/jam</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f"""
                    <div class="prediction-method">
                        <h5>Skema Prediksi Operasional</h5>
                        <p>Halaman ini menggunakan <strong>model fisika berbasis lintasan</strong> sebagai pengganti inferensi LSTM yang tidak stabil.</p>
                        <ol>
                            <li><strong>Input sequence:</strong> 8 titik observasi dengan interval {DEFAULT_INTERVAL_HOURS:.0f} jam.</li>
                            <li><strong>Ekstraksi pola gerak:</strong> jarak geodesik dan arah dihitung dari tiga segmen terakhir.</li>
                            <li><strong>Stabilisasi:</strong> median kecepatan dipakai untuk menekan outlier; nilai sebelum batas adalah <strong>{forecast['raw_speed_kmh']:.2f} km/jam</strong>.</li>
                            <li><strong>Output:</strong> posisi +3 jam diproyeksikan pada arah <strong>{forecast['bearing']:.2f}°</strong> dengan kecepatan aman <strong>{forecast['speed_kmh']:.2f} km/jam</strong>.</li>
                        </ol>
                        <p style="margin-top:8px;"><strong>Kontrol fisik:</strong> lintasan input {total_dist:.2f} km dan proyeksi dibatasi {forecast['max_distance_km']:.0f} km per 3 jam ({MAX_TRANSLATION_SPEED_KMH:.0f} km/jam), sehingga hasil tidak melonjak ribuan kilometer.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

with col2:
    with st.container(border=True):
        st.markdown("#### 🗺️ Peta Lintasan")
        st.caption("Klik peta untuk mengisi titik kosong berikutnya pada tabel koordinat.")
        valid_df = edited_df[(edited_df['LAT'] != 0.0) & (edited_df['LON'] != 0.0)]
        if not valid_df.empty:
            center_lat = valid_df['LAT'].iloc[-1]
            center_lon = valid_df['LON'].iloc[-1]
        else:
            center_lat, center_lon = -10.0, 90.0

        # Peta navigasi menjadi default agar tetap dapat dibaca bila layer
        # satelit tidak tersedia. Layer satelit dan mode gelap tersedia pada
        # kontrol layer di kanan atas.
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=5,
            tiles=None,
            control_scale=True,
            prefer_canvas=True,
        )
        folium.TileLayer(
            tiles="OpenStreetMap",
            name="Peta navigasi",
            overlay=False,
            control=True,
            show=True,
        ).add_to(m)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
            name="Citra satelit",
            overlay=False,
            control=True,
            show=False,
        ).add_to(m)
        folium.TileLayer(
            tiles="CartoDB dark_matter",
            name="Mode gelap laut",
            overlay=False,
            control=True,
            show=False,
        ).add_to(m)
        folium.TileLayer(
            tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="Labels © Esri",
            name="Label geografis",
            overlay=True,
            control=True,
            opacity=0.9,
        ).add_to(m)
        Fullscreen(position="topright", title="Layar penuh", title_cancel="Keluar layar penuh").add_to(m)
        MeasureControl(
            position="topright",
            primary_length_unit="kilometers",
            secondary_length_unit="miles",
        ).add_to(m)
        MiniMap(toggle_display=True, position="bottomright").add_to(m)

        folium.PolyLine(
            locations=[(0, 40), (0, 130)],
            color="#DC2626",
            weight=2,
            dash_array="5,5",
            tooltip="Khatulistiwa",
        ).add_to(m)
        folium.Rectangle(
            bounds=[(-40, 40), (40, 130)],
            color="#059669",
            fill=False,
            weight=2,
            dash_array="5,5",
            tooltip="Wilayah kajian",
        ).add_to(m)
        h_pts = edited_df[['LAT', 'LON']].values.tolist()
        valid_pts = [point for point in h_pts if point[0] != 0.0 and point[1] != 0.0]
        if valid_pts:
            folium.PolyLine(valid_pts, color="black", weight=3, tooltip="Observasi").add_to(m)
            for index, point in enumerate(valid_pts, start=1):
                folium.CircleMarker(
                    point,
                    radius=4,
                    color="black",
                    fill=True,
                    fill_color="white",
                    tooltip=f"Timestep observasi {index}",
                ).add_to(m)
            folium.CircleMarker(valid_pts[0], radius=8, color="green", fill=True, fill_color="green", tooltip="Mulai").add_to(m)
            folium.CircleMarker(valid_pts[-1], radius=8, color="#1E3A8A", fill=True, fill_color="#1E3A8A", tooltip="Observasi terbaru").add_to(m)
            add_estimated_motion_animation(m, valid_pts)

        if st.session_state.results is not None:
            p_pts = [[row['LAT'], row['LON']] for row in st.session_state.results["position"]]
            if valid_pts:
                AntPath(
                    locations=[valid_pts[-1]] + p_pts,
                    color="#F97316",
                    pulse_color="#FDE68A",
                    weight=5,
                    opacity=1,
                    delay=650,
                    dash_array=[14, 22],
                    tooltip="Jalur prediksi 3 jam",
                ).add_to(m)
            for point in p_pts:
                folium.CircleMarker(
                    point,
                    radius=13,
                    color="#991B1B",
                    weight=3,
                    fill=True,
                    fill_color="#EF4444",
                    fill_opacity=0.95,
                    tooltip="🔮 Posisi prediksi +3 jam",
                ).add_to(m)
                folium.Marker(
                    point,
                    icon=folium.DivIcon(
                        html="<div style='font-size:20px;line-height:20px;text-align:center;'>🔮</div>",
                        icon_size=(20, 20),
                        icon_anchor=(10, 10),
                    ),
                    tooltip="Hasil prediksi",
                ).add_to(m)

        legend = """
        <div style="position:absolute;bottom:25px;left:25px;z-index:9999;background:rgba(255,255,255,.94);padding:12px;border-radius:8px;border:2px solid #64748B;box-shadow:0 2px 8px rgba(0,0,0,.25);">
            <b>Legenda</b><br>
            <span style="display:inline-block;width:24px;height:3px;background:black;"></span> Jalur timestep/observasi<br>
            <span style="display:inline-block;border-top:4px dashed #F97316;width:24px;"></span> Jalur prediksi 3 jam<br>
            <span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:#EF4444;border:2px solid #991B1B;"></span> 🔮 Posisi prediksi<br>
            <span style="display:inline-block;width:24px;border-top:3px dashed #38BDF8;"></span> Arah gerak estimasi<br>
            <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:green;"></span> Mulai<br>
            <small>Animasi arah gerak dihitung dari posisi terakhir, bukan data angin real-time.</small>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend))
        folium.LayerControl(collapsed=False, position="topright").add_to(m)
        map_data = st_folium(m, use_container_width=True, height=650)

    if map_data and map_data.get('last_clicked'):
        lat = map_data['last_clicked']['lat']
        lon = map_data['last_clicked']['lng']
        df_temp = st.session_state.input_data
        empty_mask = (df_temp['LAT'] == 0.0) & (df_temp['LON'] == 0.0)
        empty_idx = df_temp[empty_mask].index
        if len(empty_idx) > 0:
            idx = empty_idx[0]
        else:
            idx = df_temp.index[-1]
        df_temp.loc[idx, 'LAT'] = lat
        df_temp.loc[idx, 'LON'] = lon
        st.session_state.input_data = df_temp
        st.rerun()

utils.render_footer()
