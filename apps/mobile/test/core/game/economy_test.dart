import 'package:animon_go/core/constants/creatures.dart';
import 'package:animon_go/core/game/progression.dart';
import 'package:animon_go/data/models/owned_companion.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/vectors.dart';

OwnedCompanion _c(int level, int bond) => OwnedCompanion(
      creatureId: 'mosslyn',
      level: level,
      bond: bond,
      discoveredContext: 'test',
      acquiredAt: DateTime.utc(2026),
    );

void main() {
  group('economy (FR-011, research R16) matches shared/game-vectors/economy.json', () {
    for (final c in loadVectors('economy')) {
      test(c.str('name'), () {
        final i = c.obj('input');
        final e = c.obj('expected');
        switch (i.str('op')) {
          case 'train':
            final r = applyTraining(_c(i.integer('level'), i.integer('bond')));
            expect((r.level, r.bond), (e.integer('level'), e.integer('bond')));
          case 'discover_owned':
            final r = applyOwnedDiscovery(_c(i.integer('level'), i.integer('bond')));
            expect((r.level, r.bond), (e.integer('level'), e.integer('bond')));
          case 'discover_new':
            final r = newCompanion('solcat', context: 'Local discovery', at: DateTime.utc(2026));
            expect((r.level, r.bond), (e.integer('level'), e.integer('bond')));
          case 'player_level':
            expect(playerLevelForXp(i.integer('xp')), e.integer('level'));
          case 'max_hp':
            expect(maxHp(findCreature(i.str('creature_id')), i.integer('level')), e.integer('max_hp'));
          case 'effective_attack':
            expect(effectiveAttack(findCreature(i.str('creature_id')), i.integer('level')), e.integer('attack'));
          default:
            fail('unknown op ${i.str('op')}');
        }
      });
    }
  });

  test('training never mutates the input', () {
    final before = _c(3, 10);
    applyTraining(before);
    expect((before.level, before.bond), (3, 10));
  });
}
