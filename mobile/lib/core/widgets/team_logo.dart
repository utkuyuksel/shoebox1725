import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../../app/theme.dart';

/// Cached logo with fallback. api-sports media CDN sometimes rejects requests
/// without a browser-like User-Agent; we provide one.
class TeamLogo extends StatelessWidget {
  final String? url;
  final double size;
  const TeamLogo({super.key, required this.url, this.size = 48});

  static const _spoofHeaders = {
    'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  };

  @override
  Widget build(BuildContext context) {
    if (url == null || url!.isEmpty) {
      return _Placeholder(size: size);
    }
    return CachedNetworkImage(
      imageUrl: url!,
      httpHeaders: _spoofHeaders,
      width: size,
      height: size,
      fit: BoxFit.contain,
      placeholder: (_, __) => _Placeholder(size: size),
      errorWidget: (_, __, ___) => _Placeholder(size: size),
    );
  }
}

class _Placeholder extends StatelessWidget {
  final double size;
  const _Placeholder({required this.size});
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size, height: size,
      child: const Icon(Icons.shield, color: ShoeboxColors.textLow),
    );
  }
}
