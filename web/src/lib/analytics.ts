// Analytics utilities — port dari prediction/analytics.py
import { haversineKm, bearing } from './haversine';
import type { ObservationPoint, AnalyticsResult, ReliabilityMetric } from './types';

/**
 * Format latitude in Indonesian notation (e.g. "1.5° LS")
 */
export function formatLatIndo(lat: number, precision = 1): string {
  const dir = lat < 0 ? 'LS' : 'LU';
  return `${Math.abs(lat).toFixed(precision)}° ${dir}`;
}

/**
 * Format longitude in Indonesian notation (e.g. "100.3° BT")
 */
export function formatLonIndo(lon: number, precision = 1): string {
  const dir = lon < 0 ? 'BB' : 'BT';
  return `${Math.abs(lon).toFixed(precision)}° ${dir}`;
}

/**
 * Get reliability metrics per prediction step.
 * Port dari prediction/analytics.py get_reliability_metrics()
 */
export function getReliabilityMetrics(step: number): ReliabilityMetric {
  if (step === 1) {
    return {
      reliability: 'Tinggi',
      confidence_pct: 92,
      uncertainty_km: '±15-25 km',
      text: 'Tinggi (92%)',
      color: 'green',
    };
  } else if (step === 2) {
    return {
      reliability: 'Sedang',
      confidence_pct: 78,
      uncertainty_km: '±35-55 km',
      text: 'Sedang (78%)',
      color: 'orange',
    };
  } else {
    return {
      reliability: 'Rendah (Perlu Kewaspadaan)',
      confidence_pct: 61,
      uncertainty_km: '±60-90 km',
      text: 'Rendah (61%)',
      color: 'red',
    };
  }
}

/**
 * Calculate analytics for a prediction step.
 * Port dari prediction/analytics.py calculate_analytics()
 */
export function calculateAnalytics(
  historyDf: ObservationPoint[],
  predLat: number,
  predLon: number,
  prevLat?: number,
  prevLon?: number
): AnalyticsResult {
  const lastPoint = historyDf[historyDf.length - 1];
  const pLat = prevLat !== undefined ? prevLat : lastPoint.LAT;
  const pLon = prevLon !== undefined ? prevLon : lastPoint.LON;
  const wind = lastPoint.WMO_WIND;

  // Speed (km/h) — assuming 3-hour interval
  const dist = haversineKm(pLat, pLon, predLat, predLon);
  const speed = dist / 3.0;

  // Bearing
  const brng = bearing(pLat, pLon, predLat, predLon);

  // Category classification (WMO/NOAA wind speed in knots)
  let category: string;
  let description: string;

  if (wind >= 137) {
    category = 'Siklon Tropis Kategori 5';
    description =
      'Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak sangat ekstrem apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis.';
  } else if (wind >= 113) {
    category = 'Siklon Tropis Kategori 4';
    description =
      'Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak berat apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis.';
  } else if (wind >= 96) {
    category = 'Siklon Tropis Kategori 3';
    description =
      'Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak berat pada wilayah pesisir apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis.';
  } else if (wind >= 83) {
    category = 'Siklon Tropis Kategori 2';
    description =
      'Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak sedang hingga berat apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis.';
  } else if (wind >= 64) {
    category = 'Siklon Tropis Kategori 1';
    description =
      'Berdasarkan kategori intensitas, siklon berpotensi menimbulkan dampak ringan hingga sedang apabila lintasan dan kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis.';
  } else if (wind >= 34) {
    category = 'Badai Tropis';
    description =
      'Sistem berpotensi meningkatkan kecepatan angin dan memicu gelombang tinggi di sekitar lintasan apabila kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis.';
  } else {
    category = 'Depresi Tropis';
    description =
      'Sistem tekanan rendah dengan potensi berkembang menjadi badai tropis apabila kondisi atmosfer mendukung, sesuai karakteristik umum siklon tropis.';
  }

  return {
    speed_kmh: Math.round(speed * 100) / 100,
    bearing: Math.round(brng * 10) / 10,
    category,
    description,
  };
}
