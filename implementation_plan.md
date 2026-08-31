# Migrasi Streamlit → Astro + Node.js TypeScript (Vercel)

Migrasi aplikasi prediksi siklon tropis dari Streamlit (Python) ke **Astro** (frontend TypeScript, SSR/hybrid) + **Vercel Serverless Functions** (Node.js TypeScript) dengan inference model LSTM via **ONNX Runtime** (onnxruntime-node). Proyek dibuat di subfolder `streamlit_app/web/`.

---

## Keputusan Arsitektur

| Aspek | Pilihan | Alasan |
|---|---|---|
| **Inference** | ONNX + `onnxruntime-node` | Tidak butuh Python runtime, cold-start lebih cepat |
| **Scaler (.pkl)** | Port logika MinMaxScaler ke TypeScript | Scaler sklearn hanya menyimpan `min_`, `scale_`, `data_min_`, `data_max_` — bisa diekstrak ke JSON |
| **Frontend** | Astro 4.x (hybrid mode) | Cocok untuk Vercel, partial hydration |
| **Map** | Leaflet.js | Port dari Folium, full-featured JS map |
| **Charts** | Chart.js | Port dari `st.line_chart` / `st.bar_chart` |
| **Lokasi** | `streamlit_app/web/` | Subfolder, tapi file config di root untuk Vercel |

---

## Konversi Model ONNX

Model `gab_window8.keras` (0.28 MB) sangat kecil. Langkah konversi:
1. Script Python: `tf2onnx` → `model.onnx`
2. Ekstrak scaler params ke `feature_scaler.json` & `target_scaler.json`
3. Port logika inference ke TypeScript menggunakan `onnxruntime-node`

---

## Struktur Proyek

```
streamlit_app/
├── web/                          # ← PROYEK ASTRO BARU
│   ├── astro.config.mjs
│   ├── package.json
│   ├── tsconfig.json
│   ├── vercel.json
│   │
│   ├── public/
│   │   ├── assets/               # Banner & trajectory images (copy dari ../assets/)
│   │   └── data/                 # CSV files (copy dari ../data/)
│   │
│   ├── src/
│   │   ├── layouts/
│   │   │   └── Layout.astro      # Layout global: header, sidebar, footer
│   │   ├── components/
│   │   │   ├── Sidebar.astro
│   │   │   ├── Footer.astro
│   │   │   ├── MetricCard.astro
│   │   │   └── DataTable.astro
│   │   ├── pages/
│   │   │   ├── index.astro           # Beranda
│   │   │   ├── dashboard.astro       # Dashboard Prediksi
│   │   │   ├── prediksi.astro        # Prediksi Siklon
│   │   │   ├── data-siklon.astro     # Data Observasi
│   │   │   ├── evaluasi.astro        # Evaluasi Akurasi
│   │   │   ├── tentang.astro         # Tentang Model
│   │   │   └── api/
│   │   │       └── predict.ts        # Astro API Route (Node.js serverless)
│   │   └── lib/
│   │       ├── haversine.ts          # Port haversine_km()
│   │       ├── analytics.ts          # Port calculate_analytics(), format_lat_indo()
│   │       ├── inference.ts          # ONNX inference + feature engineering
│   │       ├── scaler.ts             # Port MinMaxScaler logic
│   │       ├── data.ts               # CSV data loader utilities
│   │       └── types.ts              # TypeScript interfaces
│   │
│   └── scripts/
│       └── convert_model.py          # Script konversi keras → ONNX + ekstrak scaler
│
├── prediction/                   # ← EXISTING (tidak diubah)
│   └── models/
│       ├── gab_window8.keras
│       ├── feature_scaler_gab.pkl
│       └── target_scaler_gab.pkl
└── ...
```

---

## Proposed Changes

---

### Phase 0 – Konversi Model

#### [NEW] `web/scripts/convert_model.py`
Script Python satu-kali untuk:
- Konversi `gab_window8.keras` → `web/public/models/model.onnx` menggunakan `tf2onnx`
- Ekstrak scaler sklearn params → `web/public/models/feature_scaler.json` & `target_scaler.json`

Format JSON scaler:
```json
{
  "feature_names": ["WMO_WIND", "WMO_PRES", ...],
  "data_min_": [50.0, 900.0, ...],
  "data_max_": [180.0, 1020.0, ...]
}
```

---

### Phase 1 – Project Setup

#### [NEW] `web/package.json`
```json
{
  "dependencies": {
    "astro": "^4.x",
    "@astrojs/vercel": "^7.x",
    "onnxruntime-node": "^1.19.x"
  },
  "devDependencies": {
    "typescript": "^5.x"
  }
}
```

