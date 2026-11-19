/// A creature instance held by one player (data-model §3). `level` (≥1), `bond` (0–100).
final class OwnedCompanion {
  OwnedCompanion({
    required this.creatureId,
    required this.level,
    required this.bond,
    required this.discoveredContext,
    required this.acquiredAt,
  }) {
    if (level < 1) throw ArgumentError.value(level, 'level', 'must be >= 1');
    if (bond < 0 || bond > 100) throw ArgumentError.value(bond, 'bond', 'must be 0..100');
  }

  final String creatureId;
  final int level;
  final int bond;
  final String discoveredContext;
  final DateTime acquiredAt;

  OwnedCompanion copyWith({int? level, int? bond}) => OwnedCompanion(
        creatureId: creatureId,
        level: level ?? this.level,
        bond: bond ?? this.bond,
        discoveredContext: discoveredContext,
        acquiredAt: acquiredAt,
      );

  @override
  bool operator ==(Object other) =>
      other is OwnedCompanion &&
      other.creatureId == creatureId &&
      other.level == level &&
      other.bond == bond &&
      other.discoveredContext == discoveredContext &&
      other.acquiredAt == acquiredAt;

  @override
  int get hashCode => Object.hash(creatureId, level, bond, discoveredContext, acquiredAt);

  @override
  String toString() => 'OwnedCompanion($creatureId L$level bond $bond)';
}
