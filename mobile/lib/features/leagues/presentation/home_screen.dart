import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/skeleton.dart';
import '../data/league_dto.dart';
import '../data/leagues_repository.dart';
import 'widgets/country_tile.dart';
import 'widgets/popular_league_card.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  String _sport = 'football';

  @override
  Widget build(BuildContext context) {
    final leagues = ref.watch(leaguesProvider(_sport));

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.bolt_rounded, color: ShoeboxColors.accent, size: 22),
            const SizedBox(width: 8),
            Text(
              'SHOEBOX',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w900,
                letterSpacing: 2,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.sports_outlined),
            tooltip: 'Referees',
            onPressed: () => context.push('/referees'),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: ShoeboxColors.accent,
        backgroundColor: ShoeboxColors.surface,
        onRefresh: () async => ref.invalidate(leaguesProvider(_sport)),
        child: Column(
          children: [
            _SportSegment(
              value: _sport,
              onChanged: (s) => setState(() => _sport = s),
            ),
            Expanded(
              child: AsyncView<LeaguesPayload>(
                value: leagues,
                onRetry: () => ref.invalidate(leaguesProvider(_sport)),
                isEmpty: (p) => p.count == 0,
                emptyMessage: 'No leagues available for this sport yet.',
                emptyIcon: Icons.shield_outlined,
                loadingBuilder: (_) => SkeletonList(
                  itemCount: 6,
                  builder: () => SkeletonCard.countryTile(),
                ),
                data: (payload) => _LeaguesList(payload: payload),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SportSegment extends StatelessWidget {
  final String value;
  final ValueChanged<String> onChanged;
  const _SportSegment({required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: ShoeboxColors.surface,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            _Pill(label: 'Football', selected: value == 'football', onTap: () => onChanged('football')),
            _Pill(label: 'Basketball', selected: value == 'basketball', onTap: () => onChanged('basketball')),
          ],
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _Pill({required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: () {
          HapticFeedback.selectionClick();
          onTap();
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: selected ? ShoeboxColors.accentSoft : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              color: selected ? ShoeboxColors.accent : ShoeboxColors.textMid,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }
}

class _LeaguesList extends StatelessWidget {
  final LeaguesPayload payload;
  const _LeaguesList({required this.payload});

  @override
  Widget build(BuildContext context) {
    final countries = payload.grouped.keys.toList()..sort();
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
      children: [
        if (payload.popular.isNotEmpty) ...[
          _SectionLabel('Popular'),
          const SizedBox(height: 8),
          SizedBox(
            height: 156,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: payload.popular.length,
              itemBuilder: (c, i) {
                final l = payload.popular[i];
                return PopularLeagueCard(
                  league: l,
                  onTap: () => context.push('/leagues/${l.id}/fixtures', extra: l.name),
                );
              },
            ),
          ),
          const SizedBox(height: 24),
        ],
        _SectionLabel('All competitions'),
        const SizedBox(height: 8),
        ...countries.map((country) {
          final list = payload.grouped[country] ?? [];
          final cc = list.firstOrNull?.countryCode;
          return CountryTile(
            country: country,
            countryCode: cc,
            leagues: list,
            onLeagueTap: (l) => context.push('/leagues/${l.id}/fixtures', extra: l.name),
          );
        }),
      ],
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);
  @override
  Widget build(BuildContext context) {
    return Text(
      text.toUpperCase(),
      style: Theme.of(context).textTheme.labelMedium?.copyWith(
        color: ShoeboxColors.textMid,
        letterSpacing: 1.5,
        fontWeight: FontWeight.w700,
      ),
    );
  }
}

extension<E> on List<E> {
  E? get firstOrNull => isEmpty ? null : first;
}
