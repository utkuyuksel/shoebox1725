/// Mirrors the backend /v1/match/{id} payload. Kept verbose on purpose —
/// every field here drives a visible widget on the preview screen.

double? _asDouble(dynamic v) {
  if (v == null) return null;
  if (v is num) return v.toDouble();
  return double.tryParse('$v');
}

int? _asInt(dynamic v) {
  if (v == null) return null;
  if (v is int) return v;
  if (v is num) return v.toInt();
  return int.tryParse('$v');
}

class FixtureMetaDto {
  final int id;
  final int leagueId;
  final int season;
  final String? round;
  final DateTime kickoffAt;
  final String status;
  final String? venue;
  final String sport;             // 'football' | 'basketball'
  const FixtureMetaDto({
    required this.id,
    required this.leagueId,
    required this.season,
    required this.round,
    required this.kickoffAt,
    required this.status,
    required this.venue,
    required this.sport,
  });

  bool get isFootball => sport == 'football';
  bool get isBasketball => sport == 'basketball';

  factory FixtureMetaDto.fromJson(Map<String, dynamic> j) => FixtureMetaDto(
        id: j['id'] as int,
        leagueId: j['league_id'] as int,
        season: j['season'] as int,
        round: j['round'] as String?,
        kickoffAt: DateTime.parse(j['kickoff_at'] as String),
        status: j['status'] as String,
        venue: j['venue'] as String?,
        sport: (j['sport'] ?? 'football') as String,
      );
}

/// Football season averages for one team. Renamed in spirit to "football"
/// but kept its existing class name to avoid touching every call site.
class TeamSeasonStatsDto {
  final int played;
  final double? goalsForPg;
  final double? goalsAgainstPg;
  final double? xgPg;
  final double? shotsTotalPg;
  final double? shotsOnPg;
  final double? cornersPg;
  final double? foulsPg;
  final double? offsidesPg;
  final double? yellowCardsPg;
  final double? redCardsPg;
  final int? position;
  final int? wins;
  final int? draws;
  final int? losses;

  const TeamSeasonStatsDto({
    required this.played,
    required this.goalsForPg,
    required this.goalsAgainstPg,
    required this.xgPg,
    required this.shotsTotalPg,
    required this.shotsOnPg,
    required this.cornersPg,
    required this.foulsPg,
    required this.offsidesPg,
    required this.yellowCardsPg,
    required this.redCardsPg,
    required this.position,
    required this.wins,
    required this.draws,
    required this.losses,
  });

  factory TeamSeasonStatsDto.fromJson(Map<String, dynamic> j) => TeamSeasonStatsDto(
        played: (j['played'] ?? 0) as int,
        goalsForPg: _asDouble(j['goals_for_pg']),
        goalsAgainstPg: _asDouble(j['goals_against_pg']),
        xgPg: _asDouble(j['xg_pg']),
        shotsTotalPg: _asDouble(j['shots_total_pg']),
        shotsOnPg: _asDouble(j['shots_on_pg']),
        cornersPg: _asDouble(j['corners_pg']),
        foulsPg: _asDouble(j['fouls_pg']),
        offsidesPg: _asDouble(j['offsides_pg']),
        yellowCardsPg: _asDouble(j['yellow_cards_pg']),
        redCardsPg: _asDouble(j['red_cards_pg']),
        position: _asInt(j['position']),
        wins: _asInt(j['wins']),
        draws: _asInt(j['draws']),
        losses: _asInt(j['losses']),
      );
}

/// Basketball season averages for one team.
class BasketballTeamStatsDto {
  final int played;
  final double? pointsPg;
  final double? pointsAllowedPg;
  final double? fgPct;
  final double? twoPct;
  final double? threePct;
  final double? ftPct;
  final double? twoMadePg;
  final double? twoAttPg;
  final double? threeMadePg;
  final double? threeAttPg;
  final double? ftMadePg;
  final double? ftAttPg;
  final double? reboundsOffPg;
  final double? reboundsDefPg;
  final double? reboundsTotalPg;
  final double? assistsPg;
  final double? stealsPg;
  final double? blocksPg;
  final double? turnoversPg;
  final int? homePlayed;
  final double? homePointsPg;
  final double? homePointsAllowedPg;
  final int? awayPlayed;
  final double? awayPointsPg;
  final double? awayPointsAllowedPg;
  final int? wins;
  final int? losses;

