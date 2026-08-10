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
    """Inject global CSS and fixed header."""
    
    css_content = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* ========== BASE RESET ========== */
    *, *::before, *::after {
        box-sizing: border-box !important;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 16px !important;
        color: #1F2937 !important;
        font-weight: 500;
    }

    .main { background-color: #FFFFFF; }

    /* ========== HIDE DEFAULT STREAMLIT NAV & MAKE HEADER TRANSPARENT ========== */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] * {
        pointer-events: auto !important;
    }
    [data-testid="stSidebarNav"], nav[data-testid="stSidebarNav"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    [data-testid="stHeaderActionElements"] { display: none !important; }

    /* ========== GLOBAL HEADER (BANNER) ========== */
    #global-header {
        width: 100%;
        background: linear-gradient(135deg, #1E3A8A 0%, #11224D 100%);
        color: white;
        display: flex;
        align-items: center;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.15);
        gap: 14px;
        margin-top: 0px !important;
        margin-bottom: 24px;
    }
    .g-header-icon {
        font-size: 28px;
        flex-shrink: 0;
        line-height: 1;
    }
    .g-title {
        margin: 0;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        line-height: 1.3;
    }

    /* ========== MAIN CONTENT AREA ========== */
    [data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        padding: 4.5rem 2rem 2rem 2rem !important;
    }
    section.main > div {
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #E5E7EB !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0px !important;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 2.2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Sidebar nav link items */
    [data-testid="stSidebar"] [data-testid="stPageLink"],
    [data-testid="stSidebar"] .stPageLink {
        border-radius: 10px !important;
        margin: 6px 12px !important; /* Larger margin for comfortable spacing */
        padding: 6px 6px !important; /* Larger padding for effortless clicking/tapping */
        transition: all 0.2s ease !important;
        border: 1px solid transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
        background-color: #EFF6FF !important; /* Beautiful soft blue highlight */
        border: 1px solid #BFDBFE !important;
        transform: translateX(4px); /* Modern subtle hover slide transition */
    }
    [data-testid="stSidebar"] a {
        font-size: 21px !important; /* Maximum accessibility for all users */
        color: #1E293B !important; 
        font-weight: 700 !important;
        text-decoration: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] span,
    [data-testid="stSidebar"] .stPageLink span {
        font-size: 23px !important; 
    }

    /* Sidebar collapsed control (hamburger) — aesthetic styling */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        top: 16px !important;
        left: 16px !important;
        z-index: 999999 !important;
        background-color: #1E3A8A !important;
        border-radius: 8px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        width: auto !important;
        min-width: 80px !important;
        height: 38px !important;
        padding: 0 12px !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    [data-testid="collapsedControl"]::after,
    [data-testid="stSidebarCollapsedControl"]::after {
        content: "Menu";
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: white;
    }

    [data-testid="collapsedControl"]:hover,
    [data-testid="stSidebarCollapsedControl"]:hover {
        background-color: #11224D !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(30, 58, 138, 0.4) !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] svg {
        fill: white !important;
        color: white !important;
        width: 18px !important;
        height: 18px !important;
    }

    /* ========== BUTTONS ========== */
    .stButton > button {
        min-height: 42px !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    .stButton > button:focus-visible {
        outline: 3px solid rgba(59, 130, 246, 0.5) !important;
    }

    /* ========== DATA TABLES ========== */
    [data-testid="stDataFrame"] table,
    [data-testid="stTable"] table,
    .stDataFrame table,
    .stTable table,
    .custom-table {
        width: 100% !important;
        border-collapse: collapse !important;
    }
    .custom-table-wrapper,
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    [data-testid="stDataFrame"] th,
    [data-testid="stTable"] th,
    .stDataFrame th,
    .stTable th {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        padding: 10px 12px !important;
        border: 1px solid #1E3A8A !important;
        text-align: center !important;
    }

    [data-testid="stDataFrame"] td,
    [data-testid="stTable"] td,
    .stDataFrame td,
    .stTable td {
        font-weight: 600 !important;
        color: #1F2937 !important;
        font-size: 14px !important;
        padding: 8px 12px !important;
        border: 1px solid #E5E7EB !important;
        background-color: #FFFFFF !important;
    }

    [data-testid="stDataFrame"] tr:nth-child(even) td,
    .stDataFrame tr:nth-child(even) td {
        background-color: #F8FAFC !important;
    }

    /* ========== CUSTOM TABLE ========== */
    .custom-table-wrapper {
        width: 100%;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        margin: 16px 0 !important;
        padding-bottom: 4px;
    }

    .custom-table {
        width: 100% !important;
        border-collapse: collapse !important;
        font-family: 'Inter', sans-serif !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06) !important;
        background-color: #FFFFFF !important;
        table-layout: auto !important;
    }

    .custom-table th,
    .custom-table td {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    .custom-table th {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 13px !important;
        padding: 10px 12px !important;
        border: 1px solid #1E3A8A !important;
        text-align: center !important;
    }

    .custom-table td {
        font-weight: 600 !important;
        color: #0F172A !important;
        font-size: 13px !important;
        padding: 8px 10px !important;
        border: 1px solid #E5E7EB !important;
        background-color: #FFFFFF !important;
        text-align: center !important;
    }

    .custom-table tr:nth-child(even) td {
        background-color: #F8FAFC !important;
    }

    /* ========== CARDS & PANELS ========== */
    .page-panel {
        border-radius: 16px !important;
        padding: 20px !important;
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06) !important;
        margin-bottom: 20px !important;
    }

    .map-panel {
        min-height: 420px !important;
        border-radius: 16px !important;
        overflow: hidden !important;
    }

    .metric-card {
        background: #FFFFFF;
        border: 2px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        transition: box-shadow 0.2s ease;
    }
    .metric-card:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }
    .metric-label {
        color: #6B7280;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #1E3A8A;
        font-size: 48px;
        font-weight: 900;
        line-height: 1;
    }

    .narrative-box {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #1E3A8A;
        border-radius: 10px;
        padding: 20px 24px;
        margin: 16px 0;
        color: #1F2937;
        line-height: 1.7;
        font-size: 15px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .narrative-box h4 {
        color: #1E3A8A !important;
        margin-top: 0;
        font-size: 18px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
    }

    .info-card {
        background: #F8F9FA;
        border-left: 4px solid #1E3A8A;
        padding: 16px 20px;
        margin: 12px 0;
        border-radius: 8px;
        color: #1F2937;
        font-size: 15px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .info-card h4 { margin-top: 0; font-weight: 800; }

    .footer-text { font-size: 0.95rem !important; color: #1F2937 !important; }

    .prediksi-table th,
    .prediksi-table td {
        font-size: 14px !important;
    }

    /* ========== RESPONSIVE: TABLET ========== */
    @media (max-width: 900px) {
        html, body, [class*="css"] {
            font-size: 15px !important;
        }
        #global-header {
            padding: 12px 16px !important;
        }
        .g-header-icon { font-size: 22px; }
        .g-title { font-size: 0.82rem !important; }

        [data-testid="stMainBlockContainer"] {
            padding: 4.5rem 1rem 1rem 1rem !important;
        }
        [data-testid="stSidebar"] a {
            font-size: 18px !important;
        }
        .metric-value { font-size: 40px !important; }
        .metric-label { font-size: 12px !important; }
        .prediksi-table th,
        .prediksi-table td {
            font-size: 13px !important;
        }
    }

    /* ========== RESPONSIVE: MOBILE ========== */
    @media (max-width: 640px) {
        html, body, [class*="css"] {
            font-size: 14px !important;
        }
        #global-header {
            padding: 12px !important;
            gap: 10px;
        }
        .g-header-icon { font-size: 20px; }
        .g-title { font-size: 0.72rem !important; }

        [data-testid="stMainBlockContainer"] {
            padding: 4.5rem 0.75rem 1rem 0.75rem !important;
        }
        [data-testid="stSidebar"] a {
            font-size: 17px !important;
        }
        .stButton > button {
            min-height: 38px !important;
            font-size: 0.85rem !important;
        }

        .custom-table th, .custom-table td,
        .prediksi-table th, .prediksi-table td {
            font-size: 11px !important;
            padding: 5px 6px !important;
        }
        .custom-table {
            font-size: 11px !important;
        }

        .metric-value { font-size: 32px !important; }
        .metric-label { font-size: 11px !important; }

        .narrative-box {
            padding: 14px 16px !important;
            font-size: 13px !important;
        }
        .narrative-box h4 { font-size: 15px !important; }

        .page-panel {
            padding: 14px !important;
            border-radius: 12px !important;
        }
        .map-panel {
            min-height: 300px !important;
        }
    }

    /* ========== PRINT ========== */
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stMainBlockContainer"] { padding-top: 0 !important; max-width: 100% !important; }
        #global-header { position: relative !important; box-shadow: none !important; }
        .custom-table th { background-color: #1E3A8A !important; color: #FFFFFF !important; }
        .custom-table td { background-color: #FFFFFF !important; color: #000000 !important; }
    }
    </style>

    <div id="global-header">
        <span class="g-header-icon">🌀</span>
        <h1 class="g-title">Sistem Prediksi Siklon Tropis — Mitigasi Risiko Bencana Sumatera Barat</h1>
    </div>
    """

    st.markdown(css_content, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar navigation using native Streamlit sidebar. No manual toggle needed."""

    with st.sidebar:
        # Brand / title - Premium design with underline
        st.markdown(
            "<div style='padding: 8px 12px 16px 12px; border-bottom: 2px solid #E2E8F0; margin-bottom: 16px;'>"
            "<p style='margin:0; font-size:1.05rem; font-weight:800; color:#1E3A8A; "
            "text-transform:uppercase; letter-spacing:0.06em;'>🧭 Menu Navigasi</p>"
            "</div>",
            unsafe_allow_html=True
        )

        # Navigation links
        st.page_link("app.py", label="Beranda", icon="🏠")
        st.page_link("pages/1_Dashboard.py", label="Dashboard Prediksi", icon="🗺️")
        st.page_link("pages/Prediksi.py", label="Prediksi Siklon", icon="🔮")
        st.page_link("pages/Data_Siklon.py", label="Data Observasi", icon="📊")
        st.page_link("pages/3_Evaluasi.py", label="Evaluasi Akurasi", icon="📈")
        st.page_link("pages/4_Tentang.py", label="Tentang Model", icon="ℹ️")

        # Spacer + divider
        st.markdown("<div style='flex-grow:1; min-height:30px;'></div>", unsafe_allow_html=True)
        st.divider()

        # Model badge - Premium Dark Gradient (High Contrast & Matches Banner)
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #1E3A8A 0%, #11224D 100%);
                        padding: 16px; border-radius: 14px; border: 1px solid #1E3A8A;
                        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.15);
                        display: flex; align-items: center; gap: 14px; margin: 0 12px;">
                <span style="font-size: 32px; line-height:1; flex-shrink: 0;">🌀</span>
                <div>
                    <p style="color: #FFFFFF; font-size: 15px; margin: 0; font-weight: 800; line-height: 1.2; letter-spacing: 0.02em;">MODEL LSTM</p>
                    <p style="color: #93C5FD; font-size: 12.5px; margin: 4px 0 0 0; font-weight: 600; line-height: 1.3;">Sliding Window Gabung 8</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# Keep backward compatibility alias
render_sidebar_brand = render_sidebar


def render_footer():
    st.markdown(
        """
        <div style="margin-top: 40px; padding: 24px 16px; border-top: 2px solid #1E3A8A;
                    background-color: #F8F9FA; text-align: center; font-family: 'Inter', sans-serif; color: #1F2937;">
            <div style="max-width: 600px; margin: 0 auto;">
                <p style="font-weight: 800; font-size: 0.95rem; margin-bottom: 4px; color: #1E3A8A;">IKHWAN RAMADHAN – 22101152630411</p>
                <p style="margin-bottom: 2px; font-size: 0.85rem; color: #4B5563;">Program Studi Teknik Informatika – Fakultas Ilmu Komputer</p>
                <p style="margin-top: 0; font-size: 0.85rem; color: #4B5563;">Universitas Putra Indonesia "YPTK" Padang, 2026</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_custom_table(df, classes="custom-table"):
    html = df.to_html(index=False, classes=classes, escape=False)
    html = f"<div class='custom-table-wrapper'>{html}</div>"
    st.markdown(html, unsafe_allow_html=True)

