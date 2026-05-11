import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/match_preview_dto.dart';

/// Basketball season averages — different metrics than football. Grouped by
/// Scoring, Shooting (with made/att/% triples), Rebounds, Playmaking, Defence.
class BasketballAveragesCard extends StatelessWidget {
  final BasketballTeamStatsDto? home;
  final BasketballTeamStatsDto? away;
  final String homeLabel;
  final String awayLabel;

  const BasketballAveragesCard({
    super.key,
    required this.home,
    required this.away,
    required this.homeLabel,
    required this.awayLabel,
  });

  @override
  Widget build(BuildContext context) {
    if (home == null && away == null) return const SizedBox.shrink();

    final sections = <_Section>[
      _Section('Scoring', [
        _Row('Points',          home?.pointsPg,        away?.pointsPg),
        _Row('Points allowed',  home?.pointsAllowedPg, away?.pointsAllowedPg, lowerIsBetter: true),
      ]),
      _Section('Shooting', [
        _Row('FG %',  home?.fgPct,    away?.fgPct,    asPct: true),
        _Row('2P %',  home?.twoPct,   away?.twoPct,   asPct: true),
        _Row('3P %',  home?.threePct, away?.threePct, asPct: true),
        _Row('FT %',  home?.ftPct,    away?.ftPct,    asPct: true),
      ]),
      _Section('Rebounds', [
        _Row('Total',     home?.reboundsTotalPg, away?.reboundsTotalPg),
        _Row('Offensive', home?.reboundsOffPg,   away?.reboundsOffPg),
        _Row('Defensive', home?.reboundsDefPg,   away?.reboundsDefPg),
      ]),
      _Section('Playmaking', [
        _Row('Assists',   home?.assistsPg,    away?.assistsPg),
        _Row('Turnovers', home?.turnoversPg,  away?.turnoversPg, lowerIsBetter: true),
      ]),
      _Section('Defence', [
        _Row('Steals', home?.stealsPg, away?.stealsPg),
        _Row('Blocks', home?.blocksPg, away?.blocksPg),
      ]),
    ];

    return SectionCard(
      title: 'Season averages',
      trailing: Text(
        '${home?.played ?? 0} vs ${away?.played ?? 0} games',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
      ),
      child: Column(
        children: [
          _LegendRow(homeLabel: homeLabel, awayLabel: awayLabel),
          const SizedBox(height: 4),
          for (var i = 0; i < sections.length; i++) ...[
            _SectionHeader(sections[i].title),
            ...sections[i].rows.map((r) => _AveragesRow(row: r)),
            if (i < sections.length - 1) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _Section {
  final String title;
  final List<_Row> rows;
  _Section(this.title, this.rows);
}

class _Row {
  final String label;
  final double? home;
  final double? away;
  final bool lowerIsBetter;
  final bool asPct;
  _Row(this.label, this.home, this.away, {this.lowerIsBetter = false, this.asPct = false});
}

class _LegendRow extends StatelessWidget {
  final String homeLabel;
  final String awayLabel;
  const _LegendRow({required this.homeLabel, required this.awayLabel});
  @override
  Widget build(BuildContext context) {
    final txt = Theme.of(context).textTheme.labelSmall?.copyWith(
      color: ShoeboxColors.textMid, letterSpacing: 0.6, fontWeight: FontWeight.w700,
    );
    return Row(
      children: [
        _Dot(color: ShoeboxColors.home),
        const SizedBox(width: 6),
        Text(homeLabel, style: txt, maxLines: 1, overflow: TextOverflow.ellipsis),
        const Spacer(),
        Text(awayLabel, style: txt, maxLines: 1, overflow: TextOverflow.ellipsis),
        const SizedBox(width: 6),
        _Dot(color: ShoeboxColors.away),
      ],
    );
  }
}

class _Dot extends StatelessWidget {
  final Color color;
  const _Dot({required this.color});
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 8, height: 8,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String text;
  const _SectionHeader(this.text);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 12, bottom: 6),
      child: Text(
        text.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: ShoeboxColors.textLow, letterSpacing: 1.4, fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _AveragesRow extends StatelessWidget {
  final _Row row;
  const _AveragesRow({required this.row});

  String _fmt(double? v) {
    if (v == null) return '—';
    return row.asPct ? '${v.toStringAsFixed(1)}%' : v.toStringAsFixed(1);
  }

  @override
  Widget build(BuildContext context) {
    final h = row.home ?? 0;
    final a = row.away ?? 0;
    final total = h + a;
    final homeFrac = total == 0 ? 0.5 : h / total;
    final homeStronger = row.lowerIsBetter ? h < a : h > a;
    final awayStronger = row.lowerIsBetter ? a < h : a > h;
    final hasData = (row.home != null) || (row.away != null);

    final numStyle = Theme.of(context).textTheme.bodyMedium?.copyWith(
      fontWeight: FontWeight.w700,
      fontFeatures: const [FontFeature.tabularFigures()],
    );

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _fmt(row.home),
                style: numStyle?.copyWith(
                  color: !hasData
                      ? ShoeboxColors.textLow
                      : homeStronger
                          ? ShoeboxColors.home
                          : ShoeboxColors.textHigh,
                ),
              ),
              Text(
                row.label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: ShoeboxColors.textMid),
              ),
              Text(
                _fmt(row.away),
                style: numStyle?.copyWith(
                  color: !hasData
                      ? ShoeboxColors.textLow
                      : awayStronger
                          ? ShoeboxColors.away
                          : ShoeboxColors.textHigh,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          SizedBox(
            height: 4,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(2),
              child: Row(
                children: [
                  Expanded(
                    flex: (homeFrac * 1000).round().clamp(1, 999),
                    child: Container(color: ShoeboxColors.home),
                  ),
                  const SizedBox(width: 2),
                  Expanded(
                    flex: ((1 - homeFrac) * 1000).round().clamp(1, 999),
                    child: Container(color: ShoeboxColors.away),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
