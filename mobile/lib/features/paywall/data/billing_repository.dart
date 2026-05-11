import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import '../../../app/env.dart';

/// Thin wrapper around the RevenueCat SDK. Returns `null`s when called from
/// platforms RC doesn't support (web, desktop) so callers don't need to guard.
///
/// All methods also short-circuit if RevenueCat hasn't been configured yet —
/// the SDK turns pre-configure calls into hard `fatalError`s (not exceptions
/// we can catch), so guarding here is the only safe move. The `_ready` flag
/// is flipped by [markReady] from `main.dart` once `Purchases.configure`
/// returns.
class BillingRepository {
  static bool _ready = false;

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

  Future<CustomerInfo?> getCustomerInfo() async {
    if (!_supported) return null;
    try {
      return await Purchases.getCustomerInfo();
    } catch (e) {
      debugPrint('getCustomerInfo failed: $e');
      return null;
    }
  }

  Future<Offerings?> getOfferings() async {
    if (!_supported) return null;
    try {
      return await Purchases.getOfferings();
    } catch (e) {
      debugPrint('getOfferings failed: $e');
      return null;
    }
  }

  /// Returns the resulting customer info on success, throws on failure.
  Future<CustomerInfo> purchasePackage(Package pkg) async {
    return await Purchases.purchasePackage(pkg);
  }

  Future<CustomerInfo?> restorePurchases() async {
    if (!_supported) return null;
    try {
      return await Purchases.restorePurchases();
    } catch (e) {
      debugPrint('restorePurchases failed: $e');
      return null;
    }
  }

  /// Identify the RevenueCat customer using the Supabase user id. After this
  /// call, purchases on this device follow the user across devices.
  Future<void> identify(String userId) async {
    if (!_supported) return;
    try {
      await Purchases.logIn(userId);
    } catch (e) {
      debugPrint('Purchases.logIn failed: $e');
    }
  }

  Future<void> resetIdentity() async {
    if (!_supported) return;
    try {
      await Purchases.logOut();
    } catch (e) {
      debugPrint('Purchases.logOut failed: $e');
    }
  }

  bool isPremium(CustomerInfo? info) {
    if (info == null) return false;
    final ent = info.entitlements.active[AppEnv.premiumEntitlement];
    return ent != null && ent.isActive;
  }
}

final billingRepositoryProvider = Provider<BillingRepository>((_) => BillingRepository());
