// Data loader utilities — replaces pandas CSV loading in Python
// Runs CLIENT-SIDE using PapaParse + fetch from /data/ static files

export type CsvRow = Record<string, string>;

/**
 * Parse a CSV text string into array of typed objects.
 * Uses a lightweight manual parser to avoid bundling PapaParse server-side.
 */
function parseCsv(text: string): CsvRow[] {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''));
  return lines.slice(1).map((line) => {
    // Handle quoted fields with commas
    const values: string[] = [];
    let inQuote = false;
    let cur = '';
    for (const ch of line) {
      if (ch === '"') { inQuote = !inQuote; continue; }
      if (ch === ',' && !inQuote) { values.push(cur.trim()); cur = ''; continue; }
      cur += ch;
    }
    values.push(cur.trim());
    return Object.fromEntries(headers.map((h, i) => [h, values[i] ?? '']));
  });
}

/** Fetch and parse a CSV from /data/ static folder */
async function fetchCsv(filename: string): Promise<CsvRow[]> {
  const res = await fetch(`/data/${filename}`);
  if (!res.ok) throw new Error(`Gagal memuat ${filename}: ${res.status}`);
  const text = await res.text();
  return parseCsv(text);
}

// ─────────────────────────────────────────
// TYPED LOADERS
// ─────────────────────────────────────────

import type {
  PredictionRow,
  ObservasiRow,
  TestDataRow,
  ModelRankingRow,
  OverfittingRow,
  TrainingSummaryRow,
  PredictionSummaryRow,
} from './types';

export async function loadPredictionData(): Promise<PredictionRow[]> {
  const rows = await fetchCsv('predictions_gab8.csv');
  return rows.map((r) => ({
    SID: r['SID'] ?? '',
    NAME: r['NAME'],
    ISO_TIME: r['ISO_TIME'] ?? '',
    LAT_ACTUAL: parseFloat(r['LAT_ACTUAL'] ?? '0'),
    LON_ACTUAL: parseFloat(r['LON_ACTUAL'] ?? '0'),
    LAT_PRED: parseFloat(r['LAT_PRED'] ?? '0'),
    LON_PRED: parseFloat(r['LON_PRED'] ?? '0'),
    ERROR_KM: parseFloat(r['ERROR_KM'] ?? '0'),
  }));
}

export async function loadTestData(): Promise<TestDataRow[]> {
  const rows = await fetchCsv('model_gab_test_fix.csv');
  return rows.map((r) => ({
    SID: r['SID'] ?? '',
    NAME: r['NAME'],
    ISO_TIME: r['ISO_TIME'] ?? '',
    LAT: parseFloat(r['LAT'] ?? '0'),
    LON: parseFloat(r['LON'] ?? '0'),
  }));
}

export async function loadObservasiData(): Promise<ObservasiRow[]> {
  const rows = await fetchCsv('data_observasi.csv');
  return rows.map((r) => ({
    SID: r['SID'] ?? '',
    NAME: r['NAME'],
    ISO_TIME: r['ISO_TIME'] ?? '',
    LAT: parseFloat(r['LAT'] ?? '0'),
    LON: parseFloat(r['LON'] ?? '0'),
    WMO_WIND: parseFloat(r['WMO_WIND'] ?? '0'),
    WMO_PRES: parseFloat(r['WMO_PRES'] ?? '0'),
    wind_imputation: r['wind_imputation'],
    pres_imputation: r['pres_imputation'],
    'Status Wind': r['Status Wind'],
    'Status Pres': r['Status Pres'],
  }));
}

export async function loadModelRankingHaversine(): Promise<ModelRankingRow[]> {
  const rows = await fetchCsv('model_ranking_arversine.csv');
  return rows.map((r) => ({
    Scenario: r['Scenario'] ?? '',
    Window: r['Window'] ?? '',
    'Mean Haversine (km)': parseFloat(r['Mean Haversine (km)'] ?? '0'),
    'Min Haversine (km)': parseFloat(r['Min Haversine (km)'] ?? '0'),
    'Max Haversine (km)': parseFloat(r['Max Haversine (km)'] ?? '0'),
    'MAE LAT': parseFloat(r['MAE LAT'] ?? '0'),
    'MAE LON': parseFloat(r['MAE LON'] ?? '0'),
    'RMSE LAT': parseFloat(r['RMSE LAT'] ?? '0'),
    'RMSE LON': parseFloat(r['RMSE LON'] ?? '0'),
  }));
}

export async function loadModelRanking(): Promise<ModelRankingRow[]> {
  const rows = await fetchCsv('model_ranking.csv');
  return rows.map((r) => ({
    Scenario: r['Scenario'] ?? '',
    Window: r['Window'] ?? '',
    'R² Latitude': parseFloat(r['R² Latitude'] ?? '0'),
    'R² Longitude': parseFloat(r['R² Longitude'] ?? '0'),
    'R² Mean': parseFloat(r['R² Mean'] ?? '0'),
  }));
}

export async function loadOverfittingSummary(): Promise<OverfittingRow[]> {
  const rows = await fetchCsv('overfitting_summary.csv');
  return rows.map((r) => ({
    Scenario: r['Scenario'] ?? '',
    Window: r['Window'] ?? '',
    'Train Loss': parseFloat(r['Train Loss'] ?? '0'),
    'Validation Loss': parseFloat(r['Validation Loss'] ?? '0'),
    Gap: parseFloat(r['Gap'] ?? '0'),
    'Gap (%)': parseFloat(r['Gap (%)'] ?? '0'),
  }));
}

export async function loadTrainingSummary(): Promise<TrainingSummaryRow[]> {
  const rows = await fetchCsv('training_summary.csv');
  return rows.map((r) => ({
    Scenario: r['Scenario'] ?? '',
    Window: r['Window'] ?? '',
    'Train Samples': parseInt(r['Train Samples'] ?? '0'),
    'Validation Samples': parseInt(r['Validation Samples'] ?? '0'),
    Epoch: parseInt(r['Epoch'] ?? '0'),
    'Best Train Loss': parseFloat(r['Best Train Loss'] ?? '0'),
    'Best Validation Loss': parseFloat(r['Best Validation Loss'] ?? '0'),
    'Training Time (Second)': parseFloat(r['Training Time (Second)'] ?? '0'),
  }));
}

export async function loadPredictionSummary(): Promise<PredictionSummaryRow[]> {
  const rows = await fetchCsv('prediction_summary.csv');
  return rows.map((r) => ({
    Scenario: r['Scenario'] ?? '',
    Window: r['Window'] ?? '',
    'Prediction Time (Second)': parseFloat(r['Prediction Time (Second)'] ?? '0'),
  }));
}

// ─────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────

export function haversineKmSimple(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.asin(Math.sqrt(a));
}
