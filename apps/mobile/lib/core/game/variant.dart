import '../../data/models/creature.dart';
import '../../data/models/enums.dart';
import '../constants/creatures.dart';

/// Deterministic family x attunement -> creature table (FR-005, data-model §2).
const Map<Family, Map<Attunement, String>> variantTable = {
  Family.feline: {Attunement.day: 'mosslyn', Attunement.rain: 'solcat', Attunement.night: 'nightpurr'},
  Family.canine: {Attunement.day: 'cindertail', Attunement.rain: 'brookhound', Attunement.night: 'zephruff'},
  Family.avian: {Attunement.day: 'breezlet', Attunement.rain: 'dewfin', Attunement.night: 'duskwing'},
  Family.rodent: {Attunement.day: 'acornix', Attunement.rain: 'sparkit', Attunement.night: 'moonchest'},
  Family.insect: {Attunement.day: 'petalume', Attunement.rain: 'mistmoth', Attunement.night: 'lumoth'},
};

/// Resolves exactly one of the 15 variants for a classified family and attunement.
CreatureDefinition chooseVariant(Family family, Attunement attunement) =>
    findCreature(variantTable[family]![attunement]!);

/// Default simulated attunement from the device's local hour (research R10):
/// 06:00–17:59 is day, otherwise night. "Rain" is only ever chosen by the player.
Attunement defaultAttunementForLocalHour(int hour) =>
    (hour >= 6 && hour < 18) ? Attunement.day : Attunement.night;
