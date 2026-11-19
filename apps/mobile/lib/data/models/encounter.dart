import 'enums.dart';

/// One discovery event, the input to familiarity (data-model §3).
/// `lat`/`lon` are already rounded to 3 dp (research R9) and are both null or both set.
final class Encounter {
  Encounter({
    required this.family,
    required this.occurredAt,
    this.lat,
    this.lon,
    this.isDemo = false,
    this.attunement = Attunement.day,
    this.attunementSource = AttunementSource.simulated,
  }) {
    if ((lat == null) != (lon == null)) {
      throw ArgumentError('lat and lon must both be null or both be set');
    }
  }

  final Family family;
  final DateTime occurredAt;
  final double? lat;
  final double? lon;
  final bool isDemo;
  final Attunement attunement;
  final AttunementSource attunementSource;

  bool get hasLocation => lat != null && lon != null;

  @override
  bool operator ==(Object other) =>
      other is Encounter &&
      other.family == family &&
      other.occurredAt == occurredAt &&
      other.lat == lat &&
      other.lon == lon &&
      other.isDemo == isDemo &&
      other.attunement == attunement &&
      other.attunementSource == attunementSource;

  @override
  int get hashCode => Object.hash(family, occurredAt, lat, lon, isDemo, attunement, attunementSource);
}
