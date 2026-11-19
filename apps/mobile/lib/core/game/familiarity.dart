import '../../data/models/encounter.dart';
import '../../data/models/enums.dart';
import '../constants/creatures.dart';
import '../constants/economy.dart';
import '../utils/geo.dart';

/// Tags an encounter as New encounter / Probably familiar / Returning presence
/// (FR-007). This is a heuristic based on animal family, time and rough location.
/// It is NEVER biometric identity (FR-008, constitution III).
///
/// Rule (specs/001-mobile-core-loop/research.md R8):
/// For each prior encounter of the same family with 0 <= Δt < 7 days:
///  * demo: a *strong* match only if both are demo (demo never matches real);
///  * real, both located: *strong* if distance < the family radius;
///  * real, either unlocated: *weak* (family + recency fallback).
/// No matches -> New encounter; more than one strong -> Returning presence;
/// otherwise Probably familiar (so missing location is capped below Returning).
FamiliarityTag familiarity(Encounter current, List<Encounter> history) {
  var strong = 0;
  var weak = 0;
  final windowMs = familiarityWindow.inMilliseconds;
  for (final prior in history) {
    if (prior.family != current.family) continue;
    final dt = current.occurredAt.millisecondsSinceEpoch - prior.occurredAt.millisecondsSinceEpoch;
    if (dt < 0 || dt >= windowMs) continue;

    if (current.isDemo || prior.isDemo) {
      if (current.isDemo && prior.isDemo) strong++;
      continue;
    }
    if (current.hasLocation && prior.hasLocation) {
      final d = distanceMeters(
        fromLat: current.lat!,
        fromLon: current.lon!,
        toLat: prior.lat!,
        toLon: prior.lon!,
      );
      if (d < familiarityRadiusMeters[current.family]!) strong++;
    } else {
      weak++;
    }
  }
  if (strong + weak == 0) return FamiliarityTag.newEncounter;
  if (strong > 1) return FamiliarityTag.returningPresence;
  return FamiliarityTag.probablyFamiliar;
}
