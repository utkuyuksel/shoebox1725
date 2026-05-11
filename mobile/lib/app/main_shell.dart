import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/paywall/state/premium_provider.dart';
import '../features/watchlist/data/watchlist_repository.dart';
import 'theme.dart';

/// Three-tab bottom navigation hosted on the root route. Each tab is its own
/// navigator stack so deep pushes inside one tab don't disturb the others.
/// Full-screen routes (login, paywall, match detail, …) live outside the
/// shell so they cover the bottom bar.
class MainShell extends ConsumerWidget {
  final StatefulNavigationShell shell;
  const MainShell({super.key, required this.shell});

  void _onTap(int i) {
    HapticFeedback.selectionClick();
    // Tapping the active tab pops to that tab's root — standard iOS pattern.
    shell.goBranch(i, initialLocation: i == shell.currentIndex);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final watchlistCount =
        ref.watch(watchlistFixturesProvider).valueOrNull?.length ?? 0;
    final isPremium = ref.watch(isPremiumProvider);

    return Scaffold(
      body: shell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: shell.currentIndex,
        onDestinationSelected: _onTap,
        backgroundColor: ShoeboxColors.surface,
        indicatorColor: ShoeboxColors.accentSoft,
        surfaceTintColor: Colors.transparent,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.shield_outlined),
            selectedIcon: Icon(Icons.shield_rounded, color: ShoeboxColors.accent),
            label: 'Leagues',
          ),
          NavigationDestination(
            icon: _BadgedIcon(
              icon: Icons.bookmark_outline_rounded,
              count: watchlistCount,
            ),
            selectedIcon: _BadgedIcon(
              icon: Icons.bookmark_rounded,
              color: ShoeboxColors.accent,
              count: watchlistCount,
            ),
            label: 'Watchlist',
          ),
          NavigationDestination(
            icon: _DotIcon(
              icon: Icons.person_outline_rounded,
              showDot: isPremium,
            ),
            selectedIcon: _DotIcon(
              icon: Icons.person_rounded,
              color: ShoeboxColors.accent,
              showDot: isPremium,
            ),
            label: 'Account',
          ),
        ],
      ),
    );
  }
}

class _BadgedIcon extends StatelessWidget {
  final IconData icon;
  final Color? color;
  final int count;
  const _BadgedIcon({required this.icon, this.color, required this.count});

  @override
  Widget build(BuildContext context) {
    if (count <= 0) return Icon(icon, color: color);
    final label = count > 99 ? '99+' : '$count';
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Icon(icon, color: color),
        Positioned(
          right: -8,
          top: -4,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
            constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
            decoration: BoxDecoration(
              color: ShoeboxColors.accent,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: ShoeboxColors.surface, width: 1.5),
            ),
            child: Center(
              child: Text(
                label,
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 9,
                    fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _DotIcon extends StatelessWidget {
  final IconData icon;
  final Color? color;
  final bool showDot;
  const _DotIcon({required this.icon, this.color, required this.showDot});

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Icon(icon, color: color),
        if (showDot)
          Positioned(
            right: -2,
            top: -2,
            child: Container(
              width: 9,
              height: 9,
              decoration: BoxDecoration(
                color: ShoeboxColors.warn,
                shape: BoxShape.circle,
                border: Border.all(color: ShoeboxColors.surface, width: 1.5),
              ),
            ),
          ),
      ],
    );
  }
}
