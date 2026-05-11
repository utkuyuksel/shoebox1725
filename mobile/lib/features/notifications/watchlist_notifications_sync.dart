import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../watchlist/data/watchlist_dto.dart';
import '../watchlist/data/watchlist_repository.dart';
import 'notifications_service.dart';

/// Keeps local kickoff-reminder notifications in sync with the user's
/// watchlist. Watched once from the app shell, runs forever.
///
/// On every watchlist refresh (add, remove, server sync) we:
///   1. Cancel every scheduled reminder.
///   2. Re-schedule one per fixture, 1h before kickoff.
///
/// Cancel-then-reschedule is intentionally naive — iOS local notifications
/// have no useful "diff" API and re-scheduling 100 items is cheap.
final watchlistNotificationsSyncProvider = Provider<void>((ref) {
  ref.listen<AsyncValue<List<WatchlistFixtureDto>>>(
    watchlistFixturesProvider,
    (prev, next) async {
      final fixtures = next.valueOrNull;
      if (fixtures == null) return;
      // Wipe and rebuild — see class docs.
      await NotificationsService.cancelAll();
      for (final fx in fixtures) {
        final title = '${fx.homeTeamName} vs ${fx.awayTeamName}';
        final body = 'Kickoff in 1 hour · ${fx.leagueName}';
        await NotificationsService.scheduleKickoffReminder(
          fixtureId: fx.id,
          kickoffAtUtc: fx.kickoffAt.toUtc(),
          title: title,
          body: body,
        );
      }
    },
    fireImmediately: true,
  );
});
