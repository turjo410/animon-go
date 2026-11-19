import 'enums.dart';

/// A player-visible field journal record (FR-021). Newest first, at most 100 kept.
final class JournalEntry {
  const JournalEntry({
    required this.id,
    required this.title,
    required this.detail,
    required this.element,
    required this.occurredAt,
  });

  final String id;
  final String title;
  final String detail;
  final CreatureElement element;
  final DateTime occurredAt;

  @override
  bool operator ==(Object other) =>
      other is JournalEntry &&
      other.id == id &&
      other.title == title &&
      other.detail == detail &&
      other.element == element &&
      other.occurredAt == occurredAt;

  @override
  int get hashCode => Object.hash(id, title, detail, element, occurredAt);
}
