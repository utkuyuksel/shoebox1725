import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../../core/widgets/async_view.dart';
import '../data/referee_dto.dart';
import '../data/referee_repository.dart';

/// Default season to look up referee aggregates in. Until we wire season
/// detection per-league, this matches our seed data.
const _defaultSeason = 2024;

class RefereeSearchScreen extends ConsumerStatefulWidget {
  const RefereeSearchScreen({super.key});
  @override
  ConsumerState<RefereeSearchScreen> createState() => _RefereeSearchScreenState();
}

class _RefereeSearchScreenState extends ConsumerState<RefereeSearchScreen> {
  final _controller = TextEditingController();
  Timer? _debounce;
  String _committedQuery = '';

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    _debounce?.cancel();
    // Show local empty/hint state immediately for sub-min queries.
    if (value.trim().length < 2) {
      setState(() => _committedQuery = value.trim());
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () {
      setState(() => _committedQuery = value.trim());
    });
  }

  @override
  Widget build(BuildContext context) {
    final results = ref.watch(refereeSearchProvider(_committedQuery));
    final hasQuery = _committedQuery.length >= 2;

    return Scaffold(
      appBar: AppBar(title: const Text('Referees')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: TextField(
              controller: _controller,
              autofocus: true,
              onChanged: _onChanged,
              style: const TextStyle(color: ShoeboxColors.textHigh),
              decoration: InputDecoration(
                hintText: 'Search referees (e.g. Meler)',
                hintStyle: const TextStyle(color: ShoeboxColors.textLow),
                prefixIcon: const Icon(Icons.search_rounded, color: ShoeboxColors.textMid),
                suffixIcon: _controller.text.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close_rounded, color: ShoeboxColors.textMid),
                        onPressed: () {
                          _controller.clear();
                          setState(() => _committedQuery = '');
                        },
                      ),
                filled: true,
                fillColor: ShoeboxColors.surface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
              ),
            ),
          ),
          Expanded(
            child: !hasQuery
                ? _Hint()
                : AsyncView<List<RefereeSearchResultDto>>(
                    value: results,
                    onRetry: () => ref.invalidate(refereeSearchProvider(_committedQuery)),
                    isEmpty: (r) => r.isEmpty,
                    emptyMessage: 'No referees match “$_committedQuery”',
                    data: (r) => _ResultsList(items: r),
                  ),
          ),
        ],
      ),
    );
  }
}

class _Hint extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.sports_outlined, size: 40, color: ShoeboxColors.textLow),
            const SizedBox(height: 12),
            Text(
              'Type at least 2 letters to search.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: ShoeboxColors.textMid),
            ),
          ],
        ),
      ),
    );
  }
}

class _ResultsList extends StatelessWidget {
  final List<RefereeSearchResultDto> items;
  const _ResultsList({required this.items});

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
      itemCount: items.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (c, i) {
        final r = items[i];
        return Material(
          color: ShoeboxColors.surface,
          borderRadius: BorderRadius.circular(12),
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => c.push(
              '/referee/${r.id}?season=$_defaultSeason&name=${Uri.encodeQueryComponent(r.name)}',
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 14),
              child: Row(
                children: [
                  Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(
                      color: ShoeboxColors.surfaceAlt,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(Icons.sports, color: ShoeboxColors.textMid),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          r.name,
                          style: Theme.of(c).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600),
                        ),
                        if (r.nationality != null)
                          Text(
                            r.nationality!,
                            style: Theme.of(c).textTheme.bodySmall?.copyWith(color: ShoeboxColors.textMid),
                          ),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right_rounded, color: ShoeboxColors.textLow),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
