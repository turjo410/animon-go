import 'package:animon_go/core/constants/creatures.dart';
import 'package:animon_go/core/game/damage.dart';
import 'package:animon_go/data/models/enums.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/vectors.dart';

void main() {
  group('damage (FR-015, research R19) matches shared/game-vectors/damage.json', () {
    for (final c in loadVectors('damage')) {
      test(c.str('name'), () {
        final i = c.obj('input');
        final d = damageBetween(
          attacker: findCreature(i.str('attacker_id')),
          attackerLevel: i.integer('attacker_level'),
          defender: findCreature(i.str('defender_id')),
          power: i.dbl('power'),
          guard: i['guard'] as bool,
        );
        expect(d, c.obj('expected').integer('damage'));
      });
    }
  });

  test('advantage table: Fire>Earth>Water>Fire, Air>Earth, Light<->Dark', () {
    expect(hasAdvantage(CreatureElement.fire, CreatureElement.earth), isTrue);
    expect(hasAdvantage(CreatureElement.earth, CreatureElement.water), isTrue);
    expect(hasAdvantage(CreatureElement.water, CreatureElement.fire), isTrue);
    expect(hasAdvantage(CreatureElement.air, CreatureElement.earth), isTrue);
    expect(hasAdvantage(CreatureElement.light, CreatureElement.dark), isTrue);
    expect(hasAdvantage(CreatureElement.dark, CreatureElement.light), isTrue);
    expect(hasAdvantage(CreatureElement.earth, CreatureElement.air), isFalse);
    expect(hasAdvantage(CreatureElement.earth, CreatureElement.fire), isFalse);
  });

  test('advantaged damage is 40% above the neutral baseline before rounding', () {
    final neutral = rawDamage(attack: 30, defense: 15, advantaged: false);
    final adv = rawDamage(attack: 30, defense: 15, advantaged: true);
    expect(adv / neutral, closeTo(1.4, 1e-9));
  });
}
