import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

import '../features/fixtures/data/fixture_dto.dart';
import '../features/fixtures/presentation/fixtures_screen.dart';
import '../features/leagues/presentation/home_screen.dart';
import '../features/match/presentation/match_preview_screen.dart';
import '../features/player/presentation/player_detail_screen.dart';
import '../features/referee/presentation/referee_profile_screen.dart';
import '../features/referee/presentation/referee_search_screen.dart';
import '../features/squad/presentation/squad_screen.dart';

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

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      // Home stays as the root with the default no-op transition.
      builder: (c, s) => const HomeScreen(),
    ),
    GoRoute(
      path: '/leagues/:leagueId/fixtures',
      pageBuilder: (c, s) {
        final id = int.parse(s.pathParameters['leagueId']!);
        final name = (s.extra as String?) ?? 'League';
        return _slideFade(state: s, child: FixturesScreen(leagueId: id, leagueName: name));
      },
    ),
    GoRoute(
      path: '/match/:fixtureId',
      pageBuilder: (c, s) {
        final id = int.parse(s.pathParameters['fixtureId']!);
        final hint = s.extra as FixtureDto?;
        return _slideFade(state: s, child: MatchPreviewScreen(fixtureId: id, hint: hint));
      },
    ),
    GoRoute(
      path: '/team/:teamId/squad',
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
      pageBuilder: (c, s) => _slideFade(state: s, child: const RefereeSearchScreen()),
    ),
    GoRoute(
      path: '/referee/:refereeId',
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
  ],
);
