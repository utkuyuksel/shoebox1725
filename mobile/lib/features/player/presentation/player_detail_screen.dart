import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/section_card.dart';
import '../../../core/widgets/skeleton.dart';
import '../data/player_dto.dart';
import '../data/player_repository.dart';

class PlayerDetailScreen extends ConsumerWidget {
  final int playerId;
  final int leagueId;
  final int season;
  final String sport;
  final String? nameHint;
  const PlayerDetailScreen({
    super.key,
    required this.playerId,
    required this.leagueId,
    required this.season,
    required this.sport,
    this.nameHint,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final key = PlayerKey(
      playerId: playerId, leagueId: leagueId, season: season, sport: sport,
    );
    final player = ref.watch(playerProvider(key));

    return Scaffold(
      appBar: AppBar(title: Text(nameHint ?? 'Player')),
      body: AsyncView<PlayerPayload>(
        value: player,
        onRetry: () => ref.invalidate(playerProvider(key)),
        loadingBuilder: (_) => Skeleton(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              SkeletonCard.section(bodyHeight: 60),    // header
              const SizedBox(height: 14),
              SkeletonCard.section(bodyHeight: 70),    // highlights
              const SizedBox(height: 12),
              SkeletonCard.section(bodyHeight: 110),   // attacking
              const SizedBox(height: 12),
              SkeletonCard.section(bodyHeight: 110),   // passing
            ],
          ),
        ),
        data: (p) => _Body(payload: p),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final PlayerPayload payload;
  const _Body({required this.payload});

  @override
  Widget build(BuildContext context) {
    final p = payload.player;
    final s = payload.footballStats;
    final hasStats = s != null && s.appearances > 0;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      children: [
        _Header(player: p),
        const SizedBox(height: 16),
        if (!hasStats)
          _NoStats()
        else ...[
          _HighlightsRow(stats: s),
          const SizedBox(height: 12),
          _AttackingCard(stats: s),
          const SizedBox(height: 12),
          _PassingCard(stats: s),
          const SizedBox(height: 12),
          _DefenceCard(stats: s),
          const SizedBox(height: 12),
          _DisciplineCard(stats: s),
        ],
      ],
    );
  }
}

// ---------------- header

class _Header extends StatelessWidget {
  final PlayerProfileDto player;
  const _Header({required this.player});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 18),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: ShoeboxColors.stroke),
      ),
      child: Row(
        children: [
          Container(
            width: 72, height: 72,
            decoration: BoxDecoration(
              color: ShoeboxColors.surfaceAlt,
              borderRadius: BorderRadius.circular(36),
              image: player.photo == null
                  ? null
                  : DecorationImage(image: NetworkImage(player.photo!), fit: BoxFit.cover),
            ),
            child: player.photo == null
                ? const Icon(Icons.person, color: ShoeboxColors.textLow, size: 36)
                : null,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  player.name,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8, runSpacing: 6,
                  children: [
                    if (player.nationality != null) _MetaChip(text: player.nationality!),
                    if (player.heightCm != null) _MetaChip(text: '${player.heightCm} cm'),
                    if (player.weightKg != null) _MetaChip(text: '${player.weightKg} kg'),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  final String text;
  const _MetaChip({required this.text});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: ShoeboxColors.surfaceAlt,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: ShoeboxColors.textMid, fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

// ---------------- highlights row

class _HighlightsRow extends StatelessWidget {
  final FootballPlayerStatsDto stats;
  const _HighlightsRow({required this.stats});

  @override
  Widget build(BuildContext context) {
    final ratingStr = stats.rating == null ? '—' : stats.rating!.toStringAsFixed(1);
    return Row(
      children: [
        _HCard(label: 'RATING', value: ratingStr, color: ShoeboxColors.accent, emphasis: true),
        const SizedBox(width: 10),
        _HCard(label: 'MATCHES', value: '${stats.appearances}', color: ShoeboxColors.textHigh),
        const SizedBox(width: 10),
        _HCard(label: 'GOALS', value: '${stats.goals ?? 0}', color: ShoeboxColors.warn),
        const SizedBox(width: 10),
        _HCard(label: 'ASSISTS', value: '${stats.assists ?? 0}', color: ShoeboxColors.success),
      ],
    );
  }
}

class _HCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final bool emphasis;
  const _HCard({required this.label, required this.value, required this.color, this.emphasis = false});
  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        height: 78,
        decoration: BoxDecoration(
          color: ShoeboxColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: emphasis ? Border.all(color: color.withValues(alpha: 0.5), width: 1.5) : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              value,
              style: TextStyle(
                color: color,
                fontSize: 22,
                fontWeight: FontWeight.w900,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                color: ShoeboxColors.textLow, fontSize: 9,
                fontWeight: FontWeight.w800, letterSpacing: 0.8,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------- stat groups

String _fmtD(double? v) => v == null ? '—' : v.toStringAsFixed(1);
String _fmtPct(double? v) => v == null ? '—' : '${v.toStringAsFixed(0)}%';

class _AttackingCard extends StatelessWidget {
  final FootballPlayerStatsDto stats;
  const _AttackingCard({required this.stats});
  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'Attacking · per game',
      child: _Grid(items: [
        _Item('Shots',        _fmtD(stats.shotsPg)),
        _Item('On target',    _fmtD(stats.shotsOnPg)),
        _Item('Minutes',      _fmtD(stats.minutesPg)),
        _Item('Started',      '${stats.started}'),
      ]),
    );
  }
}

class _PassingCard extends StatelessWidget {
  final FootballPlayerStatsDto stats;
  const _PassingCard({required this.stats});
  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'Passing · per game',
      child: _Grid(items: [
        _Item('Total passes',  _fmtD(stats.passesPg)),
        _Item('Accurate',      _fmtD(stats.passesAccuratePg)),
        _Item('Accuracy',      _fmtPct(stats.passAccuracyPct)),
        _Item('Tackles',       _fmtD(stats.tacklesPg)),
      ]),
    );
  }
}

class _DefenceCard extends StatelessWidget {
  final FootballPlayerStatsDto stats;
  const _DefenceCard({required this.stats});
  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'Defence · per game',
      child: _Grid(items: [
        _Item('Tackles',       _fmtD(stats.tacklesPg)),
        _Item('Interceptions', _fmtD(stats.interceptionsPg)),
        _Item('Fouls',         _fmtD(stats.foulsPg)),
        _Item('Started',       '${stats.started}'),
      ]),
    );
  }
}