  const BasketballTeamStatsDto({
    required this.played,
    required this.pointsPg,
    required this.pointsAllowedPg,
    required this.fgPct,
    required this.twoPct,
    required this.threePct,
    required this.ftPct,
    required this.twoMadePg,
    required this.twoAttPg,
    required this.threeMadePg,
    required this.threeAttPg,
    required this.ftMadePg,
    required this.ftAttPg,
    required this.reboundsOffPg,
    required this.reboundsDefPg,
    required this.reboundsTotalPg,
    required this.assistsPg,
    required this.stealsPg,
    required this.blocksPg,
    required this.turnoversPg,
    required this.homePlayed,
    required this.homePointsPg,
    required this.homePointsAllowedPg,
    required this.awayPlayed,
    required this.awayPointsPg,
    required this.awayPointsAllowedPg,
    required this.wins,
    required this.losses,
  });

  factory BasketballTeamStatsDto.fromJson(Map<String, dynamic> j) =>
      BasketballTeamStatsDto(
        played: (j['played'] ?? 0) as int,
        pointsPg: _asDouble(j['points_pg']),
        pointsAllowedPg: _asDouble(j['points_allowed_pg']),
        fgPct: _asDouble(j['fg_pct']),
        twoPct: _asDouble(j['two_pct']),
        threePct: _asDouble(j['three_pct']),
        ftPct: _asDouble(j['ft_pct']),
        twoMadePg: _asDouble(j['two_made_pg']),
        twoAttPg: _asDouble(j['two_att_pg']),
        threeMadePg: _asDouble(j['three_made_pg']),
        threeAttPg: _asDouble(j['three_att_pg']),
        ftMadePg: _asDouble(j['ft_made_pg']),
        ftAttPg: _asDouble(j['ft_att_pg']),
        reboundsOffPg: _asDouble(j['rebounds_off_pg']),
        reboundsDefPg: _asDouble(j['rebounds_def_pg']),
        reboundsTotalPg: _asDouble(j['rebounds_total_pg']),
        assistsPg: _asDouble(j['assists_pg']),
        stealsPg: _asDouble(j['steals_pg']),
        blocksPg: _asDouble(j['blocks_pg']),
        turnoversPg: _asDouble(j['turnovers_pg']),
        homePlayed: _asInt(j['home_played']),
        homePointsPg: _asDouble(j['home_points_pg']),
        homePointsAllowedPg: _asDouble(j['home_points_allowed_pg']),
        awayPlayed: _asInt(j['away_played']),
        awayPointsPg: _asDouble(j['away_points_pg']),
        awayPointsAllowedPg: _asDouble(j['away_points_allowed_pg']),
        wins: _asInt(j['wins']),
        losses: _asInt(j['losses']),
      );
}

class TeamBlockDto {
  final int id;
  final String name;
  final String? shortName;
  final String? logo;
  final TeamSeasonStatsDto? footballStats;
  final BasketballTeamStatsDto? basketballStats;

  const TeamBlockDto({
    required this.id,
    required this.name,
    this.shortName,
    this.logo,
    this.footballStats,
    this.basketballStats,
  });

  /// Quick helpers for code that pre-existed the basketball split.
  TeamSeasonStatsDto? get stats => footballStats;

  factory TeamBlockDto.fromJson(Map<String, dynamic> j) {
    // Tolerate both new (football_stats/basketball_stats) and old (season_stats)
    // shapes so older response payloads don't crash the UI.
    final fb = j['football_stats'] ?? j['season_stats'];
    final bb = j['basketball_stats'];
    return TeamBlockDto(
      id: j['id'] as int,
      name: j['name'] as String,
      shortName: j['short_name'] as String?,
      logo: j['logo'] as String?,
      footballStats: fb == null
          ? null
          : TeamSeasonStatsDto.fromJson((fb as Map).cast<String, dynamic>()),
      basketballStats: bb == null
          ? null
          : BasketballTeamStatsDto.fromJson((bb as Map).cast<String, dynamic>()),
    );
  }
}

