import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'league_dto.dart';

class LeaguesRepository {
  final Ref ref;
  LeaguesRepository(this.ref);

  Future<LeaguesPayload> fetch({required String sport}) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get('/v1/leagues', queryParameters: {'sport': sport});
    return LeaguesPayload.fromJson(r.data as Map<String, dynamic>);
  }
}

final leaguesRepositoryProvider = Provider((ref) => LeaguesRepository(ref));

/// Family by sport — UI can toggle football/basketball and reuse cache.
final leaguesProvider = FutureProvider.family<LeaguesPayload, String>((ref, sport) {
  return ref.read(leaguesRepositoryProvider).fetch(sport: sport);
});
