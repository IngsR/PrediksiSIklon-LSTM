// StandardScaler port — mirrors sklearn.preprocessing.StandardScaler behavior
import type { ScalerParams } from './types';

/**
 * Transform (standardize) values using pre-computed StandardScaler params.
 * Formula: z = (x - mean_) / scale_
 */
export function scalerTransform(
  row: number[],
  params: ScalerParams
): number[] {
  return row.map((val, i) => {
    const scale = params.scale_[i];
    const mean = params.mean_[i];
    if (scale === 0 || isNaN(scale)) return 0;
    return (val - mean) / scale;
  });
}

/**
 * Inverse transform (unstandardize) values.
 * Formula: x = z * scale_ + mean_
 */
export function scalerInverseTransform(
  row: number[],
  params: ScalerParams
): number[] {
  return row.map((val, i) => {
    const scale = params.scale_[i];
    const mean = params.mean_[i];
    return val * scale + mean;
  });
}

/**
 * Transform a 2D matrix (rows × features) using scaler.
 */
export function scalerTransformMatrix(
  matrix: number[][],
  params: ScalerParams
): number[][] {
  return matrix.map((row) => scalerTransform(row, params));
}
