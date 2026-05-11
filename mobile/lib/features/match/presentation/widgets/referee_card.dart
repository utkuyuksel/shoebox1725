import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/match_preview_dto.dart';

class RefereeCard extends StatelessWidget {
  final RefereeBlockDto referee;
  final String homeLabel;
  final String awayLabel;
  const RefereeCard({
    super.key,
    required this.referee,
    required this.homeLabel,
    required this.awayLabel,
  });

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'Referee · history',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44, height: 44,
                decoration: BoxDecoration(
                  color: ShoeboxColors.surfaceAlt,
                  borderRadius: BorderRadius.circular(22),
                ),
                child: const Icon(Icons.sports, color: ShoeboxColors.textMid),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      referee.name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    if (referee.nationality != null)
                      Text(
                        referee.nationality!,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: ShoeboxColors.textMid,
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _TeamHistory(label: homeLabel, hist: referee.vsHome, accent: ShoeboxColors.home),
          const SizedBox(height: 10),
          _TeamHistory(label: awayLabel, hist: referee.vsAway, accent: ShoeboxColors.away),
        ],
      ),
    );
  }
}

class _TeamHistory extends StatelessWidget {
  final String label;
  final RefereeVsTeamDto? hist;
  final Color accent;
  const _TeamHistory({required this.label, required this.hist, required this.accent});

  @override
  Widget build(BuildContext context) {
    if (hist == null || hist!.matches == 0) {
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: ShoeboxColors.surfaceAlt,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Container(width: 8, height: 8, decoration: BoxDecoration(color: accent, shape: BoxShape.circle)),
            const SizedBox(width: 10),
            Expanded(child: Text(label, style: Theme.of(context).textTheme.bodyMedium)),
            Text('No history',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: ShoeboxColors.textLow)),
          ],
        ),
      );
    }

    final h = hist!;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: ShoeboxColors.surfaceAlt,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(width: 8, height: 8, decoration: BoxDecoration(color: accent, shape: BoxShape.circle)),
              const SizedBox(width: 10),
              Expanded(child: Text(label, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600))),
              Text(
                '${h.matches} matches',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _Stat(label: 'Yellow / g', value: h.yellowCardsPg, color: ShoeboxColors.warn),
              _Stat(label: 'Red / g', value: h.redCardsPg, color: ShoeboxColors.danger),
              _Stat(label: 'Fouls / g', value: h.foulsPg, color: ShoeboxColors.textHigh),
              _WDL(w: h.wins, d: h.draws, l: h.losses),
            ],
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label;
  final double? value;
  final Color color;
  const _Stat({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value == null ? '—' : value!.toStringAsFixed(2),
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w800,
              fontSize: 18,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
          Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid)),
        ],
      ),
    );
  }
}

class _WDL extends StatelessWidget {
  final int w, d, l;
  const _WDL({required this.w, required this.d, required this.l});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _Pill(text: '$w', color: ShoeboxColors.success),
              const SizedBox(width: 4),
              _Pill(text: '$d', color: ShoeboxColors.textMid),
              const SizedBox(width: 4),
              _Pill(text: '$l', color: ShoeboxColors.danger),
            ],
          ),
          Text('W-D-L', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid)),
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final String text;
  final Color color;
  const _Pill({required this.text, required this.color});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(text, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w700)),
    );
  }
}
