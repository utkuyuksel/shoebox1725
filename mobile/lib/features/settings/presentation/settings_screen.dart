import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/locale_provider.dart';
import '../../../app/theme.dart';
import '../../../l10n/generated/app_localizations.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/state/auth_provider.dart';
import '../../paywall/state/premium_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final isPremium = ref.watch(isPremiumProvider);
    final locale = ref.watch(localeControllerProvider);
    final l = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(l.settingsTitle)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          _Section(title: l.settingsSectionAccount, children: [
            if (user == null)
              _Tile(
                icon: Icons.login_rounded,
                title: l.settingsSignInCta,
                subtitle: l.settingsSignInSubtitle,
                onTap: () => context.push('/login'),
              )
            else ...[
              _Tile(
                icon: Icons.email_outlined,
                title: user.email ?? '—',
                subtitle: l.settingsSignedInSubtitle(user.id.substring(0, 8)),
                onTap: null,
              ),
              _Tile(
                icon: Icons.logout_rounded,
                title: l.settingsSignOut,
                danger: true,
                onTap: () => _confirmSignOut(context, ref),
              ),
            ],
          ]),
          const SizedBox(height: 16),
          _Section(title: l.settingsSectionSubscription, children: [
            _Tile(
              icon: isPremium
                  ? Icons.workspace_premium_rounded
                  : Icons.lock_outline_rounded,
              iconColor:
                  isPremium ? ShoeboxColors.warn : ShoeboxColors.textMid,
              title: isPremium ? l.settingsPremiumActive : l.settingsPremiumUpgrade,
              subtitle: isPremium
                  ? l.settingsPremiumActiveSubtitle
                  : l.settingsPremiumUpgradeSubtitle,
              onTap: isPremium ? null : () => context.push('/paywall'),
            ),
          ]),
          const SizedBox(height: 16),
          _Section(title: l.settingsSectionLanguage, children: [
            _LanguageTile(current: locale, l: l),
          ]),
          const SizedBox(height: 16),
          _Section(title: l.settingsSectionAbout, children: [
            _Tile(
              icon: Icons.info_outline_rounded,
              title: 'Shoebox',
              subtitle: l.settingsAboutVersion('0.2.0'),
              onTap: null,
            ),
          ]),
        ],
      ),
    );
  }

  Future<void> _confirmSignOut(BuildContext context, WidgetRef ref) async {
    HapticFeedback.selectionClick();
    final l = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l.settingsSignOutDialogTitle),
        content: Text(l.settingsSignOutDialogBody),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(l.commonCancel),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: ShoeboxColors.danger),
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(l.settingsSignOut),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await ref.read(authRepositoryProvider).signOut();
  }
}

class _LanguageTile extends ConsumerWidget {
  final Locale? current;
  final AppLocalizations l;
  const _LanguageTile({required this.current, required this.l});

  String _label(Locale? loc) {
    switch (loc?.languageCode) {
      case 'tr':
        return l.settingsLanguageTurkish;
      case 'es':
        return l.settingsLanguageSpanish;
      case 'pt':
        return l.settingsLanguagePortuguese;
      case 'en':
        return l.settingsLanguageEnglish;
      default:
        return l.settingsLanguageSystem;
    }
  }

  Future<void> _pick(BuildContext context, WidgetRef ref) async {
    HapticFeedback.selectionClick();
    final chosen = await showModalBottomSheet<Locale?>(
      context: context,
      backgroundColor: ShoeboxColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        final options = <(Locale?, String)>[
          (null, l.settingsLanguageSystem),
          (const Locale('en'), l.settingsLanguageEnglish),
          (const Locale('tr'), l.settingsLanguageTurkish),
          (const Locale('es'), l.settingsLanguageSpanish),
          (const Locale('pt'), l.settingsLanguagePortuguese),
        ];
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: ShoeboxColors.stroke,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                for (final opt in options)
                  ListTile(
                    title: Text(opt.$2),
                    trailing: (current?.languageCode ?? '') ==
                            (opt.$1?.languageCode ?? '')
                        ? const Icon(Icons.check_rounded,
                            color: ShoeboxColors.accent)
                        : null,
                    onTap: () => Navigator.pop(ctx, opt.$1),
                  ),
              ],
            ),
          ),
        );
      },
    );
    // showModalBottomSheet returns null on outside-tap; only apply when the
    // user actually picked something (any of the 5 list tiles).
    if (!context.mounted) return;
    if (chosen == null && current == null) return; // unchanged → noop
    await ref.read(localeControllerProvider.notifier).setLocale(chosen);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _Tile(
      icon: Icons.language_rounded,
      title: l.settingsSectionLanguage,
      subtitle: _label(current),
      onTap: () => _pick(context, ref),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final List<Widget> children;
  const _Section({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(4, 8, 4, 8),
          child: Text(
            title.toUpperCase(),
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: ShoeboxColors.textMid,
                  letterSpacing: 1.5,
                  fontWeight: FontWeight.w700,
                ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: ShoeboxColors.surface,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(children: children),
        ),
      ],
    );
  }
}

class _Tile extends StatelessWidget {
  final IconData icon;
  final Color? iconColor;
  final String title;
  final String? subtitle;
  final bool danger;
  final VoidCallback? onTap;

  const _Tile({
    required this.icon,
    required this.title,
    this.iconColor,
    this.subtitle,
    this.danger = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final fg = danger ? ShoeboxColors.danger : ShoeboxColors.textHigh;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
        child: Row(
          children: [
            Icon(icon,
                size: 20,
                color: danger
                    ? ShoeboxColors.danger
                    : (iconColor ?? ShoeboxColors.accent)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: TextStyle(
                          color: fg,
                          fontWeight: FontWeight.w600,
                          fontSize: 14)),
                  if (subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(subtitle!,
                        style: const TextStyle(
                            color: ShoeboxColors.textMid, fontSize: 12)),
                  ],
                ],
              ),
            ),
            if (onTap != null)
              const Icon(Icons.chevron_right_rounded,
                  size: 22, color: ShoeboxColors.textLow),
          ],
        ),
      ),
    );
  }
}
