// ONNX Inference Engine — port dari prediction/inference.py
// Runs on the server side (Astro API route / Vercel Node.js)

import * as ort from 'onnxruntime-node';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { haversineKm, bearing, angleDiff } from './haversine';
import { scalerTransform, scalerInverseTransform } from './scaler';
import type { ObservationPoint, PredictionResult, ScalerParams } from './types';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MODELS_DIR = path.resolve(__dirname, '../../public/models');

// =========================================
// WINDOW SIZE & FEATURE LISTS
// =========================================
export const WINDOW_SIZE = 8;

export const MODEL_FEATURES = [
  'LAT',
  'LON',
  'WMO_WIND',
  'WMO_PRES',
  'delta_lat',
  'delta_lon',
  'speed_kmh',
  'bearing_rate',
  'acceleration',
  'sin_month',
  'cos_month',
] as const;

export const FEATURES_TO_SCALE = [
  'WMO_WIND',
  'WMO_PRES',
  'delta_lat',
  'delta_lon',
  'speed_kmh',
  'bearing_rate',
  'acceleration',
  'sin_month',
  'cos_month',
] as const;

// =========================================
// CACHED RESOURCES
// =========================================
let _session: ort.InferenceSession | null = null;
let _featureScaler: ScalerParams | null = null;
let _targetScaler: ScalerParams | null = null;

// Function to locate model and scaler files across multiple serverless / production locations
function findModelFile(filename: string): string {
  const candidates = [
    path.join(__dirname, filename),
    path.join(__dirname, 'models', filename),
    path.join(__dirname, 'public', 'models', filename),
    path.join(__dirname, '..', 'models', filename),
    path.join(__dirname, '..', 'public', 'models', filename),
    path.join(__dirname, '..', '..', 'public', 'models', filename),
    path.join(process.cwd(), 'public', 'models', filename),
    path.join(process.cwd(), 'web', 'public', 'models', filename),
    path.join(process.cwd(), '.vercel', 'output', 'static', 'models', filename),
    path.join(process.cwd(), '.vercel', 'output', '_functions', 'public', 'models', filename),
    path.join(process.cwd(), '.vercel', 'output', 'functions', '_render.func', 'models', filename),
    path.join(process.cwd(), '.vercel', 'output', 'functions', '_render.func', 'public', 'models', filename),
    path.join(process.cwd(), 'models', filename),
    path.resolve(MODELS_DIR, filename),
  ];

  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return candidates[candidates.length - 1];
}

async function loadResources() {
  if (_session && _featureScaler && _targetScaler) {
    return { session: _session, featureScaler: _featureScaler, targetScaler: _targetScaler };
  }

  const onnxPath = findModelFile('model.onnx');
  const featPath = findModelFile('feature_scaler.json');
  const tgtPath  = findModelFile('target_scaler.json');

  if (!fs.existsSync(onnxPath)) {
    throw new Error(
      `Model ONNX tidak ditemukan di ${onnxPath}. ` +
      'Pastikan model.onnx tersedia di public/models/.'
    );
  }

  // Load ONNX session using absolute path or buffer
  const modelBuffer = fs.readFileSync(onnxPath);
  _session = await ort.InferenceSession.create(modelBuffer, {
    executionProviders: ['cpu'],
  });

  _featureScaler = JSON.parse(fs.readFileSync(featPath, 'utf-8')) as ScalerParams;
  _targetScaler  = JSON.parse(fs.readFileSync(tgtPath, 'utf-8')) as ScalerParams;

  return { session: _session, featureScaler: _featureScaler, targetScaler: _targetScaler };
}


// =========================================
// FEATURE ENGINEERING
// =========================================
interface FeatureRow {
  LAT: number;
  LON: number;
  WMO_WIND: number;
  WMO_PRES: number;
  delta_lat: number;
  delta_lon: number;
  speed_kmh: number;
  bearing_rate: number;
  acceleration: number;
  sin_month: number;
  cos_month: number;
}

