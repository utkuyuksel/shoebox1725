import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/team_logo.dart';
import '../../data/league_dto.dart';

class PopularLeagueCard extends StatelessWidget {
  final LeagueDto league;
  final VoidCallback onTap;
  const PopularLeagueCard({super.key, required this.league, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 144,
        margin: const EdgeInsets.only(right: 12),
        decoration: BoxDecoration(
          color: ShoeboxColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: ShoeboxColors.stroke),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TeamLogo(url: league.logo, size: 44),
            const SizedBox(height: 12),
            Text(
              league.name,
              maxLines: 2,
              textAlign: TextAlign.center,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              (league.country ?? '').toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: ShoeboxColors.textMid, letterSpacing: 0.8,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
