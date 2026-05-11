import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/state/auth_provider.dart';
import '../../paywall/state/premium_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final isPremium = ref.watch(isPremiumProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          _Section(title: 'Account', children: [
            if (user == null)
              _Tile(
                icon: Icons.login_rounded,
                title: 'Sign in or sign up',
                subtitle: 'Save your watchlist and unlock premium',
                onTap: () => context.push('/login'),
              )
            else ...[
              _Tile(
                icon: Icons.email_outlined,
                title: user.email ?? 'Signed in',
                subtitle: 'User ID: ${user.id.substring(0, 8)}…',
                onTap: null,
              ),
              _Tile(
                icon: Icons.logout_rounded,
                title: 'Sign out',
                danger: true,
                onTap: () => _confirmSignOut(context, ref),
              ),
            ],
          ]),
          const SizedBox(height: 16),
          _Section(title: 'Subscription', children: [
            _Tile(
              icon: isPremium
                  ? Icons.workspace_premium_rounded
                  : Icons.lock_outline_rounded,
              iconColor:
                  isPremium ? ShoeboxColors.warn : ShoeboxColors.textMid,
              title: isPremium ? 'Premium active' : 'Upgrade to Premium',
              subtitle: isPremium
                  ? 'You have access to all features'
                  : 'Hit rates, splits, full averages',
              onTap: isPremium ? null : () => context.push('/paywall'),
            ),
          ]),
          const SizedBox(height: 16),
          _Section(title: 'About', children: [
            const _Tile(
              icon: Icons.info_outline_rounded,
              title: 'Shoebox',
              subtitle: 'Version 0.2.0',
              onTap: null,
            ),
          ]),
        ],
      ),
    );
  }

  Future<void> _confirmSignOut(BuildContext context, WidgetRef ref) async {
    HapticFeedback.selectionClick();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign out?'),
        content: const Text("You'll need to sign in again to access premium."),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: ShoeboxColors.danger),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Sign out'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await ref.read(authRepositoryProvider).signOut();
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
