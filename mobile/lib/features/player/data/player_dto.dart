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

class PlayerProfileDto {
  final int id;
  final String name;
  final String? photo;
  final String? nationality;
  final String? birthDate;
  final int? heightCm;
  final int? weightKg;
  const PlayerProfileDto({
    required this.id,
    required this.name,
    required this.photo,
    required this.nationality,
    required this.birthDate,
    required this.heightCm,
    required this.weightKg,
  });

  factory PlayerProfileDto.fromJson(Map<String, dynamic> j) => PlayerProfileDto(
        id: j['id'] as int,
        name: (j['name'] ?? 'Unknown') as String,
        photo: j['photo'] as String?,
        nationality: j['nationality'] as String?,
        birthDate: j['birth_date'] as String?,
        heightCm: j['height_cm'] as int?,
        weightKg: j['weight_kg'] as int?,
      );
}

class FootballPlayerStatsDto {
  final int appearances;
  final int started;
  final double? minutesPg;
  final double? rating;
  final int? goals;
  final int? assists;
  final double? shotsPg;
  final double? shotsOnPg;
  final double? passesPg;
  final double? passesAccuratePg;
  final double? passAccuracyPct;
  final double? tacklesPg;
  final double? interceptionsPg;
  final double? foulsPg;
  final double? yellowCardsPg;
  final double? redCardsPg;

  const FootballPlayerStatsDto({
    required this.appearances,
    required this.started,
    required this.minutesPg,
    required this.rating,
    required this.goals,
    required this.assists,
    required this.shotsPg,
    required this.shotsOnPg,
    required this.passesPg,
    required this.passesAccuratePg,
    required this.passAccuracyPct,
    required this.tacklesPg,
    required this.interceptionsPg,
    required this.foulsPg,
    required this.yellowCardsPg,
    required this.redCardsPg,
  });

  factory FootballPlayerStatsDto.fromJson(Map<String, dynamic> j) =>
      FootballPlayerStatsDto(
        appearances: _asInt(j['appearances']) ?? 0,
        started: _asInt(j['started']) ?? 0,
        minutesPg: _asDouble(j['minutes_pg']),
        rating: _asDouble(j['rating']),
        goals: _asInt(j['goals']),
        assists: _asInt(j['assists']),
        shotsPg: _asDouble(j['shots_pg']),
        shotsOnPg: _asDouble(j['shots_on_pg']),
        passesPg: _asDouble(j['passes_pg']),
        passesAccuratePg: _asDouble(j['passes_accurate_pg']),
        passAccuracyPct: _asDouble(j['pass_accuracy_pct']),
        tacklesPg: _asDouble(j['tackles_pg']),
        interceptionsPg: _asDouble(j['interceptions_pg']),
        foulsPg: _asDouble(j['fouls_pg']),
        yellowCardsPg: _asDouble(j['yellow_cards_pg']),
        redCardsPg: _asDouble(j['red_cards_pg']),
      );
}

class PlayerPayload {
  final PlayerProfileDto player;
  final FootballPlayerStatsDto? footballStats;
  const PlayerPayload({required this.player, required this.footballStats});

  factory PlayerPayload.fromJson(Map<String, dynamic> j) => PlayerPayload(
        player: PlayerProfileDto.fromJson((j['player'] as Map).cast<String, dynamic>()),
        footballStats: j['stats'] == null
            ? null
            : FootballPlayerStatsDto.fromJson((j['stats'] as Map).cast<String, dynamic>()),
      );
}
