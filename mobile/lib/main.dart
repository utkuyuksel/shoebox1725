import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/router.dart';
import 'app/theme.dart';

void main() {
  // Apply system UI styling before the first frame.
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,   // Android
    statusBarBrightness: Brightness.dark,        // iOS (dark background → light icons)
    systemNavigationBarColor: ShoeboxColors.navy,
    systemNavigationBarIconBrightness: Brightness.light,
  ));
  runApp(const ProviderScope(child: ShoeboxApp()));
}

class ShoeboxApp extends StatelessWidget {
  const ShoeboxApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Shoebox',
      debugShowCheckedModeBanner: false,
      theme: buildShoeboxTheme(),
      themeMode: ThemeMode.dark,
      routerConfig: appRouter,
    );
  }
}
