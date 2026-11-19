import 'package:animon_go/core/game/familiarity.dart';
import 'package:animon_go/data/models/encounter.dart';
import 'package:animon_go/data/models/enums.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/vectors.dart';

Encounter _enc(Map<String, dynamic> j) => Encounter(
      family: Family.fromWire(j.str('family')),
      occurredAt: DateTime.fromMillisecondsSinceEpoch(j.integer('time'), isUtc: true),
      lat: j['lat'] == null ? null : j.dbl('lat'),
      lon: j['lon'] == null ? null : j.dbl('lon'),
      isDemo: (j['demo'] as bool?) ?? false,
    );

void main() {
  group('familiarity (FR-007, research R8) matches shared/game-vectors/familiarity.json', () {
    for (final c in loadVectors('familiarity')) {
      test(c.str('name'), () {
        final input = c.obj('input');
        final tag = familiarity(
          _enc(input.obj('current')),
          input.list('history').map((e) => _enc(e as Map<String, dynamic>)).toList(),
        );
        expect(tag.wireName, c.obj('expected').str('tag'));
      });
    }
  });

  test('labels never imply individual identity (FR-008)', () {
    for (final t in FamiliarityTag.values) {
      expect(t.label.toLowerCase(), isNot(anyOf(contains('same'), contains('recogni'), contains('identif'))));
    }
  });
}
