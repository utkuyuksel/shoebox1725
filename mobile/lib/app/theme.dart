import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Brand tokens. Dark-first. Designed for content density (bettors scan a lot).
class ShoeboxColors {
  static const navy = Color(0xFF0B1220);          // app background
  static const surface = Color(0xFF131C2D);       // card background
  static const surfaceAlt = Color(0xFF1B2638);    // raised card / inputs
  static const stroke = Color(0xFF24304A);        // dividers
  static const accent = Color(0xFF4F8DFF);        // primary actions, links
  static const accentSoft = Color(0xFF1F3357);    // accent backgrounds
  static const success = Color(0xFF22C55E);       // hit-rate good
  static const warn = Color(0xFFF59E0B);          // hit-rate neutral
  static const danger = Color(0xFFEF4444);        // hit-rate poor / away accent
  static const textHigh = Color(0xFFF1F5F9);
  static const textMid = Color(0xFFA5B4CB);
  static const textLow = Color(0xFF6B7B95);
  // Two-tone accents used for home/away contrasts on charts.
  static const home = Color(0xFF4F8DFF);
  static const away = Color(0xFFEF4444);
}

ThemeData buildShoeboxTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  final textTheme = GoogleFonts.interTextTheme(base.textTheme).apply(
    bodyColor: ShoeboxColors.textHigh,
    displayColor: ShoeboxColors.textHigh,
  );

  return base.copyWith(
    scaffoldBackgroundColor: ShoeboxColors.navy,
    colorScheme: ColorScheme.fromSeed(
      seedColor: ShoeboxColors.accent,
      brightness: Brightness.dark,
      surface: ShoeboxColors.surface,
    ),
    textTheme: textTheme,
    appBarTheme: AppBarTheme(
      backgroundColor: ShoeboxColors.navy,
      foregroundColor: ShoeboxColors.textHigh,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.w700,
        letterSpacing: 0.5,
      ),
    ),
    cardTheme: CardThemeData(
      color: ShoeboxColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      margin: EdgeInsets.zero,
    ),
    dividerTheme: const DividerThemeData(color: ShoeboxColors.stroke, thickness: 1),
    chipTheme: ChipThemeData(
      backgroundColor: ShoeboxColors.surfaceAlt,
      labelStyle: textTheme.labelSmall?.copyWith(color: ShoeboxColors.textHigh),
      side: BorderSide.none,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
    expansionTileTheme: const ExpansionTileThemeData(
      backgroundColor: ShoeboxColors.surface,
      collapsedBackgroundColor: ShoeboxColors.surface,
      iconColor: ShoeboxColors.textMid,
      collapsedIconColor: ShoeboxColors.textMid,
      textColor: ShoeboxColors.textHigh,
      collapsedTextColor: ShoeboxColors.textHigh,
      shape: Border(),
      collapsedShape: Border(),
    ),
  );
}
