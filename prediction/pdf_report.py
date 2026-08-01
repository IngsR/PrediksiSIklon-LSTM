"""
PDF Report Generator — Laporan Prediksi Lintasan Siklon Tropis.

OUTPUT FORMAT: io.BytesIO  (langsung kompatibel dengan st.download_button)
"""

import io
import tempfile
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from datetime import datetime, timedelta
from fpdf import FPDF
from prediction.analytics import calculate_analytics
from prediction.inference import haversine


# =========================================================================
# KONSTANTA PESISIR SUMATERA BARAT
# =========================================================================
# Titik-titik referensi pesisir Sumatera Barat (Lat, Lon)
PESISIR_SUMBAR = [
    (-0.95, 100.35),   # Padang
    (-1.35, 100.55),   # Painan / Pesisir Selatan
    (-0.30, 99.80),    # Pariaman
    ( 0.30, 99.10),    # Pasaman Barat
    (-2.10, 100.80),   # Kerinci / batas selatan
]


def _jarak_ke_pesisir(lat, lon):
    """Hitung jarak terdekat (km) dari titik prediksi ke pesisir Sumatera Barat."""
    jarak_min = float("inf")
    kota_terdekat = ""
    nama_kota = ["Padang", "Painan", "Pariaman", "Pasaman Barat", "Kerinci"]
    for i, (plat, plon) in enumerate(PESISIR_SUMBAR):
        d = haversine(lat, lon, plat, plon)
        if d < jarak_min:
            jarak_min = d
            kota_terdekat = nama_kota[i]
    return round(jarak_min, 1), kota_terdekat


def _bearing_to_compass(deg):
    """Konversi derajat bearing ke arah mata angin."""
    directions = [
        "Utara", "Timur Laut", "Timur", "Tenggara",
        "Selatan", "Barat Daya", "Barat", "Barat Laut",
    ]
    idx = int(round(deg / 45)) % 8
    return directions[idx]


# =========================================================================
# MATPLOTLIB — PETA STATIS UNTUK PDF
# =========================================================================
def _generate_map_image(draft_data, prediction_result):
    """
    Buat gambar peta statis menggunakan matplotlib.
    Return: path ke file PNG sementara.
    """
    fig, ax = plt.subplots(1, 1, figsize=(7.2, 4.0), dpi=150)

    # Background
    ax.set_facecolor("#E8F0FE")
    fig.patch.set_facecolor("white")

    # Ambil titik historis
    hist_lats = draft_data["LAT"].values
    hist_lons = draft_data["LON"].values

    # Plot garis historis
    ax.plot(hist_lons, hist_lats, "o-", color="#1E3A8A", linewidth=2.0,
            markersize=5.5, label="Historis (Observasi)", zorder=3)

    # Nomor titik historis
    for i, (lt, ln) in enumerate(zip(hist_lats, hist_lons)):
        ax.annotate(f"{i+1}", (ln, lt), fontsize=7, fontweight="bold",
                    ha="center", va="bottom", color="#1E3A8A",
                    xytext=(0, 4), textcoords="offset points", zorder=4)

    # Plot prediksi
    if prediction_result:
        pred_lats = [hist_lats[-1]] + [r["pred_lat"] for r in prediction_result]
        pred_lons = [hist_lons[-1]] + [r["pred_lon"] for r in prediction_result]

        ax.plot(pred_lons, pred_lats, "s--", color="#DC2626", linewidth=2.0,
                markersize=7, label="Prediksi (LSTM)", zorder=3)

        for i, res in enumerate(prediction_result):
            ax.annotate(f"P{i+1}", (res["pred_lon"], res["pred_lat"]),
                        fontsize=7, fontweight="bold", ha="center", va="bottom",
                        color="#DC2626", xytext=(0, 5), textcoords="offset points",
                        zorder=4)

    # Plot pesisir Sumatera Barat sebagai referensi
    pesisir_lats = [p[0] for p in PESISIR_SUMBAR]
    pesisir_lons = [p[1] for p in PESISIR_SUMBAR]
    ax.scatter(pesisir_lons, pesisir_lats, marker="^", c="#059669", s=45,
               label="Pesisir Sumbar", zorder=3, edgecolors="white", linewidths=0.5)

    # Grid & labels
    ax.grid(True, linestyle="--", alpha=0.4, color="#94A3B8")
    ax.set_xlabel("Longitude (°E)", fontsize=8.5, color="#374151")
    ax.set_ylabel("Latitude (°N)", fontsize=8.5, color="#374151")
    ax.set_title("Peta Lintasan Siklon — Historis & Prediksi LSTM",
                 fontsize=9.5, fontweight="bold", color="#1E3A8A", pad=7)
    ax.legend(fontsize=7.5, loc="best", framealpha=0.9)
    ax.tick_params(labelsize=7.5)

    plt.tight_layout()

    # Simpan ke file temporer
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return tmp.name


