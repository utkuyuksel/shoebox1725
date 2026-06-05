import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/team_logo.dart';
import '../../../l10n/generated/app_localizations.dart';
import '../data/standings_dto.dart';
import '../data/standings_repository.dart';

class StandingsScreen extends ConsumerWidget {
  final int leagueId;
  final String leagueName;
  const StandingsScreen({super.key, required this.leagueId, required this.leagueName});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final standings = ref.watch(standingsProvider(leagueId));
    return Scaffold(
      appBar: AppBar(title: Text(leagueName)),
      body: RefreshIndicator(
        color: ShoeboxColors.accent,
        backgroundColor: ShoeboxColors.surface,
        onRefresh: () async => ref.invalidate(standingsProvider(leagueId)),
        child: AsyncView<StandingsDto>(
          value: standings,
          onRetry: () => ref.invalidate(standingsProvider(leagueId)),
          isEmpty: (s) => s.rows.isEmpty,
          emptyMessage: AppLocalizations.of(context).standingsEmpty,
          emptyIcon: Icons.table_chart_outlined,
          data: (s) => _Table(standings: s, leagueId: leagueId),
        ),
      ),
    );
  }
}

class _Table extends StatelessWidget {
  final StandingsDto standings;
  final int leagueId;
  const _Table({required this.standings, required this.leagueId});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final bball = standings.isBasketball;

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
      // +1 header row
      itemCount: standings.rows.length + 1,
      itemBuilder: (c, i) {
        if (i == 0) return _HeaderRow(bball: bball, l: l);
        final row = standings.rows[i - 1];
        return _StandingRow(
          row: row,
          bball: bball,
          leagueId: leagueId,
          season: standings.season ?? 0,
        );
      },
    );
  }
}

class _HeaderRow extends StatelessWidget {
  final bool bball;
  final AppLocalizations l;
  const _HeaderRow({required this.bball, required this.l});

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme.labelSmall?.copyWith(
          color: ShoeboxColors.textLow,
          fontWeight: FontWeight.w700,
        );
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 6, 8, 10),
      child: Row(
        children: [
          SizedBox(width: 24, child: Text('#', style: style)),
          const SizedBox(width: 8),
          Expanded(child: Text(l.standingsTeam, style: style)),
          _cell(l.standingsPlayedShort, style),
          if (bball)
            _cell(l.standingsWinPctShort, style, width: 44)
          else
            _cell(l.standingsGoalDiffShort, style),
          _cell(bball ? l.standingsWinLossShort : l.standingsPointsShort, style,
              width: 40),
          SizedBox(width: 96, child: Text(l.standingsForm, style: style, textAlign: TextAlign.right)),
        ],
      ),
    );
  }

  Widget _cell(String t, TextStyle? style, {double width = 32}) =>
      SizedBox(width: width, child: Text(t, style: style, textAlign: TextAlign.center));
}

class _StandingRow extends StatelessWidget {
  final StandingRowDto row;
  final bool bball;
  final int leagueId;
  final int season;
  const _StandingRow({
    required this.row,
    required this.bball,
    required this.leagueId,
    required this.season,
  });

  @override
  Widget build(BuildContext context) {
    final label = row.shortName ?? row.name;
    final num = TextStyle(
      color: ShoeboxColors.textHigh,
      fontWeight: FontWeight.w700,
      fontSize: 13,
      fontFeatures: const [FontFeature.tabularFigures()],
    );
    final muted = num.copyWith(color: ShoeboxColors.textMid, fontWeight: FontWeight.w500);

    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: () => context.push(
        '/team/${row.teamId}/squad'
        '?league=$leagueId&season=$season'
        '&name=${Uri.encodeQueryComponent(row.name)}',
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
        child: Row(
          children: [
            SizedBox(
              width: 24,
              child: Text('${row.rank}',
                  style: num.copyWith(color: ShoeboxColors.textMid)),
            ),
            const SizedBox(width: 8),
            TeamLogo(url: row.logo, size: 22),
            const SizedBox(width: 8),
            Expanded(
              child: Text(label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      )),
            ),
            SizedBox(width: 32, child: Text('${row.played}', style: muted, textAlign: TextAlign.center)),
            if (bball)
              SizedBox(
                width: 44,
                child: Text(row.winPct == null ? '—' : row.winPct!.toStringAsFixed(3).substring(1),
                    style: muted, textAlign: TextAlign.center),
              )
            else
              SizedBox(
                width: 32,
                child: Text(_signed(row.diff), style: muted, textAlign: TextAlign.center),
              ),
            SizedBox(
              width: 40,
              child: Text(
                bball ? '${row.wins}-${row.losses}' : '${row.points ?? 0}',
                style: num,
                textAlign: TextAlign.center,
              ),
            ),
            SizedBox(
              width: 96,
              child: _FormStrip(form: row.form),
            ),
          ],
        ),
      ),
    );
  }

  String _signed(int v) => v > 0 ? '+$v' : '$v';
}

/// Last-N results as small colored chips, most recent on the right.
class _FormStrip extends StatelessWidget {
  final List<String> form;
  const _FormStrip({required this.form});

  Color _color(String r) {
    switch (r) {
      case 'W':
        return ShoeboxColors.success;
      case 'L':
        return ShoeboxColors.danger;
      default:
        return ShoeboxColors.textLow;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        for (final r in form)
          Container(
            margin: const EdgeInsets.only(left: 3),
            width: 15,
            height: 15,
            decoration: BoxDecoration(
              color: _color(r).withValues(alpha: 0.18),
              borderRadius: BorderRadius.circular(4),
            ),
            alignment: Alignment.center,
            child: Text(
              r,
              style: TextStyle(
                color: _color(r),
                fontSize: 9,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
      ],
    );
  }
}
