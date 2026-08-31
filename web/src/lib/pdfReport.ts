// PDF Report Generator — Porting 1:1 Apple-to-Apple dari prediction/pdf_report.py
// Menggunakan jsPDF & HTML5 Canvas untuk menghasilkan file PDF laporan resmi

import { haversineKm, bearing } from './haversine';
import { formatLatIndo, formatLonIndo, calculateAnalytics } from './analytics';
import type { ObservationPoint, PredictionResult } from './types';

// =========================================================================
// KONSTANTA PESISIR SUMATERA BARAT (Persis dengan pdf_report.py)
// =========================================================================
export const PESISIR_SUMBAR = [
  { lat: -0.95, lon: 100.35, name: 'Padang' },
  { lat: -1.35, lon: 100.55, name: 'Painan' },
  { lat: -0.30, lon: 99.80, name: 'Pariaman' },
  { lat: 0.30, lon: 99.10, name: 'Pasaman Barat' },
];

export function jarakKePesisir(lat: number, lon: number): { jarakKm: number; kota: string } {
  let jarakMin = Infinity;
  let kotaTerdekat = '';
  for (const p of PESISIR_SUMBAR) {
    const d = haversineKm(lat, lon, p.lat, p.lon);
    if (d < jarakMin) {
      jarakMin = d;
      kotaTerdekat = p.name;
    }
  }
  return { jarakKm: Math.round(jarakMin * 10) / 10, kota: kotaTerdekat };
}

export function bearingToCompass(deg: number): string {
  const directions = [
    'Utara', 'Timur Laut', 'Timur', 'Tenggara',
    'Selatan', 'Barat Daya', 'Barat', 'Barat Laut',
  ];
  const idx = Math.round(deg / 45) % 8;
  return directions[idx];
}

export function tanggalIndonesia(dt?: Date): string {
  const d = dt || new Date();
  const bulan = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
  ];
  return `${d.getDate()} ${bulan[d.getMonth()]} ${d.getFullYear()}`;
}

