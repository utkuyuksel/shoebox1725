import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/match_preview_dto.dart';

class HitRateCard extends StatelessWidget {
  final HitRatesDto? home;
  final HitRatesDto? away;
  final String homeLabel;
  final String awayLabel;
  const HitRateCard({
    super.key,
    required this.home,
    required this.away,
    required this.homeLabel,
    required this.awayLabel,
  });

  @override
  Widget build(BuildContext context) {
    if (home == null && away == null) return const SizedBox.shrink();

    final rows = <_HrRow>[
      _HrRow('Over 1.5 goals', home?.over15, away?.over15),
      _HrRow('Over 2.5 goals', home?.over25, away?.over25),
      _HrRow('Over 3.5 goals', home?.over35, away?.over35),
      _HrRow('BTTS', home?.btts, away?.btts),
      _HrRow('Corners > 8.5', home?.cornersOver85, away?.cornersOver85),
      _HrRow('Corners > 10.5', home?.cornersOver105, away?.cornersOver105),
      _HrRow('Cards > 3.5', home?.cardsOver35, away?.cardsOver35),
      _HrRow('Cards > 4.5', home?.cardsOver45, away?.cardsOver45),
    ];

    return SectionCard(
      title: 'Hit rate · season',
      trailing: Text(
        '${home?.matches ?? 0} vs ${away?.matches ?? 0} games',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
      ),
      child: Column(
        children: [
          _HeaderRow(homeLabel: homeLabel, awayLabel: awayLabel),
          const SizedBox(height: 8),
          ...rows.map((r) => _HrRowView(row: r)).toList(),
        ],
      ),
    );
  }
}

class _HrRow {
  final String label;
  final double? home;
  final double? away;
  _HrRow(this.label, this.home, this.away);
}

class _HeaderRow extends StatelessWidget {
  final String homeLabel;
  final String awayLabel;
  const _HeaderRow({required this.homeLabel, required this.awayLabel});

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme.labelSmall?.copyWith(
      color: ShoeboxColors.textMid, letterSpacing: 0.8,
    );
    return Row(
      children: [
        Expanded(flex: 2, child: Text('MARKET', style: style)),
        Expanded(child: Text(homeLabel, textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis, style: style)),
        Expanded(child: Text(awayLabel, textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis, style: style)),
      ],
    );
  }
}

class _HrRowView extends StatelessWidget {
  final _HrRow row;
  const _HrRowView({required this.row});

  Color _color(double? v) {
    if (v == null) return ShoeboxColors.textLow;
    if (v >= 65) return ShoeboxColors.success;
    if (v >= 45) return ShoeboxColors.warn;
    return ShoeboxColors.danger;
  }

  String _fmt(double? v) => v == null ? '—' : '${v.toStringAsFixed(0)}%';

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(
              row.label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: ShoeboxColors.textHigh,
              ),
            ),
          ),
          Expanded(child: _Cell(value: row.home, color: _color(row.home), text: _fmt(row.home))),
          Expanded(child: _Cell(value: row.away, color: _color(row.away), text: _fmt(row.away))),
        ],
      ),
    );
  }
}

class _Cell extends StatelessWidget {
  final double? value;
  final Color color;
  final String text;
  const _Cell({required this.value, required this.color, required this.text});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: value == null ? Colors.transparent : color.withValues(alpha: 0.13),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          text,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.w700,
            fontFeatures: const [FontFeature.tabularFigures()],
          ),
        ),
      ),
    );
  }
}
