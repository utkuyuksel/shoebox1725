class WatchlistFixtureDto {
  final int id;
  final int leagueId;
  final String leagueName;
  final String? leagueLogo;
  final String? leagueCountryCode;
  final DateTime kickoffAt;
  final String status;
  final int homeTeamId;
  final String homeTeamName;
  final String? homeTeamLogo;
  final int awayTeamId;
  final String awayTeamName;
  final String? awayTeamLogo;
  final int? homeGoals;
  final int? awayGoals;
  final DateTime addedAt;

  const WatchlistFixtureDto({
    required this.id,
    required this.leagueId,
    required this.leagueName,
    required this.leagueLogo,
    required this.leagueCountryCode,
    required this.kickoffAt,
    required this.status,
    required this.homeTeamId,
    required this.homeTeamName,
    required this.homeTeamLogo,
    required this.awayTeamId,
    required this.awayTeamName,
    required this.awayTeamLogo,
    required this.homeGoals,
    required this.awayGoals,
    required this.addedAt,
  });

  factory WatchlistFixtureDto.fromJson(Map<String, dynamic> j) {
    return WatchlistFixtureDto(
      id: j['id'] as int,
      leagueId: j['league_id'] as int,
      leagueName: (j['league_name'] as String?) ?? '',
      leagueLogo: j['league_logo'] as String?,
      leagueCountryCode: j['league_country_code'] as String?,
      kickoffAt: DateTime.parse(j['kickoff_at'] as String),
      status: j['status'] as String,
      homeTeamId: j['home_team_id'] as int,
      homeTeamName: (j['home_team_name'] as String?) ?? '',
      homeTeamLogo: j['home_team_logo'] as String?,
      awayTeamId: j['away_team_id'] as int,
      awayTeamName: (j['away_team_name'] as String?) ?? '',
      awayTeamLogo: j['away_team_logo'] as String?,
      homeGoals: j['home_goals'] as int?,
      awayGoals: j['away_goals'] as int?,
      addedAt: DateTime.parse(j['added_at'] as String),
    );
  }

  bool get isFinished => const {'FT', 'AET', 'PEN'}.contains(status);
  bool get isLive =>
      const {'1H', '2H', 'HT', 'ET', 'P', 'BT', 'LIVE'}.contains(status);
}
