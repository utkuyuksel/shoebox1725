double? _asDouble(dynamic v) {
  if (v == null) return null;
  if (v is num) return v.toDouble();
  return double.tryParse('$v');
}

class RefereeSearchResultDto {
  final int id;
  final String name;
  final String? nationality;
  final String? photo;
  const RefereeSearchResultDto({
    required this.id,
    required this.name,
    required this.nationality,
    required this.photo,
  });

  factory RefereeSearchResultDto.fromJson(Map<String, dynamic> j) =>
      RefereeSearchResultDto(
        id: j['id'] as int,
        name: (j['name'] ?? 'Unknown') as String,
        nationality: j['nationality'] as String?,
        photo: j['photo'] as String?,
      );
}

class RefereeProfileDto {
  final int id;
  final String name;
  final String? nationality;
  final String? photo;
  const RefereeProfileDto({
    required this.id,
    required this.name,
    required this.nationality,
    required this.photo,
  });

  factory RefereeProfileDto.fromJson(Map<String, dynamic> j) => RefereeProfileDto(
        id: j['id'] as int,
        name: (j['name'] ?? 'Unknown') as String,
        nationality: j['nationality'] as String?,
        photo: j['photo'] as String?,
      );
}

class RefereeSeasonStatsDto {
  final int leagueId;
  final int matches;
  final double? yellowCardsPg;
  final double? redCardsPg;
  final double? foulsPg;
  final double? penaltiesPg;
  final double? homeWinPct;

  const RefereeSeasonStatsDto({
    required this.leagueId,
    required this.matches,
    required this.yellowCardsPg,
    required this.redCardsPg,
    required this.foulsPg,
    required this.penaltiesPg,
    required this.homeWinPct,
  });

  factory RefereeSeasonStatsDto.fromJson(Map<String, dynamic> j) =>
      RefereeSeasonStatsDto(
        leagueId: j['league_id'] as int,
        matches: (j['matches'] ?? 0) as int,
        yellowCardsPg: _asDouble(j['yellow_cards_pg']),
        redCardsPg: _asDouble(j['red_cards_pg']),
        foulsPg: _asDouble(j['fouls_pg']),
        penaltiesPg: _asDouble(j['penalties_pg']),
        homeWinPct: _asDouble(j['home_win_pct']),
      );
}

class RefereeLastMatchDto {
  final int id;
  final int leagueId;
  final int season;
  final DateTime kickoffAt;
  final String homeName;
  final int? homeGoals;
  final String? homeLogo;
  final String awayName;
  final int? awayGoals;
  final String? awayLogo;
  final int yellowCards;
  final int redCards;

  const RefereeLastMatchDto({
    required this.id,
    required this.leagueId,
    required this.season,
    required this.kickoffAt,
    required this.homeName,
    required this.homeGoals,
    required this.homeLogo,
    required this.awayName,
    required this.awayGoals,
    required this.awayLogo,
    required this.yellowCards,
    required this.redCards,
  });

  factory RefereeLastMatchDto.fromJson(Map<String, dynamic> j) {
    final h = (j['home'] as Map).cast<String, dynamic>();
    final a = (j['away'] as Map).cast<String, dynamic>();
    return RefereeLastMatchDto(
      id: j['id'] as int,
      leagueId: j['league_id'] as int,
      season: j['season'] as int,
      kickoffAt: DateTime.parse(j['kickoff_at'] as String),
      homeName: (h['name'] ?? 'Home') as String,
      homeGoals: h['goals'] as int?,
      homeLogo: h['logo'] as String?,
      awayName: (a['name'] ?? 'Away') as String,
      awayGoals: a['goals'] as int?,
      awayLogo: a['logo'] as String?,
      yellowCards: (j['yellow_cards'] ?? 0) as int,
      redCards: (j['red_cards'] ?? 0) as int,
    );
  }
}

class RefereeProfilePayload {
  final RefereeProfileDto referee;
  final List<RefereeSeasonStatsDto> seasonStats;
  final List<RefereeLastMatchDto> lastMatches;

  const RefereeProfilePayload({
    required this.referee,
    required this.seasonStats,
    required this.lastMatches,
  });

  factory RefereeProfilePayload.fromJson(Map<String, dynamic> j) =>
      RefereeProfilePayload(
        referee: RefereeProfileDto.fromJson(
          (j['referee'] as Map).cast<String, dynamic>(),
        ),
        seasonStats: (j['season_stats'] as List? ?? const [])
            .cast<Map<String, dynamic>>()
            .map(RefereeSeasonStatsDto.fromJson)
            .toList(),
        lastMatches: (j['last_matches'] as List? ?? const [])
            .cast<Map<String, dynamic>>()
            .map(RefereeLastMatchDto.fromJson)
            .toList(),
      );
}
