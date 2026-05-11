import 'dart:io' show Platform;

/// Resolves the backend base URL at build time / runtime.
///
/// - Override at run time via:
///     flutter run --dart-define=API_BASE_URL=https://api.shoebox.app
/// - Otherwise we pick the right localhost-equivalent per platform:
///   iOS sim and macOS desktop see the host as 127.0.0.1; Android emulator
///   sees it as 10.0.2.2. Web and others fall back to 127.0.0.1.
class AppEnv {
  static const _override = String.fromEnvironment('API_BASE_URL');

  static String get apiBaseUrl {
    if (_override.isNotEmpty) return _override;
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8000';
    } catch (_) {
      // Platform is unavailable on Flutter web; fall through.
    }
    return 'http://127.0.0.1:8000';
  }
}
