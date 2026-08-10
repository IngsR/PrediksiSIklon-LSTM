import streamlit as st
import pandas as pd
import utils

# =====================================================
###### 1. KONFIGURASI HALAMAN ######
# =====================================================
st.set_page_config(page_title="Data Siklon", page_icon="📊", layout="wide")
utils.inject_custom_css()
utils.render_sidebar()

st.markdown("### DATA OBSERVASI SIKLON")

# =====================================================
###### 2. LOAD DATA OBSERVASI LENGKAP ######
# =====================================================
df = utils.load_observasi_data()
all_sids = sorted(df["SID"].unique().tolist())

# =====================================================
###### 3. INISIALISASI SESSION STATE ######
# =====================================================
if "selected_sid" not in st.session_state:
    st.session_state.selected_sid = None

# =====================================================
###### 4. SEARCHBOX (PENCARIAN MANUAL) ######
# =====================================================
try:
    from streamlit_searchbox import st_searchbox
except ImportError:
    st.error("Package 'streamlit-searchbox' belum terinstall. Jalankan: pip install streamlit-searchbox")
    st.stop()

def search_sid(searchterm: str) -> list[str]:
    """Menghasilkan daftar SID yang mengandung teks pencarian."""
    if not searchterm:
        return []
    term = searchterm.upper()
    return [sid for sid in all_sids if term in sid.upper()]

# Komponen searchbox
search_value = st_searchbox(
    search_sid,
    placeholder="Ketik ID Siklon (misal: 1980002...)",
    key="searchbox_obs",
    clear_on_submit=False,
    default=st.session_state.selected_sid,
)

# Jika searchbox mengembalikan ID yang valid, perbarui session state
if search_value is not None and search_value != st.session_state.selected_sid:
    st.session_state.selected_sid = search_value
    st.rerun()

# =====================================================
###### 5. DROPDOWN SEMUA ID SIKLON (DI BAWAH SEARCHBOX) ######
# =====================================================
default_index = 0
if st.session_state.selected_sid is not None and st.session_state.selected_sid in all_sids:
    default_index = all_sids.index(st.session_state.selected_sid)

selected_sid_dropdown = st.selectbox(
    "Atau pilih dari daftar semua ID siklon:",
    options=all_sids,
    index=default_index,
    key="selectbox_obs",
)

# Jika dropdown berubah, perbarui session state
if selected_sid_dropdown != st.session_state.selected_sid:
    st.session_state.selected_sid = selected_sid_dropdown
    st.rerun()

# Gunakan nilai final dari session state
final_sid = st.session_state.selected_sid

# =====================================================
###### 6. TAMPILKAN DATA JIKA SID SUDAH DIPILIH ######
# =====================================================
if final_sid is None:
    st.info("Silakan pilih ID siklon melalui pencarian atau dropdown di atas.")
