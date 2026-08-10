import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTION_PATH           = os.path.join(BASE_DIR, "data", "predictions_gab8.csv")
TEST_DATA_PATH            = os.path.join(BASE_DIR, "data", "model_gab_test_fix.csv")
OBSERVASI_PATH            = os.path.join(BASE_DIR, "data", "data_observasi.csv")
MODEL_RANKING_PATH        = os.path.join(BASE_DIR, "data", "model_ranking.csv")
RANKING_HAVERSINE_PATH    = os.path.join(BASE_DIR, "data", "model_ranking_arversine.csv")
OVERFITTING_PATH          = os.path.join(BASE_DIR, "data", "overfitting_summary.csv")
TRAINING_SUMMARY_PATH     = os.path.join(BASE_DIR, "data", "training_summary.csv")
TRAJECTORY_IMG_PATH       = os.path.join(BASE_DIR, "assets", "trajectory_best_model.png")
PREDICTION_SUMMARY_PATH   = os.path.join(BASE_DIR, "data", "prediction_summary.csv")

COLOR = {
    "bg_primary": "#FFFFFF", "bg_secondary": "#F8F9FA",
    "text_primary": "#1F2937", "text_secondary": "#6B7280",
    "blue_primary": "#1E3A8A", "blue_accent": "#1E3A8A",
    "red_semantic": "#DC2626", "success": "#059669",
    "border": "#D1D5DB",
}

def haversine_km(lat1, lon1, lat2, lon2):
    import numpy as np
    lat1, lon1, lat2, lon2 = map(np.asarray, [lat1, lon1, lat2, lon2])
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    d_phi = np.radians(lat2 - lat1)
    d_lam = np.radians(lon2 - lon1)
    a = np.sin(d_phi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(d_lam / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))

@st.cache_data(show_spinner="Memuat data prediksi...")
def load_prediction_data():
    df = pd.read_csv(PREDICTION_PATH)
    df["ISO_TIME"] = pd.to_datetime(df["ISO_TIME"])
    return df

@st.cache_data(show_spinner="Memuat data observasi...")
def load_test_data():
    df = pd.read_csv(TEST_DATA_PATH)
    df["ISO_TIME"] = pd.to_datetime(df["ISO_TIME"])
    return df

@st.cache_data(show_spinner="Memuat data observasi lengkap...")
def load_observasi_data():
    df = pd.read_csv(OBSERVASI_PATH)
    df["ISO_TIME"] = pd.to_datetime(df["ISO_TIME"])
    return df

@st.cache_data
def load_model_ranking():
    return pd.read_csv(MODEL_RANKING_PATH)

@st.cache_data
def load_model_ranking_haversine():
    return pd.read_csv(RANKING_HAVERSINE_PATH)

@st.cache_data
def load_overfitting_summary():
    return pd.read_csv(OVERFITTING_PATH)

@st.cache_data
def load_training_summary():
    return pd.read_csv(TRAINING_SUMMARY_PATH)

@st.cache_data
def load_prediction_summary():
    return pd.read_csv(PREDICTION_SUMMARY_PATH)

