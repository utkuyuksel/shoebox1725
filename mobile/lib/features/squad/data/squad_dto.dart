/// Mirrors /v1/teams/{teamId}/squad
class SquadPlayerDto {
  final int id;
  final String name;
  final String? photo;
  final String? nationality;
  final int? number;
  final String? position;     // 'G' | 'D' | 'M' | 'F'

  const SquadPlayerDto({
    required this.id,
    required this.name,
    required this.photo,
    required this.nationality,
    required this.number,
    required this.position,
  });

  factory SquadPlayerDto.fromJson(Map<String, dynamic> j) => SquadPlayerDto(
        id: j['id'] as int,
        name: (j['name'] ?? 'Unknown') as String,
        photo: j['photo'] as String?,
        nationality: j['nationality'] as String?,
        number: j['number'] as int?,
        position: j['position'] as String?,
      );
}

class SquadPayload {
  final List<SquadPlayerDto> players;
  const SquadPayload({required this.players});

  factory SquadPayload.fromJson(Map<String, dynamic> j) => SquadPayload(
        players: (j['squad'] as List? ?? const [])
            .cast<Map<String, dynamic>>()
            .map(SquadPlayerDto.fromJson)
            .toList(),
      );
}
