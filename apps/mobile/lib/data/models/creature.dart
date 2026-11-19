import 'enums.dart';

/// Static definition of one of the 15 elemental variants, shared by every player
/// (data-model §2). Owned instances live in [OwnedCompanion].
final class CreatureDefinition {
  const CreatureDefinition({
    required this.id,
    required this.name,
    required this.family,
    required this.element,
    required this.rarity,
    required this.description,
    required this.baseHp,
    required this.attack,
    required this.defense,
    required this.speed,
    required this.skillName,
    required this.passiveName,
    required this.spriteIndex,
    this.hue = 0,
  });

  final String id;
  final String name;
  final Family family;
  final CreatureElement element;
  final Rarity rarity;
  final String description;
  final int baseHp;
  final int attack;
  final int defense;
  final int speed;
  final String skillName;
  final String passiveName;
  final int spriteIndex;
  final int hue;

  @override
  bool operator ==(Object other) => other is CreatureDefinition && other.id == id;

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() => 'CreatureDefinition($id)';
}