Client-side scripts (di `<script>` tag Astro):
- `leaflet` (via CDN)
- `chart.js` (via CDN)
- `papaparse` (via CDN)

#### [NEW] `web/astro.config.mjs`
```js
import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel/serverless';

export default defineConfig({
  output: 'hybrid',       // Static + SSR mixed
  adapter: vercel(),
});
```

#### [NEW] `web/vercel.json`
```json
{
  "buildCommand": "cd web && npm run build",
  "outputDirectory": "web/.vercel/output",
  "framework": "astro"
}
```

---

### Phase 2 – TypeScript Inference (ONNX)

#### [NEW] `src/lib/types.ts`
```typescript
export interface ObservationPoint {
  LAT: number; LON: number; WMO_WIND: number; WMO_PRES: number;
}
export interface PredictionResult {
  pred_lat: number; pred_lon: number; time: string;
}
export interface PredictionRequest {
  observations: ObservationPoint[];
  startTime: string;
  steps: 1 | 2 | 3;
}
```

#### [NEW] `src/lib/scaler.ts`
Port logika sklearn MinMaxScaler:
- `transform(data, scalerParams)` → scaled array
- `inverseTransform(data, scalerParams)` → original values

#### [NEW] `src/lib/inference.ts`
Port penuh logika dari `prediction/inference.py`:
- Feature engineering: `delta_lat`, `delta_lon`, `speed_kmh`, `bearing_rate`, `acceleration`, `sin_month`, `cos_month`
- Haversine & bearing calculation
- ONNX model inference via `onnxruntime-node`
- Recursive inference untuk multi-step prediction

#### [NEW] `src/pages/api/predict.ts` (Astro API Route)
```typescript
export const POST: APIRoute = async ({ request }) => {
  const body = await request.json();
  const results = await runRecursiveInference(body);
  return new Response(JSON.stringify(results), {
    headers: { 'Content-Type': 'application/json' }
  });
};
```

---

### Phase 3 – Layout & Design System

#### [NEW] `src/layouts/Layout.astro`
Migrasi **persis** dari `utils.inject_custom_css()` + `render_sidebar()`:
- CSS Global: Inter font, color tokens, reset, header banner, sidebar styles
- Header: `<div id="global-header">🌀 Sistem Prediksi Siklon Tropis — ...</div>`
- Sidebar: navigasi (Beranda, Dashboard, Prediksi, Data Siklon, Evaluasi, Tentang) + badge MODEL LSTM
- CSS responsive (tablet ≤900px, mobile ≤640px)
- Print styles

---

### Phase 4 – Halaman-halaman Astro

#### [NEW] `src/pages/index.astro` — Beranda
Migrasi dari `app.py`:
- Hero card gradient `#EFF6FF → #DBEAFE`, border `#1E3A8A`
- Grid 5 fitur (card `.page-panel` style)
- Banner image kanan (`banner_beranda.png`)
- Fade-in animation

#### [NEW] `src/pages/dashboard.astro` — Dashboard Prediksi
Migrasi dari `pages/1_Dashboard.py`:
- Load `predictions_gab8.csv` + `model_gab_test_fix.csv` (PapaParse client-side dari `/data/`)
- Slider radius (500–4000 km) → filter SID dalam radius dari Padang (-0.94, 100.32)
- Dropdown/select ID Siklon
- Info card: ID, Nama, Periode, Durasi, Jumlah Titik
- Peta Leaflet:
  - PolyLine aktual (hitam, weight 3)
  - PolyLine prediksi (biru `#1E3A8A`, dashed `6 6`)
  - CircleMarker aktual & prediksi (radius 4)
  - CircleMarker start (hijau, radius 8) & end (biru, radius 8)
  - Legend HTML (posisi bottom-left)
- 2 MetricCard: RMSE (km) & MAE (km)
- Tabel perbandingan koordinat (`.custom-table`)

#### [NEW] `src/pages/prediksi.astro` — Prediksi Siklon
Migrasi dari `pages/Prediksi.py` (halaman paling kompleks):

**Kolom Kiri (Editor):**
- Select titik 1–8 untuk diedit
- Form: LAT, LON, WMO_WIND, WMO_PRES
- Tombol "Simpan Titik"
- Konfigurasi: Tanggal Awal + Jam Awal + Horizon (3/6/9 jam)
- Tabel 8 titik observasi (`.prediksi-table`)
- Tombol: 📄 Print Laporan (disabled jika belum ada hasil), 🧠 Prediksi LSTM, 🗑️ Bersihkan

