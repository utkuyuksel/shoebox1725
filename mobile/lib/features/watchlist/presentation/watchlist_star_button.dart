import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../auth/state/auth_provider.dart';
import '../data/watchlist_repository.dart';

/// Heart/star button users tap to watch a fixture. Renders an outlined star
/// when not on the list, a filled accent star when it is. Optimistic update —
/// flips immediately, rolls back on error.
class WatchlistStarButton extends ConsumerStatefulWidget {
  final int fixtureId;
  final double size;
  final Color? outlineColor;

  const WatchlistStarButton({
    super.key,
    required this.fixtureId,
    this.size = 22,
    this.outlineColor,
  });

  @override
  ConsumerState<WatchlistStarButton> createState() => _WatchlistStarButtonState();
}

class _WatchlistStarButtonState extends ConsumerState<WatchlistStarButton> {
  bool _busy = false;
  bool? _localOverride;

  Future<void> _toggle(bool currentlyOn) async {
    if (_busy) return;
    final signedIn = ref.read(isSignedInProvider);
    if (!signedIn) {
      HapticFeedback.selectionClick();
      _showSignInPrompt();
      return;
    }
    HapticFeedback.lightImpact();
    setState(() {
      _localOverride = !currentlyOn;
      _busy = true;
    });
    final repo = ref.read(watchlistRepositoryProvider);
    try {
      if (currentlyOn) {
        await repo.remove(widget.fixtureId);
      } else {
        await repo.add(widget.fixtureId);
      }
      ref.invalidate(watchlistFixturesProvider);
    } on DioException catch (e) {
      // Roll back optimistic flip.
      if (mounted) setState(() => _localOverride = currentlyOn);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Failed: ${e.response?.statusCode ?? e.message}'),
        ));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _showSignInPrompt() {
    showModalBottomSheet(
      context: context,
      backgroundColor: ShoeboxColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: ShoeboxColors.stroke,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            const Icon(Icons.bookmark_added_outlined,
                size: 36, color: ShoeboxColors.accent),
            const SizedBox(height: 12),
            const Text(
              'Sign in to save fixtures',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
            ),
            const SizedBox(height: 6),
            const Text(
              'Your watchlist syncs across devices once you sign in.',
              textAlign: TextAlign.center,
              style: TextStyle(color: ShoeboxColors.textMid),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: ShoeboxColors.accent,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () {
                  Navigator.pop(ctx);
                  context.push('/login');
                },
                child: const Text('Sign in'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ids = ref.watch(watchlistIdsProvider);
    final serverOn = ids.contains(widget.fixtureId);
    final on = _localOverride ?? serverOn;
    return InkResponse(
      radius: widget.size + 8,
      onTap: () => _toggle(on),
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 180),
        transitionBuilder: (child, anim) =>
            ScaleTransition(scale: anim, child: child),
        child: Icon(
          on ? Icons.bookmark_rounded : Icons.bookmark_outline_rounded,
          key: ValueKey(on),
          size: widget.size,
          color: on
              ? ShoeboxColors.accent
              : (widget.outlineColor ?? ShoeboxColors.textMid),
        ),
      ),
    );
  }
}
