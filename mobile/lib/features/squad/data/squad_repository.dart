import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'squad_dto.dart';

/// Composite key for the family provider — squad is scoped per
/// (team, league, season). Three params, so we wrap them.
class SquadKey {
  final int teamId;
  final int leagueId;
  final int season;
  const SquadKey({required this.teamId, required this.leagueId, required this.season});

  @override
  bool operator ==(Object other) =>
      other is SquadKey &&
      other.teamId == teamId &&
      other.leagueId == leagueId &&
      other.season == season;

  @override
  int get hashCode => Object.hash(teamId, leagueId, season);
}

class SquadRepository {
  final Ref ref;
  SquadRepository(this.ref);

  Future<SquadPayload> fetch(SquadKey k) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get(
      '/v1/teams/${k.teamId}/squad',
      queryParameters: {'league_id': k.leagueId, 'season': k.season},
    );
    return SquadPayload.fromJson(r.data as Map<String, dynamic>);
  }
}

final squadRepositoryProvider = Provider((ref) => SquadRepository(ref));

final squadProvider = FutureProvider.family<SquadPayload, SquadKey>((ref, key) {
  return ref.read(squadRepositoryProvider).fetch(key);
});
