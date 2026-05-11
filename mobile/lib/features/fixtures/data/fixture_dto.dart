class FixtureTeamDto {
  final int id;
  final String name;
  final String? logo;
  final int? goals;
  const FixtureTeamDto({required this.id, required this.name, this.logo, this.goals});

  factory FixtureTeamDto.fromJson(Map<String, dynamic> j) => FixtureTeamDto(
        id: j['id'] as int,
        name: (j['name'] ?? 'Unknown') as String,
        logo: j['logo'] as String?,
        goals: j['goals'] as int?,
      );
}

class FixtureDto {
  final int id;
  final DateTime kickoffAt;
  final String status;
  final String? round;
  final FixtureTeamDto home;
  final FixtureTeamDto away;

  const FixtureDto({
    required this.id,
    required this.kickoffAt,
    required this.status,
    required this.round,
    required this.home,
    required this.away,
  });

  bool get isUpcoming => status == 'NS' || status == 'TBD';
  bool get isLive => const {'1H', '2H', 'HT', 'ET', 'BT', 'P', 'LIVE'}.contains(status);
  bool get isFinished => const {'FT', 'AET', 'PEN'}.contains(status);

  String get statusLabel {
    return switch (status) {
      'NS' => 'Upcoming',
      'TBD' => 'TBD',
      'FT' => 'Final',
      'AET' => 'AET',
      'PEN' => 'Pens',
      '1H' => 'Live · 1H',
      '2H' => 'Live · 2H',
      'HT' => 'Half-time',
      'PST' => 'Postponed',
      'CANC' => 'Cancelled',
      _ => status,
    };
  }

  factory FixtureDto.fromJson(Map<String, dynamic> j) => FixtureDto(
        id: j['id'] as int,
        kickoffAt: DateTime.parse(j['kickoff_at'] as String),
        status: (j['status'] ?? 'NS') as String,
        round: j['round'] as String?,
        home: FixtureTeamDto.fromJson((j['home'] as Map).cast<String, dynamic>()),
        away: FixtureTeamDto.fromJson((j['away'] as Map).cast<String, dynamic>()),
      );
}

class FixturesPayload {
  final int leagueId;
  final int? season;
  final String? round;
  final List<FixtureDto> matches;
  const FixturesPayload({required this.leagueId, this.season, this.round, required this.matches});

  factory FixturesPayload.fromJson(Map<String, dynamic> j) => FixturesPayload(
        leagueId: j['league_id'] as int,
        season: j['season'] as int?,
        round: j['round'] as String?,
        matches: (j['matches'] as List? ?? [])
            .cast<Map<String, dynamic>>()
            .map(FixtureDto.fromJson)
            .toList(),
      );
}