else:
    sid_data = df[df["SID"] == final_sid].copy().sort_values("ISO_TIME").reset_index(drop=True)

    if sid_data.empty:
        st.warning(f"Tidak ada data untuk SID `{final_sid}`.")
    else:
        # ---------- 6a. Informasi Ringkas ----------
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                **🆔 ID Siklon** : `{final_sid}`
                **⏱️ Interval** : `3 Jam`
                """)
            with col2:
                periode_mulai = sid_data["ISO_TIME"].min().strftime("%d/%m/%Y")
                periode_selesai = sid_data["ISO_TIME"].max().strftime("%d/%m/%Y")
                durasi_jam = (sid_data["ISO_TIME"].max() - sid_data["ISO_TIME"].min()).total_seconds() / 3600
                st.markdown(f"""
                **📅 Periode** : `{periode_mulai} – {periode_selesai}`
                **⏳ Durasi** : `{int(durasi_jam)} jam`
                **📌 Jumlah titik** : `{len(sid_data)}`
                """)

        # ---------- 6b. Tabel Data Observasi Lengkap ----------

        # Fungsi badge warna untuk Status Wind & Status Pres
        def badge_status(val):
            val_str = str(val).strip()
            if val_str == "Asli":
                return (
                    '<span style="background:#D1FAE5;color:#065F46;border:2px solid #059669;'
                    'border-radius:6px;padding:3px 10px;font-weight:900;font-size:15px;">'
                    '✅ Asli</span>'
                )
            elif val_str == "Perbaikan":
                return (
                    '<span style="background:#FEF3C7;color:#92400E;border:2px solid #D97706;'
                    'border-radius:6px;padding:3px 10px;font-weight:900;font-size:15px;">'
                    ' Perbaikan</span>'
                )
            return val_str

        # Susun kolom yang akan ditampilkan
        tabel_tampil = sid_data[[
            "ISO_TIME", "LAT", "LON",
            "WMO_WIND", "wind_imputation",
            "WMO_PRES", "pres_imputation",
            "Status Wind", "Status Pres"
        ]].copy()

        # Format nilai
        tabel_tampil["ISO_TIME"] = tabel_tampil["ISO_TIME"].dt.strftime("%d/%m/%Y %H:%M")
        tabel_tampil["LAT"] = tabel_tampil["LAT"].map(lambda x: f"{x:.4f}°" if pd.notna(x) else "-")
        tabel_tampil["LON"] = tabel_tampil["LON"].map(lambda x: f"{x:.4f}°" if pd.notna(x) else "-")
        tabel_tampil["WMO_WIND"] = tabel_tampil["WMO_WIND"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
        tabel_tampil["WMO_PRES"] = tabel_tampil["WMO_PRES"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
        tabel_tampil["wind_imputation"] = tabel_tampil["wind_imputation"].fillna("-")
        tabel_tampil["pres_imputation"] = tabel_tampil["pres_imputation"].fillna("-")

        # Terapkan badge warna pada kolom status
        tabel_tampil["Status Wind"] = tabel_tampil["Status Wind"].apply(badge_status)
        tabel_tampil["Status Pres"] = tabel_tampil["Status Pres"].apply(badge_status)

        # Ganti nama kolom ke bahasa Indonesia yang informatif
        tabel_tampil.columns = [
            "Waktu", "LAT (°)", "LON (°)",
            "Wind (knot)", "Metode Imputasi Angin",
            "Pressure (hPa)", "Metode Imputasi Tekanan",
            "Status Angin", "Status Tekanan"
        ]

        utils.render_custom_table(tabel_tampil)

        # ---------- 6c. Catatan Sumber Data ----------
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 1.2rem; border-radius: 10px; border-left: 4px solid #1E3A8A; margin-top: 20px;">
            <h5 style="color: #1E3A8A; margin-top: 0;">📋 Sumber Data & Keterangan Kolom</h5>
            <p style="margin-bottom: 0.5rem; line-height: 1.6;">
                Data di atas adalah data observasi siklon yang digunakan sebagai input model LSTM.
                Setiap baris merepresentasikan posisi dan kondisi atmosfer siklon pada satu titik waktu (interval 3 jam).
            </p>
            <ul style="margin-bottom: 0; line-height: 2;">
                <li><strong>Wind (knot)</strong> – Kecepatan angin maksimum (WMO).</li>
                <li><strong>Pressure (hPa)</strong> – Tekanan udara minimum di pusat siklon (WMO).</li>
                <li><strong>Metode Imputasi</strong> – Teknik pengisian data hilang: <em>Original</em>, <em>Linear</em>, <em>Forward/Backward</em>, atau <em>Median</em>.</li>
                <li>
                    <strong>Status</strong> –
                    <span style="background:#D1FAE5;color:#065F46;border:2px solid #059669;border-radius:6px;padding:2px 8px;font-weight:900;">✅ Asli</span>
                    = data asli observasi; &nbsp;
                    <span style="background:#FEF3C7;color:#92400E;border:2px solid #D97706;border-radius:6px;padding:2px 8px;font-weight:900;"> Perbaikan</span>
                    = nilai diisi melalui imputasi karena data hilang/kosong.
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# =====================================================
###### 7. FOOTER ######
# =====================================================
utils.render_footer()
