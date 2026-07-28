# 🌀 Sistem Prediksi Siklon Tropis (LSTM)

Sistem Prediksi Siklon Tropis adalah aplikasi berbasis web yang dirancang untuk memprediksi lintasan siklon tropis menggunakan model **Long Short-Term Memory (LSTM)**. Aplikasi ini dikembangkan sebagai bagian dari penelitian mitigasi risiko bencana, dengan fokus khusus pada wilayah Sumatera Barat.

Aplikasi ini mengintegrasikan pengolahan data spasial, pemodelan deret waktu (*time-series*), dan visualisasi peta interaktif untuk memberikan estimasi pergerakan siklon yang akurat.

---

## ✨ Fitur Utama

1.  **🔮 Prediksi Siklon**: Editor interaktif untuk memasukkan data observasi dan menghasilkan prediksi lintasan masa depan secara langsung.
2.  **🗺️ Dashboard Interaktif**: Visualisasi lintasan siklon di atas peta (Folium) lengkap dengan metrik akurasi (RMSE & MAE).
3.  **📊 Eksplorasi Data**: Akses ke rincian data observasi mentah dari dataset **IBTrACS**.
4.  **📈 Evaluasi Model**: Analisis mendalam perbandingan koordinat aktual vs prediksi serta grafik deviasi jarak.
5.  **ℹ️ Informasi Riset**: Dokumentasi hasil penelitian, peringkat model eksperimen, dan evaluasi performa (overfitting check).

---

## 🏗️ Struktur Proyek

```text
streamlit_app/
├── app.py                # Titik masuk utama aplikasi (Home)
├── utils.py              # Fungsi pembantu (CSS, komponen UI)
├── requirements.txt      # Daftar dependensi Python
├── .streamlit/           # Konfigurasi Streamlit (tema, layout)
├── assets/               # Aset visual (banner, grafik hasil riset)
├── data/                 # Dataset CSV (hasil training, observasi, evaluasi)
├── pages/                # Halaman-halaman fitur aplikasi
│   ├── 1_Dashboard.py
│   ├── 3_Evaluasi.py
│   ├── 4_Tentang.py
│   ├── Data_Siklon.py
│   └── Prediksi.py
├── prediction/           # Logika inti prediksi
│   ├── inference.py      # Proses load model dan kalkulasi prediksi
│   ├── analytics.py      # Metrik perhitungan (RMSE, MAE, Jarak)
│   ├── state.py          # Manajemen state aplikasi
│   └── models/           # Model LSTM (.keras) dan Scaler (.pkl)
└── .venv/                # Virtual Environment (disarankan)
```

---

## 🛠️ Teknologi yang Digunakan

-   **Bahasa Pemrograman**: Python 3.x
-   **Framework Web**: [Streamlit](https://streamlit.io/)
-   **Deep Learning**: TensorFlow & Keras (Model LSTM)
-   **Analisis Data**: Pandas, NumPy, Scikit-learn
-   **Visualisasi**: Folium (Peta), Matplotlib, Seaborn

---

## 🚀 Cara Instalasi & Menjalankan

Ikuti langkah-langkah di bawah ini untuk menyiapkan lingkungan pengembangan di mesin lokal Anda (Windows/Linux/MacOS).

### 1. Persiapan Lingkungan (Virtual Environment)
Disarankan untuk menggunakan *virtual environment* agar tidak terjadi konflik pustaka.

**Windows:**
```bash
# Membuat venv
python -m venv .venv

# Mengaktifkan venv
.venv\Scripts\activate
```

**Linux/MacOS:**
```bash
# Membuat venv
python3 -m venv .venv

# Mengaktifkan venv
source .venv/bin/activate
```

### 2. Instalasi Dependensi
Setelah venv aktif, instal semua pustaka yang diperlukan:
```bash
pip install -r requirements.txt
```

### 3. Menjalankan Aplikasi
Jalankan perintah berikut untuk membuka aplikasi di browser Anda:
```bash
streamlit run app.py
```
Aplikasi biasanya akan berjalan di `http://localhost:8501`.

---

## 📂 Alur Kerja Sistem (Arsitektur)

1.  **Input**: Pengguna memasukkan data observasi siklon (Latitude, Longitude, Kecepatan Angin, Tekanan) melalui halaman **Prediksi**.
2.  **Preprocessing**: Data dinormalisasi menggunakan `target_scaler_gab.pkl` agar sesuai dengan skala input model LSTM.
3.  **Inference**: Model `gab_window8.keras` memproses urutan data (windowing) untuk memprediksi koordinat langkah berikutnya.
4.  **Post-processing**: Hasil prediksi dikembalikan ke skala aslinya (*inverse transform*).
5.  **Output**: Visualisasi lintasan ditampilkan pada peta interaktif dan tabel hasil evaluasi.

---

## 📝 Catatan Pengembangan

-   **Model**: Model yang digunakan adalah LSTM dengan *window size* 8, yang berarti membutuhkan minimal 8 data observasi sebelumnya untuk menghasilkan prediksi yang optimal.
-   **Dataset**: Dataset pelatihan berasal dari **IBTrACS** yang telah difilter untuk wilayah koordinat sekitar Sumatera Barat.

---

## 👨‍💻 Penulis

**Ikhwan Ramadhan**  
*Program ini dikembangkan untuk keperluan Kelengkapan Skripsi.*

---
*© 2024 - Sistem Prediksi Siklon Tropis*
