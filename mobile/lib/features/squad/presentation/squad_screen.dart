import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/skeleton.dart';
import '../data/squad_dto.dart';
import '../data/squad_repository.dart';

class SquadScreen extends ConsumerWidget {
  final int teamId;
  final int leagueId;
  final int season;
  final String teamName;
  const SquadScreen({
    super.key,
    required this.teamId,
    required this.leagueId,
    required this.season,
    required this.teamName,
  });

  static const _positionOrder = ['G', 'D', 'M', 'F'];
  static const _positionLabels = {
    'G': 'Goalkeepers',
    'D': 'Defenders',
    'M': 'Midfielders',
    'F': 'Forwards',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final key = SquadKey(teamId: teamId, leagueId: leagueId, season: season);
    final squad = ref.watch(squadProvider(key));

    return Scaffold(
      appBar: AppBar(
        title: Text('$teamName · Squad'),
      ),
      body: AsyncView<SquadPayload>(
        value: squad,
        onRetry: () => ref.invalidate(squadProvider(key)),
        isEmpty: (p) => p.players.isEmpty,
        emptyMessage: 'No squad data for this season.',
        emptyIcon: Icons.group_outlined,
        loadingBuilder: (_) => SkeletonList(
          itemCount: 8,
          gap: 8,
          builder: () => SkeletonCard.squadRow(),
        ),
        data: (p) => _SquadBody(
          players: p.players,
          leagueId: leagueId,
          season: season,
        ),
      ),
    );
  }
}

class _SquadBody extends StatelessWidget {
  final List<SquadPlayerDto> players;
  final int leagueId;
  final int season;
  const _SquadBody({required this.players, required this.leagueId, required this.season});

  @override
  Widget build(BuildContext context) {
    // Group by position
    final grouped = <String, List<SquadPlayerDto>>{};
    for (final p in players) {
      final pos = p.position ?? 'F';
      grouped.putIfAbsent(pos, () => []).add(p);
    }
    // Sort each group by shirt number (nulls last)
    for (final list in grouped.values) {
      list.sort((a, b) {
        final an = a.number ?? 1000;
        final bn = b.number ?? 1000;
        return an.compareTo(bn);
      });
    }
    final ordered = SquadScreen._positionOrder
        .where(grouped.containsKey)
        .map((pos) => MapEntry(pos, grouped[pos]!))
        .toList();

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      itemCount: ordered.fold<int>(0, (acc, e) => acc + 1 + e.value.length),
      itemBuilder: (c, idx) {
        var cursor = 0;
        for (final entry in ordered) {
          if (idx == cursor) {
            return _SectionHeader(SquadScreen._positionLabels[entry.key] ?? entry.key);
          }
          cursor++;
          if (idx < cursor + entry.value.length) {
            final p = entry.value[idx - cursor];
            return _PlayerRow(
              player: p,
              onTap: () => context.push(
                '/player/${p.id}?league=$leagueId&season=$season&sport=football&name=${Uri.encodeQueryComponent(p.name)}',
              ),
            );
          }
          cursor += entry.value.length;
        }
        return const SizedBox.shrink();
      },
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String label;
  const _SectionHeader(this.label);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 18, 0, 8),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: ShoeboxColors.textMid,
          letterSpacing: 1.6,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _PlayerRow extends StatelessWidget {
  final SquadPlayerDto player;
  final VoidCallback onTap;
  const _PlayerRow({required this.player, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        onTap: () {
          HapticFeedback.lightImpact();
          onTap();
        },
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        leading: SizedBox(
          width: 36,
          child: Center(
            child: Text(
              player.number?.toString() ?? '–',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: ShoeboxColors.textMid,
                fontWeight: FontWeight.w800,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ),
        ),
        title: Text(
          player.name,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600),
        ),
        subtitle: player.nationality == null
            ? null
            : Text(
                player.nationality!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: ShoeboxColors.textMid),
              ),
        trailing: const Icon(Icons.chevron_right_rounded, color: ShoeboxColors.textLow),
      ),
    );
  }
}
