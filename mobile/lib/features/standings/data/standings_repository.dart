import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'standings_dto.dart';

class StandingsRepository {
  final Ref ref;
  StandingsRepository(this.ref);

  Future<StandingsDto> fetch(int leagueId) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get('/v1/leagues/$leagueId/standings');
    return StandingsDto.fromJson(r.data as Map<String, dynamic>);
  }
}

final standingsRepositoryProvider = Provider((ref) => StandingsRepository(ref));

final standingsProvider = FutureProvider.family<StandingsDto, int>((ref, leagueId) {
  return ref.read(standingsRepositoryProvider).fetch(leagueId);
});
