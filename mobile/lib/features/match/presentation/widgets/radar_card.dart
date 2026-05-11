import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/match_preview_dto.dart';

class RadarCard extends StatelessWidget {
  final RadarDto radar;
  final String homeLabel;
  final String awayLabel;
  const RadarCard({
    super.key,
    required this.radar,
    required this.homeLabel,
    required this.awayLabel,
  });

  /// Human-readable axis labels. Covers both football and basketball axes
  /// so the same widget renders either radar payload.
  static const _labels = {
    // Football
    'goals_for_pg':      'Goals',
    'goals_against_pg':  'Defence',   // inverted on backend
    'shots_total_pg':    'Shots',
    'shots_on_pg':       'On target',
    'corners_pg':        'Corners',
    'yellow_cards_pg':   'Discipline', // inverted
    'fouls_pg':          'Clean',      // inverted
    'xg_pg':             'xG',
    // Basketball
    'points_pg':         'Scoring',
    'points_allowed_pg': 'Defence',    // inverted
    'fg_pct':            'FG %',
    'three_pct':         '3P %',
    'rebounds_total_pg': 'Rebounds',
    'assists_pg':        'Assists',
    'steals_pg':         'Steals',
    'turnovers_pg':      'Low TO',     // inverted
  };

  @override
  Widget build(BuildContext context) {
    if (radar.axes.isEmpty) return const SizedBox.shrink();

    return SectionCard(
      title: 'Form fingerprint',
      trailing: Text(
        '× league avg',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
      ),
      child: Column(
        children: [
          AspectRatio(
            aspectRatio: 1,
            child: RadarChart(
              RadarChartData(
                radarShape: RadarShape.polygon,
                radarBorderData: const BorderSide(color: ShoeboxColors.stroke, width: 1),
                radarBackgroundColor: Colors.transparent,
                gridBorderData: const BorderSide(color: ShoeboxColors.stroke, width: 1),
                tickBorderData: const BorderSide(color: ShoeboxColors.stroke, width: 0.5),
                ticksTextStyle: const TextStyle(color: Colors.transparent, fontSize: 0),
                titleTextStyle: const TextStyle(
                  color: ShoeboxColors.textMid, fontSize: 11, fontWeight: FontWeight.w600,
                ),
                getTitle: (i, _) => RadarChartTitle(text: _labels[radar.axes[i]] ?? radar.axes[i]),
                tickCount: 4,
                titlePositionPercentageOffset: 0.15,
                dataSets: [
                  RadarDataSet(
                    fillColor: ShoeboxColors.home.withValues(alpha: 0.18),
                    borderColor: ShoeboxColors.home,
                    borderWidth: 2,
                    entryRadius: 3,
                    dataEntries: radar.home.map((v) => RadarEntry(value: v ?? 0)).toList(),
                  ),
                  RadarDataSet(
                    fillColor: ShoeboxColors.away.withValues(alpha: 0.18),
                    borderColor: ShoeboxColors.away,
                    borderWidth: 2,
                    entryRadius: 3,
                    dataEntries: radar.away.map((v) => RadarEntry(value: v ?? 0)).toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _LegendDot(color: ShoeboxColors.home, label: homeLabel),
              const SizedBox(width: 24),
              _LegendDot(color: ShoeboxColors.away, label: awayLabel),
            ],
          ),
        ],
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}