def inject_custom_css():
    # Inisialisasi state sidebar jika belum ada
    if "sidebar_visible" not in st.session_state:
        st.session_state.sidebar_visible = True

    sidebar_css = ""
    if not st.session_state.sidebar_visible:
        sidebar_css = """
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        [data-testid="stMainBlockContainer"] {
            padding-top: 100px !important;
        }
        """

    css_content = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* CSS untuk menyembunyikan sidebar secara kondisional */
    {sidebar_css}

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 18px !important;
        color: #000000 !important;
        font-weight: 500;
    }

    /* Gaya untuk Tombol Tampilkan Sidebar (Floating/High Contrast) */
    .show-btn-container {
        position: fixed;
        top: 85px;
        left: 20px;
        z-index: 999999;
    }

    .stButton > button[key="show_sidebar_btn"] {
        background-color: #FACC15 !important; /* Kuning Terang agar mudah dilihat */
        color: #000000 !important;
        border: 3px solid #000000 !important;
        font-weight: 900 !important;
        padding: 10px 20px !important;
        border-radius: 12px !important;
        box-shadow: 4px 4px 0px #000000 !important;
        transition: all 0.2s ease;
    }

    .stButton > button[key="show_sidebar_btn"]:hover {
        background-color: #EAB308 !important;
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0px #000000 !important;
    }

    /* Gaya untuk Tombol Sembunyikan Sidebar */
    .stButton > button[key="hide_sidebar_btn"] {
        background-color: #E5E7EB !important;
        color: #1F2937 !important;
        border: 2px solid #9CA3AF !important;
        font-weight: 700 !important;
        margin-bottom: 15px !important;
        border-radius: 8px !important;
    }

    .main { background-color: #FFFFFF; }

    section.main > div {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 90px !important;
    }

    [data-testid="stSidebar"] {
        background-color: #F3F4F6 !important;
        border-right: 3px solid #D1D5DB !important;
    }
    .sidebar-spacer { flex-grow: 1 !important; min-height: 20px !important; }

    [data-testid="stSidebarNav"], nav[data-testid="stSidebarNav"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    .top-action-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        width: 100%;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }

    .top-action-bar .brand-label {
        font-size: 1.05rem !important;
        font-weight: 900 !important;
        color: #111827 !important;
        letter-spacing: 0.02em;
    }

    .sidebar-toggle-button {
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 320px !important;
        border-radius: 14px !important;
        border: 2px solid #1E3A8A !important;
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        padding: 12px 18px !important;
        box-shadow: 0 12px 24px rgba(30, 58, 138, 0.16) !important;
        transition: all 0.22s ease !important;
    }

    .sidebar-toggle-button:hover {
        background-color: #2563EB !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button {
        min-height: 46px !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
    }

    .stButton > button:focus-visible {
        outline: 3px solid rgba(59, 130, 246, 0.5) !important;
    }

    #global-header {
        position: fixed; top: 0; left: 0; width: 100vw; height: 70px;
        background: linear-gradient(135deg, #1E3A8A 0%, #11224D 100%);
        color: white; z-index: 999999;
        display: flex; align-items: center; padding: 0 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    .g-title {
        margin: 0; font-size: 1.4rem !important; font-weight: 900 !important;
        color: #FFFFFF !important; text-transform: uppercase;
    }

    [data-testid="stDataFrame"] table,
    [data-testid="stTable"] table,
    .stDataFrame table,
    .stTable table {
        border-collapse: collapse !important;
        border: 4px solid #000000 !important;
    }

    [data-testid="stDataFrame"] th,
    [data-testid="stTable"] th,
    .stDataFrame th,
    .stTable th {
        background-color: #2D3748 !important;
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        padding: 14px 16px !important;
        border: 3px solid #000000 !important;
        text-align: center !important;
    }

    [data-testid="stDataFrame"] td,
    [data-testid="stTable"] td,
    .stDataFrame td,
    .stTable td {
        font-weight: 700 !important;
        color: #000000 !important;
        font-size: 17px !important;
        padding: 12px 16px !important;
        border: 2px solid #000000 !important;
        background-color: #FFFFFF !important;
    }

    [data-testid="stDataFrame"] tr:nth-child(even) td,
    .stDataFrame tr:nth-child(even) td {
        background-color: #F1F5F9 !important;
    }

    .custom-table-wrapper {
        width: 100%;
        overflow-x: auto !important;
        margin: 20px 0 !important;
        padding-bottom: 8px;
    }

    .custom-table {
        width: 100% !important;
        min-width: 100% !important;
        border-collapse: collapse !important;
        font-family: 'Inter', sans-serif !important;
        border: 4px solid #000000 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        background-color: #FFFFFF !important;
        table-layout: fixed !important;
    }

    .custom-table th,
    .custom-table td {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: anywhere !important;
    }

    .custom-table th {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        padding: 14px 16px !important;
        border: 3px solid #000000 !important;
        text-align: center !important;
    }

    .custom-table td {
        font-weight: 800 !important;
        color: #000000 !important;
        font-size: 17px !important;
        padding: 12px 16px !important;
        border: 2.5px solid #000000 !important;
        background-color: #FFFFFF !important;
        text-align: center !important;
    }

    .custom-table tr:nth-child(even) td {
        background-color: #F1F5F9 !important;
    }

    .metric-card {
        background: #FFFFFF; border: 3px solid #6B7280;
        border-radius: 12px; padding: 28px 20px; text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .metric-label { color: #374151; font-size: 18px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
    .metric-value { color: #1E3A8A; font-size: 70px; font-weight: 900; line-height: 1; }

    .narrative-box {
        background: #F9FAFB; border: 3px solid #9CA3AF;
        border-radius: 12px; padding: 24px 28px; margin: 20px 0;
        color: #000000; line-height: 1.8; font-size: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .narrative-box h4 { color: #1E3A8A !important; margin-top: 0; font-size: 22px !important; font-weight: 900 !important; text-transform: uppercase; }

    .info-card {
        background: #F8F9FA; border-left: 6px solid #1E3A8A;
        padding: 20px 24px; margin: 15px 0; border-radius: 8px;
        color: #111827; font-size: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .info-card h4 { margin-top: 0; font-weight: 800; }

    div[data-testid="stSidebar"] a {
        font-size: 19px !important; color: #1F2937 !important;
        font-weight: 600; text-decoration: none !important;
    }

    .footer-text { font-size: 1.1rem !important; color: #000000 !important; }
    [data-testid="stHeaderActionElements"] { display: none !important; }

    @media (max-width: 1200px) {
        html, body, [class*="css"] {
            font-size: 16px !important;
        }
        .custom-table th, .custom-table td {
            font-size: 15px !important;
            padding: 10px 12px !important;
        }
        .metric-label { font-size: 16px !important; }
        .metric-value { font-size: 60px !important; }
    }

    @media (max-width: 900px) {
        html, body, [class*="css"] {
            font-size: 15px !important;
        }
        #global-header {
            padding: 14px 16px !important;
            height: auto !important;
            flex-wrap: wrap;
            justify-content: space-between;
        }
        .g-title {
            font-size: 1.05rem !important;
        }
        [data-testid="stMainBlockContainer"] {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 100px !important;
        }
        section.main > div {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .stButton > button {
            font-size: 0.95rem !important;
        }
        .sidebar-toggle-button {
            max-width: 100% !important;
        }
    }

    @media (max-width: 640px) {
        html, body, [class*="css"] {
            font-size: 14px !important;
        }
        .g-title {
            font-size: 0.98rem !important;
        }
        .custom-table th, .custom-table td {
            font-size: 14px !important;
            padding: 8px 10px !important;
        }
        .metric-label { font-size: 15px !important; }
        .metric-value { font-size: 50px !important; }
        .top-action-bar {
            gap: 12px;
        }
    }

    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stMainBlockContainer"] { padding-top: 0 !important; max-width: 100% !important; width: 100% !important; }
        #global-header { position: relative !important; box-shadow: none !important; background: linear-gradient(135deg, #1E3A8A 0%, #11224D 100%) !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        [data-testid="stDataFrame"] th, [data-testid="stTable"] th, .custom-table th { background-color: #1E3A8A !important; color: #FFFFFF !important; border: 3px solid #000000 !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        [data-testid="stDataFrame"] td, [data-testid="stTable"] td, .custom-table td { background-color: #FFFFFF !important; border: 2.5px solid #000000 !important; color: #000000 !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        [data-testid="stDataFrame"] tr:nth-child(even) td, [data-testid="stTable"] tr:nth-child(even) td, .custom-table tr:nth-child(even) td { background-color: #F1F5F9 !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    }
    </style>

    <div id="global-header">
        <span style="font-size: 36px; margin-right: 18px;">🌀</span>
        <h1 class="g-title">SISTEM PREDIKSI SIKLON TROPIS UNTUK MITIGASI RISIKO BENCANA DI SUMATERA BARAT</h1>
    </div>
    """

    st.markdown(css_content.replace("{sidebar_css}", sidebar_css), unsafe_allow_html=True)

def render_sidebar_brand():
    if "sidebar_visible" not in st.session_state:
        st.session_state.sidebar_visible = True

    with st.container():
        cols = st.columns([4, 1], gap="small")
        with cols[0]:
            st.markdown(
                "<div class='top-action-bar'><div class='brand-label'>" \
                "<strong>Sistem Prediksi Siklon Tropis</strong> — Navigasi Mobile Friendly</div></div>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            if st.session_state.sidebar_visible:
                if st.button("✕ Sembunyikan Menu", key="hide_sidebar_btn", help="Sembunyikan panel navigasi", use_container_width=True):
                    st.session_state.sidebar_visible = False
                    st.rerun()
            else:
                if st.button("☰ Tampilkan Menu", key="show_sidebar_btn", help="Tampilkan panel navigasi", use_container_width=True):
                    st.session_state.sidebar_visible = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return # Hentikan rendering isi sidebar jika disembunyikan

    with st.sidebar:
        # Tombol untuk menyembunyikan sidebar
        if st.button("⬅️ SEMBUNYIKAN MENU", key="hide_sidebar_btn", use_container_width=True):
            st.session_state.sidebar_visible = False
            st.rerun()

        st.markdown(
            "<div style='margin: 10px 0 20px 10px; color: #4B5563; font-weight: 900; font-size: 1.2rem; text-transform: uppercase; letter-spacing: 0.1em;'>Menu Navigasi</div>",
            unsafe_allow_html=True
        )
        st.page_link("app.py", label="Beranda", icon="🏠")
        st.page_link("pages/1_Dashboard.py", label="Dashboard Prediksi", icon="🗺️")
        st.page_link("pages/Prediksi.py", label="Prediksi Siklon", icon="🔮")
        st.page_link("pages/Data_Siklon.py", label="Data Observasi", icon="📊")
        st.page_link("pages/3_Evaluasi.py", label="Evaluasi Akurasi", icon="📈")
        st.page_link("pages/4_Tentang.py", label="Tentang Model", icon="ℹ️")

        st.markdown("<div class='sidebar-spacer'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #9CA3AF; margin-bottom: 15px; margin-top: 0;'>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="background-color: #E0E7FF; padding: 16px; border-radius: 16px; border: 2px solid #BFDBFE; box-shadow: 0 4px 12px rgba(0,0,0,0.06); display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                <span style="font-size: 32px;">🌀</span>
                <div style="display: flex; flex-direction: column;">
                    <p style="color: #1E3A8A; font-size: 18px; margin: 0; font-weight: 900; line-height: 1.2;">Model LSTM</p>
                    <p style="color: #11224D; font-size: 15px; margin: 0; font-weight: 700;">Sliding Window Gabung 8</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_footer():
    st.markdown(
        """
        <div style="margin-top: 50px; padding: 30px 15px; border-top: 3px solid #1E3A8A; border-bottom: 3px solid #1E3A8A; background-color: #FFFFFF; text-align: center; font-family: 'Times New Roman', Times, serif; color: #000000;">
            <div style="max-width: 700px; margin: 0 auto;">
                <p style="font-weight: bold; font-size: 1.15rem; margin-bottom: 8px;">IKHWAN RAMADHAN – 22101152630411</p>
                <p style="margin-bottom: 6px; font-size: 1rem;">Program Studi Teknik Informatika – Fakultas Ilmu Komputer</p>
                <p style="margin-top: 0; font-size: 1rem;">Universitas Putra Indonesia “YPTK” Padang, 2026</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_custom_table(df, classes="custom-table"):
    html = df.to_html(index=False, classes=classes, escape=False)
    html = f"<div class='custom-table-wrapper'>{html}</div>"
    st.markdown(html, unsafe_allow_html=True)
