// The 15 creature definitions, ported verbatim from the reference prototype
// animon-web/src/lib/data.ts (read-only). Changing a value here requires
// updating shared/game-vectors/ and the TS copy in supabase/functions/_shared/.

import '../../data/models/creature.dart';
import '../../data/models/enums.dart';

const List<CreatureDefinition> creatures = [
  CreatureDefinition(
    id: 'mosslyn', name: 'Mosslyn', family: Family.feline, element: CreatureElement.earth, spriteIndex: 0,
    rarity: Rarity.uncommon,
    description: 'A quiet guardian of sun-dappled paths. Tiny ferns unfurl wherever its spirit wanders.',
    baseHp: 110, attack: 24, defense: 18, speed: 30, skillName: 'Fern flourish', passiveName: 'Woodland heart',
  ),
  CreatureDefinition(
    id: 'cindertail', name: 'Cindertail', family: Family.canine, element: CreatureElement.fire, spriteIndex: 1,
    rarity: Rarity.rare,
    description: 'A warm-hearted trail companion with a spark of adventure in every step.',
    baseHp: 105, attack: 30, defense: 15, speed: 26, skillName: 'Ember rush', passiveName: 'Golden hour',
  ),
  CreatureDefinition(
    id: 'dewfin', name: 'Dewfin', family: Family.avian, element: CreatureElement.water, spriteIndex: 2,
    rarity: Rarity.uncommon,
    description: 'Born of a raindrop and a birdsong. Its little wings carry the calm of a flowing stream.',
    baseHp: 95, attack: 25, defense: 16, speed: 34, skillName: 'Tidal song', passiveName: 'Rain keeper',
  ),
  CreatureDefinition(
    id: 'acornix', name: 'Acornix', family: Family.rodent, element: CreatureElement.earth, spriteIndex: 3,
    rarity: Rarity.common,
    description: 'An endlessly curious forest spirit that keeps its favorite acorn close.',
    baseHp: 115, attack: 22, defense: 22, speed: 23, skillName: 'Root tumble', passiveName: 'Steady roots',
  ),
  CreatureDefinition(
    id: 'lumoth', name: 'Lumoth', family: Family.insect, element: CreatureElement.light, spriteIndex: 4,
    rarity: Rarity.rare,
    description: 'A gentle lantern of the twilight woods, following the first stars home.',
    baseHp: 90, attack: 29, defense: 14, speed: 32, skillName: 'Glimmer veil', passiveName: 'First light',
  ),
  CreatureDefinition(
    id: 'nightpurr', name: 'Nightpurr', family: Family.feline, element: CreatureElement.dark, spriteIndex: 0,
    rarity: Rarity.rare,
    description: 'A velvet-footed spirit that weaves moonlight into its whiskers.',
    baseHp: 100, attack: 29, defense: 16, speed: 33, skillName: 'Moon whisper', passiveName: 'Night attunement',
    hue: 150,
  ),
  CreatureDefinition(
    id: 'solcat', name: 'Solcat', family: Family.feline, element: CreatureElement.light, spriteIndex: 0,
    rarity: Rarity.rare,
    description: 'A radiant little companion that naps in the warmest patch of sunlight.',
    baseHp: 105, attack: 27, defense: 17, speed: 28, skillName: 'Solar bloom', passiveName: 'Daybreak',
    hue: 285,
  ),
  CreatureDefinition(
    id: 'brookhound', name: 'Brookhound', family: Family.canine, element: CreatureElement.water, spriteIndex: 1,
    rarity: Rarity.uncommon,
    description: 'Its swirling tail holds the memory of every stream along the trail.',
    baseHp: 112, attack: 24, defense: 21, speed: 24, skillName: 'Brook surge', passiveName: 'Rain keeper',
    hue: 160,
  ),
  CreatureDefinition(
    id: 'zephruff', name: 'Zephruff', family: Family.canine, element: CreatureElement.air, spriteIndex: 1,
    rarity: Rarity.uncommon,
    description: 'Always one step ahead, dancing through the grass like a passing breeze.',
    baseHp: 98, attack: 26, defense: 15, speed: 36, skillName: 'Gale dash', passiveName: 'Tailwind',
    hue: 70,
  ),
  CreatureDefinition(
    id: 'breezlet', name: 'Breezlet', family: Family.avian, element: CreatureElement.air, spriteIndex: 2,
    rarity: Rarity.common,
    description: 'A pocket-sized sky spirit whose songs stir the highest leaves.',
    baseHp: 90, attack: 23, defense: 14, speed: 40, skillName: 'Feather gale', passiveName: 'Tailwind',
    hue: 315,
  ),
  CreatureDefinition(
    id: 'duskwing', name: 'Duskwing', family: Family.avian, element: CreatureElement.dark, spriteIndex: 2,
    rarity: Rarity.rare,
    description: 'A soft silhouette at dusk, keeping watch over the sleeping woodland.',
    baseHp: 95, attack: 30, defense: 15, speed: 35, skillName: 'Dusk echo', passiveName: 'Night attunement',
    hue: 90,
  ),
  CreatureDefinition(
    id: 'sparkit', name: 'Sparkit', family: Family.rodent, element: CreatureElement.fire, spriteIndex: 3,
    rarity: Rarity.uncommon,
    description: 'A bright, boundless bundle of energy with a tail full of dancing embers.',
    baseHp: 100, attack: 29, defense: 16, speed: 29, skillName: 'Spark scatter', passiveName: 'Golden hour',
    hue: 330,
  ),
  CreatureDefinition(
    id: 'moonchest', name: 'Moonchest', family: Family.rodent, element: CreatureElement.dark, spriteIndex: 3,
    rarity: Rarity.rare,
    description: 'It collects fallen stars and tucks them into the hollow of an old oak.',
    baseHp: 108, attack: 26, defense: 19, speed: 27, skillName: 'Lunar leap', passiveName: 'Night attunement',
    hue: 190,
  ),
  CreatureDefinition(
    id: 'petalume', name: 'Petalume', family: Family.insect, element: CreatureElement.earth, spriteIndex: 4,
    rarity: Rarity.common,
    description: 'A tiny garden guardian with a whole meadow painted across its wings.',
    baseHp: 98, attack: 22, defense: 20, speed: 27, skillName: 'Petal dance', passiveName: 'Woodland heart',
    hue: 230,
  ),
  CreatureDefinition(
    id: 'mistmoth', name: 'Mistmoth', family: Family.insect, element: CreatureElement.water, spriteIndex: 4,
    rarity: Rarity.uncommon,
    description: 'A whisper of cool mist with wings, drawn to the quiet after rainfall.',
    baseHp: 94, attack: 26, defense: 18, speed: 30, skillName: 'Mist ribbon', passiveName: 'Rain keeper',
    hue: 290,
  ),
];

final Map<String, CreatureDefinition> _byId = {for (final c in creatures) c.id: c};

/// Looks up a creature by id. Throws [ArgumentError] for an unknown id.
CreatureDefinition findCreature(String id) =>
    _byId[id] ?? (throw ArgumentError.value(id, 'id', 'Unknown creature'));

/// Family-specific familiarity radius in metres (research R8, from the prototype).
const Map<Family, double> familiarityRadiusMeters = {
  Family.feline: 200,
  Family.canine: 300,
  Family.avian: 120,
  Family.rodent: 80,
  Family.insect: 60,
};

/// Enemy trios by wave: wave n uses `enemyRotation[(n - 1) % 5]` (research R18).
/// Index 0 is the prototype's (only) trio.
const List<List<String>> enemyRotation = [
  ['acornix', 'breezlet', 'petalume'],
  ['sparkit', 'dewfin', 'mistmoth'],
  ['zephruff', 'brookhound', 'mosslyn'],
  ['duskwing', 'moonchest', 'cindertail'],
  ['nightpurr', 'solcat', 'lumoth'],
];
