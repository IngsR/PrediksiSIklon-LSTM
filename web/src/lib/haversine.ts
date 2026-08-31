// Haversine & bearing utilities — port dari prediction/inference.py

const R = 6371.0; // Earth radius km

export function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

/**
 * Haversine distance in km between two lat/lon points.
 * Port dari Python haversine() dalam inference.py
 */
export function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const dPhi = toRad(lat2 - lat1);
  const dLam = toRad(lon2 - lon1);

  const a =
    Math.sin(dPhi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLam / 2) ** 2;

  return R * 2 * Math.asin(Math.sqrt(a));
}

/**
 * Bearing (azimuth) in degrees [0, 360) from point 1 to point 2.
 * Port dari Python bearing() dalam inference.py
 */
export function bearing(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const dLon = toRad(lon2 - lon1);

  const x = Math.sin(dLon) * Math.cos(phi2);
  const y =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(dLon);

  const angle = (Math.atan2(x, y) * 180) / Math.PI;
  return (angle + 360) % 360;
}

/**
 * Absolute angular difference between two bearings, clamped to [0, 180].
 */
export function angleDiff(b1: number, b2: number): number {
  let diff = b2 - b1;
  diff = ((diff + 180) % 360) - 180;
  return Math.abs(diff);
}
