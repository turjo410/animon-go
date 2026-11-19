// Deterministic 3v3 PvE battle engine (FR-013..017), ported exactly from the
// prototype's createBattle/battleTurn (animon-web/src/lib/game.ts, read-only),
// except for the wave-based enemy rotation (research R18).
//
// Determinism matters: the server replays the recorded moves with the TS port
// of this engine to verify a win before granting the reward (research R4).
// Both engines are checked against shared/game-vectors/battle.json.

import '../../data/models/enums.dart';
import '../constants/creatures.dart';
import '../constants/economy.dart';
import 'damage.dart';
import 'progression.dart';

typedef AllySpec = ({String id, int level});

final class BattleUnit {
  const BattleUnit({
    required this.creatureId,
    required this.level,
    required this.hp,
    required this.maxHp,
    this.skillCooldown = 0,
    this.healCooldown = 0,
  });

  final String creatureId;
  final int level;
  final int hp;
  final int maxHp;
  final int skillCooldown;
  final int healCooldown;

  bool get alive => hp > 0;

  BattleUnit copyWith({int? hp, int? skillCooldown, int? healCooldown}) => BattleUnit(
        creatureId: creatureId,
        level: level,
        hp: hp ?? this.hp,
        maxHp: maxHp,
        skillCooldown: skillCooldown ?? this.skillCooldown,
        healCooldown: healCooldown ?? this.healCooldown,
      );
}

/// One accepted player move, recorded for server replay.
final class BattleMove {
  const BattleMove(this.action, {required this.target});

  final BattleAction action;

  /// The enemy index targeted when the move was made.
  final int target;

  Map<String, Object> toJson() => {'action': action.wireName, 'target': target};
}

final class BattleState {
  const BattleState({
    required this.wave,
    required this.turn,
    required this.allies,
    required this.enemies,
    required this.active,
    required this.target,
    required this.guardUp,
    required this.status,
    required this.log,
    required this.actions,
  });

  final int wave;
  final int turn;
  final List<BattleUnit> allies;
  final List<BattleUnit> enemies;
  final int active;
  final int target;
  final bool guardUp;
  final BattleStatus status;

  /// Newest first, at most 12 lines.
  final List<String> log;

  /// Accepted moves, in order (rejected moves are not recorded).
  final List<BattleMove> actions;

  BattleUnit get activeAlly => allies[active];

  BattleState _copy({
    int? turn,
    List<BattleUnit>? allies,
    List<BattleUnit>? enemies,
    int? active,
    int? target,
    bool? guardUp,
    BattleStatus? status,
    List<String>? log,
    List<BattleMove>? actions,
  }) =>
      BattleState(
        wave: wave,
        turn: turn ?? this.turn,
        allies: allies ?? this.allies,
        enemies: enemies ?? this.enemies,
        active: active ?? this.active,
        target: target ?? this.target,
        guardUp: guardUp ?? this.guardUp,
        status: status ?? this.status,
        log: log ?? this.log,
        actions: actions ?? this.actions,
      );
}

/// Enemy trio for a wave: enemyRotation[(wave − 1) % 5] (research R18).
List<String> enemyTrio(int wave) => enemyRotation[(wave - 1) % enemyRotation.length];

/// Starts a trial. Requires exactly three distinct allies (FR-012) and wave ≥ 1.
BattleState createBattle({required List<AllySpec> allies, required int wave}) {
  if (allies.length != 3 || allies.map((a) => a.id).toSet().length != 3) {
    throw ArgumentError.value(allies, 'allies', 'exactly three distinct allies are required');
  }
  if (wave < 1) throw ArgumentError.value(wave, 'wave', 'must be >= 1');

  final allyUnits = [
    for (final a in allies)
      () {
        final hp = maxHp(findCreature(a.id), a.level);
        return BattleUnit(creatureId: a.id, level: a.level, hp: hp, maxHp: hp);
      }(),
  ];
  final trio = enemyTrio(wave);
  final enemyUnits = [
    for (var i = 0; i < trio.length; i++)
      () {
        final hp = findCreature(trio[i]).baseHp + (wave - 1) * enemyHpPerWave + i * enemyHpPerSlot;
        return BattleUnit(creatureId: trio[i], level: wave, hp: hp, maxHp: hp);
      }(),
  ];
  return BattleState(
    wave: wave,
    turn: 1,
    allies: List.unmodifiable(allyUnits),
    enemies: List.unmodifiable(enemyUnits),
    active: 0,
    target: 0,
    guardUp: false,
    status: BattleStatus.active,
    log: const ['The woodland trial begins. Your elemental spirits are ready.'],
    actions: const [],
  );
}

/// Points the player's attacks at another living enemy. Returns the same state
/// if the index is invalid or that enemy has fallen.
BattleState selectTarget(BattleState s, int enemyIndex) {
  if (s.status != BattleStatus.active) return s;
  if (enemyIndex < 0 || enemyIndex >= s.enemies.length || !s.enemies[enemyIndex].alive) return s;
  return s._copy(target: enemyIndex);
}

