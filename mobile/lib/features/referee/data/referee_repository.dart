import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import 'referee_dto.dart';

class RefereeProfileKey {
  final int refereeId;
  final int season;
  const RefereeProfileKey({required this.refereeId, required this.season});

  @override
  bool operator ==(Object other) =>
      other is RefereeProfileKey &&
      other.refereeId == refereeId &&
      other.season == season;

  @override
  int get hashCode => Object.hash(refereeId, season);
}

class RefereeRepository {
  final Ref ref;
  RefereeRepository(this.ref);

  Future<List<RefereeSearchResultDto>> search(String query) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get('/v1/referees/search', queryParameters: {'q': query});
    return ((r.data as Map<String, dynamic>)['results'] as List? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(RefereeSearchResultDto.fromJson)
        .toList();
  }

  Future<RefereeProfilePayload> profile(RefereeProfileKey k) async {
    final dio = ref.read(dioProvider);
    final r = await dio.get(
      '/v1/referees/${k.refereeId}',
      queryParameters: {'season': k.season},
    );
    return RefereeProfilePayload.fromJson(r.data as Map<String, dynamic>);
  }
}

final refereeRepositoryProvider = Provider((ref) => RefereeRepository(ref));

/// Search results, keyed by query string. Returns empty for queries < 2 chars
/// so the UI can render a hint state without firing a request.
final refereeSearchProvider =
    FutureProvider.family<List<RefereeSearchResultDto>, String>((ref, query) async {
  final q = query.trim();
  if (q.length < 2) return const [];
  return ref.read(refereeRepositoryProvider).search(q);
});

final refereeProfileProvider =
    FutureProvider.family<RefereeProfilePayload, RefereeProfileKey>((ref, key) {
  return ref.read(refereeRepositoryProvider).profile(key);
});
