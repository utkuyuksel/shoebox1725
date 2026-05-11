import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme.dart';
import '../../../l10n/generated/app_localizations.dart';
import '../state/onboarding_provider.dart';

/// Three-page first-launch tour. Lightweight — no images, no animations
/// beyond the page controller. Bettors hate friction; this exists only to
/// surface the three pillars they'd otherwise have to discover.
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _controller = PageController();
  int _page = 0;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _next(int total) {
    HapticFeedback.selectionClick();
    if (_page < total - 1) {
      _controller.nextPage(
          duration: const Duration(milliseconds: 280), curve: Curves.easeOutCubic);
    } else {
      _finish();
    }
  }

  Future<void> _finish() async {
    await ref.read(onboardingControllerProvider.notifier).markCompleted();
    if (!mounted) return;
    context.go('/');
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final pages = <_Page>[
      _Page(
        icon: Icons.bolt_rounded,
        title: l.onboarding1Title,
        body: l.onboarding1Body,
      ),
      _Page(
        icon: Icons.percent_rounded,
        title: l.onboarding2Title,
        body: l.onboarding2Body,
      ),
      _Page(
        icon: Icons.bookmark_added_rounded,
        title: l.onboarding3Title,
        body: l.onboarding3Body,
      ),
    ];
    final total = pages.length;
    final isLast = _page == total - 1;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(8, 8, 16, 0),
                child: TextButton(
                  onPressed: _finish,
                  child: Text(
                    l.onboardingSkip,
                    style: const TextStyle(color: ShoeboxColors.textMid),
                  ),
                ),
              ),
            ),
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: total,
                onPageChanged: (i) => setState(() => _page = i),
                itemBuilder: (c, i) => pages[i],
              ),
            ),
            _Dots(count: total, active: _page),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: ShoeboxColors.accent,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  onPressed: () => _next(total),
                  child: Text(
                    isLast ? l.onboardingDone : l.onboardingNext,
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 15),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Page extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  const _Page({required this.icon, required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(32, 0, 32, 16),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 110,
            height: 110,
            decoration: BoxDecoration(
              color: ShoeboxColors.accentSoft,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 54, color: ShoeboxColors.accent),
          ),
          const SizedBox(height: 32),
          Text(
            title,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(height: 12),
          Text(
            body,
            textAlign: TextAlign.center,
            style: const TextStyle(
                color: ShoeboxColors.textMid, fontSize: 14, height: 1.45),
          ),
        ],
      ),
    );
  }
}

class _Dots extends StatelessWidget {
  final int count;
  final int active;
  const _Dots({required this.count, required this.active});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(count, (i) {
        final isActive = i == active;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          width: isActive ? 22 : 7,
          height: 7,
          decoration: BoxDecoration(
            color:
                isActive ? ShoeboxColors.accent : ShoeboxColors.stroke,
            borderRadius: BorderRadius.circular(4),
          ),
        );
      }),
    );
  }
}
