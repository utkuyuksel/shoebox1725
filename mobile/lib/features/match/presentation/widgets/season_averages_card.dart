import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../../../l10n/generated/app_localizations.dart';
import '../../data/match_preview_dto.dart';

/// The bread-and-butter comparison view: home vs away season averages.
/// Mirrors what the Telegram bot showed, but visual: each row has values on
/// either side and a horizontal bar split by the home/away ratio.
class SeasonAveragesCard extends StatelessWidget {
  final TeamSeasonStatsDto? home;
  final TeamSeasonStatsDto? away;
  final String homeLabel;
  final String awayLabel;

  const SeasonAveragesCard({
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
        _Row('Goals scored',          home?.goalsForPg,     away?.goalsForPg),
        _Row('Goals conceded',        home?.goalsAgainstPg, away?.goalsAgainstPg, lowerIsBetter: true),
        _Row('Expected goals (xG)',   home?.xgPg,           away?.xgPg),
      ]),
      _Section('Shooting', [
        _Row('Total shots',           home?.shotsTotalPg,   away?.shotsTotalPg),
        _Row('Shots on target',       home?.shotsOnPg,      away?.shotsOnPg),
      ]),
      _Section('Set pieces', [
        _Row('Corners',               home?.cornersPg,      away?.cornersPg),
      ]),
      _Section('Match flow', [
        _Row('Fouls',                 home?.foulsPg,        away?.foulsPg, lowerIsBetter: true),
        _Row('Offsides',              home?.offsidesPg,     away?.offsidesPg, lowerIsBetter: true),
      ]),
      _Section('Cards', [
        _Row('Yellow cards',          home?.yellowCardsPg,  away?.yellowCardsPg, lowerIsBetter: true),
        _Row('Red cards',             home?.redCardsPg,     away?.redCardsPg, lowerIsBetter: true),
      ]),
    ];

    return SectionCard(
      title: AppLocalizations.of(context).matchSectionSeasonAverages,
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
  _Row(this.label, this.home, this.away, {this.lowerIsBetter = false});
}

class _LegendRow extends StatelessWidget {
  final String homeLabel;
  final String awayLabel;
  const _LegendRow({required this.homeLabel, required this.awayLabel});

  @override
  Widget build(BuildContext context) {
    final txt = Theme.of(context).textTheme.labelSmall?.copyWith(
      color: ShoeboxColors.textMid,
      letterSpacing: 0.6,
      fontWeight: FontWeight.w700,
    );
    return Row(
      children: [
        _LegendDot(color: ShoeboxColors.home),
        const SizedBox(width: 6),
        Text(homeLabel, style: txt, maxLines: 1, overflow: TextOverflow.ellipsis),
        const Spacer(),
        Text(awayLabel, style: txt, maxLines: 1, overflow: TextOverflow.ellipsis),
        const SizedBox(width: 6),
        _LegendDot(color: ShoeboxColors.away),
      ],
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  const _LegendDot({required this.color});
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
          color: ShoeboxColors.textLow,
          letterSpacing: 1.4,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _AveragesRow extends StatelessWidget {
  final _Row row;
  const _AveragesRow({required this.row});

  String _fmt(double? v) => v == null ? '—' : v.toStringAsFixed(1);

  @override
  Widget build(BuildContext context) {
    final h = row.home ?? 0;
    final a = row.away ?? 0;
    final total = h + a;
    // Both 0 → 50/50; missing data → keep visual stable.
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
                  color: !hasData ? ShoeboxColors.textLow
                      : homeStronger ? ShoeboxColors.home : ShoeboxColors.textHigh,
                ),
              ),
              Text(
                row.label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: ShoeboxColors.textMid,
                ),
              ),
              Text(
                _fmt(row.away),
                style: numStyle?.copyWith(
                  color: !hasData ? ShoeboxColors.textLow
                      : awayStronger ? ShoeboxColors.away : ShoeboxColors.textHigh,
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
