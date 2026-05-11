import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../app/theme.dart';
import '../../../../l10n/generated/app_localizations.dart';
import '../../state/premium_provider.dart';

/// Wraps a premium-only widget. When the user has the entitlement we render
/// [child] untouched; otherwise we blur it, lay a "Unlock with Premium"
/// pill on top, and route the tap to the paywall.
class PremiumGate extends ConsumerWidget {
  final Widget child;

  /// Tier label shown inside the lock pill. Defaults to "Premium" so the
  /// English/Turkish/etc. paywallGateLabel ARB picks up "Unlock with Premium".
  final String label;

  const PremiumGate({
    super.key,
    required this.child,
    this.label = 'Premium',
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isPremium = ref.watch(isPremiumProvider);
    if (isPremium) return child;
    return Stack(
      children: [
        // Slight desaturation + opacity hint that the content is real but
        // behind a wall, not just a teaser.
        IgnorePointer(child: Opacity(opacity: 0.55, child: child)),
        Positioned.fill(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 4, sigmaY: 4),
              child: Container(
                color: ShoeboxColors.navy.withValues(alpha: 0.18),
                child: Center(
                  child: _LockPill(label: label),
                ),
              ),
            ),
          ),
        ),
        Positioned.fill(
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () {
                HapticFeedback.selectionClick();
                context.push('/paywall');
              },
            ),
          ),
        ),
      ],
    );
  }
}

class _LockPill extends StatelessWidget {
  final String label;
  const _LockPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: ShoeboxColors.accent.withValues(alpha: 0.45)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.lock_rounded, size: 16, color: ShoeboxColors.accent),
          const SizedBox(width: 6),
          Text(
            AppLocalizations.of(context).paywallGateLabel(label),
            style: const TextStyle(
                color: ShoeboxColors.accent,
                fontWeight: FontWeight.w700,
                fontSize: 13),
          ),
          const SizedBox(width: 6),
          const Icon(Icons.arrow_forward_rounded,
              size: 14, color: ShoeboxColors.accent),
        ],
      ),
    );
  }
}
