import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/team_logo.dart';
import '../../data/match_preview_dto.dart';

class MatchHeader extends StatelessWidget {
  final MatchPreviewDto preview;
  const MatchHeader({super.key, required this.preview});

  @override
  Widget build(BuildContext context) {
    final kickoff = preview.fixture.kickoffAt.toLocal();
    final date = DateFormat('EEE, d MMM').format(kickoff);
    final time = DateFormat.Hm().format(kickoff);

    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter, end: Alignment.bottomCenter,
          colors: [Color(0xFF1A2540), ShoeboxColors.navy],
        ),
      ),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      child: Column(
        children: [
          Text(
            '$date · $time   ·   ${preview.fixture.round?.toUpperCase() ?? ''}',
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: ShoeboxColors.textMid,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Expanded(child: _TeamSide(team: preview.home, alignEnd: false)),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 8),
                child: Text(
                  'VS',
                  style: TextStyle(
                    color: ShoeboxColors.textLow,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 2,
                  ),
                ),
              ),
              Expanded(child: _TeamSide(team: preview.away, alignEnd: true)),
            ],
          ),
          if (preview.fixture.venue != null) ...[
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.place_outlined, size: 14, color: ShoeboxColors.textLow),
                const SizedBox(width: 4),
                Text(
                  preview.fixture.venue!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: ShoeboxColors.textLow),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _TeamSide extends StatelessWidget {
  final TeamBlockDto team;
  final bool alignEnd;
  const _TeamSide({required this.team, required this.alignEnd});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        TeamLogo(url: team.logo, size: 56),
        const SizedBox(height: 8),
        Text(
          team.name,
          textAlign: alignEnd ? TextAlign.end : TextAlign.start,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        if (team.stats != null && team.stats!.played > 0)
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text(
              '${team.stats!.played} matches · ${team.stats!.wins ?? 0}W-${team.stats!.draws ?? 0}D-${team.stats!.losses ?? 0}L',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ShoeboxColors.textMid),
            ),
          ),
      ],
    );
  }
}
