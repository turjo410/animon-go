import 'package:animon_go/core/constants/creatures.dart';
import 'package:animon_go/core/game/battle_engine.dart';
import 'package:animon_go/data/models/enums.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/vectors.dart';

void main() {
  group('battle engine (FR-013..017, research R19) matches shared/game-vectors/battle.json', () {
    for (final c in loadVectors('battle')) {
      test(c.str('name'), () {
        final i = c.obj('input');
        final e = c.obj('expected');
        final allies = i
            .list('allies')
            .map((a) => (id: (a as Map<String, dynamic>).str('id'), level: a.integer('level')))
            .toList();
        var state = createBattle(allies: allies, wave: i.integer('wave'));
        var accepted = 0;
        for (final a in i.list('actions')) {
          final next = battleTurn(state, BattleAction.fromWire(a as String));
          if (!identical(next, state)) accepted++;
          state = next;
        }
        expect(state.status.wireName, e.str('status'));
        expect(state.turn, e.integer('turn'));
        expect(accepted, e.integer('accepted_actions'));
        expect(state.allies.map((u) => u.hp).toList(), e.list('allies_hp'));
        expect(state.allies.map((u) => u.maxHp).toList(), e.list('allies_max_hp'));
        expect(state.enemies.map((u) => u.hp).toList(), e.list('enemies_hp'));
        expect(state.enemies.map((u) => u.maxHp).toList(), e.list('enemies_max_hp'));
        expect(
          state.allies.map((u) => [u.skillCooldown, u.healCooldown]).toList(),
          e.list('cooldowns'),
        );
        expect(state.active, e.integer('active'));
        expect(state.target, e.integer('target'));
      });
    }
  });

  const starters = [(id: 'mosslyn', level: 5), (id: 'cindertail', level: 4), (id: 'dewfin', level: 3)];

  test('a rejected action returns the identical state (no turn consumed, US2-3)', () {
    final s1 = battleTurn(createBattle(allies: starters, wave: 1), BattleAction.skill);
    final s2 = battleTurn(s1, BattleAction.skill);
    expect(identical(s1, s2), isTrue);
    expect(s2.turn, s1.turn);
  });

  test('accepted actions are recorded for server replay (research R4)', () {
    var s = createBattle(allies: starters, wave: 1);
    s = battleTurn(s, BattleAction.skill);
    s = battleTurn(s, BattleAction.skill); // rejected, not recorded
    s = battleTurn(s, BattleAction.basic);
    expect(s.actions.map((m) => m.action), [BattleAction.skill, BattleAction.basic]);
  });

  test('replay of the recorded actions reproduces the same end state', () {
    var s = createBattle(allies: starters, wave: 1);
    for (final a in [BattleAction.skill, BattleAction.basic, BattleAction.heal, BattleAction.skill, BattleAction.guard]) {
      s = battleTurn(s, a);
    }
    final replayed = replay(allies: starters, wave: 1, moves: s.actions);
    expect(replayed.allies.map((u) => u.hp), s.allies.map((u) => u.hp));
    expect(replayed.enemies.map((u) => u.hp), s.enemies.map((u) => u.hp));
    expect(replayed.turn, s.turn);
  });

  test('wave n fields enemyRotation[(n-1) % 5] with wave scaling (research R18)', () {
    for (var wave = 1; wave <= 7; wave++) {
      final s = createBattle(allies: starters, wave: wave);
      final trio = enemyRotation[(wave - 1) % 5];
      expect(s.enemies.map((u) => u.creatureId), trio, reason: 'wave $wave');
      for (var slot = 0; slot < 3; slot++) {
        expect(s.enemies[slot].maxHp, findCreature(trio[slot]).baseHp + (wave - 1) * 12 + slot * 3);
        expect(s.enemies[slot].level, wave);
      }
    }
  });

  test('selecting a target only accepts living enemies', () {
    final s = createBattle(allies: starters, wave: 1);
    expect(selectTarget(s, 2).target, 2);
    expect(identical(selectTarget(s, 5), s), isTrue);
  });

  test('createBattle requires exactly three distinct allies (FR-012)', () {
    expect(() => createBattle(allies: starters.sublist(0, 2), wave: 1), throwsArgumentError);
    expect(() => createBattle(allies: [starters[0], starters[0], starters[1]], wave: 1), throwsArgumentError);
    expect(() => createBattle(allies: starters, wave: 0), throwsArgumentError);
  });
}
