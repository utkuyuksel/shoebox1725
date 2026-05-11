import 'package:flutter/material.dart';

import '../../app/theme.dart';

/// Lightweight shimmer placeholder primitives. No external package — a single
/// AnimationController feeds a LinearGradient that slides left → right.
///
/// Usage:
///   - SkeletonBox(width, height) for atomic boxes
///   - SkeletonText(width) for single-line text rows
///   - SkeletonCard.fixture()/.match()/.squadRow() — pre-baked layouts that
///     match real cards so the LCP transition isn't jarring.
class Skeleton extends StatefulWidget {
  final Widget child;
  const Skeleton({super.key, required this.child});

  @override
  State<Skeleton> createState() => _SkeletonState();
}

class _SkeletonState extends State<Skeleton> with SingleTickerProviderStateMixin {
  late final AnimationController _c;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400))
      ..repeat();
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _c,
      builder: (context, child) {
        final t = _c.value;
        return ShaderMask(
          blendMode: BlendMode.srcATop,
          shaderCallback: (rect) {
            return LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              colors: const [
                ShoeboxColors.surface,
                ShoeboxColors.surfaceAlt,
                ShoeboxColors.surface,
              ],
              // Slide window across; values 0..1 → -1..2 to glide off-canvas.
              stops: [
                (t - 0.3).clamp(0.0, 1.0),
                t.clamp(0.0, 1.0),
                (t + 0.3).clamp(0.0, 1.0),
              ],
            ).createShader(rect);
          },
          child: child,
        );
      },
      child: widget.child,
    );
  }
}

class SkeletonBox extends StatelessWidget {
  final double width;
  final double height;
  final double radius;
  const SkeletonBox({super.key, required this.width, required this.height, this.radius = 6});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(radius),
      ),
    );
  }
}

class SkeletonText extends StatelessWidget {
  final double width;
  final double height;
  const SkeletonText({super.key, required this.width, this.height = 12});

  @override
  Widget build(BuildContext context) {
    return SkeletonBox(width: width, height: height, radius: 4);
  }
}

/// Pre-baked card-shaped skeletons. Each one matches a real list/grid card so
/// the layout doesn't jump when real data arrives.
class SkeletonCard {
  /// Mimics a FixtureCard (date + two team sides + center score).
  static Widget fixture() {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: const [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              SkeletonText(width: 56, height: 10),
              SkeletonText(width: 60, height: 10),
            ],
          ),
          SizedBox(height: 14),
          Row(
            children: [
              Expanded(child: _TeamSkeleton(rightAligned: false)),
              SizedBox(width: 14),
              SkeletonText(width: 44, height: 22),
              SizedBox(width: 14),
              Expanded(child: _TeamSkeleton(rightAligned: true)),
            ],
          ),
        ],
      ),
    );
  }

  /// Mimics a squad row.
  static Widget squadRow() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 14),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: const [
          SkeletonBox(width: 24, height: 24, radius: 12),
          SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SkeletonText(width: 140, height: 12),
                SizedBox(height: 6),
                SkeletonText(width: 80, height: 10),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Mimics a country tile.
  static Widget countryTile() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: const [
          SkeletonBox(width: 24, height: 24, radius: 4),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SkeletonText(width: 120, height: 12),
                SizedBox(height: 4),
                SkeletonText(width: 80, height: 10),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Mimics a SectionCard ~ used on the match preview.
  static Widget section({double bodyHeight = 80}) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
      decoration: BoxDecoration(
        color: ShoeboxColors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SkeletonText(width: 140, height: 10),
          const SizedBox(height: 16),
          SkeletonBox(width: double.infinity, height: bodyHeight, radius: 8),
        ],
      ),
    );
  }
}

class _TeamSkeleton extends StatelessWidget {
  final bool rightAligned;
  const _TeamSkeleton({required this.rightAligned});

  @override
  Widget build(BuildContext context) {
    final logo = const SkeletonBox(width: 38, height: 38, radius: 19);
    final txt = const SkeletonText(width: 80, height: 12);
    final children = rightAligned
        ? [Expanded(child: Align(alignment: Alignment.centerRight, child: txt)), const SizedBox(width: 10), logo]
        : [logo, const SizedBox(width: 10), Expanded(child: txt)];
    return Row(children: children);
  }
}

/// Composes N skeleton cards into a vertical list. Useful as a "data loading"
/// placeholder for screens whose content is a list of homogeneous cards.
class SkeletonList extends StatelessWidget {
  final int itemCount;
  final Widget Function() builder;
  final EdgeInsetsGeometry padding;
  final double gap;
  const SkeletonList({
    super.key,
    required this.builder,
    this.itemCount = 6,
    this.padding = const EdgeInsets.fromLTRB(16, 8, 16, 16),
    this.gap = 10,
  });

  @override
  Widget build(BuildContext context) {
    return Skeleton(
      child: ListView.separated(
        physics: const NeverScrollableScrollPhysics(),
        padding: padding,
        itemCount: itemCount,
        separatorBuilder: (_, _) => SizedBox(height: gap),
        itemBuilder: (_, _) => builder(),
      ),
    );
  }
}
