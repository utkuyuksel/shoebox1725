import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../data/match_preview_dto.dart';

class InsightsStrip extends StatelessWidget {
  final List<InsightDto> insights;
  const InsightsStrip({super.key, required this.insights});

  @override
  Widget build(BuildContext context) {
    if (insights.isEmpty) return const SizedBox.shrink();
    return SizedBox(
      height: 96,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: insights.length,
        separatorBuilder: (_, __) => const SizedBox(width: 10),
        itemBuilder: (c, i) => _InsightCard(insight: insights[i]),
      ),
    );
  }
}

class _InsightCard extends StatelessWidget {
  final InsightDto insight;
  const _InsightCard({required this.insight});

  Color get _accent {
    switch (insight.severity) {
      case 4:
      case 5:
        return ShoeboxColors.danger;
      case 3:
        return ShoeboxColors.warn;
      default:
        return ShoeboxColors.accent;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 260,
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border(left: BorderSide(color: _accent, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            children: [
              Icon(Icons.bolt_rounded, color: _accent, size: 14),
              const SizedBox(width: 6),
              Text(
                'INSIGHT',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: _accent, letterSpacing: 1.4, fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Flexible(
            child: Text(
              insight.headline,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: ShoeboxColors.textHigh,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
