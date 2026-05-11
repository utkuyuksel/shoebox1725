import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/skeleton.dart';
import '../../../core/widgets/team_logo.dart';
import '../../watchlist/presentation/watchlist_star_button.dart';
import '../data/fixture_dto.dart';
import '../data/fixtures_repository.dart';

class FixturesScreen extends ConsumerWidget {
  final int leagueId;
  final String leagueName;
  const FixturesScreen({super.key, required this.leagueId, required this.leagueName});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fixtures = ref.watch(fixturesProvider(leagueId));
    return Scaffold(
      appBar: AppBar(title: Text(leagueName)),
      body: RefreshIndicator(
        color: ShoeboxColors.accent,
        backgroundColor: ShoeboxColors.surface,
        onRefresh: () async => ref.invalidate(fixturesProvider(leagueId)),
        child: AsyncView<FixturesPayload>(
          value: fixtures,
          onRetry: () => ref.invalidate(fixturesProvider(leagueId)),
          isEmpty: (p) => p.matches.isEmpty,
          emptyMessage: 'No upcoming matches for this round yet.',
          emptyIcon: Icons.calendar_today_outlined,
          loadingBuilder: (_) => SkeletonList(
            itemCount: 5,
            builder: () => SkeletonCard.fixture(),
          ),
          data: (p) => _FixturesList(payload: p, leagueId: leagueId),
        ),
      ),
    );
  }
}

class _FixturesList extends StatelessWidget {
  final FixturesPayload payload;
  final int leagueId;
  const _FixturesList({required this.payload, required this.leagueId});

  @override
  Widget build(BuildContext context) {
    final dayFmt = DateFormat.MMMd();
    final timeFmt = DateFormat.Hm();
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      itemCount: payload.matches.length + 1,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (c, i) {
        if (i == 0) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              payload.round?.toUpperCase() ?? 'CURRENT ROUND',
              style: Theme.of(c).textTheme.labelMedium?.copyWith(
                color: ShoeboxColors.textMid,
                letterSpacing: 1.5,
                fontWeight: FontWeight.w700,
              ),
            ),
          );
        }
        final m = payload.matches[i - 1];
        return _FixtureCard(
          match: m,
          dayFmt: dayFmt,
          timeFmt: timeFmt,
          onTap: m.isUpcoming
              ? () => context.push('/match/${m.id}', extra: m)
              : null,
        );
      },
    );
  }
}

class _FixtureCard extends StatelessWidget {
  final FixtureDto match;
  final DateFormat dayFmt;
  final DateFormat timeFmt;
  final VoidCallback? onTap;
  const _FixtureCard({
    required this.match,
    required this.dayFmt,
    required this.timeFmt,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isClickable = onTap != null;
    final centreText = match.isUpcoming
        ? timeFmt.format(match.kickoffAt.toLocal())
        : (match.home.goals == null || match.away.goals == null)
            ? '—'
            : '${match.home.goals} : ${match.away.goals}';

    return Opacity(
      opacity: isClickable ? 1.0 : 0.55,
      child: Material(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          onTap: onTap == null
              ? null
              : () {
                  HapticFeedback.lightImpact();
                  onTap!();
                },
          borderRadius: BorderRadius.circular(14),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      dayFmt.format(match.kickoffAt.toLocal()),
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: ShoeboxColors.textLow,
                        letterSpacing: 0.6,
                      ),
                    ),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _StatusBadge(match: match),
                        const SizedBox(width: 6),
                        WatchlistStarButton(fixtureId: match.id, size: 18),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(child: _TeamSide(name: match.home.name, logo: match.home.logo)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      child: Text(
                        centreText,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                          color: match.isUpcoming
                              ? ShoeboxColors.accent
                              : ShoeboxColors.textHigh,
                          fontFeatures: const [FontFeature.tabularFigures()],
                        ),
                      ),
                    ),
                    Expanded(child: _TeamSide(name: match.away.name, logo: match.away.logo, rightAligned: true)),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TeamSide extends StatelessWidget {
  final String name;
  final String? logo;
  final bool rightAligned;
  const _TeamSide({required this.name, required this.logo, this.rightAligned = false});

  @override
  Widget build(BuildContext context) {
    final children = [
      TeamLogo(url: logo, size: 38),
      const SizedBox(width: 10),
      Flexible(
        child: Text(
          name,
          textAlign: rightAligned ? TextAlign.right : TextAlign.left,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    ];
    return Row(
      mainAxisAlignment:
          rightAligned ? MainAxisAlignment.end : MainAxisAlignment.start,
      children: rightAligned ? children.reversed.toList() : children,
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final FixtureDto match;
  const _StatusBadge({required this.match});

  @override
  Widget build(BuildContext context) {
    final Color bg;
    final Color fg;
    if (match.isLive) {
      bg = ShoeboxColors.danger.withValues(alpha: 0.15);
      fg = ShoeboxColors.danger;
    } else if (match.isFinished) {
      bg = ShoeboxColors.stroke;
      fg = ShoeboxColors.textMid;
    } else {
      bg = ShoeboxColors.accentSoft;
      fg = ShoeboxColors.accent;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        match.statusLabel.toUpperCase(),
        style: TextStyle(
          color: fg,
          fontSize: 10,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.8,
        ),
      ),
    );
  }
}
