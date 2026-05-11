/// Mirrors the backend /v1/leagues response.
class LeagueDto {
  final int id;
  final String name;
  final String sport;            // 'football' | 'basketball'
  final String? country;
  final String? countryCode;     // ISO-2, used for flag rendering
  final String? logo;
  final bool isDefaultPopular;
  final bool isFreeTier;
  final int sortOrder;

  const LeagueDto({
    required this.id,
    required this.name,
    required this.sport,
    required this.country,
    required this.countryCode,
    required this.logo,
    required this.isDefaultPopular,
    required this.isFreeTier,
    required this.sortOrder,
  });

  factory LeagueDto.fromJson(Map<String, dynamic> j) => LeagueDto(
        id: j['id'] as int,
        name: j['name'] as String,
        sport: j['sport'] as String,
        country: j['country'] as String?,
        countryCode: j['country_code'] as String?,
        logo: j['logo'] as String?,
        isDefaultPopular: (j['is_default_popular'] ?? false) as bool,
        isFreeTier: (j['is_free_tier'] ?? false) as bool,
        sortOrder: (j['sort_order'] ?? 999) as int,
      );
}

class LeaguesPayload {
  final int count;
  final List<LeagueDto> popular;
  final Map<String, List<LeagueDto>> grouped;
  const LeaguesPayload({required this.count, required this.popular, required this.grouped});

  factory LeaguesPayload.fromJson(Map<String, dynamic> j) {
    final popular = (j['popular'] as List? ?? [])
        .cast<Map<String, dynamic>>()
        .map(LeagueDto.fromJson)
        .toList();

    final grouped = <String, List<LeagueDto>>{};
    final rawGrouped = (j['grouped'] as Map?)?.cast<String, dynamic>() ?? {};
    for (final entry in rawGrouped.entries) {
      grouped[entry.key] = (entry.value as List)
          .cast<Map<String, dynamic>>()
          .map(LeagueDto.fromJson)
          .toList();
    }
    return LeaguesPayload(
      count: (j['count'] ?? 0) as int,
      popular: popular,
      grouped: grouped,
    );
  }
}
