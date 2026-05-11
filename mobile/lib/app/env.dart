import 'dart:io' show Platform;

/// Build-time / runtime configuration.
///
/// Values can be overridden at run time with:
///   flutter run --dart-define=API_BASE_URL=https://api.shoebox.app \
///               --dart-define=SUPABASE_URL=... \
///               --dart-define=SUPABASE_ANON_KEY=... \
///               --dart-define=REVENUECAT_SDK_KEY=...
///
/// The defaults below match our dev Supabase + RevenueCat projects. The
/// Supabase anon key and RevenueCat SDK key are *publishable* by design —
/// they're meant to ship inside the client. Supabase RLS and RevenueCat's
/// server-side enforcement keep the real authorisation in the backend.
class AppEnv {
  static const _apiOverride = String.fromEnvironment('API_BASE_URL');
  static const _supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://rfccwixwkkifrmbnetjp.supabase.co',
  );
  static const _supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue:
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmY2N3aXh3a2tpZnJtYm5ldGpwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg1MTA0OTIsImV4cCI6MjA5NDA4NjQ5Mn0.ZEOXKJ7gNo5SFN-5RAEkyWwigfVgyD0WcGHCs_p7WGc',
  );
  static const _revenueCatKey = String.fromEnvironment(
    'REVENUECAT_SDK_KEY',
    defaultValue: 'test_iKMYaaCRGMWMzdZILRgbHLSdRQX',
  );

  static String get apiBaseUrl {
    if (_apiOverride.isNotEmpty) return _apiOverride;
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8000';
    } catch (_) {
      // Platform is unavailable on Flutter web; fall through.
    }
    return 'http://127.0.0.1:8000';
  }

  static String get supabaseUrl => _supabaseUrl;
  static String get supabaseAnonKey => _supabaseAnonKey;
  static String get revenueCatSdkKey => _revenueCatKey;

  /// Entitlement identifier used in RevenueCat dashboard. Anything in this
  /// entitlement unlocks the premium tier app-wide.
  static const premiumEntitlement = 'premium';

  // AdMob ad unit IDs. The defaults are Google's official TEST IDs — every
  // call returns a test ad without billing anyone. Override at build time
  // once real AdMob units exist:
  //   --dart-define=ADMOB_REWARDED_IOS=ca-app-pub-XXXX/XXXX
  //   --dart-define=ADMOB_REWARDED_ANDROID=ca-app-pub-XXXX/XXXX
  static const _testRewardedIos = 'ca-app-pub-3940256099942544/1712485313';
  static const _testRewardedAndroid = 'ca-app-pub-3940256099942544/5224354917';

  static const _rewardedIos = String.fromEnvironment(
    'ADMOB_REWARDED_IOS',
    defaultValue: _testRewardedIos,
  );
  static const _rewardedAndroid = String.fromEnvironment(
    'ADMOB_REWARDED_ANDROID',
    defaultValue: _testRewardedAndroid,
  );

  /// Platform-correct rewarded ad unit. Falls back to test units when no
  /// real `ADMOB_REWARDED_*` override is provided at build time.
  static String get rewardedAdUnitId {
    try {
      if (Platform.isIOS) return _rewardedIos;
      if (Platform.isAndroid) return _rewardedAndroid;
    } catch (_) {}
    return _rewardedIos;
  }

  /// How long an ad-unlocked feature stays open after a successful ad view.
  /// Refreshed on every successful ad — so a user who watches one ad for a
  /// match keeps access until they restart the app (in-memory store).
  static const adUnlockSessionOnly = true;
}
