import '../../data/models/creature.dart';
import '../../data/models/owned_companion.dart';
import '../constants/economy.dart';

/// Max HP at a level: baseHp + (level − 1) × 6 (FR-011).
int maxHp(CreatureDefinition c, int level) => c.baseHp + (level - 1) * hpPerLevel;

/// Attack at a level: attack + (level − 1) × 2 (FR-011).
int effectiveAttack(CreatureDefinition c, int level) => c.attack + (level - 1) * atkPerLevel;

/// Player level: floor(xp / 250) + 1.
int playerLevelForXp(int xp) => xp ~/ xpPerPlayerLevel + 1;

int _capBond(int bond) => bond > bondCap ? bondCap : bond;

/// One training action: +1 level, bond +5 (capped at 100). The essence cost is
/// applied by the server/repository, never here (FR-019).
OwnedCompanion applyTraining(OwnedCompanion c) =>
    c.copyWith(level: c.level + 1, bond: _capBond(c.bond + trainBond));

/// Discovering a creature the player already owns: +1 level, bond +15 (capped).
OwnedCompanion applyOwnedDiscovery(OwnedCompanion c) =>
    c.copyWith(level: c.level + 1, bond: _capBond(c.bond + ownedDiscoveryBond));

/// A newly discovered companion joins at level 1 with bond 15.
OwnedCompanion newCompanion(String creatureId, {required String context, required DateTime at}) =>
    OwnedCompanion(
      creatureId: creatureId,
      level: 1,
      bond: newCompanionBond,
      discoveredContext: context,
      acquiredAt: at,
    );