class HitRatesDto {
  final int matches;
  final double? over15;
  final double? over25;
  final double? over35;
  final double? btts;
  final double? cornersOver85;
  final double? cornersOver105;
  final double? cardsOver35;
  final double? cardsOver45;

  const HitRatesDto({
    required this.matches,
    required this.over15,
    required this.over25,
    required this.over35,
    required this.btts,
    required this.cornersOver85,
    required this.cornersOver105,
    required this.cardsOver35,
    required this.cardsOver45,
  });

  factory HitRatesDto.fromJson(Map<String, dynamic> j) => HitRatesDto(
        matches: (j['matches'] ?? 0) as int,
        over15: _asDouble(j['over_15']),
        over25: _asDouble(j['over_25']),
        over35: _asDouble(j['over_35']),
        btts: _asDouble(j['btts']),
        cornersOver85: _asDouble(j['corners_over_85']),
        cornersOver105: _asDouble(j['corners_over_105']),
        cardsOver35: _asDouble(j['cards_over_35']),
        cardsOver45: _asDouble(j['cards_over_45']),
      );
}

class RadarDto {
  final List<String> axes;
  final List<double?> home;
  final List<double?> away;
  const RadarDto({required this.axes, required this.home, required this.away});

  factory RadarDto.fromJson(Map<String, dynamic> j) {
    return RadarDto(
      axes: ((j['axes'] as List?) ?? const []).cast<String>(),
      home: ((j['home'] as List?) ?? const []).map(_asDouble).toList(),
      away: ((j['away'] as List?) ?? const []).map(_asDouble).toList(),
    );
  }
}

class TrendSeriesDto {
  final String metric;
  final List<double> values;
  final double? seasonAvg;
  const TrendSeriesDto({required this.metric, required this.values, required this.seasonAvg});

  factory TrendSeriesDto.fromJson(Map<String, dynamic> j) => TrendSeriesDto(
        metric: j['metric'] as String,
        values: ((j['values'] as List?) ?? const [])
            .map((v) => _asDouble(v) ?? 0.0)
            .toList(),
        seasonAvg: _asDouble(j['season_avg']),
      );
}

class RefereeBlockDto {
  final int id;
  final String name;
  final String? nationality;
  final String? photo;
  final RefereeVsTeamDto? vsHome;
  final RefereeVsTeamDto? vsAway;
  const RefereeBlockDto({
    required this.id, required this.name, this.nationality, this.photo,
    this.vsHome, this.vsAway,
  });

  factory RefereeBlockDto.fromJson(Map<String, dynamic> j) => RefereeBlockDto(
        id: j['id'] as int,
        name: j['name'] as String,
        nationality: j['nationality'] as String?,
        photo: j['photo'] as String?,
        vsHome: j['vs_home_team'] == null
            ? null
            : RefereeVsTeamDto.fromJson((j['vs_home_team'] as Map).cast<String, dynamic>()),
        vsAway: j['vs_away_team'] == null
            ? null
            : RefereeVsTeamDto.fromJson((j['vs_away_team'] as Map).cast<String, dynamic>()),
      );
}

class RefereeVsTeamDto {
  final int matches;
  final double? yellowCardsPg;
  final double? redCardsPg;
  final double? foulsPg;
  final int wins;
  final int draws;
  final int losses;
  const RefereeVsTeamDto({
    required this.matches,
    required this.yellowCardsPg,
    required this.redCardsPg,
    required this.foulsPg,
    required this.wins,
    required this.draws,
    required this.losses,
  });