class _DisciplineCard extends StatelessWidget {
  final FootballPlayerStatsDto stats;
  const _DisciplineCard({required this.stats});
  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'Discipline · per game',
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _CardStat(color: ShoeboxColors.warn, label: 'Yellow / g', value: _fmtD(stats.yellowCardsPg)),
          Container(width: 1, height: 40, color: ShoeboxColors.stroke),
          _CardStat(color: ShoeboxColors.danger, label: 'Red / g', value: _fmtD(stats.redCardsPg)),
        ],
      ),
    );
  }
}

class _CardStat extends StatelessWidget {
  final Color color;
  final String label;
  final String value;
  const _CardStat({required this.color, required this.label, required this.value});
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(Icons.style, color: color, size: 24),
        const SizedBox(height: 6),
        Text(
          value,
          style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.w800,
              fontFeatures: const [FontFeature.tabularFigures()]),
        ),
        Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid)),
      ],
    );
  }
}

class _Item {
  final String label;
  final String value;
  _Item(this.label, this.value);
}

class _Grid extends StatelessWidget {
  final List<_Item> items;
  const _Grid({required this.items});
  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      childAspectRatio: 2.4,
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      children: items.map((it) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: ShoeboxColors.surfaceAlt,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              it.value,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w800,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
            const SizedBox(height: 2),
            Text(
              it.label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
            ),
          ],
        ),
      )).toList(),
    );
  }
}

class _NoStats extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Center(
        child: Text(
          'No season stats available for this player.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: ShoeboxColors.textMid),
        ),
      ),
    );
  }
}
