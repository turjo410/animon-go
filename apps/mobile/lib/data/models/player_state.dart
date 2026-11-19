import 'package:flutter/foundation.dart' show listEquals;

import '../../core/game/progression.dart';
import 'journal_entry.dart';
import 'owned_companion.dart';
import 'trail_status.dart';

/// The client's view of the server-authoritative player state (FR-018).
/// The client never computes balances itself; it renders what the server returns.
final class PlayerState {
  PlayerState({
    required this.displayName,
    required this.essence,
    required this.xp,
    required this.roster,
    required this.squad,
    required this.journal,
    required this.trails,
    required this.snapshotAt,
    required this.timezone,
    this.isLocalMode = false,
  }) {
    if (essence < 0) throw ArgumentError.value(essence, 'essence', 'must be >= 0');
    if (xp < 0) throw ArgumentError.value(xp, 'xp', 'must be >= 0');
  }

  final String displayName;
  final int essence;
  final int xp;
  final List<OwnedCompanion> roster;

  /// Exactly three distinct owned creature ids (FR-012).
  final List<String> squad;
  final List<JournalEntry> journal;
  final List<TrailStatus> trails;
  final DateTime snapshotAt;
  final String timezone;

  /// True when backed by the in-memory LocalGameRepository (research R14).
  final bool isLocalMode;

  int get playerLevel => playerLevelForXp(xp);

  OwnedCompanion? owned(String creatureId) {
    for (final c in roster) {
      if (c.creatureId == creatureId) return c;
    }
    return null;
  }

  @override
  bool operator ==(Object other) =>
      other is PlayerState &&
      other.displayName == displayName &&
      other.essence == essence &&
      other.xp == xp &&
      listEquals(other.roster, roster) &&
      listEquals(other.squad, squad) &&
      listEquals(other.journal, journal) &&
      listEquals(other.trails, trails) &&
      other.snapshotAt == snapshotAt &&
      other.timezone == timezone &&
      other.isLocalMode == isLocalMode;

  @override
  int get hashCode => Object.hash(displayName, essence, xp, Object.hashAll(roster), Object.hashAll(squad),
      Object.hashAll(journal), Object.hashAll(trails), snapshotAt, timezone, isLocalMode);
}
