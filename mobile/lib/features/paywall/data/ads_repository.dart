import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import '../../../app/env.dart';

/// Thin wrapper around the rewarded-ad lifecycle. The SDK is a fire-and-
/// forget model: you `load`, you get a callback with the ad instance, you
/// `show`, and the show-time callbacks tell you whether the user earned
/// the reward.
///
/// Returns false for unsupported platforms (web, desktop) and for
/// non-mobile environments so callers don't need to guard.
class AdsRepository {
  static bool _ready = false;

  /// Initialised once from `main()` after `MobileAds.instance.initialize()`
  /// resolves. We don't track init state via a Future because we want a
  /// cheap synchronous check on every call.
  static void markReady() {
    _ready = true;
  }

  bool get _supported {
    if (!_ready) return false;
    if (kIsWeb) return false;
    try {
      return Platform.isIOS || Platform.isAndroid;
    } catch (_) {
      return false;
    }
  }

  /// Loads a single rewarded ad and shows it. Resolves to `true` when the
  /// user actually watched through to the reward callback; `false` otherwise
  /// (skipped, failed to load, errored out, unsupported platform).
  ///
  /// Single-shot: don't re-use the returned ad — RewardedAd is consumed on
  /// `show()` and dispose is called for you in the close-callback.
  Future<bool> loadAndShowRewarded() async {
    if (!_supported) return false;
    final completer = Completer<bool>();
    bool earned = false;

    try {
      await RewardedAd.load(
        adUnitId: AppEnv.rewardedAdUnitId,
        request: const AdRequest(),
        rewardedAdLoadCallback: RewardedAdLoadCallback(
          onAdLoaded: (ad) {
            ad.fullScreenContentCallback = FullScreenContentCallback(
              onAdDismissedFullScreenContent: (ad) {
                ad.dispose();
                if (!completer.isCompleted) completer.complete(earned);
              },
              onAdFailedToShowFullScreenContent: (ad, error) {
                debugPrint('rewarded_ad_show_failed: $error');
                ad.dispose();
                if (!completer.isCompleted) completer.complete(false);
              },
            );
            ad.show(onUserEarnedReward: (_, __) {
              earned = true;
            });
          },
          onAdFailedToLoad: (error) {
            debugPrint('rewarded_ad_load_failed: $error');
            if (!completer.isCompleted) completer.complete(false);
          },
        ),
      );
    } catch (e) {
      debugPrint('rewarded_ad_exception: $e');
      if (!completer.isCompleted) completer.complete(false);
    }

    return completer.future;
  }
}

final adsRepositoryProvider = Provider<AdsRepository>((_) => AdsRepository());
