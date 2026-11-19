import 'enums.dart';

/// Status of one daily trail for the server-determined local date (FR-020, research R17).
final class TrailStatus {
  const TrailStatus({
    required this.trailId,
    required this.goalMet,
    required this.claimedToday,
    required this.reward,
  });

  final TrailId trailId;
  final bool goalMet;
  final bool claimedToday;
  final int reward;

  bool get canClaim => goalMet && !claimedToday;

  @override
  bool operator ==(Object other) =>
      other is TrailStatus &&
      other.trailId == trailId &&
      other.goalMet == goalMet &&
      other.claimedToday == claimedToday &&
      other.reward == reward;

  @override
  int get hashCode => Object.hash(trailId, goalMet, claimedToday, reward);
}
