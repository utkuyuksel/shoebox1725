import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../app/theme.dart';
import '../../../../l10n/generated/app_localizations.dart';
import '../../data/ads_repository.dart';
import '../../state/premium_provider.dart';
import '../../state/unlocked_features_provider.dart';

/// Wraps a premium-only widget. Three states:
///
/// 1. Premium subscriber → renders `child` untouched.
/// 2. Ad-unlocked for this `featureKey` this session → renders `child`.
/// 3. Locked → blurs `child`, shows a "Watch ad or upgrade" pill that opens
///    an action sheet with two options.
///
/// `featureKey` must be unique per feature instance so unlocking the home
/// team's hit rates on match A doesn't also unlock match B's. Convention:
/// `"<scope>:<id>:<feature>"` — e.g. `"match:9900100:hit_rates"`.
class PremiumGate extends ConsumerWidget {
  final Widget child;

  /// Identifier for this specific premium item. See class docs.
  final String featureKey;

  /// Pill label (the tier name shown in "Unlock with X"). Defaults to
  /// "Premium" so the AppLocalizations.paywallGateLabel reads naturally.
  final String label;

  const PremiumGate({
    super.key,
    required this.child,
    required this.featureKey,
    this.label = 'Premium',
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isPremium = ref.watch(isPremiumProvider);
    final isAdUnlocked = ref.watch(featureUnlockedProvider(featureKey));
    if (isPremium || isAdUnlocked) return child;

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
                _openSheet(context, ref);
              },
            ),
          ),
        ),
      ],
    );
  }

  void _openSheet(BuildContext context, WidgetRef ref) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: ShoeboxColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _UnlockSheet(featureKey: featureKey),
    );
  }
}

class _UnlockSheet extends ConsumerStatefulWidget {
  final String featureKey;
  const _UnlockSheet({required this.featureKey});

  @override
  ConsumerState<_UnlockSheet> createState() => _UnlockSheetState();
}

class _UnlockSheetState extends ConsumerState<_UnlockSheet> {
  bool _loadingAd = false;

  Future<void> _watchAd() async {
    HapticFeedback.lightImpact();
    setState(() => _loadingAd = true);
    final ads = ref.read(adsRepositoryProvider);
    final earned = await ads.loadAndShowRewarded();
    if (!mounted) return;
    setState(() => _loadingAd = false);
    if (earned) {
      ref.read(unlockedFeaturesProvider.notifier).unlock(widget.featureKey);
      Navigator.of(context).pop();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text("Couldn't load ad. Try again."),
      ));
    }
  }

  void _goPremium() {
    HapticFeedback.selectionClick();
    Navigator.of(context).pop();
    context.push('/paywall');
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: ShoeboxColors.stroke,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            const Icon(Icons.lock_open_rounded,
                size: 36, color: ShoeboxColors.accent),
            const SizedBox(height: 12),
            Text(
              l.paywallSheetTitle,
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
            ),
            const SizedBox(height: 6),
            Text(
              l.paywallSheetBody,
              textAlign: TextAlign.center,
              style: const TextStyle(color: ShoeboxColors.textMid, fontSize: 13),
            ),
            const SizedBox(height: 20),
            _OptionTile(
              icon: Icons.play_circle_outline_rounded,
              iconColor: ShoeboxColors.accent,
              title: l.paywallWatchAdTitle,
              subtitle: l.paywallWatchAdSubtitle,
              loading: _loadingAd,
              onTap: _loadingAd ? null : _watchAd,
            ),
            const SizedBox(height: 10),
            _OptionTile(
              icon: Icons.workspace_premium_rounded,
              iconColor: ShoeboxColors.warn,
              title: l.paywallUpgradeTitle,
              subtitle: l.paywallUpgradeSubtitle,
              accent: true,
              onTap: _loadingAd ? null : _goPremium,
            ),
          ],
        ),
      ),
    );
  }
}

class _OptionTile extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String subtitle;
  final bool loading;
  final bool accent;
  final VoidCallback? onTap;

  const _OptionTile({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    this.loading = false,
    this.accent = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: accent ? ShoeboxColors.accentSoft : ShoeboxColors.surfaceAlt,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
          child: Row(
            children: [
              Icon(icon, size: 24, color: iconColor),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        style: const TextStyle(
                            fontWeight: FontWeight.w700, fontSize: 14)),
                    const SizedBox(height: 2),
                    Text(subtitle,
                        style: const TextStyle(
                            color: ShoeboxColors.textMid, fontSize: 12)),
                  ],
                ),
              ),
              if (loading)
                const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: ShoeboxColors.accent,
                  ),
                )
              else
                const Icon(Icons.chevron_right_rounded,
                    color: ShoeboxColors.textLow),
            ],
          ),
        ),
      ),
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
