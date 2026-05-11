import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'fixture_dto.dart';

class FixturesRepository {
  final Ref ref;
  FixturesRepository(this.ref);

  Future<FixturesPayload> fetch(int leagueId) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get('/v1/leagues/$leagueId/fixtures');
    return FixturesPayload.fromJson(r.data as Map<String, dynamic>);
  }
}

final fixturesRepositoryProvider = Provider((ref) => FixturesRepository(ref));

final fixturesProvider = FutureProvider.family<FixturesPayload, int>((ref, leagueId) {
  return ref.read(fixturesRepositoryProvider).fetch(leagueId);
});
