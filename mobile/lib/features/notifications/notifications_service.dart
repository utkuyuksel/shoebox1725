import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

/// Single source of truth for local notifications. Responsibilities:
///
///   - One-time SDK init at app start (`init`), idempotent.
///   - First-time permission request when the user adds their first match to
///     the watchlist (`requestPermissionIfNeeded`).
///   - Per-fixture kickoff reminders, scheduled 1h before kickoff
///     (`scheduleKickoffReminder`).
///   - Cancellation when the user removes a fixture from the watchlist
///     (`cancelForFixture`).
///
/// All scheduling is local-only — no server, no Firebase. iOS caps the queue
/// at 64 active notifications; we don't enforce that on our side, the OS just
/// drops the surplus silently.
class NotificationsService {
  static const _channelId = 'kickoff_reminders';
  static const _channelName = 'Kickoff reminders';
  static const _reminderLeadMinutes = 60;

  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _initialised = false;
  static bool _permissionGranted = false;

  /// Wires platform-specific init. Safe to call multiple times.
  static Future<void> init() async {
    if (_initialised) return;
    if (kIsWeb) {
      _initialised = true;
      return;
    }
    try {
      tz.initializeTimeZones();
    } catch (_) {
      // already initialised
    }

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    final iosInit = DarwinInitializationSettings(
      // We request permission lazily on first watchlist-add, not on init.
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );
    final initSettings = InitializationSettings(
      android: androidInit,
      iOS: iosInit,
      macOS: iosInit,
    );

    await _plugin.initialize(initSettings);
    _initialised = true;
  }

  /// Asks the OS for notification permission once. After the first prompt
  /// the user controls this via system Settings — we honour their answer
  /// silently and don't re-ask.
  static Future<bool> requestPermissionIfNeeded() async {
    if (!_initialised) await init();
    if (_permissionGranted) return true;
    if (kIsWeb) return false;

    bool ok = false;
    try {
      if (Platform.isIOS || Platform.isMacOS) {
        ok = await _plugin
                .resolvePlatformSpecificImplementation<
                    IOSFlutterLocalNotificationsPlugin>()
                ?.requestPermissions(alert: true, badge: true, sound: true) ??
            false;
      } else if (Platform.isAndroid) {
        ok = await _plugin
                .resolvePlatformSpecificImplementation<
                    AndroidFlutterLocalNotificationsPlugin>()
                ?.requestNotificationsPermission() ??
            false;
      }
    } catch (e) {
      debugPrint('notifications_permission_failed: $e');
    }
    _permissionGranted = ok;
    return ok;
  }

  /// Schedule a single reminder for [fixtureId] at `kickoffAtUtc - 1h`.
  /// If the lead time is in the past (kickoff in less than an hour or
  /// already happened), the call is a no-op.
  static Future<void> scheduleKickoffReminder({
    required int fixtureId,
    required DateTime kickoffAtUtc,
    required String title,
    required String body,
  }) async {
    if (!_initialised) await init();
    if (kIsWeb) return;
    if (!_permissionGranted) return;

    final fireAt = kickoffAtUtc.subtract(const Duration(minutes: _reminderLeadMinutes));
    if (fireAt.isBefore(DateTime.now().toUtc())) return;

    final tzFire = tz.TZDateTime.from(fireAt, tz.UTC);

    final androidDetails = AndroidNotificationDetails(
      _channelId, _channelName,
      channelDescription: 'Heads-up before your watchlisted matches kick off.',
      importance: Importance.high,
      priority: Priority.high,
    );
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );
    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
      macOS: iosDetails,
    );

    try {
      await _plugin.zonedSchedule(
        fixtureId, // notification id = fixture id, so we can cancel by it
        title,
        body,
        tzFire,
        details,
        payload: 'match:$fixtureId',
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
      );
    } catch (e) {
      debugPrint('notifications_schedule_failed fixture=$fixtureId err=$e');
    }
  }

  static Future<void> cancelForFixture(int fixtureId) async {
    if (!_initialised) await init();
    if (kIsWeb) return;
    try {
      await _plugin.cancel(fixtureId);
    } catch (e) {
      debugPrint('notifications_cancel_failed fixture=$fixtureId err=$e');
    }
  }

  static Future<void> cancelAll() async {
    if (!_initialised) await init();
    if (kIsWeb) return;
    try {
      await _plugin.cancelAll();
    } catch (e) {
      debugPrint('notifications_cancel_all_failed: $e');
    }
  }
}

final notificationsServiceProvider = Provider<NotificationsService>((_) {
  // The class is fully static — the provider exists so callers stay
  // consistent with the rest of the app (everything else is via Riverpod).
  return NotificationsService();
});
