import 'dart:ui';

import 'package:android_alarm_manager_plus/android_alarm_manager_plus.dart';
import 'package:geolocator/geolocator.dart' as geo;
import 'package:shared_preferences/shared_preferences.dart';

import 'log_file_service.dart';
import 'notification_service.dart';
import 'location_judgment_service.dart';

@pragma('vm:entry-point')
Future<void> backgroundMonitorCallback() async {
  DartPluginRegistrant.ensureInitialized();
  await BackgroundMonitorService.runPositionCheck(
    recordMonitorCallback: true,
    requireMonitorActive: true,
    scheduleNextWhenDone: true,
    source: '백그라운드 감시',
  );
}

class BackgroundMonitorService {
  static const int monitorAlarmId = 9004;
  static const int defaultIntervalSeconds = 60;
  static const int entryWatchIntervalSeconds = 15;
  static const int nearWatchIntervalSeconds = 30;
  static const int farWatchIntervalSeconds = 120;
  static const double entryWatchNearMeters = 150;
  static const double farWatchDistanceMeters = 500;

  static Future<bool> runPositionCheck({
    bool recordMonitorCallback = false,
    bool requireMonitorActive = true,
    bool scheduleNextWhenDone = false,
    String source = '백그라운드 감시',
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    if (scheduleNextWhenDone && (prefs.getBool('monitor_resetting') ?? false)) {
      LogFileService.log('[NH알리미] $source 종료 — 모니터링 리셋 진행 중');
      return false;
    }

    if (recordMonitorCallback) {
      final nowMs = DateTime.now().millisecondsSinceEpoch;
      final scheduledMs = prefs.getInt('last_monitor_scheduled_ms') ?? 0;
      final dueMs = prefs.getInt('last_monitor_due_ms') ?? 0;
      final scheduledDelaySec = prefs.getInt('last_monitor_delay_sec') ?? 0;

      await prefs.setInt(
        'last_monitor_callback_ms',
        nowMs,
      );

      if (scheduledMs > 0 && dueMs > 0 && scheduledDelaySec > 0) {
        final actualDelaySec = ((nowMs - scheduledMs) / 1000).round();
        final delayedBySec = ((nowMs - dueMs) / 1000).round();
        if (delayedBySec > 10) {
          final scheduledDelayText = scheduledDelaySec.toString();
          final actualDelayText = actualDelaySec.toString();
          final delayedByText = delayedBySec.toString();
          LogFileService.log(
            '[NH알리미] $source 실행 지연 — 예정:$scheduledDelayText초, '
            '실제:$actualDelayText초, 지연:+$delayedByText초, '
            '추정:Android 백그라운드/절전 정책으로 알람 실행 지연 가능',
          );
        }
      }
    }

    if (requireMonitorActive && !(prefs.getBool('monitor_active') ?? false)) {
      await AndroidAlarmManager.cancel(monitorAlarmId);
      LogFileService.log('[NH알리미] $source 종료 — monitor_active=false');
      return false;
    }

    if (prefs.getBool('is_paused') ?? false) {
      await BackgroundMonitorService.stop();
      await NotificationService().initialize();
      await NotificationService().stopReminder();
      LogFileService.log('[NH알리미] $source 종료 — 일시정지 상태');
      return false;
    }

    final lat = prefs.getDouble('geofence_lat') ?? 37.56600;
    final lng = prefs.getDouble('geofence_lng') ?? 126.96730;
    final radius = prefs.getDouble('geofence_radius') ?? 30.0;
    var allowNotificationRefresh = true;
    var nextDelaySeconds = defaultIntervalSeconds;

    try {
      final dismissedUntilExit = prefs.getBool('dismissed_until_exit') ?? false;
      final notifActive = prefs.getBool('notif_active') ?? false;
      final judgment = await _getJudgmentForMonitor(
        notifActive: notifActive,
        centerLat: lat,
        centerLng: lng,
        radius: radius,
      );
      await prefs.setInt(
          'last_location_ok_ms', DateTime.now().millisecondsSinceEpoch);

      if (judgment.zone == LocationZone.reliableInside) {
        await prefs.setInt('monitor_outside_count', 0);
        LogFileService.log(
          '[NH알리미] $source — 범위 안 '
          '(${judgment.decisionText})',
        );

        if (!dismissedUntilExit && !notifActive) {
          final intervalSec = prefs.getInt('repeat_interval_sec') ?? 60;
          await NotificationService().initialize();
          await NotificationService()
              .startReminder(intervalSeconds: intervalSec);
          LogFileService.log('[NH알리미] $source — 알림 시작 ($intervalSec초 간격)');
        }
      } else if (judgment.zone == LocationZone.unreliableInside) {
        await prefs.setInt('monitor_outside_count', 0);
        if (!notifActive) {
          nextDelaySeconds = nearWatchIntervalSeconds;
          allowNotificationRefresh = false;
        }
        LogFileService.log(
          '[NH알리미] $source — 범위 안 보류 '
          '(${judgment.decisionText})',
        );
      } else if (judgment.isOutside) {
        final outsideCount = (prefs.getInt('monitor_outside_count') ?? 0) + 1;
        allowNotificationRefresh = false;
        if (!notifActive) {
          nextDelaySeconds = _delayForOutsideDistance(
            distance: judgment.distance,
            radius: radius,
          );
        }

        if (dismissedUntilExit &&
            !LocationJudgmentService.isConfirmedExitAfterDismissal(judgment)) {
          await prefs.setInt('monitor_outside_count', 0);
          LogFileService.log(
            '[NH알리미] $source — 출퇴근 확인 차단 유지 '
            '(${judgment.outsideText}, 확정이탈 기준 '
            '${LocationJudgmentService.confirmedExitThreshold(radius).toStringAsFixed(0)}m)',
          );
          if (nextDelaySeconds < defaultIntervalSeconds) {
            nextDelaySeconds = defaultIntervalSeconds;
          }
        } else {
          await prefs.setInt('monitor_outside_count', outsideCount);

          if (outsideCount >= 2) {
            await prefs.setBool('dismissed_until_exit', false);
            await prefs.setInt('monitor_outside_count', 0);
            if (notifActive) {
              await NotificationService().initialize();
              await NotificationService().stopReminder();
            }
            LogFileService.log(
              '[NH알리미] $source — 범위 밖 2회 확인 '
              '(${judgment.outsideText}), '
              '알림 중지/차단 해제',
            );
          } else {
            LogFileService.log(
              '[NH알리미] $source — 범위 밖 1회 유예 '
              '(${judgment.outsideText})',
            );
          }
        }
      } else {
        await prefs.setInt('monitor_outside_count', 0);
        if (!notifActive) {
          nextDelaySeconds = _delayForOutsideDistance(
            distance: judgment.distance,
            radius: radius,
          );
        }
        LogFileService.log(
          '[NH알리미] $source — 경계 흔들림 '
          '(${judgment.outsideText})',
        );
      }
    } catch (e) {
      allowNotificationRefresh = false;
      LogFileService.log('[NH알리미] $source 위치 확인 실패: $e');
    }

    if (scheduleNextWhenDone) {
      await prefs.reload();
      final stillActive = prefs.getBool('monitor_active') ?? false;
      final stillPaused = prefs.getBool('is_paused') ?? false;
      if (stillActive && !stillPaused) {
        await scheduleNext(delaySeconds: nextDelaySeconds);
      } else {
        LogFileService.log(
          '[NH알리미] $source 다음 예약 생략 — '
          'active:$stillActive, paused:$stillPaused',
        );
      }
    }
    return allowNotificationRefresh;
  }

  static Future<LocationJudgment> _getJudgmentForMonitor({
    required bool notifActive,
    required double centerLat,
    required double centerLng,
    required double radius,
  }) {
    return LocationJudgmentService.fromCurrentPosition(
      centerLat: centerLat,
      centerLng: centerLng,
      radius: radius,
      desiredAccuracy:
          notifActive ? geo.LocationAccuracy.medium : geo.LocationAccuracy.high,
      timeout: Duration(seconds: notifActive ? 15 : 25),
    );
  }

  static int _delayForOutsideDistance({
    required double distance,
    required double radius,
  }) {
    final outsideDistance = distance - radius;
    if (outsideDistance <= 30) {
      return entryWatchIntervalSeconds;
    }
    if (outsideDistance <= entryWatchNearMeters) {
      return nearWatchIntervalSeconds;
    }
    if (outsideDistance <= farWatchDistanceMeters) {
      return defaultIntervalSeconds;
    }
    return farWatchIntervalSeconds;
  }

  static Future<bool> verifyBeforeNotificationRefresh() {
    return runPositionCheck(
      recordMonitorCallback: false,
      requireMonitorActive: false,
      scheduleNextWhenDone: false,
      source: '리프레시 전 위치 확인',
    );
  }

  static Future<void> start({int initialDelaySeconds = 5}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('monitor_active', true);
    await prefs.setInt('monitor_outside_count', 0);
    await scheduleNext(delaySeconds: initialDelaySeconds);
    LogFileService.log('[NH알리미] 백그라운드 감시 시작 — $initialDelaySeconds초 후 첫 확인');
  }

  static Future<void> stop() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('monitor_active', false);
    await prefs.setInt('monitor_outside_count', 0);
    await AndroidAlarmManager.cancel(monitorAlarmId);
    LogFileService.log('[NH알리미] 백그라운드 감시 중지');
  }

