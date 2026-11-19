import 'dart:convert';
import 'dart:io';

/// Loads a shared golden-vector file (`shared/game-vectors/<name>.json`).
/// `flutter test` runs with the package root (apps/mobile) as the working directory.
List<Map<String, dynamic>> loadVectors(String name) {
  final file = File('../../shared/game-vectors/$name.json');
  if (!file.existsSync()) {
    throw StateError('Missing ${file.absolute.path} — run: node shared/game-vectors/generate.mjs');
  }
  final cases = (jsonDecode(file.readAsStringSync()) as List<dynamic>).cast<Map<String, dynamic>>();
  if (cases.isEmpty) throw StateError('${file.path} has no cases');
  return cases;
}

extension JsonMap on Map<String, dynamic> {
  Map<String, dynamic> obj(String key) => this[key] as Map<String, dynamic>;
  List<dynamic> list(String key) => this[key] as List<dynamic>;
  String str(String key) => this[key] as String;
  int integer(String key) => (this[key] as num).toInt();
  double dbl(String key) => (this[key] as num).toDouble();
}
