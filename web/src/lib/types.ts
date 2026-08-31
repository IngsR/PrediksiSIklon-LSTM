// TypeScript type definitions — port dari Python data structures

export interface ObservationPoint {
  LAT: number;
  LON: number;
  WMO_WIND: number;
  WMO_PRES: number;
  ISO_TIME?: string;
}

export interface PredictionResult {
  pred_lat: number;
  pred_lon: number;
  time: string;      // ISO string
}

export interface PredictionRequest {
  observations: ObservationPoint[];
  startTime: string;  // ISO string
  steps: 1 | 2 | 3;
}

export interface PredictionResponse {
  predictions: PredictionResult[];
  error?: string;
}

// CSV data row types
export interface PredictionRow {
  SID: string;
  NAME?: string;
  ISO_TIME: string;
  LAT_ACTUAL: number;
  LON_ACTUAL: number;
  LAT_PRED: number;
  LON_PRED: number;
  ERROR_KM: number;
}

export interface ObservasiRow {
  SID: string;
  NAME?: string;
  ISO_TIME: string;
  LAT: number;
  LON: number;
  WMO_WIND: number;
  WMO_PRES: number;
  wind_imputation?: string;
  pres_imputation?: string;
  'Status Wind'?: string;
  'Status Pres'?: string;
}

export interface TestDataRow {
  SID: string;
  NAME?: string;
  ISO_TIME: string;
  LAT: number;
  LON: number;
}

export interface ModelRankingRow {
  Rank?: number;
  Scenario: string;
  Window: string | number;
  'Mean Haversine (km)'?: number;
  'Min Haversine (km)'?: number;
  'Max Haversine (km)'?: number;
  MAE?: number;
  RMSE?: number;
  'MAE LAT'?: number;
  'MAE LON'?: number;
  'RMSE LAT'?: number;
  'RMSE LON'?: number;
  'R² Latitude'?: number;
  'R² Longitude'?: number;
  'R² Mean'?: number;
}

export interface OverfittingRow {
  Scenario: string;
  Window: string | number;
  'Train Loss': number;
  'Validation Loss': number;
  Gap: number;
  'Gap (%)'?: number;
}

export interface TrainingSummaryRow {
  Scenario: string;
  Window: string | number;
  'Train Samples': number;
  'Validation Samples': number;
  Epoch: number;
  'Best Train Loss': number;
  'Best Validation Loss': number;
  'Training Time (Second)': number;
}

export interface PredictionSummaryRow {
  Scenario: string;
  Window: string | number;
  'Prediction Time (Second)': number;
}

export interface ScalerParams {
  scaler_type?: string;
  feature_names?: string[];
  mean_: number[];
  scale_: number[];
  var_?: number[];
}

export interface AnalyticsResult {
  speed_kmh: number;
  bearing: number;
  category: string;
  description: string;
}

export interface ReliabilityMetric {
  reliability: string;
  confidence_pct: number;
  uncertainty_km: string;
  text: string;
  color: string;
}
