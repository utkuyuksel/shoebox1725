import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/skeleton.dart';
import '../../../core/widgets/team_logo.dart';
import '../../auth/state/auth_provider.dart';
import '../data/watchlist_dto.dart';
import '../data/watchlist_repository.dart';
import 'watchlist_star_button.dart';

class WatchlistScreen extends ConsumerWidget {
  const WatchlistScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final signedIn = ref.watch(isSignedInProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Watchlist')),
      body: signedIn
          ? _SignedInBody(ref: ref)
          : const _SignedOutBody(),
    );
  }
}

class _SignedOutBody extends StatelessWidget {
  const _SignedOutBody();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: ShoeboxColors.surface,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.bookmark_outline_rounded,
                  size: 32, color: ShoeboxColors.accent),
            ),
            const SizedBox(height: 16),
            const Text('Sign in to use the watchlist',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 4),
            const Text(
              'Bookmark fixtures and keep them synced across devices.',
              textAlign: TextAlign.center,
              style: TextStyle(color: ShoeboxColors.textMid),
            ),
            const SizedBox(height: 20),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: ShoeboxColors.accent,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
              ),
              onPressed: () => context.push('/login'),
              child: const Text('Sign in'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SignedInBody extends StatelessWidget {
  final WidgetRef ref;
  const _SignedInBody({required this.ref});

  @override
  Widget build(BuildContext context) {
    final value = ref.watch(watchlistFixturesProvider);
    return RefreshIndicator(
      color: ShoeboxColors.accent,
      backgroundColor: ShoeboxColors.surface,
      onRefresh: () async => ref.invalidate(watchlistFixturesProvider),
      child: AsyncView<List<WatchlistFixtureDto>>(
        value: value,
        onRetry: () => ref.invalidate(watchlistFixturesProvider),
        isEmpty: (l) => l.isEmpty,
        emptyMessage: 'Tap the bookmark on any fixture to add it here.',
        emptyIcon: Icons.bookmark_outline_rounded,
        loadingBuilder: (_) => SkeletonList(
          itemCount: 6,
          builder: () => SkeletonCard.fixture(),
        ),
        data: (fixtures) => ListView.separated(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
          itemCount: fixtures.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (c, i) => _WatchlistTile(fixture: fixtures[i]),
        ),
      ),
    );
  }
}

class _WatchlistTile extends StatelessWidget {
  final WatchlistFixtureDto fixture;
  const _WatchlistTile({required this.fixture});

  @override
  Widget build(BuildContext context) {
    final dateLabel = DateFormat('d MMM, HH:mm').format(fixture.kickoffAt.toLocal());
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () => context.push('/match/${fixture.id}'),
      child: Container(
        padding: const EdgeInsets.fromLTRB(14, 12, 10, 12),
        decoration: BoxDecoration(
          color: ShoeboxColors.surface,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          children: [
            Row(
              children: [
                if (fixture.leagueLogo != null) ...[
                  CachedNetworkImage(
                    imageUrl: fixture.leagueLogo!,
                    width: 14,
                    height: 14,
                    placeholder: (_, __) => const SizedBox(width: 14, height: 14),
                    errorWidget: (_, __, ___) => const SizedBox(width: 14, height: 14),
                  ),
                  const SizedBox(width: 6),
                ],
                Expanded(
                  child: Text(
                    fixture.leagueName,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        color: ShoeboxColors.textMid,
                        fontSize: 11,
                        fontWeight: FontWeight.w600),
                  ),
                ),
                _StatusChip(fixture: fixture, dateLabel: dateLabel),
                const SizedBox(width: 4),
                WatchlistStarButton(fixtureId: fixture.id, size: 20),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: _TeamLine(
                    name: fixture.homeTeamName,
                    logoUrl: fixture.homeTeamLogo,
                  ),
                ),
                const SizedBox(width: 12),
                _ScoreOrTime(fixture: fixture, dateLabel: dateLabel),
                const SizedBox(width: 12),
                Expanded(
                  child: _TeamLine(
                    name: fixture.awayTeamName,
                    logoUrl: fixture.awayTeamLogo,
                    alignEnd: true,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _TeamLine extends StatelessWidget {
  final String name;
  final String? logoUrl;
  final bool alignEnd;
  const _TeamLine({required this.name, this.logoUrl, this.alignEnd = false});

  @override
  Widget build(BuildContext context) {
    final logo = TeamLogo(url: logoUrl, size: 24);
    return Row(
      mainAxisAlignment:
          alignEnd ? MainAxisAlignment.end : MainAxisAlignment.start,
      children: alignEnd
          ? [
              Flexible(
                child: Text(
                  name,
                  textAlign: TextAlign.end,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontWeight: FontWeight.w600, fontSize: 13),
                ),
              ),
              const SizedBox(width: 8),
              logo,
            ]
          : [
              logo,
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  name,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontWeight: FontWeight.w600, fontSize: 13),
                ),
              ),
            ],
    );
  }
}

class _ScoreOrTime extends StatelessWidget {
  final WatchlistFixtureDto fixture;
  final String dateLabel;
  const _ScoreOrTime({required this.fixture, required this.dateLabel});

  @override
  Widget build(BuildContext context) {
    if (fixture.isFinished &&
        fixture.homeGoals != null &&
        fixture.awayGoals != null) {
      return Text(
        '${fixture.homeGoals}–${fixture.awayGoals}',
        style: const TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 17,
            letterSpacing: 0.5),
      );
    }
    return Text(
      DateFormat('HH:mm').format(fixture.kickoffAt.toLocal()),
      style: const TextStyle(
          fontWeight: FontWeight.w700,
          fontSize: 14,
          color: ShoeboxColors.textHigh),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final WatchlistFixtureDto fixture;
  final String dateLabel;
  const _StatusChip({required this.fixture, required this.dateLabel});

  @override
  Widget build(BuildContext context) {
    final Color bg;
    final Color fg;
    final String text;
    if (fixture.isLive) {
      bg = ShoeboxColors.danger.withValues(alpha: 0.15);
      fg = ShoeboxColors.danger;
      text = 'LIVE';
    } else if (fixture.isFinished) {
      bg = ShoeboxColors.surfaceAlt;
      fg = ShoeboxColors.textMid;
      text = 'FT';
    } else {
      bg = ShoeboxColors.accentSoft;
      fg = ShoeboxColors.accent;
      text = dateLabel;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(text,
          style: TextStyle(
              color: fg, fontWeight: FontWeight.w700, fontSize: 11)),
    );
  }
}
