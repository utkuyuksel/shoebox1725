import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import '../../auth/state/auth_provider.dart';
import '../data/billing_repository.dart';

/// Caches the latest CustomerInfo. Refreshed on:
/// - app start (StreamProvider's initial value)
/// - auth state change (premiumStatusSyncProvider)
/// - manual ref.invalidate(customerInfoProvider) after a successful purchase.
final customerInfoProvider = FutureProvider<CustomerInfo?>((ref) async {
  // Re-evaluate whenever auth flips so the customer info follows the user.
  ref.watch(currentUserProvider);
  final billing = ref.watch(billingRepositoryProvider);
  return billing.getCustomerInfo();
});

final isPremiumProvider = Provider<bool>((ref) {
  final info = ref.watch(customerInfoProvider).valueOrNull;
  return ref.watch(billingRepositoryProvider).isPremium(info);
});

/// Side-effect provider: identify RevenueCat with the Supabase user id on
/// sign-in and reset on sign-out. Watched from ShoeboxApp so it stays alive
/// for the whole app lifecycle.
final premiumStatusSyncProvider = Provider<void>((ref) {
  final billing = ref.watch(billingRepositoryProvider);
  ref.listen(currentUserProvider, (prev, next) async {
    if (next != null && (prev == null || prev.id != next.id)) {
      await billing.identify(next.id);
    } else if (next == null && prev != null) {
      await billing.resetIdentity();
    }
    // Either way refresh the cached customer info.
    ref.invalidate(customerInfoProvider);
  }, fireImmediately: true);
});