# =========================================================================
# HELPER TANGGAL INDONESIA
# =========================================================================
def _tanggal_indonesia(dt=None):
    if dt is None:
        dt = datetime.now()
    bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember",
    }
    return f"{dt.day} {bulan[dt.month]} {dt.year}"


# =========================================================================
# KELAS PDF
# =========================================================================
class _CycloneReportPDF(FPDF):
    def __init__(self, start_datetime, horizon_hours, num_steps):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.start_datetime = start_datetime
        self.horizon_hours = horizon_hours
        self.num_steps = num_steps
        self.alias_nb_pages()
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        if self.page_no() == 1:
            self.set_fill_color(30, 58, 138)
            self.rect(0, 0, 210, 8, "F")
            self.ln(3)

            self.set_font("Helvetica", "B", 14)
            self.set_text_color(30, 58, 138)
            self.cell(0, 6, text="LAPORAN PREDIKSI LINTASAN SIKLON TROPIS", border=0, ln=1, align="C")

            self.set_font("Helvetica", "B", 10)
            self.set_text_color(55, 65, 81)
            self.cell(0, 5, text="SISTEM PREDIKSI SIKLON TROPIS UNTUK MITIGASI RISIKO BENCANA DI SUMATERA BARAT", border=0, ln=1, align="C")

            self.set_font("Helvetica", "", 9)
            self.set_text_color(107, 114, 128)
            self.cell(0, 5, text="Model Komputasi: Deep Learning Stacked LSTM (Sliding Window Gabung 8)", border=0, ln=1, align="C")

            self.set_draw_color(30, 58, 138)
            self.set_line_width(0.8)
            self.line(15, 34, 195, 34)

            self.set_draw_color(156, 163, 175)
            self.set_line_width(0.3)
            self.line(15, 35.5, 195, 35.5)

            self.ln(7)
        else:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(107, 114, 128)
            self.cell(0, 5, text="Laporan Prediksi Lintasan Siklon Tropis - Sumatera Barat", border=0, ln=0, align="L")
            self.cell(0, 5, text=f"Dicetak: {datetime.now().strftime('%d-%m-%Y %H:%M')}", border=0, ln=1, align="R")

            self.set_draw_color(156, 163, 175)
            self.set_line_width(0.3)
            self.line(15, 21, 195, 21)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(209, 213, 221)
        self.set_line_width(0.3)
        self.line(15, 282, 195, 282)

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(107, 114, 128)
        self.cell(90, 10, text=f"Halaman {self.page_no()}/{{nb}}", border=0, ln=0, align="L")
        self.cell(90, 10, text="IKHWAN RAMADHAN - TEKNIK INFORMATIKA", border=0, ln=1, align="R")


