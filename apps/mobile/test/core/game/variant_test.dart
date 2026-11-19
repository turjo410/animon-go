import 'package:animon_go/core/game/variant.dart';
import 'package:animon_go/data/models/enums.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/vectors.dart';

void main() {
  group('chooseVariant (FR-005) matches shared/game-vectors/variant.json', () {
    final cases = loadVectors('variant');

    test('covers all 15 family x attunement pairs', () => expect(cases, hasLength(15)));

    for (final c in cases) {
      test(c.str('name'), () {
        final input = c.obj('input');
        final result = chooseVariant(
          Family.fromWire(input.str('family')),
          Attunement.fromWire(input.str('attunement')),
        );
        expect(result.id, c.obj('expected').str('creature_id'));
      });
    }
  });

  test('every variant is unique (5 families x 3 attunements -> 15 creatures)', () {
    final ids = {
      for (final f in Family.values)
        for (final a in Attunement.values) chooseVariant(f, a).id,
    };
    expect(ids, hasLength(15));
  });
}