// =========================================================================
// CANVAS MAP GENERATOR (Pengganti Matplotlib di browser)
// =========================================================================
export function generateMapDataUrl(
  observations: ObservationPoint[],
  predictionResult: PredictionResult[]
): string {
  const canvas = document.createElement('canvas');
  canvas.width = 900;
  canvas.height = 480;
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';

  // Background laut biru lembut
  ctx.fillStyle = '#E8F0FE';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Ambil semua titik untuk scaling
  const allPts: { lat: number; lon: number }[] = [
    ...observations.filter((p) => p.LAT !== 0 || p.LON !== 0).map((p) => ({ lat: p.LAT, lon: p.LON })),
    ...predictionResult.map((p) => ({ lat: p.pred_lat, lon: p.pred_lon })),
    ...PESISIR_SUMBAR.map((p) => ({ lat: p.lat, lon: p.lon })),
  ];

  if (allPts.length === 0) return '';

  const lats = allPts.map((p) => p.lat);
  const lons = allPts.map((p) => p.lon);

  const minLat = Math.min(...lats) - 1.5;
  const maxLat = Math.max(...lats) + 1.5;
  const minLon = Math.min(...lons) - 1.5;
  const maxLon = Math.max(...lons) + 1.5;

  const padX = 60;
  const padY = 40;
  const mapW = canvas.width - padX * 2;
  const mapH = canvas.height - padY * 2;

  function toScreen(lat: number, lon: number): [number, number] {
    const x = padX + ((lon - minLon) / (maxLon - minLon)) * mapW;
    const y = padY + ((maxLat - lat) / (maxLat - minLat)) * mapH;
    return [x, y];
  }

  // Grid lines & labels
  ctx.strokeStyle = '#CBD5E1';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  ctx.font = '11px sans-serif';
  ctx.fillStyle = '#64748B';

  const numGrid = 5;
  for (let i = 0; i <= numGrid; i++) {
    const lonVal = minLon + (i / numGrid) * (maxLon - minLon);
    const [gx] = toScreen(0, lonVal);
    ctx.beginPath();
    ctx.moveTo(gx, padY);
    ctx.lineTo(gx, canvas.height - padY);
    ctx.stroke();
    ctx.fillText(`${lonVal.toFixed(1)}°E`, gx - 14, canvas.height - padY + 16);

    const latVal = minLat + (i / numGrid) * (maxLat - minLat);
    const [, gy] = toScreen(latVal, 0);
    ctx.beginPath();
    ctx.moveTo(padX, gy);
    ctx.lineTo(canvas.width - padX, gy);
    ctx.stroke();
    ctx.fillText(`${latVal.toFixed(1)}°N`, padX - 45, gy + 4);
  }
  ctx.setLineDash([]);

  // Plot Pesisir Sumbar (Segitiga Hijau)
  ctx.fillStyle = '#059669';
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 1.5;
  for (const p of PESISIR_SUMBAR) {
    const [px, py] = toScreen(p.lat, p.lon);
    ctx.beginPath();
    ctx.moveTo(px, py - 7);
    ctx.lineTo(px + 6, py + 5);
    ctx.lineTo(px - 6, py + 5);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#065F46';
    ctx.font = 'bold 10px sans-serif';
    ctx.fillText(p.name, px + 8, py + 3);
    ctx.fillStyle = '#059669';
  }

  // Plot Garis Historis (Biru #1E3A8A)
  const histPts = observations.filter((p) => p.LAT !== 0 || p.LON !== 0);
  if (histPts.length > 0) {
    ctx.strokeStyle = '#1E3A8A';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    histPts.forEach((p, i) => {
      const [hx, hy] = toScreen(p.LAT, p.LON);
      if (i === 0) ctx.moveTo(hx, hy);
      else ctx.lineTo(hx, hy);
    });
    ctx.stroke();

    // Titik lingkaran historis
    histPts.forEach((p, i) => {
      const [hx, hy] = toScreen(p.LAT, p.LON);
      ctx.fillStyle = '#1E3A8A';
      ctx.beginPath();
      ctx.arc(hx, hy, 5.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.fillStyle = '#1E3A8A';
      ctx.font = 'bold 10px sans-serif';
      ctx.fillText(`${i + 1}`, hx - 3, hy - 8);
    });
  }

  // Plot Garis Prediksi (Merah #DC2626 Putus-putus)
  if (predictionResult.length > 0 && histPts.length > 0) {
    const lastHist = histPts[histPts.length - 1];
    const fullPredPts = [
      { lat: lastHist.LAT, lon: lastHist.LON },
      ...predictionResult.map((r) => ({ lat: r.pred_lat, lon: r.pred_lon })),
    ];

    ctx.strokeStyle = '#DC2626';
    ctx.lineWidth = 2.5;
    ctx.setLineDash([6, 5]);
    ctx.beginPath();
    fullPredPts.forEach((p, i) => {
      const [px, py] = toScreen(p.lat, p.lon);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    ctx.setLineDash([]);

    // Marker Kotak Prediksi
    predictionResult.forEach((r, i) => {
      const [px, py] = toScreen(r.pred_lat, r.pred_lon);
      ctx.fillStyle = '#DC2626';
      ctx.fillRect(px - 5.5, py - 5.5, 11, 11);
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(px - 5.5, py - 5.5, 11, 11);

      ctx.fillStyle = '#DC2626';
      ctx.font = 'bold 10.5px sans-serif';
      ctx.fillText(`P${i + 1}`, px - 6, py - 9);
    });
  }

  // Judul Peta
  ctx.fillStyle = '#1E3A8A';
  ctx.font = 'bold 13px sans-serif';
  ctx.fillText('Peta Lintasan Siklon — Historis & Prediksi LSTM', padX, padY - 14);

  // Legenda
  const legX = canvas.width - 240;
  const legY = padY - 24;
  ctx.fillStyle = 'rgba(255,255,255,0.9)';
  ctx.fillRect(legX, legY, 180, 52);
  ctx.strokeStyle = '#CBD5E1';
  ctx.strokeRect(legX, legY, 180, 52);

  // Legenda item 1: Historis
  ctx.fillStyle = '#1E3A8A';
  ctx.beginPath();
  ctx.arc(legX + 12, legY + 12, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.font = '10px sans-serif';
  ctx.fillText('Historis (Observasi)', legX + 22, legY + 15);

  // Legenda item 2: Prediksi
  ctx.fillStyle = '#DC2626';
  ctx.fillRect(legX + 8, legY + 24, 8, 8);
  ctx.fillText('Prediksi (LSTM)', legX + 22, legY + 31);

  // Legenda item 3: Pesisir
  ctx.fillStyle = '#059669';
  ctx.beginPath();
  ctx.moveTo(legX + 12, legY + 38);
  ctx.lineTo(legX + 16, legY + 46);
  ctx.lineTo(legX + 8, legY + 46);
  ctx.closePath();
  ctx.fill();
  ctx.fillText('Pesisir Sumbar', legX + 22, legY + 45);

  return canvas.toDataURL('image/png');
}

// =========================================================================
// LOAD JSPDF SECARA DINAMIS (Client-Side)
// =========================================================================
async function loadJsPDF(): Promise<any> {
  if ((window as any).jspdf) return (window as any).jspdf;
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
    s.onload = () => resolve();
    s.onerror = (e) => reject(e);
    document.head.appendChild(s);
  });
  return (window as any).jspdf;
}

// =========================================================================
// GENERATE PDF LAPORAN LENGKAP (Apple-to-Apple dengan pdf_report.py)
// =========================================================================
export async function generateAndDownloadPdfReport(
  observations: ObservationPoint[],
  predictionResult: PredictionResult[],
  startDateTime: Date,
  horizonHours: number,
  numSteps: number
): Promise<void> {
  const { jsPDF } = await loadJsPDF();
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const now = new Date();
  const tglCetak = tanggalIndonesia(now);
  const waktuCetak = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')} WIB`;
  const reportId = `REP-CYCLONE-${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}-${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}${now.getSeconds().toString().padStart(2, '0')}`;

  function drawHeader(isPage1: boolean) {
    if (isPage1) {
      // Pita biru tua atas
      doc.setFillColor(30, 58, 138);
      doc.rect(0, 0, 210, 8, 'F');

      // Judul Laporan
      doc.setFont('Helvetica', 'bold');
      doc.setFontSize(14);
      doc.setTextColor(30, 58, 138);
      doc.text('LAPORAN PREDIKSI LINTASAN SIKLON TROPIS', 105, 16, { align: 'center' });

      // Subjudul
      doc.setFontSize(8.5);
      doc.setTextColor(55, 65, 81);
      doc.text(
        'SISTEM PREDIKSI SIKLON TROPIS UNTUK MITIGASI RISIKO BENCANA DI SUMATERA BARAT',
        105,
        21,
        { align: 'center' }
      );

      // Model info
      doc.setFont('Helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);
      doc.text(
        'Model Komputasi: Deep Learning LSTM 64 Units (Sliding Window Gabung 8)',
        105,
        26,
        { align: 'center' }
      );

      // Garis ganda
      doc.setDrawColor(30, 58, 138);
      doc.setLineWidth(0.8);
      doc.line(15, 30, 195, 30);

      doc.setDrawColor(156, 163, 175);
      doc.setLineWidth(0.3);
      doc.line(15, 31.5, 195, 31.5);
    } else {
      doc.setFont('Helvetica', 'italic');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);
      doc.text('Laporan Prediksi Lintasan Siklon Tropis - Sumatera Barat', 15, 12);
      doc.text(`Dicetak: ${now.toLocaleDateString('id-ID')} ${now.toLocaleTimeString('id-ID')}`, 195, 12, { align: 'right' });

      doc.setDrawColor(156, 163, 175);
      doc.setLineWidth(0.3);
      doc.line(15, 15, 195, 15);
    }
  }

  function drawFooter(pageNum: number) {
    doc.setDrawColor(209, 213, 221);
    doc.setLineWidth(0.3);
    doc.line(15, 282, 195, 282);

    doc.setFont('Helvetica', 'italic');
    doc.setFontSize(8);
    doc.setTextColor(107, 114, 128);
    doc.text(`Halaman ${pageNum}`, 15, 287);
    doc.text('IKHWAN RAMADHAN - TEKNIK INFORMATIKA', 195, 287, { align: 'right' });
  }

  // =========================================================================
  // HALAMAN 1
  // =========================================================================
  drawHeader(true);

  let currentY = 36;

  // I. DATA METADATA LAPORAN
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(30, 58, 138);
  doc.text('I. DATA METADATA LAPORAN', 15, currentY);
  currentY += 4;

  // Box Metadata
  doc.setFillColor(249, 250, 251);
  doc.setDrawColor(209, 213, 221);
  doc.setLineWidth(0.3);
  doc.rect(15, currentY, 180, 36, 'FD');

  const metaItems = [
    { label: 'ID Laporan', val: reportId },
    { label: 'Tanggal Cetak', val: `${tglCetak} / ${waktuCetak}` },
    { label: 'ID Siklon', val: 'AUTOGEN-CYCLONE' },
    { label: 'Nama Siklon', val: 'Siklon Tropis (Prediksi Model)' },
    { label: 'Basin / Wilayah', val: 'Samudra Hindia' },
    { label: 'Sumber Data', val: 'IBTrACS v4 (1980-2025)' },
    {
      label: 'Mulai Prediksi',
      val: `${tanggalIndonesia(startDateTime)} / ${startDateTime.getHours().toString().padStart(2, '0')}:${startDateTime.getMinutes().toString().padStart(2, '0')} WIB`,
    },
    { label: 'Horizon Prediksi', val: `${horizonHours} Jam (${numSteps} Langkah)` },
    { label: 'Versi Model', val: 'LSTM 64 Units' },
    { label: 'Versi Dataset', val: 'IBTrACS v4 (1980-2025)' },
  ];

  doc.setFontSize(7.8);
  metaItems.forEach((item, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 18 + col * 90;
    const y = currentY + 5.5 + row * 6.5;

    doc.setFont('Helvetica', 'bold');
    doc.setTextColor(55, 65, 81);
    doc.text(`${item.label}:`, x, y);

    doc.setFont('Helvetica', 'normal');
    doc.setTextColor(17, 24, 39);
    doc.text(` ${item.val}`, x + 28, y);
  });

  currentY += 40;

  // II. DATA HISTORIS OBSERVASI
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(30, 58, 138);
  doc.text('II. DATA HISTORIS OBSERVASI (INPUT SLIDING WINDOW)', 15, currentY);
  currentY += 4;

  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(75, 85, 99);
  const obsDesc =
    'Tabel berikut menyajikan urutan data observasi meteorologi sebanyak 8 titik (sliding window) yang diinputkan oleh operator. Data ini diolah secara bertahap oleh LSTM untuk memprediksi arah pergerakan selanjutnya.';
  doc.text(doc.splitTextToSize(obsDesc, 180), 15, currentY);
  currentY += 8;

  // Table Headers
  const obsHeaders = ['Titik', 'Waktu (WIB)', 'Lintang', 'Bujur', 'Kec. Angin (Knot)', 'Tekanan (hPa)'];
  const obsWidths = [12, 34, 34, 34, 33, 33];
  let tableX = 15;

  doc.setFillColor(30, 58, 138);
  doc.setDrawColor(31, 41, 55);
  doc.setLineWidth(0.3);
  doc.rect(15, currentY, 180, 5.5, 'FD');

  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(255, 255, 255);

  tableX = 15;
  obsHeaders.forEach((h, idx) => {
    doc.text(h, tableX + obsWidths[idx] / 2, currentY + 3.8, { align: 'center' });
    tableX += obsWidths[idx];
  });
  currentY += 5.5;

  // Table Rows
  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(17, 24, 39);

  observations.forEach((row, idx) => {
    if (idx % 2 === 1) doc.setFillColor(243, 244, 246);
    else doc.setFillColor(255, 255, 255);

    doc.rect(15, currentY, 180, 4.8, 'FD');

    const ptTime = new Date(startDateTime.getTime() + idx * 3 * 3600 * 1000);
    const timeStr = `${ptTime.getDate().toString().padStart(2, '0')}-${(ptTime.getMonth() + 1).toString().padStart(2, '0')}-${ptTime.getFullYear()} ${ptTime.getHours().toString().padStart(2, '0')}:${ptTime.getMinutes().toString().padStart(2, '0')}`;

    tableX = 15;
    const rowVals = [
      `${idx + 1}`,
      timeStr,
      formatLatIndo(row.LAT, 1),
      formatLonIndo(row.LON, 1),
      `${row.WMO_WIND.toFixed(1)}`,
      `${row.WMO_PRES.toFixed(1)}`,
    ];

    rowVals.forEach((val, cIdx) => {
      doc.text(val, tableX + obsWidths[cIdx] / 2, currentY + 3.4, { align: 'center' });
      tableX += obsWidths[cIdx];
    });

    currentY += 4.8;
  });

  currentY += 5;

  // III. PETA LINTASAN PREDIKSI (GAMBAR CANVAS)
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(30, 58, 138);
  doc.text('III. PETA LINTASAN PREDIKSI', 15, currentY);
  currentY += 4;

  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(7.8);
  doc.setTextColor(75, 85, 99);
  const mapDesc =
    'Visualisasi peta di bawah ini menampilkan lintasan observasi historis (biru) dan hasil prediksi model LSTM (merah). Titik segitiga hijau menandakan lokasi referensi pesisir Sumatera Barat.';
  doc.text(doc.splitTextToSize(mapDesc, 180), 15, currentY);
  currentY += 6;

  const mapDataUrl = generateMapDataUrl(observations, predictionResult);
  if (mapDataUrl) {
    const imgW = 160;
    const imgH = 85;
    const imgX = (210 - imgW) / 2;
    doc.addImage(mapDataUrl, 'PNG', imgX, currentY, imgW, imgH);
    currentY += imgH + 4;
  }

  drawFooter(1);

  // =========================================================================
  // HALAMAN 2
  // =========================================================================
  doc.addPage();
  drawHeader(false);

  currentY = 22;

  // IV. HASIL PREDIKSI LINTASAN REKURSIF MODEL LSTM
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(30, 58, 138);
  doc.text('IV. HASIL PREDIKSI LINTASAN REKURSIF MODEL LSTM', 15, currentY);
  currentY += 4;

  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(75, 85, 99);
  const predDesc =
    'Hasil di bawah ini diperoleh melalui mekanisme inferensi rekursif (recursive forecasting). Prediksi koordinat pada suatu langkah dimasukkan kembali sebagai data masukan historis baru secara otomatis untuk meramalkan koordinat di langkah berikutnya.';
  doc.text(doc.splitTextToSize(predDesc, 180), 15, currentY);
  currentY += 8;

  // Table Prediksi
  const predHeaders = ['Step', 'Waktu (WIB)', 'Lintang', 'Bujur', 'Kecepatan', 'Arah', 'Jarak Sumbar', 'Kategori'];
  const predWidths = [10, 30, 20, 20, 20, 22, 22, 36];

  doc.setFillColor(30, 58, 138);
  doc.rect(15, currentY, 180, 5.5, 'FD');
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(7.2);
  doc.setTextColor(255, 255, 255);

  tableX = 15;
  predHeaders.forEach((h, idx) => {
    doc.text(h, tableX + predWidths[idx] / 2, currentY + 3.8, { align: 'center' });
    tableX += predWidths[idx];
  });
  currentY += 5.5;

  let prevLat = observations[observations.length - 1].LAT;
  let prevLon = observations[observations.length - 1].LON;

  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(7.2);
  doc.setTextColor(17, 24, 39);

  predictionResult.forEach((res, idx) => {
    if (idx % 2 === 1) doc.setFillColor(243, 244, 246);
    else doc.setFillColor(255, 255, 255);

    doc.rect(15, currentY, 180, 5.2, 'FD');

    const analytics = calculateAnalytics(observations, res.pred_lat, res.pred_lon, prevLat, prevLon);
    const { jarakKm, kota } = jarakKePesisir(res.pred_lat, res.pred_lon);
    const arahText = bearingToCompass(analytics.bearing);

    const rTime = new Date(res.time);
    const timeStr = `${rTime.getDate().toString().padStart(2, '0')}-${(rTime.getMonth() + 1).toString().padStart(2, '0')} ${rTime.getHours().toString().padStart(2, '0')}:${rTime.getMinutes().toString().padStart(2, '0')}`;

    tableX = 15;
    const rowVals = [
      `${idx + 1}`,
      timeStr,
      formatLatIndo(res.pred_lat, 2),
      formatLonIndo(res.pred_lon, 2),
      `${analytics.speed_kmh} km/h`,
      `${arahText} (${analytics.bearing}°)`,
      `${jarakKm} km (${kota})`,
      analytics.category,
    ];

    rowVals.forEach((val, cIdx) => {
      doc.text(val, tableX + predWidths[cIdx] / 2, currentY + 3.6, { align: 'center' });
      tableX += predWidths[cIdx];
    });

    prevLat = res.pred_lat;
    prevLon = res.pred_lon;
    currentY += 5.2;
  });

  currentY += 6;

  // V. ANALISIS DAMPAK TERHADAP PESISIR SUMATERA BARAT
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(30, 58, 138);
  doc.text('V. ANALISIS DAMPAK TERHADAP PESISIR SUMATERA BARAT', 15, currentY);
  currentY += 4;

  if (predictionResult.length > 0) {
    const step1 = predictionResult[0];
    const analytics1 = calculateAnalytics(
      observations,
      step1.pred_lat,
      step1.pred_lon,
      observations[observations.length - 1].LAT,
      observations[observations.length - 1].LON
    );
    const arah1 = bearingToCompass(analytics1.bearing);

    let jarakMinAll = Infinity;
    let kotaMinAll = '';
    for (const res of predictionResult) {
      const { jarakKm, kota } = jarakKePesisir(res.pred_lat, res.pred_lon);
      if (jarakKm < jarakMinAll) {
        jarakMinAll = jarakKm;
        kotaMinAll = kota;
      }
    }

    // Box Dampak Kuning
    doc.setFillColor(254, 243, 199);
    doc.setDrawColor(245, 158, 11);
    doc.setLineWidth(0.4);
    doc.rect(15, currentY, 180, 24, 'FD');

    doc.setFont('Helvetica', 'normal');
    doc.setFontSize(7.6);
    doc.setTextColor(120, 53, 4);

    const infoLines = [
      `• Kategori Terkini: ${analytics1.category}`,
      `• Jarak Terdekat ke Pesisir Sumbar: ${jarakMinAll} km (Terdekat dari pesisir ${kotaMinAll})`,
      `• Arah & Kecepatan Pergerakan (Step 1): ${arah1} (${analytics1.bearing}°) | ${analytics1.speed_kmh} km/h`,
      `• Ringkasan Karakteristik: ${analytics1.description}`,
    ];

    infoLines.forEach((l, i) => {
      doc.text(l, 18, currentY + 5 + i * 5);
    });

    currentY += 28;

    // Peringatan
    doc.setFont('Helvetica', 'normal');
    doc.setFontSize(7.8);
    doc.setTextColor(31, 41, 55);

    let warningText = '';
    if (jarakMinAll < 500) {
      warningText = `PERINGATAN: Berdasarkan koordinat lintasan prediksi, jarak terdekat berada pada ${jarakMinAll} km dari pesisir ${kotaMinAll}. Dengan intensitas ${analytics1.category}, masyarakat di wilayah pesisir diimbau untuk meningkatkan kewaspadaan terhadap potensi peningkatan angin kencang, hujan lebat, dan gelombang tinggi sesuai karakteristik umum siklon tropis.`;
    } else {
      warningText = `Posisi prediksi terdekat berjarak ${jarakMinAll} km dari pesisir ${kotaMinAll}. Meskipun jarak relatif jauh, tetap diimbau untuk memantau perkembangan sistem cuaca ini secara berkala sesuai karakteristik umum siklon tropis yang dapat berubah arah.`;
    }

    doc.text(doc.splitTextToSize(warningText, 180), 15, currentY);
    currentY += 12;
  }

  // VI. CATATAN ILMIAH & REKOMENDASI MITIGASI BENCANA
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(30, 58, 138);
  doc.text('VI. CATATAN ILMIAH & REKOMENDASI MITIGASI BENCANA', 15, currentY);
  currentY += 4;

  doc.setFillColor(255, 251, 235);
  doc.setDrawColor(245, 158, 11);
  doc.setLineWidth(0.3);
  doc.rect(15, currentY, 180, 28, 'FD');

  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(7.2);
  doc.setTextColor(120, 53, 4);

  const notes = [
    '1. Pendekatan Komputasi Data-Driven: Prediksi lintasan berbasis Deep Learning LSTM 64 Units mengekstraksi pola temporal dinamis dari data historis IBTrACS v4 (1980-2025). Model mempelajari pola statistik spasial-temporal data latih.',
    '2. Akumulasi Ketidakpastian: Inferensi rekursif secara inheren mengalami akumulasi kesalahan (error accumulation) seiring penambahan horizon waktu (3-9 jam). Langkah pertama memiliki tingkat reliabilitas tertinggi.',
    '3. Rekomendasi Mitigasi: Hasil prediksi sebagai pendukung informasi peringatan dini. Masyarakat & instansi terkait diimbau memantau visualisasi berkala serta verifikasi rilis resmi BMKG.',
  ];

  notes.forEach((note, i) => {
    const splitNote = doc.splitTextToSize(note, 174);
    doc.text(splitNote, 18, currentY + 4.5 + i * 8);
  });

  currentY += 33;

  // VII. TANDA TANGAN PENELITI
  const signX = 135;
  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(17, 24, 39);
  doc.text(`Padang, ${tglCetak}`, signX, currentY, { align: 'center' });
  doc.text('Penyusun Laporan / Peneliti,', signX, currentY + 4.5, { align: 'center' });

  currentY += 16;
  doc.setFont('Helvetica', 'bold');
  doc.setFontSize(9);
  doc.text('IKHWAN RAMADHAN', signX, currentY, { align: 'center' });

  doc.setFont('Helvetica', 'normal');
  doc.setFontSize(8);
  doc.text('NIM: 22101152630411', signX, currentY + 4, { align: 'center' });
  doc.text('Fakultas Ilmu Komputer', signX, currentY + 8, { align: 'center' });
  doc.text('Universitas Putra Indonesia "YPTK" Padang', signX, currentY + 12, { align: 'center' });

  drawFooter(2);

  // Output sebagai Blob PDF untuk Preview interaktif di browser (bisa Print & Simpan PDF)
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);

  // Buka preview di tab baru
  const previewWin = window.open(blobUrl, '_blank');
  if (!previewWin || previewWin.closed || typeof previewWin.closed === 'undefined') {
    // Fallback jika popup diblokir browser: buka di iframe tersembunyi untuk dialog print
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = blobUrl;
    document.body.appendChild(iframe);
    iframe.onload = () => {
      iframe.contentWindow?.focus();
      iframe.contentWindow?.print();
    };
  }
}
