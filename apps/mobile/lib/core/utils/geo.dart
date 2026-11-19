import 'dart:math' as math;

/// Rounds a coordinate to 3 decimal places (~110 m) before it leaves the device or is
/// stored (FR-009 / SRS FR-122, research R9).
double roundCoord(double value) => (value * 1000).round() / 1000;

/// Equirectangular distance in metres, exactly as the prototype computes it
/// (animon-web familiarity): hypot(Δlat·111000, Δlon·111000·cos(lat)).
/// Kept identical (including operation order) for parity with the TS engine.
double distanceMeters({
  required double fromLat,
  required double fromLon,
  required double toLat,
  required double toLon,
}) {
  final dy = (toLat - fromLat) * 111000;
  final dx = (toLon - fromLon) * 111000 * math.cos((fromLat * math.pi) / 180);
  return math.sqrt(dx * dx + dy * dy);
}
