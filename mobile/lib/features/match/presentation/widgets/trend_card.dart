import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/match_preview_dto.dart';

/// Renders the "last N matches" trend for one team across multiple metrics.
/// Series are listed as small line charts, each with the season average drawn
/// as a horizontal dashed line. Bettor eye candy.
class TrendCard extends StatefulWidget {
  final String teamLabel;
  final List<TrendSeriesDto> series;
  final Color accent;
  const TrendCard({
    super.key,
    required this.teamLabel,
    required this.series,
    required this.accent,
  });

  @override
  State<TrendCard> createState() => _TrendCardState();
}

class _TrendCardState extends State<TrendCard> {
  late TrendSeriesDto _selected;

  @override
  void initState() {
    super.initState();
    _selected = widget.series.firstWhere(
      (s) => s.values.isNotEmpty,
      orElse: () => widget.series.first,
    );
  }

  static const _labels = {
    // Football metrics
    'goals_for':     'Goals for',
    'goals_against': 'Goals against',
    'corners':       'Corners',
    'yellow_cards':  'Yellow cards',
    'shots_total':   'Shots',
    // Basketball metrics
    'points':          'Points',
    'points_allowed':  'Points allowed',
    'rebounds_total':  'Rebounds',
    'assists':         'Assists',
    'three_made':      '3-pointers made',
  };

  @override
  Widget build(BuildContext context) {
    if (widget.series.isEmpty) return const SizedBox.shrink();

    return SectionCard(
      title: '${widget.teamLabel} · last ${_selected.values.length} matches',
      trailing: Container(
        width: 8, height: 8,
        decoration: BoxDecoration(color: widget.accent, shape: BoxShape.circle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 36,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: widget.series.length,
              separatorBuilder: (_, __) => const SizedBox(width: 6),
              itemBuilder: (c, i) {
                final s = widget.series[i];
                final selected = s.metric == _selected.metric;
                return ChoiceChip(
                  label: Text(_labels[s.metric] ?? s.metric),
                  selected: selected,
                  onSelected: (_) => setState(() => _selected = s),
                  selectedColor: widget.accent.withValues(alpha: 0.2),
                  side: BorderSide(color: selected ? widget.accent : ShoeboxColors.stroke),
                  labelStyle: TextStyle(
                    color: selected ? widget.accent : ShoeboxColors.textMid,
                    fontWeight: FontWeight.w600,
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 140,
            child: _TrendChart(series: _selected, accent: widget.accent),
          ),
          const SizedBox(height: 6),
          if (_selected.seasonAvg != null)
            Text(
              'Season avg: ${_selected.seasonAvg!.toStringAsFixed(1)} per game',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
            ),
        ],
      ),
    );
  }
}

class _TrendChart extends StatelessWidget {
  final TrendSeriesDto series;
  final Color accent;
  const _TrendChart({required this.series, required this.accent});

  @override
  Widget build(BuildContext context) {
    if (series.values.isEmpty) {
      return Center(
        child: Text(
          'No data for this metric.',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: ShoeboxColors.textMid),
        ),
      );
    }
    // Reverse so x=0 is the oldest match (left), x=N-1 is the most recent.
    final reversed = series.values.reversed.toList();
    final spots = [
      for (var i = 0; i < reversed.length; i++) FlSpot(i.toDouble(), reversed[i]),
    ];
    final maxY = [reversed.reduce((a, b) => a > b ? a : b), series.seasonAvg ?? 0].reduce((a, b) => a > b ? a : b) * 1.25 + 0.5;
    final minY = 0.0;
    final avg = series.seasonAvg;

    return LineChart(
      LineChartData(
        minY: minY,
        maxY: maxY,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (_) => const FlLine(color: ShoeboxColors.stroke, strokeWidth: 0.5),
        ),
        borderData: FlBorderData(show: false),
        titlesData: const FlTitlesData(
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: accent,
            barWidth: 2.5,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, p, bar, idx) => FlDotCirclePainter(
                radius: 3, color: accent, strokeColor: ShoeboxColors.navy, strokeWidth: 1.5,
              ),
            ),
            belowBarData: BarAreaData(show: true, color: accent.withValues(alpha: 0.10)),
          ),
        ],
        extraLinesData: avg == null
            ? const ExtraLinesData()
            : ExtraLinesData(horizontalLines: [
                HorizontalLine(
                  y: avg,
                  color: ShoeboxColors.textMid,
                  strokeWidth: 1,
                  dashArray: const [4, 4],
                  label: HorizontalLineLabel(
                    show: true,
                    alignment: Alignment.topRight,
                    style: const TextStyle(color: ShoeboxColors.textMid, fontSize: 10),
                    labelResolver: (_) => 'avg ${avg.toStringAsFixed(1)}',
                  ),
                ),
              ]),
      ),
    );
  }
}
