import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// User's chosen UI language. `null` means "follow the system locale".
/// Persisted via SharedPreferences so the choice survives cold starts.
class LocaleController extends StateNotifier<Locale?> {
  LocaleController(this._prefs) : super(_read(_prefs));

  static const _key = 'ui_locale';

  final SharedPreferences _prefs;

  static Locale? _read(SharedPreferences prefs) {
    final raw = prefs.getString(_key);
    if (raw == null || raw.isEmpty) return null;
    return Locale(raw);
  }

  Future<void> setLocale(Locale? locale) async {
    state = locale;
    if (locale == null) {
      await _prefs.remove(_key);
    } else {
      await _prefs.setString(_key, locale.languageCode);
    }
  }
}

/// Loaded async by `main()` before runApp, so this is always non-null in scope.
final sharedPreferencesProvider = Provider<SharedPreferences>((_) {
  throw UnimplementedError('Override with the value from main()');
});

final localeControllerProvider =
    StateNotifierProvider<LocaleController, Locale?>((ref) {
  return LocaleController(ref.watch(sharedPreferencesProvider));
});
