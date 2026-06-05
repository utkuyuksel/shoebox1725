import 'dart:ui' show FontFeature;

import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../../../l10n/generated/app_localizations.dart';
import '../../data/match_preview_dto.dart';

/// Historical meetings between the two teams. Sport-agnostic — scores are
/// goals (football) or points (basketball). The W/D/L summary is expressed
/// from the fixture's home/away perspective; per-meeting rows map each side
/// back to its short label via the team ids.
class H2HCard extends StatelessWidget {
  final H2HDto h2h;
  final int homeId;
  final int awayId;
  final String homeLabel;
  final String awayLabel;

  const H2HCard({
    super.key,
    required this.h2h,
    required this.homeId,
    required this.awayId,
    required this.homeLabel,
    required this.awayLabel,
  });

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return SectionCard(
      title: l.matchSectionH2H,
      trailing: Text(
        '${h2h.matches}',
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: ShoeboxColors.textMid,
              fontWeight: FontWeight.w700,
            ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SummaryBar(h2h: h2h, homeLabel: homeLabel, awayLabel: awayLabel),
          if (h2h.avgTotal != null) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                Text(
                  '${l.matchH2HAvgTotal}: ',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: ShoeboxColors.textMid,
                      ),
                ),
                Text(
                  h2h.avgTotal!.toStringAsFixed(1),
                  style: const TextStyle(
                    color: ShoeboxColors.textHigh,
                    fontWeight: FontWeight.w800,
                    fontFeatures: [FontFeature.tabularFigures()],
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 12),
          for (final m in h2h.meetings)
            _MeetingRow(
              meeting: m,
              homeId: homeId,
              awayId: awayId,
              homeLabel: homeLabel,
              awayLabel: awayLabel,
            ),
        ],
      ),
    );
  }
}

/// Three-segment bar: fixture-home wins · draws · fixture-away wins.
class _SummaryBar extends StatelessWidget {
  final H2HDto h2h;
  final String homeLabel;
  final String awayLabel;
  const _SummaryBar({required this.h2h, required this.homeLabel, required this.awayLabel});

  @override
  Widget build(BuildContext context) {
    final total = (h2h.homeWins + h2h.draws + h2h.awayWins).clamp(1, 1 << 30);
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: Text(homeLabel,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: ShoeboxColors.home,
                        fontWeight: FontWeight.w700,
                      )),
            ),
            Text('${h2h.homeWins}–${h2h.draws}–${h2h.awayWins}',
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: ShoeboxColors.textMid,
                      fontFeatures: const [FontFeature.tabularFigures()],
                    )),
            Expanded(
              child: Text(awayLabel,
                  textAlign: TextAlign.right,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: ShoeboxColors.away,
                        fontWeight: FontWeight.w700,
                      )),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: Row(
            children: [
              Expanded(flex: h2h.homeWins, child: Container(height: 6, color: ShoeboxColors.home)),
              Expanded(flex: h2h.draws, child: Container(height: 6, color: ShoeboxColors.textLow)),
              Expanded(flex: h2h.awayWins, child: Container(height: 6, color: ShoeboxColors.away)),
              // Keep the bar full-width even when one side has 0 wins.
              if (h2h.homeWins + h2h.draws + h2h.awayWins == 0)
                Expanded(flex: total, child: Container(height: 6, color: ShoeboxColors.surfaceAlt)),
            ],
          ),
        ),
      ],
    );
  }
}

class _MeetingRow extends StatelessWidget {
  final H2HMeetingDto meeting;
  final int homeId;
  final int awayId;
  final String homeLabel;
  final String awayLabel;
  const _MeetingRow({
    required this.meeting,
    required this.homeId,
    required this.awayId,
    required this.homeLabel,
    required this.awayLabel,
  });

  String _labelFor(int teamId) {
    if (teamId == homeId) return homeLabel;
    if (teamId == awayId) return awayLabel;
    return '?';
  }

  @override
  Widget build(BuildContext context) {
    final hg = meeting.homeGoals;
    final ag = meeting.awayGoals;
    final decided = hg != null && ag != null;
    final homeWon = decided && hg > ag;
    final awayWon = decided && ag > hg;

    TextStyle nameStyle(bool won) => Theme.of(context).textTheme.bodyMedium!.copyWith(
          color: won ? ShoeboxColors.textHigh : ShoeboxColors.textMid,
          fontWeight: won ? FontWeight.w700 : FontWeight.w500,
        );

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          SizedBox(
            width: 64,
            child: Text(
              meeting.date,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textLow),
            ),
          ),
          Expanded(
            child: Text(_labelFor(meeting.homeTeamId),
                textAlign: TextAlign.right,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: nameStyle(homeWon)),
          ),
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 8),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: ShoeboxColors.surfaceAlt,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              decided ? '$hg–$ag' : '—',
              style: const TextStyle(
                color: ShoeboxColors.textHigh,
                fontWeight: FontWeight.w800,
                fontFeatures: [FontFeature.tabularFigures()],
              ),
            ),
          ),
          Expanded(
            child: Text(_labelFor(meeting.awayTeamId),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: nameStyle(awayWon)),
          ),
        ],
      ),
    );
  }
}
