import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'app/env.dart';
import 'app/router.dart';
import 'app/theme.dart';
import 'features/paywall/state/premium_provider.dart';

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

  // Supabase Auth — persists session to flutter_secure_storage and exposes
  // the singleton via Supabase.instance.client.
  await Supabase.initialize(
    url: AppEnv.supabaseUrl,
    anonKey: AppEnv.supabaseAnonKey,
    debug: kDebugMode,
  );

  // RevenueCat — best-effort. Failures here must not block app boot (e.g. no
  // network on cold start, or running on a platform RC doesn't support).
  unawaited(_configureRevenueCat());

  runApp(const ProviderScope(child: ShoeboxApp()));
}

Future<void> _configureRevenueCat() async {
  try {
    // The `test_` SDK key works on both iOS and Android in sandbox. For
    // production swap to `appl_*` / `goog_*` keys via --dart-define.
    final isMobile = !kIsWeb && (Platform.isIOS || Platform.isAndroid);
    if (!isMobile) return;
    await Purchases.setLogLevel(kDebugMode ? LogLevel.warn : LogLevel.error);
    await Purchases.configure(PurchasesConfiguration(AppEnv.revenueCatSdkKey));
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
    return MaterialApp.router(
      title: 'Shoebox',
      debugShowCheckedModeBanner: false,
      theme: buildShoeboxTheme(),
      themeMode: ThemeMode.dark,
      routerConfig: appRouter,
    );
  }
}