  factory RefereeVsTeamDto.fromJson(Map<String, dynamic> j) => RefereeVsTeamDto(
        matches: (j['matches'] ?? 0) as int,
        yellowCardsPg: _asDouble(j['yellow_cards_pg']),
        redCardsPg: _asDouble(j['red_cards_pg']),
        foulsPg: _asDouble(j['fouls_pg']),
        wins: (j['wins'] ?? 0) as int,
        draws: (j['draws'] ?? 0) as int,
        losses: (j['losses'] ?? 0) as int,
      );
}

class InsightDto {
  final String rule;
  final int severity;
  final String headline;
  final String? metricKey;
  final double? metricValue;
  const InsightDto({
    required this.rule,
    required this.severity,
    required this.headline,
    this.metricKey,
    this.metricValue,
  });

  factory InsightDto.fromJson(Map<String, dynamic> j) => InsightDto(
        rule: j['rule'] as String,
        severity: (j['severity'] ?? 1) as int,
        headline: j['headline'] as String,
        metricKey: j['metric_key'] as String?,
        metricValue: _asDouble(j['metric_value']),
      );
}

class SplitsDto {
  final HitRatesDto? homeTeamAtHome;
  final HitRatesDto? awayTeamAway;
  const SplitsDto({this.homeTeamAtHome, this.awayTeamAway});

  factory SplitsDto.fromJson(Map<String, dynamic> j) {
    HitRatesDto? parse(dynamic v) =>
        v == null ? null : HitRatesDto.fromJson((v as Map).cast<String, dynamic>());
    return SplitsDto(
      homeTeamAtHome: parse(j['home_team_at_home']),
      awayTeamAway: parse(j['away_team_away']),
    );
  }
}

class MatchPreviewDto {
  final FixtureMetaDto fixture;
  final TeamBlockDto home;
  final TeamBlockDto away;
  final SplitsDto? splits;
  final HitRatesDto? homeSeasonHr;
  final HitRatesDto? awaySeasonHr;
  final RadarDto? radar;
  final List<TrendSeriesDto> trendsHome;
  final List<TrendSeriesDto> trendsAway;
  final RefereeBlockDto? referee;
  final List<InsightDto> insights;

  const MatchPreviewDto({
    required this.fixture,
    required this.home,
    required this.away,
    required this.splits,
    required this.homeSeasonHr,
    required this.awaySeasonHr,
    required this.radar,
    required this.trendsHome,
    required this.trendsAway,
    required this.referee,
    required this.insights,
  });

  factory MatchPreviewDto.fromJson(Map<String, dynamic> j) {
    final hr = j['hit_rates'] as Map?;
    HitRatesDto? parseHr(dynamic v) =>
        v == null ? null : HitRatesDto.fromJson((v as Map).cast<String, dynamic>());

    final trends = (j['trends'] as Map?)?.cast<String, dynamic>() ?? const {};
    List<TrendSeriesDto> parseTrends(dynamic v) =>
        (v as List? ?? const []).cast<Map<String, dynamic>>().map(TrendSeriesDto.fromJson).toList();

    return MatchPreviewDto(
      fixture: FixtureMetaDto.fromJson((j['fixture'] as Map).cast<String, dynamic>()),
      home: TeamBlockDto.fromJson((j['home'] as Map).cast<String, dynamic>()),
      away: TeamBlockDto.fromJson((j['away'] as Map).cast<String, dynamic>()),
      splits: j['splits'] == null
          ? null
          : SplitsDto.fromJson((j['splits'] as Map).cast<String, dynamic>()),
      homeSeasonHr: parseHr(hr?['home_season']),
      awaySeasonHr: parseHr(hr?['away_season']),
      radar: j['radar'] == null
          ? null
          : RadarDto.fromJson((j['radar'] as Map).cast<String, dynamic>()),
      trendsHome: parseTrends(trends['home']),
      trendsAway: parseTrends(trends['away']),
      referee: j['referee'] == null
          ? null
          : RefereeBlockDto.fromJson((j['referee'] as Map).cast<String, dynamic>()),
      insights: (j['insights'] as List? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(InsightDto.fromJson)
          .toList(),
    );
  }
}
