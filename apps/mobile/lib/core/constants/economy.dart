// Game economy constants, ported from the prototype (animon-web/src/App.tsx and
// game.ts). See specs/001-mobile-core-loop/research.md R16–R19. Changing a value
// here requires updating shared/game-vectors/ in the same change.

import '../../data/models/enums.dart';

// Training (FR-011)
const int trainCost = 30;
const int trainBond = 5;
const int bondCap = 100;
const int hpPerLevel = 6;
const int atkPerLevel = 2;

// Discovery
const int discoverXp = 50;
const int discoverEssence = 15;
const int newCompanionBond = 15;
const int ownedDiscoveryBond = 15;
const int dailyRewardedDiscoveryCap = 20;
const int discoverPerHourLimit = 30;

// Trials (FR-016)
const int waveEssence = 60;
const int waveXp = 100;
const double skillPower = 1.65;
const int skillCooldown = 2;
const int healAmount = 36;
const int healCooldown = 3;
const double advantageMultiplier = 1.4;
const double guardMultiplier = 0.5;
const double defenseFactor = 0.3;
const int minDamage = 4;
const int enemyHpPerWave = 12;
const int enemyHpPerSlot = 3;
const double enemyPowerPerWave = 0.12;
const int battleLogLimit = 12;

// Player
const int xpPerPlayerLevel = 250;

// Bounds (FR-021)
const int journalLimit = 100;
const int encounterHistoryLimit = 200;
const Duration familiarityWindow = Duration(days: 7);

// Daily trails (FR-020, research R17)
const Map<TrailId, int> trailRewards = {
  TrailId.scan: 30,
  TrailId.bond: 40,
  TrailId.trial: 60,
};

// Onboarding starter set (research R16)
const int starterEssence = 240;
const int starterXp = 120;

typedef StarterCompanion = ({String creatureId, int level, int bond, String context});

const List<StarterCompanion> starterCompanions = [
  (creatureId: 'mosslyn', level: 5, bond: 36, context: 'Woodland trail'),
  (creatureId: 'cindertail', level: 4, bond: 24, context: 'Sunlit clearing'),
  (creatureId: 'dewfin', level: 3, bond: 18, context: 'Brookside path'),
];
