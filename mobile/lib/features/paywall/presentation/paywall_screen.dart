import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import '../../../app/theme.dart';
import '../../../l10n/generated/app_localizations.dart';
import '../../auth/state/auth_provider.dart';
import '../data/billing_repository.dart';
import '../state/premium_provider.dart';

class PaywallScreen extends ConsumerStatefulWidget {
  const PaywallScreen({super.key});

  @override
  ConsumerState<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends ConsumerState<PaywallScreen> {
  Offerings? _offerings;
  bool _loading = true;
  bool _purchasing = false;
  String? _error;
  String? _selectedIdentifier;

  @override
  void initState() {
    super.initState();
    _loadOfferings();
  }

  Future<void> _loadOfferings() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final billing = ref.read(billingRepositoryProvider);
    final offerings = await billing.getOfferings();
    if (!mounted) return;
    setState(() {
      _offerings = offerings;
      _selectedIdentifier = offerings?.current?.availablePackages.firstOrNull?.identifier;
      _loading = false;
    });
  }

  Future<void> _purchase(Package pkg) async {
    final signedIn = ref.read(isSignedInProvider);
    if (!signedIn) {
      context.push('/login');
      return;
    }
    HapticFeedback.selectionClick();
    setState(() {
      _purchasing = true;
      _error = null;
    });
    try {
      final billing = ref.read(billingRepositoryProvider);
      await billing.purchasePackage(pkg);
      ref.invalidate(customerInfoProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).paywallUnlocked)),
      );
      if (context.canPop()) context.pop();
    } on PlatformException catch (e) {
      final errorCode = PurchasesErrorHelper.getErrorCode(e);
      if (errorCode != PurchasesErrorCode.purchaseCancelledError) {
        setState(() => _error = e.message ?? 'Purchase failed');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _purchasing = false);
    }
  }

  Future<void> _restore() async {
    HapticFeedback.selectionClick();
    setState(() => _purchasing = true);
    final billing = ref.read(billingRepositoryProvider);
    await billing.restorePurchases();
    ref.invalidate(customerInfoProvider);
    if (!mounted) return;
    setState(() => _purchasing = false);
    final isPremium = ref.read(isPremiumProvider);
    final l = AppLocalizations.of(context);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(isPremium ? l.paywallRestored : l.paywallNothingToRestore),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.paywallTitle)),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const _Hero(),
                    const SizedBox(height: 24),
                    const _BenefitList(),
                    const SizedBox(height: 24),
                    ..._buildPackages(),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Text(_error!,
                          style: const TextStyle(color: ShoeboxColors.danger)),
                    ],
                    const SizedBox(height: 12),
                    Center(
                      child: TextButton(
                        onPressed: _purchasing ? null : _restore,
                        child: Text(l.paywallRestore),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const _LegalFooter(),
                  ],
                ),
              ),
      ),
    );
  }

  List<Widget> _buildPackages() {
    final l = AppLocalizations.of(context);
    final packages = _offerings?.current?.availablePackages ?? const [];
    if (packages.isEmpty) {
      return [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: ShoeboxColors.surface,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            l.paywallNoPlans,
            style: const TextStyle(color: ShoeboxColors.textMid),
          ),
        ),
      ];
    }
    return [
      for (final pkg in packages) ...[
        _PackageTile(
          package: pkg,
          selected: pkg.identifier == _selectedIdentifier,
          onTap: () => setState(() => _selectedIdentifier = pkg.identifier),
        ),
        const SizedBox(height: 8),
      ],
      const SizedBox(height: 8),
      FilledButton(
        onPressed: _purchasing
            ? null
            : () {
                final pkg = packages.firstWhere(
                  (p) => p.identifier == _selectedIdentifier,
                  orElse: () => packages.first,
                );
                _purchase(pkg);
              },
        style: FilledButton.styleFrom(
          backgroundColor: ShoeboxColors.accent,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: _purchasing
            ? const SizedBox(
                height: 18,
                width: 18,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Text(l.paywallContinue,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
      ),
    ];
  }
}

class _Hero extends StatelessWidget {
  const _Hero();

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: ShoeboxColors.accentSoft,
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.workspace_premium_rounded,
              size: 40, color: ShoeboxColors.accent),
        ),
        const SizedBox(height: 12),
        Text(
          l.paywallHeroTitle,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 4),
        Text(
          l.paywallHeroSubtitle,
          textAlign: TextAlign.center,
          style: const TextStyle(color: ShoeboxColors.textMid),
        ),
      ],
    );
  }
}

class _BenefitList extends StatelessWidget {
  const _BenefitList();

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final items = <(IconData, String, String)>[
      (Icons.percent_rounded, l.paywallBenefitHitRatesTitle,
          l.paywallBenefitHitRatesBody),
      (Icons.show_chart_rounded, l.paywallBenefitSplitsTitle,
          l.paywallBenefitSplitsBody),
      (Icons.bolt_rounded, l.paywallBenefitRefereeTitle,
          l.paywallBenefitRefereeBody),
    ];
    return Column(
      children: [
        for (final item in items) ...[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: ShoeboxColors.surface,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(item.$1, color: ShoeboxColors.accent, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(item.$2,
                        style: const TextStyle(
                            fontWeight: FontWeight.w700, fontSize: 14)),
                    const SizedBox(height: 2),
                    Text(item.$3,
                        style: const TextStyle(
                            color: ShoeboxColors.textMid, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
        ],
      ],
    );
  }
}

class _PackageTile extends StatelessWidget {
  final Package package;
  final bool selected;
  final VoidCallback onTap;

  const _PackageTile({
    required this.package,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final price = package.storeProduct.priceString;
    final title = package.storeProduct.title.isNotEmpty
        ? package.storeProduct.title
        : package.identifier;
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () {
        HapticFeedback.selectionClick();
        onTap();
      },
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: ShoeboxColors.surface,
          border: Border.all(
            color: selected ? ShoeboxColors.accent : ShoeboxColors.stroke,
            width: selected ? 1.4 : 1,
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Icon(
              selected
                  ? Icons.radio_button_checked
                  : Icons.radio_button_unchecked,
              color: selected ? ShoeboxColors.accent : ShoeboxColors.textMid,
              size: 22,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(
                          fontWeight: FontWeight.w700, fontSize: 15)),
                  const SizedBox(height: 2),
                  Text(package.storeProduct.description,
                      style: const TextStyle(
                          color: ShoeboxColors.textMid, fontSize: 12)),
                ],
              ),
            ),
            Text(
              price,
              style: const TextStyle(
                  fontWeight: FontWeight.w800, fontSize: 15),
            ),
          ],
        ),
      ),
    );
  }
}

class _LegalFooter extends StatelessWidget {
  const _LegalFooter();

  @override
  Widget build(BuildContext context) {
    return Text(
      AppLocalizations.of(context).paywallLegal,
      textAlign: TextAlign.center,
      style: const TextStyle(color: ShoeboxColors.textLow, fontSize: 11),
    );
  }
}

extension<E> on List<E> {
  E? get firstOrNull => isEmpty ? null : first;
}