  static Future<void> scheduleNext(
      {int delaySeconds = defaultIntervalSeconds}) async {
    final prefs = await SharedPreferences.getInstance();
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    await prefs.setInt(
      'last_monitor_scheduled_ms',
      nowMs,
    );
    await prefs.setInt(
      'last_monitor_due_ms',
      nowMs + delaySeconds * 1000,
    );
    await prefs.setInt('last_monitor_delay_sec', delaySeconds);
    await AndroidAlarmManager.cancel(monitorAlarmId);
    await AndroidAlarmManager.oneShot(
      Duration(seconds: delaySeconds),
      monitorAlarmId,
      backgroundMonitorCallback,
      exact: true,
      wakeup: true,
      allowWhileIdle: true,
      rescheduleOnReboot: true,
    );
    LogFileService.log('[NH알리미] 다음 백그라운드 감시 예약 → $delaySeconds초 후');
  }

  static Future<void> refreshIfStale() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    if (prefs.getBool('is_paused') ?? false) {
      await stop();
      return;
    }

    final monitorActive = prefs.getBool('monitor_active') ?? false;
    final now = DateTime.now().millisecondsSinceEpoch;
    final lastCallback = prefs.getInt('last_monitor_callback_ms') ?? 0;
    final lastScheduled = prefs.getInt('last_monitor_scheduled_ms') ?? 0;
    final staleCallback =
        lastCallback != 0 && now - lastCallback > 3 * 60 * 1000;
    final staleSchedule =
        lastScheduled == 0 || now - lastScheduled > 2 * 60 * 1000;

    if (!monitorActive || staleCallback || staleSchedule) {
      await start(initialDelaySeconds: 5);
      LogFileService.log(
        '[NH알리미] 백그라운드 감시 리프레시 — '
        'active:$monitorActive, lastCallback:${now - lastCallback}ms, '
        'lastSchedule:${now - lastScheduled}ms',
      );
    }
  }
}
