import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/presentation/login_screen.dart';
import '../features/fixtures/data/fixture_dto.dart';
import '../features/fixtures/presentation/fixtures_screen.dart';
import '../features/leagues/presentation/home_screen.dart';
import '../features/match/presentation/match_preview_screen.dart';
import '../features/onboarding/presentation/onboarding_screen.dart';
import '../features/paywall/presentation/paywall_screen.dart';
import '../features/player/presentation/player_detail_screen.dart';
import '../features/referee/presentation/referee_profile_screen.dart';
import '../features/referee/presentation/referee_search_screen.dart';
import '../features/settings/presentation/settings_screen.dart';
import '../features/squad/presentation/squad_screen.dart';
import '../features/standings/presentation/standings_screen.dart';
import '../features/watchlist/presentation/watchlist_screen.dart';
import 'main_shell.dart';

/// Smooth slide-from-right + fade for every pushed route. Cuts the snap-in
/// feel that go_router's default transitions have on iOS Material routes.
CustomTransitionPage<T> _slideFade<T>({required Widget child, required GoRouterState state}) {
  return CustomTransitionPage<T>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 260),
    reverseTransitionDuration: const Duration(milliseconds: 220),
    transitionsBuilder: (context, animation, secondary, child) {
      final curved = CurvedAnimation(parent: animation, curve: Curves.easeOutCubic);
      return FadeTransition(
        opacity: curved,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0.08, 0),
            end: Offset.zero,
          ).animate(curved),
          child: child,
        ),
      );
    },
  );
}

/// Crossfade for bottom-nav tab switches — pushing a slide transition would
/// look like a back-stack pop, which is misleading.
CustomTransitionPage<T> _fade<T>({required Widget child, required GoRouterState state}) {
  return CustomTransitionPage<T>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 180),
    reverseTransitionDuration: const Duration(milliseconds: 160),
    transitionsBuilder: (_, animation, __, child) =>
        FadeTransition(opacity: animation, child: child),
  );
}

final _rootNavigatorKey = GlobalKey<NavigatorState>();

/// Flipped by [setOnboardingComplete] (called from the OnboardingController
/// when the user finishes the tour, or set during boot from SharedPreferences).
/// Read by GoRouter's `redirect` callback — when false, every navigation to
/// the shell is rerouted to /onboarding so the first-launch tour is
/// unavoidable. Kept as a module-level mutable boolean (not a Riverpod
/// provider) because GoRouter's redirect signature is sync and can't await
/// a provider read.
bool _onboardingComplete = false;

void setOnboardingComplete(bool v) {
  _onboardingComplete = v;
  appRouter.refresh();
}

final appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/',
  redirect: (context, state) {
    if (_onboardingComplete) return null;
    if (state.matchedLocation == '/onboarding') return null;
    return '/onboarding';
  },
  routes: [
    // ── Shell: bottom nav over three branches ──────────────────────────
    StatefulShellRoute.indexedStack(
      builder: (context, state, shell) => MainShell(shell: shell),
      branches: [
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/',
            pageBuilder: (c, s) => _fade(state: s, child: const HomeScreen()),
          ),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/watchlist',
            pageBuilder: (c, s) => _fade(state: s, child: const WatchlistScreen()),
          ),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/settings',
            pageBuilder: (c, s) => _fade(state: s, child: const SettingsScreen()),
          ),
        ]),
      ],
    ),

    // ── Full-screen routes pushed over the shell ────────────────────────
    GoRoute(
      path: '/leagues/:leagueId/fixtures',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) {
        final id = int.parse(s.pathParameters['leagueId']!);
        final name = (s.extra as String?) ?? 'League';
        return _slideFade(state: s, child: FixturesScreen(leagueId: id, leagueName: name));
      },
    ),
    GoRoute(
      path: '/leagues/:leagueId/standings',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) {
        final id = int.parse(s.pathParameters['leagueId']!);
        final name = (s.extra as String?) ?? (s.uri.queryParameters['name'] ?? 'Standings');
        return _slideFade(state: s, child: StandingsScreen(leagueId: id, leagueName: name));
      },
    ),
    GoRoute(
      path: '/match/:fixtureId',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) {
        final id = int.parse(s.pathParameters['fixtureId']!);
        final hint = s.extra as FixtureDto?;
        return _slideFade(state: s, child: MatchPreviewScreen(fixtureId: id, hint: hint));
      },
    ),
    GoRoute(
      path: '/team/:teamId/squad',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) {
        final teamId = int.parse(s.pathParameters['teamId']!);
        final q = s.uri.queryParameters;
        return _slideFade(
          state: s,
          child: SquadScreen(
            teamId: teamId,
            leagueId: int.parse(q['league'] ?? '0'),
            season: int.parse(q['season'] ?? '0'),
            teamName: q['name'] ?? 'Squad',
          ),
        );
      },
    ),
    GoRoute(
      path: '/player/:playerId',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) {
        final id = int.parse(s.pathParameters['playerId']!);
        final q = s.uri.queryParameters;
        return _slideFade(
          state: s,
          child: PlayerDetailScreen(
            playerId: id,
            leagueId: int.parse(q['league'] ?? '0'),
            season: int.parse(q['season'] ?? '0'),
            sport: q['sport'] ?? 'football',
            nameHint: q['name'],
          ),
        );
      },
    ),
    GoRoute(
      path: '/referees',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) => _slideFade(state: s, child: const RefereeSearchScreen()),
    ),
    GoRoute(
      path: '/referee/:refereeId',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) {
        final id = int.parse(s.pathParameters['refereeId']!);
        final q = s.uri.queryParameters;
        return _slideFade(
          state: s,
          child: RefereeProfileScreen(
            refereeId: id,
            season: int.parse(q['season'] ?? '0'),
            nameHint: q['name'],
          ),
        );
      },
    ),
    GoRoute(
      path: '/login',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) => _slideFade(state: s, child: const LoginScreen()),
    ),
    GoRoute(
      path: '/paywall',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) => _slideFade(state: s, child: const PaywallScreen()),
    ),
    GoRoute(
      path: '/onboarding',
      parentNavigatorKey: _rootNavigatorKey,
      pageBuilder: (c, s) => _slideFade(state: s, child: const OnboardingScreen()),
    ),
  ],
);
