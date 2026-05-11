import 'package:flutter/material.dart';

import '../../../../app/theme.dart';
import '../../../../core/widgets/team_logo.dart';
import '../../data/league_dto.dart';

class CountryTile extends StatelessWidget {
  final String country;
  final String? countryCode;
  final List<LeagueDto> leagues;
  final void Function(LeagueDto) onLeagueTap;

  const CountryTile({
    super.key,
    required this.country,
    required this.countryCode,
    required this.leagues,
    required this.onLeagueTap,
  });

  String _flagEmoji(String? code) {
    if (code == null || code.length != 2) return '';
    final base = 0x1F1E6;
    final upper = code.toUpperCase();
    return String.fromCharCode(base + upper.codeUnitAt(0) - 65) +
        String.fromCharCode(base + upper.codeUnitAt(1) - 65);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(14),
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 16),
        childrenPadding: const EdgeInsets.only(bottom: 8),
        shape: const Border(),
        collapsedShape: const Border(),
        leading: SizedBox(
          width: 28,
          child: Center(
            child: Text(
              _flagEmoji(countryCode),
              style: const TextStyle(fontSize: 20),
            ),
          ),
        ),
        title: Text(country, style: Theme.of(context).textTheme.bodyLarge?.copyWith(
          fontWeight: FontWeight.w600,
        )),
        subtitle: Text(
          '${leagues.length} competition${leagues.length == 1 ? '' : 's'}',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: ShoeboxColors.textMid),
        ),
        children: leagues
            .map((l) => ListTile(
                  onTap: () => onLeagueTap(l),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                  leading: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: TeamLogo(url: l.logo, size: 22),
                  ),
                  title: Text(l.name),
                  trailing: const Icon(Icons.chevron_right_rounded,
                      color: ShoeboxColors.textLow),
                ))
            .toList(),
      ),
    );
  }
}