**Kolom Kanan (Peta & Hasil):**
- Peta Leaflet (600px tinggi):
  - PolyLine biru untuk observasi historis
  - CircleMarker per titik observasi (tooltip "Titik N")
  - AntPath animasi merah untuk jalur prediksi (CSS animation)
  - Marker bintang merah per titik prediksi
  - LatLngPopup (klik peta → isi titik kosong)
  - MiniMap, MeasureControl, Fullscreen
- Hasil Prediksi (setelah klik prediksi):
  - Per step: LAT/LON (format `1.5° LS`), kecepatan km/h
  - Status kategori (Depresi/Badai/Siklon Cat 1-5)
  - Arah (bearing°)
  - Reliability badge (Tinggi/Sedang/Rendah)
  - Warning disclaimer ilmiah

#### [NEW] `src/pages/data-siklon.astro` — Data Observasi
Migrasi dari `pages/Data_Siklon.py`:
- Load `data_observasi.csv` client-side
- Input pencarian SID + dropdown semua SID
- Info ringkas siklon
- Tabel lengkap: Waktu, LAT, LON, Wind, Metode Imputasi Angin, Pressure, Metode Imputasi Tekanan, Status Angin, Status Tekanan
- Badge HTML: ✅ Asli (hijau) / Perbaikan (oranye)
- Catatan sumber data

#### [NEW] `src/pages/evaluasi.astro` — Evaluasi Akurasi
Migrasi dari `pages/3_Evaluasi.py`:
- Load `predictions_gab8.csv` client-side
- Dropdown pilih SID
- Info ringkas siklon + penjelasan metrik (`.info-card`)
- 4 MetricCard: MAE, RMSE, Min Error, Max Error
- Badge predikat akurasi (Error Sangat Rendah/Rendah/Sedang/Tinggi)
- **Chart.js Line** – Deviasi Jarak Per Waktu (km)
- **Chart.js Bar** – Distribusi Frekuensi Error (0-10, 10-25, 25-50, >50 km)
- **Chart.js Line (multi)** – Dekomposisi LAT vs LON (dua dataset, biru & oranye)
- Tabel + tombol Download CSV
- Narasi evaluasi spasial (`.narrative-box`)

#### [NEW] `src/pages/tentang.astro` — Tentang Model
Migrasi dari `pages/4_Tentang.py`:
- Pengantar (`.narrative-box`)
- **Chart.js Bar** – Perbandingan Haversine semua model
- Tabel ranking Haversine (`.custom-table`)
- Tabel R² score (`.custom-table`)
- Analisis overfitting (tabel) + kecepatan inferensi (bar chart)
- Info box pemilihan GAB-8
- Grid 2×2 gambar trajectory (`trajectory_best_model1-4.png`)

---

### Phase 5 – TypeScript Utilities

#### [NEW] `src/lib/haversine.ts`
```typescript
export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number
export function bearing(lat1: number, lon1: number, lat2: number, lon2: number): number
```

#### [NEW] `src/lib/analytics.ts`
```typescript
export function formatLatIndo(lat: number, precision?: number): string
export function formatLonIndo(lon: number, precision?: number): string
export function getReliabilityMetrics(step: number): ReliabilityMetric
export function calculateAnalytics(historyDf: ObservationPoint[], predLat: number, predLon: number, ...): AnalyticsResult
```

#### [NEW] `src/lib/data.ts`
```typescript
export async function loadPredictionData(): Promise<PredictionRow[]>
export async function loadObservasiData(): Promise<ObservasiRow[]>
export async function loadModelRanking(): Promise<ModelRankingRow[]>
// ... dll
```

---

## Verification Plan

### Konversi Model ONNX
1. Jalankan `python web/scripts/convert_model.py`
2. Verifikasi output `model.onnx` dan `feature_scaler.json` ter-generate
3. Test inference TypeScript: input 8 titik dummy → output pred_lat/pred_lon valid

### Build
```bash
cd web && npm run build
```

### Manual Verification
1. `npm run dev` → buka http://localhost:4321
2. Test semua 5 halaman, navigasi sidebar
3. Test prediksi end-to-end: isi 8 titik → klik Prediksi → hasil di peta + hasil card
4. Test klik peta → isi titik kosong
5. Test download CSV di halaman Evaluasi
6. Test responsif mobile (Chrome DevTools)
7. Deploy ke Vercel preview via `vercel --prebuilt`
