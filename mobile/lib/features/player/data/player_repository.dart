import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'player_dto.dart';

class PlayerKey {
  final int playerId;
  final int leagueId;
  final int season;
  final String sport;
  const PlayerKey({
    required this.playerId,
    required this.leagueId,
    required this.season,
    required this.sport,
  });

  @override
  bool operator ==(Object other) =>
      other is PlayerKey &&
      other.playerId == playerId &&
      other.leagueId == leagueId &&
      other.season == season &&
      other.sport == sport;

  @override
  int get hashCode => Object.hash(playerId, leagueId, season, sport);
}

class PlayerRepository {
  final Ref ref;
  PlayerRepository(this.ref);

  Future<PlayerPayload> fetch(PlayerKey k) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get(
      '/v1/players/${k.playerId}',
      queryParameters: {'league_id': k.leagueId, 'season': k.season, 'sport': k.sport},
    );
    return PlayerPayload.fromJson(r.data as Map<String, dynamic>);
  }
}

final playerRepositoryProvider = Provider((ref) => PlayerRepository(ref));

final playerProvider = FutureProvider.family<PlayerPayload, PlayerKey>((ref, key) {
  return ref.read(playerRepositoryProvider).fetch(key);
});
