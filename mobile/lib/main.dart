import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'app/env.dart';
import 'app/locale_provider.dart';
import 'app/router.dart';
import 'app/theme.dart';
import 'features/notifications/notifications_service.dart';
import 'features/notifications/watchlist_notifications_sync.dart';
import 'features/paywall/data/ads_repository.dart';
import 'features/paywall/data/billing_repository.dart';
import 'features/paywall/state/premium_provider.dart';
import 'l10n/generated/app_localizations.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Apply system UI styling before the first frame.
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,   // Android
    statusBarBrightness: Brightness.dark,        // iOS (dark background → light icons)
    systemNavigationBarColor: ShoeboxColors.navy,
    systemNavigationBarIconBrightness: Brightness.light,
  ));

  // SharedPreferences for the locale override (and future tiny settings).
  final prefs = await SharedPreferences.getInstance();

  // Seed the router's onboarding flag before the first frame so a returning
  // user goes straight to the shell instead of flashing the tour.
  setOnboardingComplete(prefs.getBool('onboarding_completed') ?? false);

  // Supabase Auth — persists session to flutter_secure_storage and exposes
  // the singleton via Supabase.instance.client.
  await Supabase.initialize(
    url: AppEnv.supabaseUrl,
    anonKey: AppEnv.supabaseAnonKey,
    debug: kDebugMode,
  );

  // RevenueCat must be configured *before* the first `Purchases.logIn` call
  // (which the premium provider fires immediately on app start when a user
  // is already signed in). Calling logIn pre-configure is a hard fatalError
  // in the SDK, not a recoverable exception — so we await here. Wrapped in
  // try/catch so a transient configure failure doesn't block app boot.
  await _configureRevenueCat();

  // AdMob — fire and forget. We only need init to complete *before* the
  // first ad load (which is user-triggered, not on boot), so unawaited is
  // fine. Failures are non-fatal: AdsRepository.markReady stays false and
  // the rewarded-ad path is a no-op.
  unawaited(_configureAdMob());

  // Local notifications init is cheap; no permission prompt yet — that's
  // requested lazily the first time the user adds a match to their watchlist.
  unawaited(NotificationsService.init());

  runApp(ProviderScope(
    overrides: [
      sharedPreferencesProvider.overrideWithValue(prefs),
    ],
    child: const ShoeboxApp(),
  ));
}

Future<void> _configureAdMob() async {
  try {
    final isMobile = !kIsWeb && (Platform.isIOS || Platform.isAndroid);
    if (!isMobile) return;
    await MobileAds.instance.initialize();
    AdsRepository.markReady();
  } catch (e) {
    debugPrint('AdMob initialize failed: $e');
  }
}

Future<void> _configureRevenueCat() async {
  try {
    // The `test_` SDK key works on both iOS and Android in sandbox. For
    // production swap to `appl_*` / `goog_*` keys via --dart-define.
    final isMobile = !kIsWeb && (Platform.isIOS || Platform.isAndroid);
    if (!isMobile) return;
    await Purchases.setLogLevel(kDebugMode ? LogLevel.warn : LogLevel.error);
    await Purchases.configure(PurchasesConfiguration(AppEnv.revenueCatSdkKey));
    BillingRepository.markReady();
  } catch (e) {
    debugPrint('RevenueCat configure failed: $e');
  }
}

class ShoeboxApp extends ConsumerWidget {
  const ShoeboxApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Keep premium status fresh — the provider eagerly listens to auth
    // changes and refreshes RC customer info.
    ref.watch(premiumStatusSyncProvider);
    // Keep local kickoff-reminder notifications in sync with the watchlist.
    ref.watch(watchlistNotificationsSyncProvider);
    final localeOverride = ref.watch(localeControllerProvider);

    return MaterialApp.router(
      title: 'Shoebox',
      debugShowCheckedModeBanner: false,
      theme: buildShoeboxTheme(),
      themeMode: ThemeMode.dark,
      locale: localeOverride,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      routerConfig: appRouter,
    );
  }
}
