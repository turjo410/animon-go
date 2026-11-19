import 'package:animon_go/core/constants/creatures.dart';
import 'package:animon_go/data/models/enums.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('exactly 15 definitions with unique ids', () {
    expect(creatures, hasLength(15));
    expect(creatures.map((c) => c.id).toSet(), hasLength(15));
  });

  test('each family has exactly three variants', () {
    for (final f in Family.values) {
      expect(creatures.where((c) => c.family == f), hasLength(3), reason: f.name);
    }
  });

  test('findCreature resolves and rejects unknown ids', () {
    expect(findCreature('solcat').name, 'Solcat');
    expect(() => findCreature('pikachu'), throwsArgumentError);
  });

  test('enemy rotation covers all 15 creatures exactly once', () {
    final all = enemyRotation.expand((t) => t).toList();
    expect(all, hasLength(15));
    expect(all.toSet(), creatures.map((c) => c.id).toSet());
  });
}
