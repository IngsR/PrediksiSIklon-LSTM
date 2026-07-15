# app.py
import streamlit as st
import utils
import os

# Pastikan st.set_page_config berada di baris paling awal
st.set_page_config(
    page_title="Sistem Prediksi Siklon Tropis",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

utils.inject_custom_css()
utils.render_sidebar_brand()

# Animasi fade-in
st.markdown(
    """
    <style>
    .stApp { animation: fadeIn 0.5s ease-in; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 40px; border-radius: 16px; border-left: 6px solid #1E3A8A; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); margin-top: 10px;">
        <h2 style="color: #1E3A8A; font-weight: 900; margin-top: 0; font-size: 2rem;">Selamat Datang di Sistem Prediksi Siklon Tropis</h2>
        <p style="color: #374151; font-size: 1.15rem; line-height: 1.7; margin-top: 15px;">
            Aplikasi ini dirancang untuk memprediksi lintasan siklon tropis menggunakan model Long Short-Term Memory (LSTM). Sistem ini memfokuskan mitigasi risiko bencana khususnya di wilayah Sumatera Barat.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1.5, 1], gap="large")

with col1:
    st.markdown("### Silakan gunakan menu navigasi di sebelah kiri untuk mengakses fitur-fitur berikut:")
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; gap: 15px; margin-top: 20px;">
            <div style="background-color: #F8FAFC; padding: 15px 20px; border-radius: 10px; border: 1px solid #E2E8F0;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #0F172A;">🗺️ Dashboard</span>
                <p style="margin: 5px 0 0 0; color: #475569;">Visualisasi interaktif prediksi lintasan siklon di atas peta beserta metrik akurasinya (RMSE & MAE).</p>
            </div>
            <div style="background-color: #F8FAFC; padding: 15px 20px; border-radius: 10px; border: 1px solid #E2E8F0;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #0F172A;">📊 Data Siklon</span>
                <p style="margin: 5px 0 0 0; color: #475569;">Rincian data observasi mentah dari IBTrACS yang digunakan sebagai input model.</p>
            </div>
            <div style="background-color: #F8FAFC; padding: 15px 20px; border-radius: 10px; border: 1px solid #E2E8F0;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #0F172A;">📈 Evaluasi</span>
                <p style="margin: 5px 0 0 0; color: #475569;">Perbandingan detail koordinat aktual vs prediksi beserta grafik deviasi jarak pergerakan.</p>
            </div>
            <div style="background-color: #F8FAFC; padding: 15px 20px; border-radius: 10px; border: 1px solid #E2E8F0;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #0F172A;">ℹ️ Tentang</span>
                <p style="margin: 5px 0 0 0; color: #475569;">Informasi lebih lanjut mengenai hasil penelitian, peringkat model eksperimen, dan evaluasi overfitting.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.info("Pilih **Dashboard** untuk mulai melihat hasil prediksi.", icon="💡")

with col2:
    img_path = os.path.join("assets", "banner_beranda.png")
    if os.path.exists(img_path):
        # PERBAIKAN: Ganti use_container_width dengan width='stretch'
        st.image(img_path, width='stretch') 
    else:
        st.markdown(
            """
            <div style="height: 100%; min-height: 400px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1E3A8A 0%, #11224D 100%); border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.4); text-align: center; padding: 30px;">
                <div>
                    <div style="font-size: 80px; margin-bottom: 20px;">🌪️</div>
                    <h3 style="color: white; margin: 0; font-weight: 800;">[ TEMPAT GAMBAR SIKLON ]</h3>
                    <p style="color: #DBEAFE; margin-top: 10px;">Simpan gambar Anda di:<br><code>assets/banner_beranda.png</code></p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

utils.render_footer()