# Contract — FamilyClassifier (device-side seam)

**Location**: `apps/mobile/lib/features/exploration/classification/`
**Purpose**: Isolates *which model* classifies a photo from the rest of the discovery flow (FR-001..004). This feature ships only the mock. The real model plugs in after [`docs/research/model-evaluation-plan.md`](../../../docs/research/model-evaluation-plan.md) step 6, with **no change to callers**.

## Interface (Dart, behavioural contract)

```dart
abstract interface class FamilyClassifier {
  /// Human-readable implementation id stored with debug telemetry, e.g. "mock", "mlkit", "siglip2-b".
  String get id;

  /// Classify one captured image. Must not retain, upload or persist the image (FR-004).
  /// Never throws for "no animal": that is a ClassificationResult with family == null.
  /// Throws ClassifierUnavailable only if the model cannot run at all (e.g. failed to load).
  Future<ClassificationResult> classify(CapturedImage image);
}

final class ClassificationResult {
  final Family? family;               // null => nothing in the five families
  final double confidence;            // 0..1 for `family` (0 when family == null)
  final Map<Family, double> scores;   // per-family scores, for debugging and threshold tuning
}
```

## Rules every implementation must satisfy

1. **The threshold gate is outside the classifier.** The `DiscoveryController` applies `ClassifierThresholds.forFamily(family)` (default 0.55 each, R11). A result below the threshold is a **soft fail** (FR-003) and is never sent to the server.
2. **Images aren't kept.** `CapturedImage` wraps bytes or a temp path. The caller deletes the temp file in a `finally` block after `classify` returns, whether it succeeded or threw (R12).
3. **Determinism in tests.** Implementations used in tests must give the same output for the same input.
4. **Offline.** Classification must work with no network. It runs on the device.
5. **Latency budget.** The real implementations will be measured against NFR-LAT-1 (≤ 1.5 s, capture to result, on the reference device). The mock has no latency.

## `MockFamilyClassifier` (this feature)

- **Debug builds**: after capture, a sheet asks the tester for a family and a confidence (preset buttons: "Confident cat 0.92", "Ambiguous 0.40", "No animal"). This makes US1 scenarios 1–2 testable on a real device before any model exists.
- **Tests**: constructed with a script, e.g. `MockFamilyClassifier.scripted([result1, result2])`.
- **Labelling**: the result screen shows a small "Mock classifier" badge whenever `id == "mock"`, so mock results are never mistaken for real ones.

## Acceptance (contract tests)

- A confident result (≥ threshold) leads to a `discover` call carrying the same family and confidence.
- Below threshold, or `family == null`: no `discover` call, and a distinct "No confident match" UI (SC-003).
- The temp file is gone after `classify` returns or throws.
