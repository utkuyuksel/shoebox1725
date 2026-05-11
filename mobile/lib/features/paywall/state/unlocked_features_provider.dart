import 'package:flutter_riverpod/flutter_riverpod.dart';

/// In-memory set of feature keys the user has unlocked via rewarded ads
/// this session. Premium subscription bypasses this entirely (see
/// `isPremiumProvider`). Keys are arbitrary strings — typical shape:
///
///   "match:9900100:hit_rates"
///   "match:9900100:splits"
///   "referee:42"
///
/// Session-only by design (see AppEnv.adUnlockSessionOnly). A relaunch
/// re-locks everything; the user can re-watch an ad to re-unlock.
class UnlockedFeaturesNotifier extends StateNotifier<Set<String>> {
  UnlockedFeaturesNotifier() : super(const <String>{});

  bool isUnlocked(String key) => state.contains(key);

  void unlock(String key) {
    if (state.contains(key)) return;
    state = {...state, key};
  }

  /// Used on sign-out / premium-revocation flows to start fresh.
  void clear() {
    state = const <String>{};
  }
}

final unlockedFeaturesProvider =
    StateNotifierProvider<UnlockedFeaturesNotifier, Set<String>>((ref) {
  return UnlockedFeaturesNotifier();
});

/// Sugar for widgets — returns true if the user has either premium OR an
/// active ad-unlock for `key`. Watch this in PremiumGate.
final featureUnlockedProvider = Provider.family<bool, String>((ref, key) {
  // Late import to avoid circular dep with premium_provider.
  final unlocked = ref.watch(unlockedFeaturesProvider);
  return unlocked.contains(key);
});
