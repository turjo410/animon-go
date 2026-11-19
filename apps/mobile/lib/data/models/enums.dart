/// Domain enumerations. `wireName` matches the snake_case strings used by the
/// backend (specs/001-mobile-core-loop/contracts/backend-api.md) and the shared
/// game vectors (shared/game-vectors/).
library;

T _fromWire<T extends Enum>(List<T> values, String wire, String Function(T) name) =>
    values.firstWhere(
      (v) => name(v) == wire,
      orElse: () => throw ArgumentError.value(wire, 'wire', 'Unknown ${T.toString()}'),
    );

enum Family {
  feline,
  canine,
  avian,
  rodent,
  insect;

  String get wireName => name;
  static Family fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

enum CreatureElement {
  earth,
  fire,
  water,
  air,
  light,
  dark;

  String get wireName => name;
  static CreatureElement fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

enum Rarity {
  common,
  uncommon,
  rare;

  String get wireName => name;
  static Rarity fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

enum Attunement {
  day,
  rain,
  night;

  String get wireName => name;
  static Attunement fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

/// Only `simulated` exists in this feature (FR-006). A real weather feed is Roadmap Phase 4.
enum AttunementSource {
  simulated;

  String get wireName => name;
  static AttunementSource fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

/// Familiarity is a heuristic, never biometric identity (FR-008, constitution III).
enum FamiliarityTag {
  newEncounter('New encounter'),
  probablyFamiliar('Probably familiar'),
  returningPresence('Returning presence');

  const FamiliarityTag(this.label);
  final String label;

  String get wireName => name;
  static FamiliarityTag fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

enum BattleAction {
  basic,
  skill,
  heal,
  guard;

  String get wireName => name;
  static BattleAction fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

enum BattleStatus {
  active,
  victory,
  defeat,
  abandoned;

  String get wireName => name;
  static BattleStatus fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}

enum TrailId {
  scan,
  bond,
  trial;

  String get wireName => name;
  static TrailId fromWire(String w) => _fromWire(values, w, (v) => v.wireName);
}