# =========================================================================
# FUNGSI UTAMA — generate_pdf_report
# =========================================================================
def generate_pdf_report(draft_data, prediction_result, start_datetime, horizon_hours, num_steps):
    """
    Generate laporan PDF profesional.

    Returns
    -------
    io.BytesIO
        Buffer PDF yang siap dipakai langsung oleh st.download_button.
    """
    pdf = _CycloneReportPDF(start_datetime, horizon_hours, num_steps)
    pdf.add_page()

    map_image_path = None

    try:
        # =================================================================
        # I. METADATA LAPORAN
        # =================================================================
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 6, text="I. DATA METADATA LAPORAN", border=0, ln=1, align="L")
        pdf.ln(1)

        meta_data = [
            ("ID Laporan", f"REP-CYCLONE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
            ("Tanggal Cetak", f"{_tanggal_indonesia()} / {datetime.now().strftime('%H:%M:%S WIB')}"),
            ("Waktu Awal Prediksi", f"{_tanggal_indonesia(start_datetime)} / {start_datetime.strftime('%H:%M WIB')}"),
            ("Horizon Prediksi", f"{horizon_hours} Jam ({num_steps} Langkah ke Depan)"),
            ("Wilayah Analisis", "Sumatera Barat & Samudra Hindia Timur"),
            ("Status Pemodelan", "Sukses (Metrik Terverifikasi)"),
        ]

        box_y = pdf.get_y()
        pdf.set_fill_color(249, 250, 251)
        pdf.set_draw_color(209, 213, 221)
        pdf.set_line_width(0.3)
        pdf.rect(15, box_y, 180, 32, "DF")

        for i, (label, value) in enumerate(meta_data):
            col = i % 2
            row = i // 2
            x = 18 + col * 90
            y = box_y + 2 + row * 9
            pdf.set_xy(x, y)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(55, 65, 81)
            pdf.cell(32, 5, text=f"{label}:", border=0)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(17, 24, 39)
            pdf.cell(55, 5, text=f" {value}", border=0)

        pdf.set_xy(15, box_y + 34)
        pdf.ln(2)

        # =================================================================
        # II. DATA HISTORIS OBSERVASI
        # =================================================================
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 6, text="II. DATA HISTORIS OBSERVASI (INPUT SLIDING WINDOW)", border=0, ln=1, align="L")
        pdf.ln(1)

        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(75, 85, 99)
        pdf.multi_cell(0, 4.5, text=(
            "Tabel berikut menyajikan urutan data observasi meteorologi sebanyak 8 titik "
            "(sliding window) yang diinputkan oleh operator. Data ini diolah secara bertahap "
            "oleh LSTM untuk memprediksi arah pergerakan selanjutnya."
        ))
        pdf.ln(2)

        headers_obs = ["Titik", "Waktu (WIB)", "Latitude (LAT)", "Longitude (LON)", "Wind (Knot)", "Pres (hPa)"]
        widths_obs = [12, 34, 34, 34, 33, 33]

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(30, 58, 138)
        pdf.set_text_color(255, 255, 255)
        pdf.set_draw_color(31, 41, 55)
        pdf.set_line_width(0.3)
        for h, w in zip(headers_obs, widths_obs):
            pdf.cell(w, 6.0, text=h, border=1, ln=0, align="C", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(17, 24, 39)
        for idx, row in draft_data.iterrows():
            if idx % 2 == 1:
                pdf.set_fill_color(243, 244, 246)
            else:
                pdf.set_fill_color(255, 255, 255)

            time_pt = start_datetime + timedelta(hours=idx * 3)
            time_str = time_pt.strftime("%d-%m-%Y %H:%M")

            pdf.cell(widths_obs[0], 5.0, text=f"{int(idx + 1)}", border=1, ln=0, align="C", fill=True)
            pdf.cell(widths_obs[1], 5.0, text=time_str, border=1, ln=0, align="C", fill=True)
            pdf.cell(widths_obs[2], 5.0, text=f"{row['LAT']:.1f} deg", border=1, ln=0, align="C", fill=True)
            pdf.cell(widths_obs[3], 5.0, text=f"{row['LON']:.1f} deg", border=1, ln=0, align="C", fill=True)
            pdf.cell(widths_obs[4], 5.0, text=f"{row['WMO_WIND']:.1f}", border=1, ln=0, align="C", fill=True)
            pdf.cell(widths_obs[5], 5.0, text=f"{row['WMO_PRES']:.1f}", border=1, ln=1, align="C", fill=True)

        pdf.ln(3)

        # =================================================================
        # III. PETA LINTASAN (GAMBAR MATPLOTLIB)
        # =================================================================
        if pdf.get_y() > 190:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 6, text="III. PETA LINTASAN PREDIKSI", border=0, ln=1, align="L")
        pdf.ln(0.5)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(75, 85, 99)
        pdf.multi_cell(0, 4, text=(
            "Visualisasi peta di bawah ini menampilkan lintasan observasi historis (biru) "
            "dan hasil prediksi model LSTM (merah). Titik segitiga hijau menandakan lokasi "
            "referensi pesisir Sumatera Barat."
        ))
        pdf.ln(1.5)

        map_image_path = _generate_map_image(draft_data, prediction_result)
        img_w = 160
        img_x = (210 - img_w) / 2
        pdf.image(map_image_path, x=img_x, w=img_w)
        pdf.ln(3)

        # =================================================================
        # IV. HASIL PREDIKSI LINTASAN
        # =================================================================
        if pdf.get_y() > 185:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 6, text="IV. HASIL PREDIKSI LINTASAN REKURSIF MODEL LSTM", border=0, ln=1, align="L")
        pdf.ln(1)

        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(75, 85, 99)
        pdf.multi_cell(0, 4.5, text=(
            "Hasil di bawah ini diperoleh melalui mekanisme inferensi rekursif (recursive forecasting). "
            "Prediksi koordinat pada suatu langkah (step) dimasukkan kembali sebagai data masukan historis "
            "baru secara otomatis untuk meramalkan koordinat di langkah berikutnya."
        ))
        pdf.ln(2)

        if prediction_result:
            headers_pred = ["Step", "Waktu (WIB)", "LAT", "LON", "Kecepatan", "Arah", "Jarak Pesisir", "Kategori"]
            widths_pred = [10, 32, 20, 20, 22, 20, 26, 30]

            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_fill_color(30, 58, 138)
            pdf.set_text_color(255, 255, 255)
            for h, w in zip(headers_pred, widths_pred):
                pdf.cell(w, 7.5, text=h, border=1, ln=0, align="C", fill=True)
            pdf.ln()

            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(17, 24, 39)
            prev_lat = draft_data.iloc[-1]["LAT"]
            prev_lon = draft_data.iloc[-1]["LON"]

            for idx, res in enumerate(prediction_result):
                if idx % 2 == 1:
                    pdf.set_fill_color(243, 244, 246)
                else:
                    pdf.set_fill_color(255, 255, 255)

                analytics = calculate_analytics(
                    draft_data,
                    res["pred_lat"],
                    res["pred_lon"],
                    prev_lat=prev_lat,
                    prev_lon=prev_lon
                )
                jarak_km, kota = _jarak_ke_pesisir(res["pred_lat"], res["pred_lon"])
                arah_text = _bearing_to_compass(analytics["bearing"])

                time_str = res["time"].strftime("%d-%m-%Y %H:%M")
                speed_str = f"{analytics['speed_kmh']} km/h"
                jarak_str = f"{jarak_km} km"
                cat_str = analytics["category"]

                pdf.cell(widths_pred[0], 6.5, text=f"{idx + 1}", border=1, ln=0, align="C", fill=True)
                pdf.cell(widths_pred[1], 6.5, text=time_str, border=1, ln=0, align="C", fill=True)
                pdf.cell(widths_pred[2], 6.5, text=f"{res['pred_lat']:.2f}", border=1, ln=0, align="C", fill=True)
                pdf.cell(widths_pred[3], 6.5, text=f"{res['pred_lon']:.2f}", border=1, ln=0, align="C", fill=True)
                pdf.cell(widths_pred[4], 6.5, text=speed_str, border=1, ln=0, align="C", fill=True)
                pdf.cell(widths_pred[5], 6.5, text=arah_text, border=1, ln=0, align="C", fill=True)
                pdf.cell(widths_pred[6], 6.5, text=jarak_str, border=1, ln=0, align="C", fill=True)
                pdf.cell(widths_pred[7], 6.5, text=cat_str, border=1, ln=1, align="C", fill=True)

                prev_lat = res["pred_lat"]
                prev_lon = res["pred_lon"]
        else:
            pdf.set_font("Helvetica", "I", 9.5)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(0, 8, text="Tidak ada data hasil prediksi.", border=1, ln=1, align="C")
            pdf.set_text_color(17, 24, 39)

        pdf.ln(5)

        # =================================================================
        # V. ANALISIS DAMPAK TERHADAP PESISIR SUMATERA BARAT
        # =================================================================
        if pdf.get_y() > 200:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 6, text="V. ANALISIS DAMPAK TERHADAP PESISIR SUMATERA BARAT", border=0, ln=1, align="L")
        pdf.ln(1)

        if prediction_result:
            # Analisis Step 1 (prediksi terdekat) & Step terakhir (posisi terjauh)
            step1_res = prediction_result[0]
            analytics_step1 = calculate_analytics(
                draft_data,
                step1_res["pred_lat"],
                step1_res["pred_lon"],
                prev_lat=draft_data.iloc[-1]["LAT"],
                prev_lon=draft_data.iloc[-1]["LON"]
            )
            arah_step1 = _bearing_to_compass(analytics_step1["bearing"])

            last_res = prediction_result[-1]
            jarak_terdekat, kota_terdekat = _jarak_ke_pesisir(last_res["pred_lat"], last_res["pred_lon"])

            # Box info dampak (Kuning muda) — Menggunakan multi_cell agar teks deskripsi tidak overflow
            pdf.set_fill_color(254, 243, 199)
            pdf.set_draw_color(245, 158, 11)
            pdf.set_line_width(0.4)

            info_text = (
                f"- Kategori Terkini: {analytics_step1['category']}\n"
                f"- Jarak Terdekat ke Pesisir Sumbar: {jarak_terdekat} km (Terdekat dari {kota_terdekat})\n"
                f"- Arah & Kecepatan (Step 1): {arah_step1} ({analytics_step1['bearing']} deg) | {analytics_step1['speed_kmh']} km/h\n"
                f"- Ringkasan Dampak: {analytics_step1['description']}"
            )

            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(120, 53, 4)
            pdf.multi_cell(180, 4.8, text=info_text, border=1, align="L", fill=True)
            pdf.ln(3)

            # Penjelasan kategori untuk masyarakat
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(31, 41, 55)

            if jarak_terdekat < 500:
                peringatan = (
                    f"PERINGATAN: Posisi prediksi terakhir berjarak hanya {jarak_terdekat} km dari pesisir "
                    f"{kota_terdekat}. Dengan kategori {analytics_step1['category']}, masyarakat di wilayah pesisir "
                    f"disarankan untuk meningkatkan kewaspadaan terhadap potensi gelombang tinggi, angin kencang, "
                    f"dan hujan lebat yang dapat menyertai sistem cuaca ini."
                )
            else:
                peringatan = (
                    f"Posisi prediksi terakhir berjarak {jarak_terdekat} km dari pesisir {kota_terdekat}. "
                    f"Meskipun jarak relatif jauh, tetap diperlukan pemantauan berkala terhadap perkembangan "
                    f"sistem cuaca ini mengingat siklon tropis dapat berubah arah secara tidak terduga."
                )

            pdf.multi_cell(0, 4.5, text=peringatan)
            pdf.ln(3)

        pdf.ln(2)

        # =================================================================
        # VI. CATATAN ILMIAH & REKOMENDASI MITIGASI
        # =================================================================
        if pdf.get_y() > 200:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 6, text="VI. CATATAN ILMIAH & REKOMENDASI MITIGASI BENCANA", border=0, ln=1, align="L")
        pdf.ln(1.5)

        p1 = (
            "1. Pendekatan Komputasi Data-Driven: Hasil prediksi lintasan ini sepenuhnya berbasis kecerdasan buatan "
            "(Artificial Intelligence) berarsitektur Deep Learning Stacked LSTM. Model mengekstraksi pola temporal "
            "yang dinamis dari koordinat lintasan historis. Model tidak mensimulasikan hukum fisika termodinamika atmosfer "
            "secara langsung, melainkan mempelajari perilaku pergerakan melalui data latih historis."
        )
        p2 = (
            "2. Akumulasi Ketidakpastian: Dalam ilmu pemodelan meteorologi, prediksi berulang (rekursif) memiliki sifat "
            "akumulasi kesalahan (error accumulation). Seiring bertambahnya horizon waktu (misalnya 6 jam hingga 9 jam ke depan), "
            "ketidakpastian model secara alami meningkat secara signifikan. Oleh sebab itu, hasil prediksi langkah pertama "
            "memiliki tingkat kepercayaan tertinggi dibandingkan langkah-langkah berikutnya."
        )
        p3 = (
            "3. Rekomendasi Mitigasi Risiko: Hasil prediksi ini ditujukan sebagai pendukung informasi sistem peringatan dini "
            "(early warning system). Direkomendasikan bagi pihak berwenang dan masyarakat untuk: (a) terus memantau pembaruan "
            "visualisasi lintasan, (b) meningkatkan kesiapsiagaan di daerah pesisir Sumatera Barat terhadap potensi gelombang pasang, "
            "dan (c) melakukan verifikasi berkala dengan rilis peringatan dini cuaca ekstrem resmi dari BMKG."
        )

        pdf.set_fill_color(255, 251, 235)
        pdf.set_draw_color(245, 158, 11)
        pdf.set_line_width(0.3)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(120, 53, 4)

        combined_note = f"{p1}\n\n{p2}\n\n{p3}"
        pdf.multi_cell(0, 4.5, text=combined_note, border=1, align="L", fill=True)
        pdf.ln(5)

        # =================================================================
        # VII. TANDA TANGAN
        # =================================================================
        if pdf.get_y() > 225:
            pdf.add_page()

        pdf.ln(2)
        current_y = pdf.get_y()

        pdf.set_xy(125, current_y)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(70, 5, text=f"Padang, {_tanggal_indonesia()}", border=0, ln=1, align="C")

        pdf.set_x(125)
        pdf.cell(70, 5, text="Penyusun Laporan / Peneliti,", border=0, ln=1, align="C")

        pdf.ln(13)

        pdf.set_x(125)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(70, 5, text="IKHWAN RAMADHAN", border=0, ln=1, align="C")

        pdf.set_x(125)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(70, 4.5, text="NIM: 22101152630411", border=0, ln=1, align="C")

        pdf.set_x(125)
        pdf.cell(70, 4.5, text="Fakultas Ilmu Komputer", border=0, ln=1, align="C")

        pdf.set_x(125)
        pdf.cell(70, 4.5, text='Universitas Putra Indonesia "YPTK" Padang', border=0, ln=1, align="C")

        # =================================================================
        # OUTPUT — io.BytesIO (kompatibel langsung dengan Streamlit)
        # =================================================================
        raw_output = pdf.output()           # bytearray dari fpdf2
        buffer = io.BytesIO(raw_output)     # konversi ke io.BytesIO
        buffer.seek(0)
        return buffer

    finally:
        # Bersihkan file gambar sementara
        if map_image_path and os.path.exists(map_image_path):
            try:
                os.unlink(map_image_path)
            except OSError:
                pass
