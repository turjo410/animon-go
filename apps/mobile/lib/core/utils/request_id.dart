import 'package:uuid/uuid.dart';

const _uuid = Uuid();

/// A client-generated idempotency key (UUID v4), created once per user intent and
/// reused on every retry of that intent (research R6).
String newRequestId() => _uuid.v4();
