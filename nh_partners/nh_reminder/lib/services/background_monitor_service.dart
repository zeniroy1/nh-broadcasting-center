import 'dart:ui';
import 'dart:math' as math;

import 'package:android_alarm_manager_plus/android_alarm_manager_plus.dart';
import 'package:geolocator/geolocator.dart' as geo;
import 'package:shared_preferences/shared_preferences.dart';

import 'log_file_service.dart';
import 'notification_service.dart';
import 'location_judgment_service.dart';
import 'arrival_confirmation_service.dart';

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
  static const int dismissedLowPowerIntervalSeconds = 180;
  static const int dismissedStableIntervalSeconds = 300;
  static const int dismissedLastKnownMaxAgeSeconds = 300;
  static const double entryWatchNearMeters = 150;
  static const double farWatchDistanceMeters = 500;
  static const double dismissedNearConfirmedExitMeters = 30;
  static const double dismissedLastKnownMaxAccuracyMeters = 120;
  static const int insidePendingFallbackSeconds = 60;
  static const int insidePendingFallbackCount = 3;
  static const double insidePendingFallbackCoreRatio = 0.85;

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
      final dismissedLowPower = dismissedUntilExit;
      final judgment = await _getJudgmentForMonitor(
        notifActive: notifActive,
        dismissedLowPower: dismissedLowPower,
        centerLat: lat,
        centerLng: lng,
        radius: radius,
      );
      await prefs.setInt(
          'last_location_ok_ms', DateTime.now().millisecondsSinceEpoch);
      await _saveRecentJudgment(prefs, judgment, source);

      if (judgment.zone == LocationZone.reliableInside) {
        await prefs.setInt('monitor_outside_count', 0);
        await _resetInsidePending(prefs);
        if (!dismissedUntilExit && !notifActive) {
          if (!await ArrivalConfirmationService.confirmIfNeeded(
            prefs: prefs,
            judgment: judgment,
            source: source,
          )) {
            nextDelaySeconds = entryWatchIntervalSeconds;
            allowNotificationRefresh = false;
            return _finishPositionCheck(
              prefs: prefs,
              scheduleNextWhenDone: scheduleNextWhenDone,
              nextDelaySeconds: nextDelaySeconds,
              source: source,
              allowNotificationRefresh: allowNotificationRefresh,
            );
          }
        } else {
          await prefs.setInt('arrival_grace_confirm_count', 0);
        }
        LogFileService.log(
          '[NH알리미] $source — 범위 안 '
          '(${judgment.decisionText})',
        );

        if (!dismissedUntilExit && !notifActive) {
          final intervalSec = prefs.getInt('repeat_interval_sec') ??
              NotificationService.defaultRepeatIntervalSeconds;
          await NotificationService().initialize();
          final started = await NotificationService().startReminderOnce(
            source: source,
            intervalSeconds: intervalSec,
          );
          if (started) {
            LogFileService.log('[NH알리미] $source — 알림 시작 ($intervalSec초 간격)');
          }
        } else if (dismissedUntilExit) {
          nextDelaySeconds = _delayForDismissedLowPower(judgment);
          allowNotificationRefresh = false;
          LogFileService.log(
            '[NH알리미] $source — 범위 안이지만 출퇴근 확인 차단 상태라 '
            '알림 시작 안 함, 저전력 감시 $nextDelaySeconds초',
          );
        } else if (notifActive) {
          LogFileService.log(
            '[NH알리미] $source — 범위 안이지만 알림 활성 상태라 새 알림 시작 생략',
          );
        }
      } else if (judgment.zone == LocationZone.unreliableInside) {
        await prefs.setInt('monitor_outside_count', 0);
        await prefs.setInt('arrival_grace_confirm_count', 0);
        var fallbackStarted = false;
        if (dismissedLowPower) {
          await _resetInsidePending(prefs);
          nextDelaySeconds = _delayForDismissedLowPower(judgment);
          allowNotificationRefresh = false;
        } else if (!notifActive) {
          if (await _shouldAllowInsideFallback(prefs, judgment)) {
            final intervalSec = prefs.getInt('repeat_interval_sec') ??
                NotificationService.defaultRepeatIntervalSeconds;
            await NotificationService().initialize();
            fallbackStarted = await NotificationService().startReminderOnce(
              source: '$source fallback',
              intervalSeconds: intervalSec,
            );
            if (fallbackStarted) {
              LogFileService.log(
                '[NH알리미] $source — 범위 안 보류 지속으로 fallback 알림 허용 '
                '(${judgment.decisionText}, $insidePendingFallbackSeconds초 이상 확인)',
              );
            }
          } else {
            nextDelaySeconds = nearWatchIntervalSeconds;
            allowNotificationRefresh = false;
          }
        } else {
          await _resetInsidePending(prefs);
        }
        if (!fallbackStarted) {
          LogFileService.log(
            '[NH알리미] $source — 범위 안 보류 '
            '(${judgment.decisionText})'
            '${dismissedLowPower ? ', 출퇴근 확인 차단 저전력 감시 $nextDelaySeconds초' : ''}',
          );
        }
      } else if (judgment.isOutside) {
        await prefs.setInt('arrival_grace_confirm_count', 0);
        await _resetInsidePending(prefs);
        allowNotificationRefresh = false;

        if (notifActive) {
          final activeExitThreshold =
              LocationJudgmentService.confirmedExitThreshold(radius);
          if (judgment.distance <= activeExitThreshold) {
            await prefs.setInt('monitor_outside_count', 0);
            LogFileService.log(
              '[NH알리미] $source — 범위 밖이지만 알림 활성 보호구간 유지 '
              '(${judgment.outsideText}, 알림중지 기준 '
              '${activeExitThreshold.toStringAsFixed(0)}m)',
            );
          } else {
            final outsideCount =
                (prefs.getInt('monitor_outside_count') ?? 0) + 1;
            await prefs.setInt('monitor_outside_count', outsideCount);
            if (outsideCount >= 2) {
              await prefs.setInt('monitor_outside_count', 0);
              await NotificationService().initialize();
              await NotificationService().stopReminder();
              LogFileService.log(
                '[NH알리미] $source — 알림 활성 확정 이탈 2회 확인 '
                '(${judgment.outsideText}, 알림중지 기준 '
                '${activeExitThreshold.toStringAsFixed(0)}m), 알림 중지',
              );
            } else {
              LogFileService.log(
                '[NH알리미] $source — 알림 활성 이탈 후보 1회 유예 '
                '(${judgment.outsideText}, 알림중지 기준 '
                '${activeExitThreshold.toStringAsFixed(0)}m)',
              );
            }
          }
        } else if (dismissedLowPower &&
            !LocationJudgmentService.isConfirmedExitAfterDismissal(judgment)) {
          nextDelaySeconds = _delayForDismissedLowPower(judgment);
          await prefs.setInt('monitor_outside_count', 0);
          LogFileService.log(
            '[NH알리미] $source — 출퇴근 확인 차단 유지 '
            '(${judgment.outsideText}, 차단해제 기준 '
            '${LocationJudgmentService.dismissalResetExitThreshold(radius).toStringAsFixed(0)}m, '
            '저전력 감시 $nextDelaySeconds초)',
          );
        } else {
          nextDelaySeconds = _delayForOutsideDistance(
            distance: judgment.distance,
            radius: radius,
          );
          final outsideCount = (prefs.getInt('monitor_outside_count') ?? 0) + 1;
          await prefs.setInt('monitor_outside_count', outsideCount);

          if (outsideCount >= 2) {
            await prefs.setBool('dismissed_until_exit', false);
            await prefs.setInt('monitor_outside_count', 0);
            LogFileService.log(
              '[NH알리미] $source — 범위 밖 2회 확인 '
              '(${judgment.outsideText}), '
              '차단 해제',
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
        var bridgedArrival = false;
        if (!dismissedLowPower &&
            !notifActive &&
            judgment.isArrivalGraceInside) {
          bridgedArrival = await ArrivalConfirmationService.confirmIfNeeded(
            prefs: prefs,
            judgment: judgment,
            source: source,
          );
        } else {
          await prefs.setInt('arrival_grace_confirm_count', 0);
        }
        if (bridgedArrival) {
          final intervalSec = prefs.getInt('repeat_interval_sec') ??
              NotificationService.defaultRepeatIntervalSeconds;
          await _resetInsidePending(prefs);
          await NotificationService().initialize();
          final started = await NotificationService().startReminderOnce(
            source: '$source 도착 후보',
            intervalSeconds: intervalSec,
          );
          if (started) {
            LogFileService.log(
              '[NH알리미] $source — 도착 후보 GPS 튐 보정으로 알림 시작 '
              '($intervalSec초 간격)',
            );
          }
        } else {
          await _resetInsidePending(prefs);
        }
        if (dismissedLowPower) {
          nextDelaySeconds = _delayForDismissedLowPower(judgment);
        } else if (!notifActive) {
          nextDelaySeconds = _delayForOutsideDistance(
            distance: judgment.distance,
            radius: radius,
          );
        }
        if (!bridgedArrival) {
          LogFileService.log(
            '[NH알리미] $source — 경계 흔들림 '
            '(${judgment.outsideText})'
            '${dismissedLowPower ? ', 출퇴근 확인 차단 저전력 감시 $nextDelaySeconds초' : ''}',
          );
        }
      }
    } catch (e) {
      allowNotificationRefresh = false;
      LogFileService.log('[NH알리미] $source 위치 확인 실패: $e');
    }

    return _finishPositionCheck(
      prefs: prefs,
      scheduleNextWhenDone: scheduleNextWhenDone,
      nextDelaySeconds: nextDelaySeconds,
      source: source,
      allowNotificationRefresh: allowNotificationRefresh,
    );
  }

  static Future<bool> _finishPositionCheck({
    required SharedPreferences prefs,
    required bool scheduleNextWhenDone,
    required int nextDelaySeconds,
    required String source,
    required bool allowNotificationRefresh,
  }) async {
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

  static Future<bool> _shouldAllowInsideFallback(
    SharedPreferences prefs,
    LocationJudgment judgment,
  ) async {
    final now = DateTime.now().millisecondsSinceEpoch;
    final firstMs = prefs.getInt('inside_pending_since_ms') ?? now;
    final count = (prefs.getInt('inside_pending_count') ?? 0) + 1;
    final bestDistance = math.min(
      prefs.getDouble('inside_pending_best_distance_m') ?? judgment.distance,
      judgment.distance,
    );

    await prefs.setInt('inside_pending_since_ms', firstMs);
    await prefs.setInt('inside_pending_count', count);
    await prefs.setDouble('inside_pending_best_distance_m', bestDistance);

    final elapsedSeconds = ((now - firstMs) / 1000).floor();
    final fallbackCoreDistance =
        judgment.radius * insidePendingFallbackCoreRatio;
    final closeEnough = bestDistance <= fallbackCoreDistance;
    final stableEnough = count >= insidePendingFallbackCount;

    return elapsedSeconds >= insidePendingFallbackSeconds &&
        (closeEnough || stableEnough);
  }

  static Future<void> _resetInsidePending(SharedPreferences prefs) async {
    await prefs.remove('inside_pending_since_ms');
    await prefs.remove('inside_pending_count');
    await prefs.remove('inside_pending_best_distance_m');
  }

  static Future<void> _saveRecentJudgment(
    SharedPreferences prefs,
    LocationJudgment judgment,
    String source,
  ) async {
    await prefs.setString('last_location_zone', judgment.zone.name);
    await prefs.setString('last_location_source', source);
    await prefs.setInt(
      'last_location_judgment_ms',
      DateTime.now().millisecondsSinceEpoch,
    );
    await prefs.setDouble('last_location_distance_m', judgment.distance);
    await prefs.setDouble('last_location_accuracy_m', judgment.accuracy);
    await prefs.setDouble('last_location_radius_m', judgment.radius);
  }

  static Future<LocationJudgment> _getJudgmentForMonitor({
    required bool notifActive,
    required bool dismissedLowPower,
    required double centerLat,
    required double centerLng,
    required double radius,
  }) async {
    if (dismissedLowPower) {
      final lastKnownJudgment = await _judgmentFromLastKnownForDismissed(
        centerLat: centerLat,
        centerLng: centerLng,
        radius: radius,
      );
      if (lastKnownJudgment != null) {
        return lastKnownJudgment;
      }
    }

    return LocationJudgmentService.fromCurrentPosition(
      centerLat: centerLat,
      centerLng: centerLng,
      radius: radius,
      desiredAccuracy: (notifActive || dismissedLowPower)
          ? geo.LocationAccuracy.medium
          : geo.LocationAccuracy.high,
      timeout: Duration(seconds: (notifActive || dismissedLowPower) ? 15 : 25),
    );
  }

  static Future<LocationJudgment?> _judgmentFromLastKnownForDismissed({
    required double centerLat,
    required double centerLng,
    required double radius,
  }) async {
    final position = await geo.Geolocator.getLastKnownPosition();
    if (position == null) {
      return null;
    }

    final age = DateTime.now().difference(position.timestamp);
    if (age.inSeconds < 0 || age.inSeconds > dismissedLastKnownMaxAgeSeconds) {
      return null;
    }
    if (position.accuracy > dismissedLastKnownMaxAccuracyMeters) {
      return null;
    }

    final distance = geo.Geolocator.distanceBetween(
      position.latitude,
      position.longitude,
      centerLat,
      centerLng,
    );
    final judgment = LocationJudgmentService.judge(
      distance: distance,
      radius: radius,
      accuracy: position.accuracy,
    );
    final dismissalResetThreshold =
        LocationJudgmentService.dismissalResetExitThreshold(radius);
    final distanceToDismissalReset =
        dismissalResetThreshold - judgment.distance;
    if (distanceToDismissalReset <= dismissedNearConfirmedExitMeters) {
      return null;
    }

    LogFileService.log(
      '[NH알리미] 백그라운드 감시 저전력 위치 — lastKnown 사용 '
      '(age:${age.inSeconds}초, ${judgment.decisionText})',
    );
    return judgment;
  }

  static int _delayForDismissedLowPower(LocationJudgment judgment) {
    final dismissalResetThreshold =
        LocationJudgmentService.dismissalResetExitThreshold(judgment.radius);
    final distanceToDismissalReset =
        dismissalResetThreshold - judgment.distance;
    if (distanceToDismissalReset <= dismissedNearConfirmedExitMeters) {
      return dismissedLowPowerIntervalSeconds;
    }
    return dismissedStableIntervalSeconds;
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
    await prefs.setInt('arrival_grace_confirm_count', 0);
    await scheduleNext(delaySeconds: initialDelaySeconds);
    LogFileService.log('[NH알리미] 백그라운드 감시 시작 — $initialDelaySeconds초 후 첫 확인');
  }

  static Future<void> stop() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('monitor_active', false);
    await prefs.setInt('monitor_outside_count', 0);
    await prefs.setInt('arrival_grace_confirm_count', 0);
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
    final lastDelaySec =
        prefs.getInt('last_monitor_delay_sec') ?? defaultIntervalSeconds;
    final scheduleStaleMs = ((lastDelaySec * 2) + 60) * 1000;
    final callbackStaleMs = ((lastDelaySec * 2) + 180) * 1000;
    final staleCallback =
        lastCallback != 0 && now - lastCallback > callbackStaleMs;
    final staleSchedule =
        lastScheduled == 0 || now - lastScheduled > scheduleStaleMs;
    final dismissedLowPower = prefs.getBool('dismissed_until_exit') ?? false;
    if (monitorActive &&
        dismissedLowPower &&
        staleCallback &&
        !staleSchedule &&
        lastScheduled > 0) {
      LogFileService.log(
        '[NH알리미] 백그라운드 감시 리프레시 생략 — '
        '출퇴근 확인 차단 저전력 예약 유지, '
        'lastCallback:${now - lastCallback}ms, '
        'lastSchedule:${now - lastScheduled}ms, lastDelay:${lastDelaySec}s',
      );
      return;
    }

    if (!monitorActive || staleCallback || staleSchedule) {
      await start(initialDelaySeconds: 5);
      LogFileService.log(
        '[NH알리미] 백그라운드 감시 리프레시 — '
        'active:$monitorActive, lastCallback:${now - lastCallback}ms, '
        'lastSchedule:${now - lastScheduled}ms, lastDelay:${lastDelaySec}s',
      );
    }
  }
}
