import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../app/locale_provider.dart';
import '../../../app/router.dart' as router;

/// Tracks whether the user has completed the first-launch onboarding tour.
/// Persisted to SharedPreferences so we only show the tour once per install.
class OnboardingController extends StateNotifier<bool> {
  OnboardingController(this._prefs) : super(_prefs.getBool(_key) ?? false);

  static const _key = 'onboarding_completed';

  final SharedPreferences _prefs;

  Future<void> markCompleted() async {
    state = true;
    await _prefs.setBool(_key, true);
    // Lift the redirect gate so further navigation works normally.
    router.setOnboardingComplete(true);
  }

  /// Test helper / "Show onboarding again" debug action.
  Future<void> reset() async {
    state = false;
    await _prefs.remove(_key);
    router.setOnboardingComplete(false);
  }
}

final onboardingControllerProvider =
    StateNotifierProvider<OnboardingController, bool>((ref) {
  return OnboardingController(ref.watch(sharedPreferencesProvider));
});

final hasSeenOnboardingProvider = Provider<bool>((ref) {
  return ref.watch(onboardingControllerProvider);
});
