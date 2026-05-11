import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/section_card.dart';
import '../../../core/widgets/skeleton.dart';
import '../data/referee_dto.dart';
import '../data/referee_repository.dart';

class RefereeProfileScreen extends ConsumerWidget {
  final int refereeId;
  final int season;
  final String? nameHint;
  const RefereeProfileScreen({
    super.key,
    required this.refereeId,
    required this.season,
    this.nameHint,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final key = RefereeProfileKey(refereeId: refereeId, season: season);
    final profile = ref.watch(refereeProfileProvider(key));

    return Scaffold(
      appBar: AppBar(title: Text(nameHint ?? 'Referee')),
      body: AsyncView<RefereeProfilePayload>(
        value: profile,
        onRetry: () => ref.invalidate(refereeProfileProvider(key)),
        loadingBuilder: (_) => Skeleton(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              SkeletonCard.section(bodyHeight: 70),    // header
              const SizedBox(height: 14),
              SkeletonCard.section(bodyHeight: 90),    // league season card
              const SizedBox(height: 12),
              SkeletonCard.section(bodyHeight: 240),   // last matches
            ],
          ),
        ),
        data: (p) => _Body(payload: p, season: season),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final RefereeProfilePayload payload;
  final int season;
  const _Body({required this.payload, required this.season});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      children: [
        _Header(ref: payload.referee, season: season),
        const SizedBox(height: 14),
        if (payload.seasonStats.isEmpty)
          _NoData(text: 'No season stats yet for this referee.')
        else
          ...payload.seasonStats.map((s) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _SeasonCard(stats: s),
              )),
        const SizedBox(height: 4),
        if (payload.lastMatches.isEmpty)
          _NoData(text: 'No recent matches in our database.')
        else
          _LastMatchesCard(matches: payload.lastMatches),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  final RefereeProfileDto ref;
  final int season;
  const _Header({required this.ref, required this.season});

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
            width: 60, height: 60,
            decoration: BoxDecoration(
              color: ShoeboxColors.surfaceAlt,
              borderRadius: BorderRadius.circular(30),
            ),
            child: const Icon(Icons.sports, color: ShoeboxColors.textMid, size: 30),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  ref.name,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  children: [
                    if (ref.nationality != null) _MetaChip(text: ref.nationality!),
                    _MetaChip(text: 'Season $season'),
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

String _fmtD(double? v) => v == null ? '—' : v.toStringAsFixed(2);
String _fmtPct(double? v) => v == null ? '—' : '${v.toStringAsFixed(0)}%';

class _SeasonCard extends StatelessWidget {
  final RefereeSeasonStatsDto stats;
  const _SeasonCard({required this.stats});

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'League ${stats.leagueId} · per game',
      trailing: Text(
        '${stats.matches} matches',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
      ),
      child: Row(
        children: [
          _Stat(label: 'Yellow', value: _fmtD(stats.yellowCardsPg), color: ShoeboxColors.warn),
          _Stat(label: 'Red',    value: _fmtD(stats.redCardsPg),    color: ShoeboxColors.danger),
          _Stat(label: 'Fouls',  value: _fmtD(stats.foulsPg),       color: ShoeboxColors.textHigh),
          _Stat(label: 'Pens',   value: _fmtD(stats.penaltiesPg),   color: ShoeboxColors.accent),
          _Stat(label: 'Home W', value: _fmtPct(stats.homeWinPct),  color: ShoeboxColors.success),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _Stat({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w800,
              fontSize: 16,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
          Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid)),
        ],
      ),
    );
  }
}

class _LastMatchesCard extends StatelessWidget {
  final List<RefereeLastMatchDto> matches;
  const _LastMatchesCard({required this.matches});

  @override
  Widget build(BuildContext context) {
    final dateFmt = DateFormat('d MMM yyyy');
    return SectionCard(
      title: 'Last ${matches.length} matches',
      child: Column(
        children: [
          for (var i = 0; i < matches.length; i++) ...[
            _MatchRow(match: matches[i], dateFmt: dateFmt),
            if (i < matches.length - 1)
              const Divider(height: 18, color: ShoeboxColors.stroke),
          ],
        ],
      ),
    );
  }
}

class _MatchRow extends StatelessWidget {
  final RefereeLastMatchDto match;
  final DateFormat dateFmt;
  const _MatchRow({required this.match, required this.dateFmt});

  @override
  Widget build(BuildContext context) {
    final score = (match.homeGoals == null || match.awayGoals == null)
        ? '—'
        : '${match.homeGoals} : ${match.awayGoals}';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                match.homeName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Text(
                score,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: ShoeboxColors.textHigh,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            ),
            Expanded(
              child: Text(
                match.awayName,
                textAlign: TextAlign.right,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Row(
          children: [
            Text(
              dateFmt.format(match.kickoffAt.toLocal()),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textLow),
            ),
            const Spacer(),
            _CardPill(count: match.yellowCards, color: ShoeboxColors.warn, icon: '🟨'),
            const SizedBox(width: 8),
            _CardPill(count: match.redCards, color: ShoeboxColors.danger, icon: '🟥'),
          ],
        ),
      ],
    );
  }
}

class _CardPill extends StatelessWidget {
  final int count;
  final Color color;
  final String icon;
  const _CardPill({required this.count, required this.color, required this.icon});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        '$icon $count',
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w700,
          fontFeatures: const [FontFeature.tabularFigures()],
        ),
      ),
    );
  }
}

class _NoData extends StatelessWidget {
  final String text;
  const _NoData({required this.text});
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Center(
        child: Text(
          text,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: ShoeboxColors.textMid),
        ),
      ),
    );
  }
}
