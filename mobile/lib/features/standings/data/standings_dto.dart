/// Mirrors GET /v1/leagues/{id}/standings. One row per team; sport-specific
/// columns (draws/points for football, winPct for basketball) are nullable.

int? _asInt(dynamic v) {
  if (v == null) return null;
  if (v is int) return v;
  if (v is num) return v.toInt();
  return int.tryParse('$v');
}

double? _asDouble(dynamic v) {
  if (v == null) return null;
  if (v is num) return v.toDouble();
  return double.tryParse('$v');
}

class StandingRowDto {
  final int rank;
  final int teamId;
  final String name;
  final String? shortName;
  final String? logo;
  final int played;
  final int wins;
  final int losses;
  final int? draws;            // football only
  final int pointsFor;         // goals or points scored
  final int pointsAgainst;
  final int diff;
  final int? points;           // football table points
  final double? winPct;        // basketball
  final List<String> form;     // 'W' / 'D' / 'L', most recent last

  const StandingRowDto({
    required this.rank,
    required this.teamId,
    required this.name,
    required this.shortName,
    required this.logo,
    required this.played,
    required this.wins,
    required this.losses,
    required this.draws,
    required this.pointsFor,
    required this.pointsAgainst,
    required this.diff,
    required this.points,
    required this.winPct,
    required this.form,
  });

  factory StandingRowDto.fromJson(Map<String, dynamic> j) => StandingRowDto(
        rank: (j['rank'] ?? 0) as int,
        teamId: j['team_id'] as int,
        name: j['name'] as String,
        shortName: j['short_name'] as String?,
        logo: j['logo'] as String?,
        played: (j['played'] ?? 0) as int,
        wins: (j['wins'] ?? 0) as int,
        losses: (j['losses'] ?? 0) as int,
        draws: _asInt(j['draws']),
        pointsFor: (j['points_for'] ?? 0) as int,
        pointsAgainst: (j['points_against'] ?? 0) as int,
        diff: (j['diff'] ?? 0) as int,
        points: _asInt(j['points']),
        winPct: _asDouble(j['win_pct']),
        form: ((j['form'] as List?) ?? const []).map((e) => '$e').toList(),
      );
}

class StandingsDto {
  final int leagueId;
  final int? season;
  final String sport;          // 'football' | 'basketball'
  final List<StandingRowDto> rows;

  const StandingsDto({
    required this.leagueId,
    required this.season,
    required this.sport,
    required this.rows,
  });

  bool get isBasketball => sport == 'basketball';

  factory StandingsDto.fromJson(Map<String, dynamic> j) => StandingsDto(
        leagueId: j['league_id'] as int,
        season: _asInt(j['season']),
        sport: (j['sport'] ?? 'football') as String,
        rows: ((j['rows'] as List?) ?? const [])
            .cast<Map<String, dynamic>>()
            .map(StandingRowDto.fromJson)
            .toList(),
      );
}
