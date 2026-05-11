import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'match_preview_dto.dart';

class MatchRepository {
  final Ref ref;
  MatchRepository(this.ref);

  Future<MatchPreviewDto> preview(int fixtureId) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get('/v1/match/$fixtureId');
    return MatchPreviewDto.fromJson(r.data as Map<String, dynamic>);
  }
}

final matchRepositoryProvider = Provider((ref) => MatchRepository(ref));

final matchPreviewProvider =
    FutureProvider.family<MatchPreviewDto, int>((ref, fixtureId) {
  return ref.read(matchRepositoryProvider).preview(fixtureId);
});
