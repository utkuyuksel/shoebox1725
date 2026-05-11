import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'watchlist_dto.dart';

class WatchlistRepository {
  WatchlistRepository(this._dio);

  final Dio _dio;

  Future<List<WatchlistFixtureDto>> list() async {
    final res = await _dio.get<Map<String, dynamic>>('/v1/me/watchlist');
    final fixtures = (res.data?['fixtures'] as List?) ?? const [];
    return fixtures
        .cast<Map<String, dynamic>>()
        .map(WatchlistFixtureDto.fromJson)
        .toList(growable: false);
  }

  Future<void> add(int fixtureId) async {
    await _dio.post<void>('/v1/me/watchlist/$fixtureId');
  }

  Future<void> remove(int fixtureId) async {
    await _dio.delete<void>('/v1/me/watchlist/$fixtureId');
  }
}

final watchlistRepositoryProvider = Provider<WatchlistRepository>((ref) {
  return WatchlistRepository(ref.watch(dioProvider));
});

/// Cached list of fixture IDs that are on the user's watchlist. Used by the
/// star button to render its filled / outline state without re-fetching.
final watchlistFixturesProvider =
    FutureProvider<List<WatchlistFixtureDto>>((ref) async {
  // Re-fetch when auth flips.
  final repo = ref.watch(watchlistRepositoryProvider);
  return repo.list();
});

/// Quick set of fixture ids on the watchlist. Star button derives from this.
final watchlistIdsProvider = Provider<Set<int>>((ref) {
  final value = ref.watch(watchlistFixturesProvider).valueOrNull;
  if (value == null) return const <int>{};
  return value.map((f) => f.id).toSet();
});
