import '../../data/models/creature.dart';
import '../../data/models/enums.dart';
import '../constants/economy.dart';
import 'progression.dart';

/// Which element each element beats (FR-015): Fire > Earth > Water > Fire,
/// Air > Earth, Light and Dark beat each other.
const Map<CreatureElement, CreatureElement> strongAgainst = {
  CreatureElement.fire: CreatureElement.earth,
  CreatureElement.earth: CreatureElement.water,
  CreatureElement.water: CreatureElement.fire,
  CreatureElement.air: CreatureElement.earth,
  CreatureElement.light: CreatureElement.dark,
  CreatureElement.dark: CreatureElement.light,
};

bool hasAdvantage(CreatureElement attacker, CreatureElement defender) => strongAgainst[attacker] == defender;

/// Damage before rounding and the minimum floor.
double rawDamage({
  required int attack,
  required int defense,
  required bool advantaged,
  double power = 1,
  bool guard = false,
}) =>
    (attack * power - defense * defenseFactor) *
    (advantaged ? advantageMultiplier : 1) *
    (guard ? guardMultiplier : 1);

/// JavaScript `Math.round` semantics (half rounds toward +∞), so the client and the
/// TS server replay produce identical integers.
int jsRound(double x) => (x + 0.5).floor();

/// max(4, round((atk·power − def·0.3) · (adv ? 1.4 : 1) · (guard ? 0.5 : 1)))  (research R19)
int damage({
  required int attack,
  required CreatureElement attackerElement,
  required int defense,
  required CreatureElement defenderElement,
  double power = 1,
  bool guard = false,
}) {
  final d = jsRound(rawDamage(
    attack: attack,
    defense: defense,
    advantaged: hasAdvantage(attackerElement, defenderElement),
    power: power,
    guard: guard,
  ));
  return d < minDamage ? minDamage : d;
}

/// Convenience: a levelled ally attacking a creature. Enemy attacks use the
/// creature's base attack (pass `attackerLevel: 1`), exactly as in the prototype.
int damageBetween({
  required CreatureDefinition attacker,
  required int attackerLevel,
  required CreatureDefinition defender,
  double power = 1,
  bool guard = false,
}) =>
    damage(
      attack: effectiveAttack(attacker, attackerLevel),
      attackerElement: attacker.element,
      defense: defender.defense,
      defenderElement: defender.element,
      power: power,
      guard: guard,
    );
