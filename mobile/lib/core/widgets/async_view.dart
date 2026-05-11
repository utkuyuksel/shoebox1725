import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../l10n/generated/app_localizations.dart';

/// Single source of truth for the loading / error / empty / data cycle.
/// Each variant is intentionally tasteful — a sports stats app spends a lot
/// of time in transitional states and the user should never feel "stuck".
class AsyncView<T> extends StatelessWidget {
  final AsyncValue<T> value;
  final Widget Function(T data) data;
  final VoidCallback? onRetry;
  final String? emptyMessage;
  final IconData? emptyIcon;
  final bool Function(T data)? isEmpty;

  /// Optional loading placeholder — usually a [SkeletonList] that mimics the
  /// real list layout. Falls back to a small spinner when null.
  final WidgetBuilder? loadingBuilder;

  const AsyncView({
    super.key,
    required this.value,
    required this.data,
    this.onRetry,
    this.emptyMessage,
    this.emptyIcon,
    this.isEmpty,
    this.loadingBuilder,
  });

  @override
  Widget build(BuildContext context) {
    return value.when(
      loading: () => loadingBuilder != null
          ? loadingBuilder!(context)
          : const Center(
              child: SizedBox(
                width: 28, height: 28,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: ShoeboxColors.accent,
                ),
              ),
            ),
      error: (e, _) => _ErrorView(error: e, onRetry: onRetry),
      data: (d) {
        if (isEmpty != null && isEmpty!(d)) {
          return _EmptyView(
            message: emptyMessage ??
                AppLocalizations.of(context).commonNothingHere,
            icon: emptyIcon ?? Icons.inbox_outlined,
          );
        }
        return data(d);
      },
    );
  }
}

class _ErrorView extends StatelessWidget {
  final Object error;
  final VoidCallback? onRetry;
  const _ErrorView({required this.error, this.onRetry});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72, height: 72,
              decoration: BoxDecoration(
                color: ShoeboxColors.danger.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(36),
              ),
              child: const Icon(Icons.cloud_off_rounded,
                  color: ShoeboxColors.danger, size: 32),
            ),
            const SizedBox(height: 16),
            Text(
              l.commonGenericError,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '$error',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: ShoeboxColors.textMid,
              ),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 20),
              FilledButton.tonalIcon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded, size: 18),
                label: Text(l.commonRetry),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  final String message;
  final IconData icon;
  const _EmptyView({required this.message, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64, height: 64,
              decoration: BoxDecoration(
                color: ShoeboxColors.surfaceAlt,
                borderRadius: BorderRadius.circular(32),
              ),
              child: Icon(icon, color: ShoeboxColors.textMid, size: 30),
            ),
            const SizedBox(height: 14),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: ShoeboxColors.textMid,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