/// Applies one player action and the enemy response.
///
/// Returns the IDENTICAL state object when the action is rejected (battle over,
/// skill or heal on cooldown, active ally or target down), so no turn is consumed
/// (US2 scenario 3).
BattleState battleTurn(BattleState b, BattleAction action) {
  if (b.status != BattleStatus.active) return b;
  final ai = b.active;
  final ti = b.target;
  if (ai < 0 || ai >= b.allies.length || ti < 0 || ti >= b.enemies.length) return b;
  var a = b.allies[ai];
  var t = b.enemies[ti];
  if (!a.alive || !t.alive) return b;
  if ((action == BattleAction.skill && a.skillCooldown > 0) ||
      (action == BattleAction.heal && a.healCooldown > 0)) {
    return b;
  }

  final ac = findCreature(a.creatureId);
  final tc = findCreature(t.creatureId);
  final log = <String>[...b.log];
  var guardUp = b.guardUp;

  // Every ally's cooldowns tick down at the start of each accepted action.
  final allies = [
    for (final u in b.allies)
      u.copyWith(
        skillCooldown: u.skillCooldown > 0 ? u.skillCooldown - 1 : 0,
        healCooldown: u.healCooldown > 0 ? u.healCooldown - 1 : 0,
      ),
  ];
  final enemies = [...b.enemies];
  a = allies[ai];

  switch (action) {
    case BattleAction.heal:
      final healed = a.hp + healAmount > a.maxHp ? a.maxHp : a.hp + healAmount;
      a = a.copyWith(hp: healed, healCooldown: healCooldown);
      log.insert(0, '${ac.name} restores $healAmount spirit energy with Renewal.');
    case BattleAction.guard:
      guardUp = true;
      log.insert(0, '${ac.name} raises an elemental ward.');
    case BattleAction.basic:
    case BattleAction.skill:
      final isSkill = action == BattleAction.skill;
      final d = damageBetween(attacker: ac, attackerLevel: a.level, defender: tc, power: isSkill ? skillPower : 1);
      t = t.copyWith(hp: t.hp - d < 0 ? 0 : t.hp - d);
      enemies[ti] = t;
      if (isSkill) a = a.copyWith(skillCooldown: skillCooldown);
      log.insert(0, '${ac.name} uses ${isSkill ? ac.skillName : 'Spirit strike'} · $d energy.');
  }
  allies[ai] = a;
  final moves = [...b.actions, BattleMove(action, target: ti)];

  if (enemies.every((e) => e.hp == 0)) {
    log.insert(0, 'Trial complete! The woodland spirits bow in respect.');
    return b._copy(
      allies: List.unmodifiable(allies),
      enemies: List.unmodifiable(enemies),
      guardUp: guardUp,
      status: BattleStatus.victory,
      log: List.unmodifiable(log),
      actions: List.unmodifiable(moves),
    );
  }

  // Enemy response: the living enemy at (turn − 1) mod living strikes the active ally.
  final living = enemies.where((e) => e.alive).toList();
  final enemy = living[(b.turn - 1) % living.length];
  final ec = findCreature(enemy.creatureId);
  final taken = damage(
    attack: ec.attack,
    attackerElement: ec.element,
    defense: ac.defense,
    defenderElement: ac.element,
    power: 1 + (b.wave - 1) * enemyPowerPerWave,
    guard: guardUp,
  );
  a = a.copyWith(hp: a.hp - taken < 0 ? 0 : a.hp - taken);
  allies[ai] = a;
  log.insert(0, '${ec.name} responds · $taken energy.');
  guardUp = false;

  var status = BattleStatus.active;
  var active = ai;
  if (allies.every((u) => u.hp == 0)) {
    status = BattleStatus.defeat;
  } else if (a.hp == 0) {
    active = allies.indexWhere((u) => u.hp > 0);
  }
  var target = ti;
  if (t.hp == 0) target = enemies.indexWhere((e) => e.hp > 0);

  return b._copy(
    turn: b.turn + 1,
    allies: List.unmodifiable(allies),
    enemies: List.unmodifiable(enemies),
    active: active,
    target: target,
    guardUp: guardUp,
    status: status,
    log: List.unmodifiable(log.take(battleLogLimit)),
    actions: List.unmodifiable(moves),
  );
}

/// Re-runs recorded moves from a fresh battle. Used by the local repository and
/// mirrored by the server's complete-trial replay (research R4).
BattleState replay({required List<AllySpec> allies, required int wave, required List<BattleMove> moves}) {
  var s = createBattle(allies: allies, wave: wave);
  for (final m in moves) {
    s = selectTarget(s, m.target);
    s = battleTurn(s, m.action);
  }
  return s;
}
