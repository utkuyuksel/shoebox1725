import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/skeleton.dart';
import '../../fixtures/data/fixture_dto.dart';
import '../../paywall/presentation/widgets/premium_gate.dart';
import '../../watchlist/presentation/watchlist_star_button.dart';
import '../data/match_preview_dto.dart';
import '../data/match_repository.dart';
import 'widgets/basketball_averages_card.dart';
import 'widgets/hit_rate_card.dart';
import 'widgets/insights_strip.dart';
import 'widgets/match_header.dart';
import 'widgets/radar_card.dart';
import 'widgets/referee_card.dart';
import 'widgets/season_averages_card.dart';
import 'widgets/trend_card.dart';

class MatchPreviewScreen extends ConsumerWidget {
  final int fixtureId;
  final FixtureDto? hint;
  const MatchPreviewScreen({super.key, required this.fixtureId, this.hint});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preview = ref.watch(matchPreviewProvider(fixtureId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Match preview'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 6),
            child: Center(
              child: WatchlistStarButton(fixtureId: fixtureId, size: 24),
            ),
          ),
        ],
      ),
      body: AsyncView<MatchPreviewDto>(
        value: preview,
        onRetry: () => ref.invalidate(matchPreviewProvider(fixtureId)),
        loadingBuilder: (_) => Skeleton(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 24, 16, 32),
            children: [
              SkeletonCard.section(bodyHeight: 100),       // header placeholder
              const SizedBox(height: 16),
              SkeletonCard.section(bodyHeight: 60),        // squad buttons
              const SizedBox(height: 12),
              SkeletonCard.section(bodyHeight: 320),       // season averages
              const SizedBox(height: 12),
              SkeletonCard.section(bodyHeight: 220),       // radar
            ],
          ),
        ),
        data: (p) => _Body(preview: p, refresh: () => ref.invalidate(matchPreviewProvider(fixtureId))),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final MatchPreviewDto preview;
  final VoidCallback refresh;
  const _Body({required this.preview, required this.refresh});

  @override
  Widget build(BuildContext context) {
    final homeLabel = preview.home.shortName ?? preview.home.name;
    final awayLabel = preview.away.shortName ?? preview.away.name;

    return RefreshIndicator(
      color: ShoeboxColors.accent,
      backgroundColor: ShoeboxColors.surface,
      onRefresh: () async => refresh(),
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          MatchHeader(preview: preview),
          if (preview.insights.isNotEmpty) ...[
            const SizedBox(height: 12),
            InsightsStrip(insights: preview.insights),
          ],
          const SizedBox(height: 16),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              children: [
                _SquadButtons(
                  preview: preview,
                  homeLabel: homeLabel,
                  awayLabel: awayLabel,
                ),
                const SizedBox(height: 12),

                // ── Sport-specific season averages ────────────────────────────
                if (preview.fixture.isBasketball)
                  BasketballAveragesCard(
                    home: preview.home.basketballStats,
                    away: preview.away.basketballStats,
                    homeLabel: homeLabel,
                    awayLabel: awayLabel,
                  )
                else
                  SeasonAveragesCard(
                    home: preview.home.footballStats,
                    away: preview.away.footballStats,
                    homeLabel: homeLabel,
                    awayLabel: awayLabel,
                  ),

                // ── Football-only sections ────────────────────────────────────
                if (preview.fixture.isFootball) ...[
                  const SizedBox(height: 12),
                  PremiumGate(
                    featureKey: 'match:${preview.fixture.id}:hit_rates',
                    child: HitRateCard(
                      home: preview.homeSeasonHr,
                      away: preview.awaySeasonHr,
                      homeLabel: homeLabel,
                      awayLabel: awayLabel,
                    ),
                  ),
                  if (preview.splits != null &&
                      (preview.splits!.homeTeamAtHome != null ||
                          preview.splits!.awayTeamAway != null)) ...[
                    const SizedBox(height: 12),
                    PremiumGate(
                      featureKey: 'match:${preview.fixture.id}:splits',
                      child: _SplitsCard(
                          splits: preview.splits!,
                          homeLabel: homeLabel,
                          awayLabel: awayLabel),
                    ),
                  ],
                ],

                // ── Shared sections (both sports) ─────────────────────────────
                if (preview.radar != null) ...[
                  const SizedBox(height: 12),
                  RadarCard(radar: preview.radar!, homeLabel: homeLabel, awayLabel: awayLabel),
                ],
                if (preview.trendsHome.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  TrendCard(
                    teamLabel: homeLabel,
                    series: preview.trendsHome,
                    accent: ShoeboxColors.home,
                  ),
                ],
                if (preview.trendsAway.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  TrendCard(
                    teamLabel: awayLabel,
                    series: preview.trendsAway,
                    accent: ShoeboxColors.away,
                  ),
                ],

                // ── Referee (football-only for v1) ────────────────────────────
                if (preview.referee != null) ...[
                  const SizedBox(height: 12),
                  RefereeCard(
                    referee: preview.referee!,
                    homeLabel: homeLabel,
                    awayLabel: awayLabel,
                  ),
                ],
                const SizedBox(height: 32),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Pair of CTA buttons that drop the user into each team's squad list.
class _SquadButtons extends StatelessWidget {
  final MatchPreviewDto preview;
  final String homeLabel;
  final String awayLabel;
  const _SquadButtons({
    required this.preview,
    required this.homeLabel,
    required this.awayLabel,
  });

  void _open(BuildContext c, int teamId, String teamName) {
    HapticFeedback.lightImpact();
    c.push(
      '/team/$teamId/squad'
      '?league=${preview.fixture.leagueId}'
      '&season=${preview.fixture.season}'
      '&name=${Uri.encodeQueryComponent(teamName)}',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _Pill(
            label: '$homeLabel squad',
            color: ShoeboxColors.home,
            onTap: () => _open(context, preview.home.id, preview.home.name),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _Pill(
            label: '$awayLabel squad',
            color: ShoeboxColors.away,
            onTap: () => _open(context, preview.away.id, preview.away.name),
          ),
        ),
      ],
    );
  }
}

class _Pill extends StatelessWidget {
  final String label;
  final Color color;
  final VoidCallback onTap;
  const _Pill({required this.label, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: ShoeboxColors.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border(left: BorderSide(color: color, width: 3)),
          ),
          child: Row(
            children: [
              const Icon(Icons.group_rounded, size: 18, color: ShoeboxColors.textMid),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const Icon(Icons.chevron_right_rounded, size: 18, color: ShoeboxColors.textLow),
            ],
          ),
        ),
      ),
    );
  }
}

/// Home-when-at-home and Away-when-away. Bettors look at these first.
class _SplitsCard extends StatelessWidget {
  final SplitsDto splits;
  final String homeLabel;
  final String awayLabel;
  const _SplitsCard({required this.splits, required this.homeLabel, required this.awayLabel});

  @override
  Widget build(BuildContext context) {
    return HitRateCard(
      home: splits.homeTeamAtHome,
      away: splits.awayTeamAway,
      homeLabel: '$homeLabel · home',
      awayLabel: '$awayLabel · away',
    );
  }
}