function engineerFeatures(
  observations: ObservationPoint[],
  startTime: Date
): FeatureRow[] {
  const n = observations.length;
  const times: Date[] = Array.from({ length: n }, (_, i) => {
    const t = new Date(startTime);
    t.setHours(t.getHours() + i * 3);
    return t;
  });

  const rows: FeatureRow[] = [];
  const bearings: number[] = [];

  for (let i = 0; i < n; i++) {
    const cur = observations[i];
    const prev = i > 0 ? observations[i - 1] : cur;

    const deltaLat = cur.LAT - prev.LAT;
    const deltaLon = cur.LON - prev.LON;

    // Delta time in hours
    const dtHours = i > 0
      ? (times[i].getTime() - times[i - 1].getTime()) / 3_600_000
      : 3;

    // Distance km between consecutive points
    const dist = i > 0 ? haversineKm(prev.LAT, prev.LON, cur.LAT, cur.LON) : 0;
    const speedKmh = dtHours > 0 ? dist / dtHours : 0;

    // Bearing
    const brng = i > 0 ? bearing(prev.LAT, prev.LON, cur.LAT, cur.LON) : 0;
    bearings.push(brng);

    // Bearing rate (angular change)
    const bearingRate = i > 1 ? angleDiff(bearings[i - 1], brng) : 0;

    // Acceleration
    const prevSpeed = i > 1 ? rows[i - 1].speed_kmh : 0;
    const acceleration = dtHours > 0 ? (speedKmh - prevSpeed) / dtHours : 0;

    // Seasonal cyclical encoding
    const month = times[i].getMonth() + 1;
    const sinMonth = Math.sin((2 * Math.PI * month) / 12);
    const cosMonth = Math.cos((2 * Math.PI * month) / 12);

    rows.push({
      LAT: cur.LAT,
      LON: cur.LON,
      WMO_WIND: cur.WMO_WIND,
      WMO_PRES: cur.WMO_PRES,
      delta_lat: deltaLat,
      delta_lon: deltaLon,
      speed_kmh: speedKmh,
      bearing_rate: bearingRate,
      acceleration,
      sin_month: sinMonth,
      cos_month: cosMonth,
    });
  }

  return rows;
}

// =========================================
// SINGLE STEP INFERENCE
// =========================================
async function runInference(
  observations: ObservationPoint[],
  startTime: Date
): Promise<{ pred_lat: number; pred_lon: number }> {
  if (observations.length !== WINDOW_SIZE) {
    throw new Error(`Data harus berisi tepat ${WINDOW_SIZE} observasi.`);
  }

  const { session, featureScaler, targetScaler } = await loadResources();

  // 1. Feature engineering
  const rows = engineerFeatures(observations, startTime);

  // 2. Scale features_to_scale
  const scaledRows = rows.map((row) => {
    const toScale = FEATURES_TO_SCALE.map((f) => row[f as keyof FeatureRow] as number);
    const scaled = scalerTransform(toScale, featureScaler);
    return { ...row, ...Object.fromEntries(FEATURES_TO_SCALE.map((f, i) => [f, scaled[i]])) } as FeatureRow;
  });

  // 3. Build input tensor (1 × WINDOW_SIZE × 11)
  const inputData = new Float32Array(WINDOW_SIZE * MODEL_FEATURES.length);
  for (let t = 0; t < WINDOW_SIZE; t++) {
    const row = scaledRows[t];
    for (let f = 0; f < MODEL_FEATURES.length; f++) {
      inputData[t * MODEL_FEATURES.length + f] = row[MODEL_FEATURES[f] as keyof FeatureRow] as number;
    }
  }

  const tensor = new ort.Tensor('float32', inputData, [1, WINDOW_SIZE, MODEL_FEATURES.length]);

  // 4. Run ONNX inference
  const inputName = session.inputNames[0];
  const results = await session.run({ [inputName]: tensor });
  const outputName = session.outputNames[0];
  const output = results[outputName]!.data as Float32Array;

  // output is [pred_lat, pred_lon] directly in degrees (matching Python inference.py)
  return { pred_lat: output[0], pred_lon: output[1] };
}

// =========================================
// RECURSIVE INFERENCE (multi-step)
// =========================================
export async function runRecursiveInference(
  observations: ObservationPoint[],
  startTime: Date,
  steps: number
): Promise<PredictionResult[]> {
  let current = [...observations];

  // Assign times to observations starting from startTime
  const startDt = new Date(startTime);
  const withTimes: ObservationPoint[] = current.map((obs, i) => {
    const t = new Date(startDt);
    t.setHours(t.getHours() + i * 3);
    return { ...obs, ISO_TIME: t.toISOString() };
  });

  let window = [...withTimes];
  const predictions: PredictionResult[] = [];

  const lastObsTime = new Date(startDt);
  lastObsTime.setHours(lastObsTime.getHours() + (WINDOW_SIZE - 1) * 3);
  let currentTime = new Date(lastObsTime);

  for (let i = 0; i < steps; i++) {
    // Window start time is the timestamp of the first point in the current sliding window
    const firstPointTime = window[0].ISO_TIME ? new Date(window[0].ISO_TIME) : new Date(startDt.getTime() + i * 3 * 3600000);
    const result = await runInference(window, firstPointTime);




    const targetTime = new Date(currentTime);
    targetTime.setHours(targetTime.getHours() + 3);

    predictions.push({
      pred_lat: result.pred_lat,
      pred_lon: result.pred_lon,
      time: targetTime.toISOString(),
    });

    // Slide window
    const lastPoint = window[window.length - 1];
    const newPoint: ObservationPoint = {
      LAT: result.pred_lat,
      LON: result.pred_lon,
      WMO_WIND: lastPoint.WMO_WIND,
      WMO_PRES: lastPoint.WMO_PRES,
      ISO_TIME: targetTime.toISOString(),
    };

    window = [...window.slice(1), newPoint];
    currentTime = targetTime;
  }

  return predictions;
}
