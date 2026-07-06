import 'dart:convert';
import 'dart:io';
import 'dart:ui';

import 'package:android_alarm_manager_plus/android_alarm_manager_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart' as geo;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/app_state.dart';
import 'location_judgment_service.dart';
import 'log_file_service.dart';
import 'notification_service.dart';

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

enum ProximityFreshAction {
  none,
  startCycle,
  recheck,
  consumeShared,
}

class _MonitorLocationResult {
  const _MonitorLocationResult({
    required this.judgment,
    this.verifiedByFreshCycle = false,
  });

  final LocationJudgment judgment;
  final bool verifiedByFreshCycle;
}

class _SharedProximityFreshPayload {
  const _SharedProximityFreshPayload({
    required this.verifiedAtMs,
    required this.distanceMm,
    required this.accuracyMm,
    required this.source,
    required this.configGeneration,
  });

  final int verifiedAtMs;
  final int distanceMm;
  final int accuracyMm;
  final String source;
  final int configGeneration;
}

class BackgroundMonitorService {
  static const int monitorAlarmId = 9004;
  static const int defaultIntervalSeconds = 120;
  static const int pendingTriggerIntervalSeconds = 120;
  static const int approachTriggerIntervalSeconds = 60;
  static const int proximityFreshRecheckIntervalSeconds = 30;
  static const int proximityFreshCooldownSeconds = 3 * 60;
  static const int proximityFreshTimeoutSeconds = 12;
  static const int proximityFreshRecheckLimit = 2;
  static const double proximityFreshTriggerDistanceMeters = 300;
  static const int proximityFreshCycleMaxSeconds = 2 * 60;
  static const int proximityFreshSharedResultMaxAgeSeconds = 45;
  static const String _proximityFreshCycleLockFileName =
      'nh_proximity_fresh_cycle.lock';
  static const int notificationActiveLowPowerIntervalSeconds = 300;
  static const int notificationActiveLastKnownMaxAgeSeconds = 300;
  static const double notificationActiveLastKnownMaxAccuracyMeters = 150;
  static const int inactiveLastKnownMaxAgeSeconds = 180;
  static const double inactiveLastKnownMaxAccuracyMeters = 150;
  static const int dismissedStableIntervalSeconds = 300;
  static const int dismissedOutsideIntervalSeconds = 300;
  static const int dismissedLastKnownMaxAgeSeconds = 300;
  static const double dismissedExitThresholdMeters = 100;
  static const double dismissedLastKnownMaxAccuracyMeters = 120;
  static const double approachBandMaxMeters = 80;
  static const int staleScheduleGraceSeconds = 90;
  static const int diagnosticSummaryIntervalSeconds = 15 * 60;
  static const String _diagStartedMsKey = 'monitor_diag_started_ms';
  static const String _diagLastSummaryMsKey = 'monitor_diag_last_summary_ms';
  static const String _diagCheckCountKey = 'monitor_diag_check_count';
  static const String _diagPositionRequestCountKey =
      'monitor_diag_position_request_count';
  static const String _diagLastKnownCountKey = 'monitor_diag_last_known_count';
  static const String _diagProximityFreshCountKey =
      'monitor_diag_proximity_fresh_count';
  static const String _diagFailureCountKey = 'monitor_diag_failure_count';
  static const String _diagDelayedCallbackCountKey =
      'monitor_diag_delayed_callback_count';
  static const String _diagMinDelaySecKey = 'monitor_diag_min_delay_sec';
  static const String _diagMaxDelaySecKey = 'monitor_diag_max_delay_sec';
  static const String _diagLastDelaySecKey = 'monitor_diag_last_delay_sec';
  static const String _approachPendingActiveKey = 'approach_pending_active';
  static const String _approachPendingAtMsKey = 'approach_pending_at_ms';
  static const String _approachPendingDistanceKey =
      'approach_pending_distance_m';
  static const String _approachPendingAccuracyKey =
      'approach_pending_accuracy_m';
  static const String _proximityFreshLastRequestMsKey =
      'proximity_fresh_last_request_ms';
  static const String _proximityFreshCycleActiveKey =
      'proximity_fresh_cycle_active';
  static const String _proximityFreshCycleOwnerKey =
      'proximity_fresh_cycle_owner';
  static const String _proximityFreshCycleIdKey = 'proximity_fresh_cycle_id';
  static const String _proximityFreshCycleStartedMsKey =
      'proximity_fresh_cycle_started_ms';
  static const String _proximityFreshCycleFinishedMsKey =
      'proximity_fresh_cycle_finished_ms';
  static const String _proximityFreshRechecksRemainingKey =
      'proximity_fresh_rechecks_remaining';
  static const String _proximityFreshVerifiedAtMsKey =
      'proximity_fresh_verified_at_ms';
  static const String _proximityFreshVerifiedDistanceMmKey =
      'proximity_fresh_verified_distance_mm';
  static const String _proximityFreshVerifiedAccuracyMmKey =
      'proximity_fresh_verified_accuracy_mm';
  static const String _proximityFreshVerifiedSourceKey =
      'proximity_fresh_verified_source';
  static const String _proximityFreshVerifiedPayloadKey =
      'proximity_fresh_verified_payload';
  static const String _proximityFreshOwnerFlutter = 'flutter';
  static const String geofenceConfigGenerationKey =
      'geofence_config_generation';
  static const String geofenceConfigUpdateStartedMsKey =
      'geofence_config_update_started_ms';
  static const int geofenceConfigUpdateStaleSeconds = 10;
  static File? _proximityFreshCycleLockFileOverrideForTesting;

  static Future<bool> runPositionCheck({
    bool recordMonitorCallback = false,
    bool requireMonitorActive = true,
    bool scheduleNextWhenDone = false,
    String source = '백그라운드 감시',
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    await recoverStaleGeofenceConfigUpdate(prefs);
    await _ensureDiagnosticWindow(prefs);
    await _incrementDiagnosticCounter(prefs, _diagCheckCountKey);
    if (scheduleNextWhenDone && (prefs.getBool('monitor_resetting') ?? false)) {
      LogFileService.log('[NH알리미] $source 종료 — 모니터링 리셋 진행 중');
      return false;
    }

    if (recordMonitorCallback) {
      final nowMs = DateTime.now().millisecondsSinceEpoch;
      final scheduledMs = prefs.getInt('last_monitor_scheduled_ms') ?? 0;
      final dueMs = prefs.getInt('last_monitor_due_ms') ?? 0;
      final scheduledDelaySec = prefs.getInt('last_monitor_delay_sec') ?? 0;

      await prefs.setInt('last_monitor_callback_ms', nowMs);

      if (scheduledMs > 0 && dueMs > 0 && scheduledDelaySec > 0) {
        final actualDelaySec = ((nowMs - scheduledMs) / 1000).round();
        final delayedBySec = ((nowMs - dueMs) / 1000).round();
        if (delayedBySec > 10) {
          await _incrementDiagnosticCounter(
            prefs,
            _diagDelayedCallbackCountKey,
          );
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

    final lat =
        prefs.getDouble('geofence_lat') ?? AppSettings.defaultGeofenceLat;
    final lng =
        prefs.getDouble('geofence_lng') ?? AppSettings.defaultGeofenceLng;
    final radius = AppSettings.clampGeofenceRadius(
      prefs.getDouble('geofence_radius') ?? AppSettings.defaultGeofenceRadius,
    );
    final configGeneration = currentGeofenceConfigGeneration(prefs);
    var allowNotificationRefresh = true;
    var nextDelaySeconds = defaultIntervalSeconds;

    try {
      var dismissedUntilExit = prefs.getBool('dismissed_until_exit') ?? false;
      var notifActive = prefs.getBool('notif_active') ?? false;
      final inactiveLowPower = _isInactiveExecutionMode(prefs);
      final locationResult = await _getJudgmentForMonitor(
        prefs: prefs,
        notifActive: notifActive,
        dismissedLowPower: dismissedUntilExit,
        inactiveLowPower: inactiveLowPower,
        centerLat: lat,
        centerLng: lng,
        radius: radius,
      );
      await prefs.reload();
      final monitorActive = prefs.getBool('monitor_active') ?? false;
      final paused = prefs.getBool('is_paused') ?? false;
      dismissedUntilExit = prefs.getBool('dismissed_until_exit') ?? false;
      notifActive = prefs.getBool('notif_active') ?? false;
      final currentConfigGeneration = currentGeofenceConfigGeneration(prefs);
      if (!shouldContinueAfterLocationRequest(
        monitorActive: monitorActive,
        requireMonitorActive: requireMonitorActive,
        isPaused: paused,
        expectedConfigGeneration: configGeneration,
        currentConfigGeneration: currentConfigGeneration,
      )) {
        LogFileService.log(
          '[NH알리미] $source 위치 응답 폐기 — '
          'active:$monitorActive, paused:$paused, '
          'dismissed:$dismissedUntilExit, '
          'config:$configGeneration->$currentConfigGeneration',
        );
        if (scheduleNextWhenDone) {
          await _scheduleNextIfStillActive(
            prefs,
            source: source,
            delaySeconds: nextDelaySeconds,
          );
        }
        await _maybeLogDiagnosticSummary(prefs);
        return false;
      }
      final judgment = locationResult.judgment;
      await prefs.setInt(
        'last_location_ok_ms',
        DateTime.now().millisecondsSinceEpoch,
      );
      final nowMs = DateTime.now().millisecondsSinceEpoch;
      await _refreshApproachPendingState(
        prefs: prefs,
        judgment: judgment,
        nowMs: nowMs,
        blocked: dismissedUntilExit || notifActive,
        source: source,
      );

      final initialAlertCandidate = !dismissedUntilExit &&
          !notifActive &&
          shouldAllowInitialAlertCandidate(
            judgment: judgment,
            verifiedByFreshCycle: locationResult.verifiedByFreshCycle,
          );
      if (!initialAlertCandidate &&
          judgment.isInitialAlertCandidate &&
          !judgment.isStrongInitialAlertCandidate) {
        LogFileService.log(
          '[NH알리미] $source — 약한 초기 알림 후보 보류 '
          '(${judgment.initialAlertText}, 검증된 fresh 위치 필요)',
        );
      }

      if (judgment.zone == LocationZone.reliableInside ||
          initialAlertCandidate) {
        await prefs.setInt('monitor_outside_count', 0);
        if (judgment.zone == LocationZone.reliableInside) {
          LogFileService.log(
            '[NH알리미] $source — 범위 안 '
            '(${judgment.decisionText})',
          );
        } else {
          LogFileService.log(
            '[NH알리미] $source — 초기 알림 후보 통과 '
            '(${judgment.initialAlertText}, zone:${judgment.zoneLabel})',
          );
        }

        if (!dismissedUntilExit && !notifActive) {
          await clearApproachPendingState(prefs);
          await _finishProximityFreshCycle(
            prefs,
            DateTime.now().millisecondsSinceEpoch,
          );
          final intervalSec = prefs.getInt('repeat_interval_sec') ??
              NotificationService.defaultRepeatIntervalSeconds;
          await NotificationService().initialize();
          await NotificationService().startReminder(
            intervalSeconds: intervalSec,
          );
          nextDelaySeconds = notificationActiveLowPowerIntervalSeconds;
          allowNotificationRefresh = false;
          LogFileService.log('[NH알리미] $source — 알림 시작 ($intervalSec초 간격)');
          _logNotificationActiveLocationBackoff(
            source: source,
            delaySeconds: nextDelaySeconds,
            reason: '범위 안 감지 후 반복 알림 시작',
          );
        } else if (dismissedUntilExit) {
          nextDelaySeconds = _delayForDismissedLowPower(judgment);
          allowNotificationRefresh = false;
          LogFileService.log(
            '[NH알리미] $source — 범위 안이지만 출퇴근 확인 차단 상태라 '
            '알림 시작 안 함, 저전력 감시 $nextDelaySeconds초',
          );
        } else if (notifActive) {
          nextDelaySeconds = notificationActiveLowPowerIntervalSeconds;
          allowNotificationRefresh = false;
          _logNotificationActiveLocationBackoff(
            source: source,
            delaySeconds: nextDelaySeconds,
            reason: '범위 안, 반복 알림 유지 중',
          );
        }
      } else if (judgment.zone == LocationZone.unreliableInside) {
        await prefs.setInt('monitor_outside_count', 0);
        if (dismissedUntilExit) {
          nextDelaySeconds = _delayForDismissedLowPower(judgment);
          allowNotificationRefresh = false;
        } else if (notifActive) {
          nextDelaySeconds = notificationActiveLowPowerIntervalSeconds;
          allowNotificationRefresh = false;
          _logNotificationActiveLocationBackoff(
            source: source,
            delaySeconds: nextDelaySeconds,
            reason: '범위 안 보류, 반복 알림 유지 중',
          );
        } else {
          nextDelaySeconds = await _delayForPendingEntry(prefs, judgment);
          allowNotificationRefresh = false;
        }
        LogFileService.log(
          '[NH알리미] $source — 범위 안 보류 '
          '(${judgment.decisionText})'
          '${_lowPowerSuffix(
            dismissedUntilExit: dismissedUntilExit,
            inactiveLowPower: inactiveLowPower && !notifActive,
            delaySeconds: nextDelaySeconds,
          )}',
        );
      } else if (judgment.isOutside) {
        if (dismissedUntilExit) {
          allowNotificationRefresh = false;
          nextDelaySeconds = dismissedOutsideIntervalSeconds;
        } else if (notifActive) {
          await prefs.setInt('monitor_outside_count', 0);
          LogFileService.log(
            '[NH알리미] $source — 범위 밖 감지지만 초기 진입 알림 유지 '
            '(${judgment.outsideText})',
          );
          nextDelaySeconds = notificationActiveLowPowerIntervalSeconds;
          allowNotificationRefresh = false;
          _logNotificationActiveLocationBackoff(
            source: source,
            delaySeconds: nextDelaySeconds,
            reason: '범위 밖 감지, 반복 알림 유지 중',
          );
        } else {
          allowNotificationRefresh = false;
          nextDelaySeconds = await _delayForPendingEntry(prefs, judgment);
        }

        if (dismissedUntilExit && !notifActive) {
          if (judgment.distance > dismissedExitThresholdMeters) {
            await prefs.setBool('dismissed_until_exit', false);
            await prefs.setInt('monitor_outside_count', 0);
            LogFileService.log(
              '[NH알리미] $source — 출퇴근 확인 차단 해제 '
              '(${judgment.outsideText}, 차단 해제 기준 '
              '${dismissedExitThresholdMeters.toStringAsFixed(0)}m 초과)',
            );
          } else {
            await prefs.setInt('monitor_outside_count', 0);
            LogFileService.log(
              '[NH알리미] $source — 출퇴근 확인 차단 유지 '
              '(${judgment.outsideText}, 차단 해제 기준 '
              '${dismissedExitThresholdMeters.toStringAsFixed(0)}m 초과, '
              '저전력 감시 $nextDelaySeconds초)',
            );
          }
        } else if (!notifActive) {
          await prefs.setInt('monitor_outside_count', 0);
          LogFileService.log(
            '[NH알리미] $source — 범위 밖, ENTER 대기 '
            '(${judgment.outsideText})'
            '${inactiveLowPower ? ', 화면꺼짐 저전력 감시 $nextDelaySeconds초' : ''}',
          );
        }
      } else {
        await prefs.setInt('monitor_outside_count', 0);
        if (dismissedUntilExit) {
          nextDelaySeconds = _delayForDismissedLowPower(judgment);
        } else if (notifActive) {
          nextDelaySeconds = notificationActiveLowPowerIntervalSeconds;
          allowNotificationRefresh = false;
          _logNotificationActiveLocationBackoff(
            source: source,
            delaySeconds: nextDelaySeconds,
            reason: '경계 흔들림, 반복 알림 유지 중',
          );
        } else {
          nextDelaySeconds = await _delayForPendingEntry(prefs, judgment);
        }
        LogFileService.log(
          '[NH알리미] $source — 경계 흔들림 '
          '(${judgment.outsideText})'
          '${_lowPowerSuffix(
            dismissedUntilExit: dismissedUntilExit,
            inactiveLowPower: inactiveLowPower && !notifActive,
            delaySeconds: nextDelaySeconds,
          )}',
        );
      }
    } catch (e) {
      allowNotificationRefresh = false;
      await _incrementDiagnosticCounter(prefs, _diagFailureCountKey);
      final notifActive = prefs.getBool('notif_active') ?? false;
      if (notifActive) {
        nextDelaySeconds = notificationActiveLowPowerIntervalSeconds;
        _logNotificationActiveLocationBackoff(
          source: source,
          delaySeconds: nextDelaySeconds,
          reason: '위치 확인 실패/timeout, 반복 알림 유지 중',
        );
      }
      LogFileService.log('[NH알리미] $source 위치 확인 실패: $e');
    }

    if (scheduleNextWhenDone) {
      await _scheduleNextIfStillActive(
        prefs,
        source: source,
        delaySeconds: nextDelaySeconds,
      );
    }
    await _maybeLogDiagnosticSummary(prefs);
    return allowNotificationRefresh;
  }

  static Future<_MonitorLocationResult> _getJudgmentForMonitor({
    required SharedPreferences prefs,
    required bool notifActive,
    required bool dismissedLowPower,
    required bool inactiveLowPower,
    required double centerLat,
    required double centerLng,
    required double radius,
  }) async {
    if (dismissedLowPower || notifActive || inactiveLowPower) {
      final lastKnownJudgment = await _judgmentFromLastKnownForLowPower(
        centerLat: centerLat,
        centerLng: centerLng,
        radius: radius,
        source: _lowPowerLocationSource(
          notifActive: notifActive,
          dismissedLowPower: dismissedLowPower,
          inactiveLowPower: inactiveLowPower,
        ),
        maxAgeSeconds: _lowPowerLastKnownMaxAgeSeconds(
          notifActive: notifActive,
          dismissedLowPower: dismissedLowPower,
        ),
        maxAccuracyMeters: _lowPowerLastKnownMaxAccuracyMeters(
          notifActive: notifActive,
          dismissedLowPower: dismissedLowPower,
        ),
      );
      if (lastKnownJudgment != null) {
        await _incrementDiagnosticCounter(prefs, _diagLastKnownCountKey);
        return _upgradeWithProximityFreshIfNeeded(
          prefs: prefs,
          fallbackResult: _MonitorLocationResult(judgment: lastKnownJudgment),
          notifActive: notifActive,
          dismissedLowPower: dismissedLowPower,
          inactiveLowPower: inactiveLowPower,
          centerLat: centerLat,
          centerLng: centerLng,
          radius: radius,
        );
      }
    }

    await _incrementDiagnosticCounter(prefs, _diagPositionRequestCountKey);
    final mediumJudgment = await LocationJudgmentService.fromCurrentPosition(
      centerLat: centerLat,
      centerLng: centerLng,
      radius: radius,
      desiredAccuracy: geo.LocationAccuracy.medium,
      timeout: const Duration(seconds: 15),
    );
    return _upgradeWithProximityFreshIfNeeded(
      prefs: prefs,
      fallbackResult: _MonitorLocationResult(judgment: mediumJudgment),
      notifActive: notifActive,
      dismissedLowPower: dismissedLowPower,
      inactiveLowPower: inactiveLowPower,
      centerLat: centerLat,
      centerLng: centerLng,
      radius: radius,
    );
  }

  static Future<_MonitorLocationResult> _upgradeWithProximityFreshIfNeeded({
    required SharedPreferences prefs,
    required _MonitorLocationResult fallbackResult,
    required bool notifActive,
    required bool dismissedLowPower,
    required bool inactiveLowPower,
    required double centerLat,
    required double centerLng,
    required double radius,
  }) async {
    final fallbackJudgment = fallbackResult.judgment;
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    final requestConfigGeneration = currentGeofenceConfigGeneration(prefs);
    final action = await _resolveProximityFreshAction(
      prefs: prefs,
      distance: fallbackJudgment.distance,
      notifActive: notifActive,
      dismissedUntilExit: dismissedLowPower,
      inactiveLowPower: inactiveLowPower,
      nowMs: nowMs,
    );
    if (action == ProximityFreshAction.consumeShared) {
      final sharedJudgment = _judgmentFromSharedProximityFresh(prefs, radius);
      return sharedJudgment == null
          ? fallbackResult
          : _MonitorLocationResult(
              judgment: sharedJudgment,
              verifiedByFreshCycle: true,
            );
    }
    if (action != ProximityFreshAction.startCycle &&
        action != ProximityFreshAction.recheck) {
      return fallbackResult;
    }

    await prefs.reload();
    final cycleId = prefs.getInt(_proximityFreshCycleIdKey);
    final ownsSharedCycle = ownsProximityFreshCycle(
      cycleActive: prefs.getBool(_proximityFreshCycleActiveKey) ?? false,
      cycleOwner: prefs.getString(_proximityFreshCycleOwnerKey),
      cycleId: cycleId,
      expectedOwner: _proximityFreshOwnerFlutter,
    );
    final ownsCycleLock = cycleId != null &&
        await _ownsProximityFreshCycleLock(
          owner: _proximityFreshOwnerFlutter,
          cycleId: cycleId,
        );
    if (!ownsSharedCycle || !ownsCycleLock) {
      final sharedJudgment = _judgmentFromSharedProximityFresh(prefs, radius);
      LogFileService.log(
        '[NH알리미] 근접 정밀 측정 양보 — owner 또는 lock 변경 감지, 공유값 재사용',
      );
      return sharedJudgment == null
          ? fallbackResult
          : _MonitorLocationResult(
              judgment: sharedJudgment,
              verifiedByFreshCycle: true,
            );
    }

    await prefs.setInt(_proximityFreshLastRequestMsKey, nowMs);
    await _incrementDiagnosticCounter(prefs, _diagPositionRequestCountKey);
    await _incrementDiagnosticCounter(prefs, _diagProximityFreshCountKey);
    LogFileService.log(
      '[NH알리미] 근접 정밀 측정 요청 — provider:high, '
      'action:${action.name}, '
      '거리:${fallbackJudgment.distance.toStringAsFixed(0)}m, '
      'timeout:$proximityFreshTimeoutSeconds초',
    );
    LogFileService.logImportant('[NH알리미] 근접 위치 재확인 시작');

    try {
      final judgment = await LocationJudgmentService.fromCurrentPosition(
        centerLat: centerLat,
        centerLng: centerLng,
        radius: radius,
        desiredAccuracy: geo.LocationAccuracy.high,
        timeout: const Duration(seconds: proximityFreshTimeoutSeconds),
      );
      final stored = await _storeSharedProximityFreshResult(
        prefs: prefs,
        judgment: judgment,
        source: _proximityFreshOwnerFlutter,
        configGeneration: requestConfigGeneration,
      );
      if (!stored) return fallbackResult;
      LogFileService.log(
        '[NH알리미] 근접 정밀 측정 성공 — provider:high, '
        '거리:${judgment.distance.toStringAsFixed(0)}m, '
        '정확도:${judgment.accuracy.toStringAsFixed(0)}m',
      );
      LogFileService.logImportant('[NH알리미] 근접 위치 재확인 성공');
      return _MonitorLocationResult(
        judgment: judgment,
        verifiedByFreshCycle: true,
      );
    } catch (e) {
      await _incrementDiagnosticCounter(prefs, _diagFailureCountKey);
      LogFileService.log(
        '[NH알리미] 근접 정밀 측정 실패 — provider:high, '
        'fallback:lastKnown 또는 medium 유지, error:$e',
      );
      LogFileService.logImportant(
        '[NH알리미] 근접 위치 재확인 실패 후 medium 대체 측정',
      );
      try {
        await _incrementDiagnosticCounter(prefs, _diagPositionRequestCountKey);
        final judgment = await LocationJudgmentService.fromCurrentPosition(
          centerLat: centerLat,
          centerLng: centerLng,
          radius: radius,
          desiredAccuracy: geo.LocationAccuracy.medium,
          timeout: const Duration(seconds: proximityFreshTimeoutSeconds),
        );
        final stored = await _storeSharedProximityFreshResult(
          prefs: prefs,
          judgment: judgment,
          source: 'flutterMediumFallback',
          configGeneration: requestConfigGeneration,
        );
        if (!stored) return fallbackResult;
        LogFileService.log(
          '[NH알리미] 근접 정밀 측정 fallback 성공 — provider:medium, '
          '거리:${judgment.distance.toStringAsFixed(0)}m, '
          '정확도:${judgment.accuracy.toStringAsFixed(0)}m',
        );
        return _MonitorLocationResult(
          judgment: judgment,
          verifiedByFreshCycle: true,
        );
      } catch (fallbackError) {
        await _incrementDiagnosticCounter(prefs, _diagFailureCountKey);
        LogFileService.log(
          '[NH알리미] 근접 정밀 측정 fallback 실패 — provider:medium, '
          'fallback:lastKnown 또는 기존 medium 유지, error:$fallbackError',
        );
        return fallbackResult;
      }
    }
  }

  static Future<ProximityFreshAction> _resolveProximityFreshAction({
    required SharedPreferences prefs,
    required double distance,
    required bool notifActive,
    required bool dismissedUntilExit,
    required bool inactiveLowPower,
    required int nowMs,
  }) async {
    await prefs.reload();
    if (!isStableGeofenceConfigGeneration(
      currentGeofenceConfigGeneration(prefs),
    )) {
      return ProximityFreshAction.none;
    }
    await _expireProximityFreshCycleIfNeeded(prefs, nowMs);

    if (!inactiveLowPower || notifActive || dismissedUntilExit) {
      if (prefs.getBool(_proximityFreshCycleActiveKey) ?? false) {
        await _finishProximityFreshCycle(prefs, nowMs);
      }
      return ProximityFreshAction.none;
    }

    final active = prefs.getBool(_proximityFreshCycleActiveKey) ?? false;
    final owner = prefs.getString(_proximityFreshCycleOwnerKey);
    final remaining = prefs.getInt(_proximityFreshRechecksRemainingKey) ?? 0;
    if (active) {
      if (distance > proximityFreshTriggerDistanceMeters) {
        await _finishProximityFreshCycle(prefs, nowMs);
        return ProximityFreshAction.none;
      }
      if (shouldRunOwnedProximityFreshRecheck(
        cycleActive: active,
        cycleOwner: owner,
        expectedOwner: _proximityFreshOwnerFlutter,
        rechecksRemaining: remaining,
      )) {
        await prefs.setInt(_proximityFreshRechecksRemainingKey, remaining - 1);
        return ProximityFreshAction.recheck;
      }
      if (_hasRecentSharedProximityFreshResult(prefs)) {
        return ProximityFreshAction.consumeShared;
      }
      return ProximityFreshAction.none;
    }

    if (distance > proximityFreshTriggerDistanceMeters) {
      return ProximityFreshAction.none;
    }

    if (_hasRecentSharedProximityFreshResult(prefs)) {
      return ProximityFreshAction.consumeShared;
    }

    final lastFinishedMs = prefs.getInt(_proximityFreshCycleFinishedMsKey) ?? 0;
    if (!shouldRequestProximityFresh(
      distance: distance,
      notifActive: notifActive,
      dismissedUntilExit: dismissedUntilExit,
      inactiveLowPower: inactiveLowPower,
      nowMs: nowMs,
      lastRequestMs: lastFinishedMs,
    )) {
      return ProximityFreshAction.none;
    }

    final cycleId = DateTime.now().microsecondsSinceEpoch;
    final lockAcquired = await _tryAcquireProximityFreshCycleLock(
      owner: _proximityFreshOwnerFlutter,
      cycleId: cycleId,
    );
    if (!lockAcquired) {
      await prefs.reload();
      return _hasRecentSharedProximityFreshResult(prefs)
          ? ProximityFreshAction.consumeShared
          : ProximityFreshAction.none;
    }

    try {
      await prefs.setBool(_proximityFreshCycleActiveKey, true);
      await prefs.setString(
        _proximityFreshCycleOwnerKey,
        _proximityFreshOwnerFlutter,
      );
      await prefs.setInt(_proximityFreshCycleIdKey, cycleId);
      await prefs.setInt(_proximityFreshCycleStartedMsKey, nowMs);
      await prefs.setInt(
        _proximityFreshRechecksRemainingKey,
        proximityFreshRecheckLimit,
      );
    } catch (_) {
      await _clearProximityFreshCycleLock(
        expectedOwner: _proximityFreshOwnerFlutter,
        expectedCycleId: cycleId,
      );
      rethrow;
    }
    await prefs.reload();
    if (!ownsProximityFreshCycle(
      cycleActive: prefs.getBool(_proximityFreshCycleActiveKey) ?? false,
      cycleOwner: prefs.getString(_proximityFreshCycleOwnerKey),
      cycleId: prefs.getInt(_proximityFreshCycleIdKey),
      expectedOwner: _proximityFreshOwnerFlutter,
      expectedCycleId: cycleId,
    )) {
      await _clearProximityFreshCycleLock(
        expectedOwner: _proximityFreshOwnerFlutter,
        expectedCycleId: cycleId,
      );
      return ProximityFreshAction.none;
    }
    LogFileService.log(
      '[NH알리미] 근접 정밀 검증 사이클 시작 — '
      'owner:$_proximityFreshOwnerFlutter, id:$cycleId, '
      '재확인:$proximityFreshRecheckLimit회',
    );
    return ProximityFreshAction.startCycle;
  }

  static Future<void> _expireProximityFreshCycleIfNeeded(
    SharedPreferences prefs,
    int nowMs,
  ) async {
    if (!(prefs.getBool(_proximityFreshCycleActiveKey) ?? false)) return;
    final startedMs = prefs.getInt(_proximityFreshCycleStartedMsKey) ?? 0;
    if (startedMs <= 0 ||
        nowMs - startedMs > proximityFreshCycleMaxSeconds * 1000) {
      await _finishProximityFreshCycle(prefs, nowMs);
    }
  }

  static Future<bool> _storeSharedProximityFreshResult({
    required SharedPreferences prefs,
    required LocationJudgment judgment,
    required String source,
    required int configGeneration,
  }) async {
    await prefs.reload();
    final currentConfigGenerationValue = currentGeofenceConfigGeneration(prefs);
    if (!shouldAcceptFreshResultForConfig(
      requestConfigGeneration: configGeneration,
      currentConfigGeneration: currentConfigGenerationValue,
    )) {
      LogFileService.log(
        '[NH알리미] 근접 정밀 측정 결과 폐기 — '
        '설정 변경 감지:$configGeneration->$currentConfigGenerationValue',
      );
      return false;
    }
    await prefs.setString(
      _proximityFreshVerifiedPayloadKey,
      encodeSharedProximityFreshPayload(
        verifiedAtMs: DateTime.now().millisecondsSinceEpoch,
        distanceMm: (judgment.distance * 1000).round(),
        accuracyMm: (judgment.accuracy * 1000).round(),
        source: source,
        configGeneration: configGeneration,
      ),
    );
    await prefs.remove(_proximityFreshVerifiedAtMsKey);
    await prefs.remove(_proximityFreshVerifiedDistanceMmKey);
    await prefs.remove(_proximityFreshVerifiedAccuracyMmKey);
    await prefs.remove(_proximityFreshVerifiedSourceKey);
    return true;
  }

  static LocationJudgment? _judgmentFromSharedProximityFresh(
    SharedPreferences prefs,
    double radius,
  ) {
    final payload = _decodeSharedProximityFreshPayload(
      prefs.getString(_proximityFreshVerifiedPayloadKey),
    );
    if (!_isRecentSharedProximityFreshPayload(
      payload,
      expectedConfigGeneration: currentGeofenceConfigGeneration(prefs),
    )) {
      return null;
    }
    return LocationJudgmentService.judge(
      distance: payload!.distanceMm / 1000,
      radius: radius,
      accuracy: payload.accuracyMm / 1000,
    );
  }

  static bool _hasRecentSharedProximityFreshResult(SharedPreferences prefs) {
    return isUsableSharedProximityFreshPayload(
      prefs.getString(_proximityFreshVerifiedPayloadKey),
      expectedConfigGeneration: currentGeofenceConfigGeneration(prefs),
    );
  }

  static String encodeSharedProximityFreshPayload({
    required int verifiedAtMs,
    required int distanceMm,
    required int accuracyMm,
    required String source,
    required int configGeneration,
  }) {
    return jsonEncode(<String, Object>{
      'verifiedAtMs': verifiedAtMs,
      'distanceMm': distanceMm,
      'accuracyMm': accuracyMm,
      'source': source,
      'configGeneration': configGeneration,
    });
  }

  static bool isUsableSharedProximityFreshPayload(
    String? encodedPayload, {
    int? nowMs,
    int? expectedConfigGeneration,
  }) {
    return _isRecentSharedProximityFreshPayload(
      _decodeSharedProximityFreshPayload(encodedPayload),
      nowMs: nowMs,
      expectedConfigGeneration: expectedConfigGeneration,
    );
  }

  static _SharedProximityFreshPayload? _decodeSharedProximityFreshPayload(
    String? encodedPayload,
  ) {
    if (encodedPayload == null || encodedPayload.isEmpty) return null;
    try {
      final decoded = jsonDecode(encodedPayload);
      if (decoded is! Map<String, dynamic>) return null;
      final verifiedAtMs = decoded['verifiedAtMs'];
      final distanceMm = decoded['distanceMm'];
      final accuracyMm = decoded['accuracyMm'];
      final source = decoded['source'];
      final configGeneration = decoded['configGeneration'];
      if (verifiedAtMs is! int ||
          distanceMm is! int ||
          accuracyMm is! int ||
          source is! String ||
          configGeneration is! int ||
          verifiedAtMs <= 0 ||
          distanceMm < 0 ||
          accuracyMm < 0 ||
          !isStableGeofenceConfigGeneration(configGeneration)) {
        return null;
      }
      return _SharedProximityFreshPayload(
        verifiedAtMs: verifiedAtMs,
        distanceMm: distanceMm,
        accuracyMm: accuracyMm,
        source: source,
        configGeneration: configGeneration,
      );
    } catch (_) {
      return null;
    }
  }

  static bool _isRecentSharedProximityFreshPayload(
    _SharedProximityFreshPayload? payload, {
    int? nowMs,
    int? expectedConfigGeneration,
  }) {
    if (payload == null) return false;
    final currentMs = nowMs ?? DateTime.now().millisecondsSinceEpoch;
    return (expectedConfigGeneration == null ||
            payload.configGeneration == expectedConfigGeneration) &&
        currentMs >= payload.verifiedAtMs &&
        currentMs - payload.verifiedAtMs <=
            proximityFreshSharedResultMaxAgeSeconds * 1000;
  }

  static bool shouldRunOwnedProximityFreshRecheck({
    required bool cycleActive,
    required String? cycleOwner,
    required String expectedOwner,
    required int rechecksRemaining,
  }) {
    return cycleActive && cycleOwner == expectedOwner && rechecksRemaining > 0;
  }

  static bool ownsProximityFreshCycle({
    required bool cycleActive,
    required String? cycleOwner,
    required int? cycleId,
    required String expectedOwner,
    int? expectedCycleId,
  }) {
    return cycleActive &&
        cycleOwner == expectedOwner &&
        cycleId != null &&
        (expectedCycleId == null || cycleId == expectedCycleId);
  }

  static String _proximityFreshCycleLockToken({
    required String owner,
    required int cycleId,
  }) {
    return '$owner:$cycleId';
  }

  static Future<File?> _proximityFreshCycleLockFile() async {
    if (_proximityFreshCycleLockFileOverrideForTesting != null) {
      return _proximityFreshCycleLockFileOverrideForTesting;
    }
    try {
      final directory = await getApplicationSupportDirectory();
      return File(
        '${directory.path}${Platform.pathSeparator}'
        '$_proximityFreshCycleLockFileName',
      );
    } catch (e) {
      LogFileService.log(
        '[NH알리미] 근접 정밀 lock 경로 확인 실패 — error:$e',
      );
      return null;
    }
  }

  static Future<bool> _tryAcquireProximityFreshCycleLock({
    required String owner,
    required int cycleId,
  }) async {
    final file = await _proximityFreshCycleLockFile();
    if (file == null) return false;
    return _tryAcquireProximityFreshCycleLockFile(
      file: file,
      owner: owner,
      cycleId: cycleId,
    );
  }

  static Future<bool> _tryAcquireProximityFreshCycleLockFile({
    required File file,
    required String owner,
    required int cycleId,
  }) async {
    await _clearExpiredProximityFreshCycleLock(file);
    try {
      await file.create(exclusive: true);
      await file.writeAsString(
        _proximityFreshCycleLockToken(owner: owner, cycleId: cycleId),
        flush: true,
      );
      return true;
    } on FileSystemException {
      return false;
    } catch (e) {
      LogFileService.log(
        '[NH알리미] 근접 정밀 lock 확보 실패 — error:$e',
      );
      await _deleteProximityFreshCycleLockFile(file);
      return false;
    }
  }

  static Future<bool> _ownsProximityFreshCycleLock({
    required String owner,
    required int cycleId,
  }) async {
    final file = await _proximityFreshCycleLockFile();
    if (file == null || !await file.exists()) return false;
    try {
      final token = await file.readAsString();
      return token.trim() ==
          _proximityFreshCycleLockToken(owner: owner, cycleId: cycleId);
    } catch (_) {
      return false;
    }
  }

  static Future<void> _clearExpiredProximityFreshCycleLock(File file) async {
    if (!await file.exists()) return;
    try {
      final stat = await file.stat();
      final ageMs = DateTime.now().millisecondsSinceEpoch -
          stat.modified.millisecondsSinceEpoch;
      if (ageMs > proximityFreshCycleMaxSeconds * 1000) {
        await _deleteProximityFreshCycleLockFile(file);
      }
    } catch (_) {
      return;
    }
  }

  static bool shouldDeleteProximityFreshCycleLock({
    required String lockToken,
    String? expectedOwner,
    int? expectedCycleId,
    bool force = false,
  }) {
    if (force) return true;
    if (expectedOwner == null || expectedCycleId == null) return false;
    return lockToken.trim() ==
        _proximityFreshCycleLockToken(
          owner: expectedOwner,
          cycleId: expectedCycleId,
        );
  }

  static Future<void> _clearProximityFreshCycleLock({
    String? expectedOwner,
    int? expectedCycleId,
    bool force = false,
  }) async {
    final file = await _proximityFreshCycleLockFile();
    if (file == null || !await file.exists()) return;
    await _clearProximityFreshCycleLockFile(
      file: file,
      expectedOwner: expectedOwner,
      expectedCycleId: expectedCycleId,
      force: force,
    );
  }

  static Future<void> _clearProximityFreshCycleLockFile({
    required File file,
    String? expectedOwner,
    int? expectedCycleId,
    bool force = false,
  }) async {
    if (!await file.exists()) return;
    try {
      final lockToken = await file.readAsString();
      if (shouldDeleteProximityFreshCycleLock(
        lockToken: lockToken,
        expectedOwner: expectedOwner,
        expectedCycleId: expectedCycleId,
        force: force,
      )) {
        await _deleteProximityFreshCycleLockFile(file);
      }
    } catch (_) {
      return;
    }
  }

  static Future<void> _deleteProximityFreshCycleLockFile(File file) async {
    try {
      if (await file.exists()) {
        await file.delete();
      }
    } catch (_) {
      return;
    }
  }

  static bool shouldAllowInitialAlertCandidate({
    required LocationJudgment judgment,
    required bool verifiedByFreshCycle,
  }) {
    return judgment.isInitialAlertCandidate &&
        (judgment.isStrongInitialAlertCandidate || verifiedByFreshCycle);
  }

  static bool shouldContinueAfterLocationRequest({
    required bool monitorActive,
    required bool requireMonitorActive,
    required bool isPaused,
    required int expectedConfigGeneration,
    required int currentConfigGeneration,
  }) {
    return (!requireMonitorActive || monitorActive) &&
        !isPaused &&
        shouldAcceptFreshResultForConfig(
          requestConfigGeneration: expectedConfigGeneration,
          currentConfigGeneration: currentConfigGeneration,
        );
  }

  static bool shouldAcceptFreshResultForConfig({
    required int requestConfigGeneration,
    required int currentConfigGeneration,
  }) {
    return isStableGeofenceConfigGeneration(requestConfigGeneration) &&
        requestConfigGeneration == currentConfigGeneration;
  }

  static bool isStableGeofenceConfigGeneration(int generation) {
    return generation.isEven;
  }

  static int currentGeofenceConfigGeneration(SharedPreferences prefs) {
    return prefs.getInt(geofenceConfigGenerationKey) ?? 0;
  }

  static bool shouldRecoverStaleGeofenceConfigUpdate({
    required int configGeneration,
    required int updateStartedMs,
    required int nowMs,
  }) {
    if (isStableGeofenceConfigGeneration(configGeneration)) return false;
    return updateStartedMs <= 0 ||
        nowMs < updateStartedMs ||
        nowMs - updateStartedMs >= geofenceConfigUpdateStaleSeconds * 1000;
  }

  static Future<bool> recoverStaleGeofenceConfigUpdate(
    SharedPreferences prefs, {
    int? nowMs,
  }) async {
    await prefs.reload();
    final configGeneration = currentGeofenceConfigGeneration(prefs);
    final updateStartedMs = prefs.getInt(geofenceConfigUpdateStartedMsKey) ?? 0;
    if (!shouldRecoverStaleGeofenceConfigUpdate(
      configGeneration: configGeneration,
      updateStartedMs: updateStartedMs,
      nowMs: nowMs ?? DateTime.now().millisecondsSinceEpoch,
    )) {
      return false;
    }
    await clearProximityFreshState(prefs);
    await prefs.setInt(geofenceConfigGenerationKey, configGeneration + 1);
    await prefs.remove(geofenceConfigUpdateStartedMsKey);
    LogFileService.log(
      '[NH알리미] 중단된 위치 설정 변경 복구 — '
      'config:$configGeneration->${configGeneration + 1}',
    );
    return true;
  }

  static Future<int> beginGeofenceConfigUpdate(
    SharedPreferences prefs,
  ) async {
    await prefs.reload();
    final current = currentGeofenceConfigGeneration(prefs);
    final updatingGeneration = current.isEven ? current + 1 : current + 2;
    await prefs.setInt(
      geofenceConfigUpdateStartedMsKey,
      DateTime.now().millisecondsSinceEpoch,
    );
    await prefs.setInt(geofenceConfigGenerationKey, updatingGeneration);
    await clearProximityFreshState(prefs);
    return updatingGeneration;
  }

  static Future<void> finishGeofenceConfigUpdate(
    SharedPreferences prefs,
    int updatingGeneration,
  ) async {
    await prefs.reload();
    if (currentGeofenceConfigGeneration(prefs) != updatingGeneration) return;
    await prefs.setInt(geofenceConfigGenerationKey, updatingGeneration + 1);
    await prefs.remove(geofenceConfigUpdateStartedMsKey);
  }

  @visibleForTesting
  static void setProximityFreshCycleLockFileOverrideForTesting(File? file) {
    _proximityFreshCycleLockFileOverrideForTesting = file;
  }

  @visibleForTesting
  static Future<bool> tryAcquireProximityFreshCycleLockFileForTesting({
    required File file,
    required String owner,
    required int cycleId,
  }) {
    return _tryAcquireProximityFreshCycleLockFile(
      file: file,
      owner: owner,
      cycleId: cycleId,
    );
  }

  @visibleForTesting
  static Future<void> clearProximityFreshCycleLockFileForTesting({
    required File file,
    String? expectedOwner,
    int? expectedCycleId,
    bool force = false,
  }) {
    return _clearProximityFreshCycleLockFile(
      file: file,
      expectedOwner: expectedOwner,
      expectedCycleId: expectedCycleId,
      force: force,
    );
  }

  static bool shouldRequestProximityFresh({
    required double distance,
    required bool notifActive,
    required bool dismissedUntilExit,
    required bool inactiveLowPower,
    required int nowMs,
    required int lastRequestMs,
  }) {
    if (!inactiveLowPower || notifActive || dismissedUntilExit) {
      return false;
    }
    if (distance > proximityFreshTriggerDistanceMeters) {
      return false;
    }
    if (lastRequestMs <= 0) {
      return true;
    }
    return nowMs - lastRequestMs >= proximityFreshCooldownSeconds * 1000;
  }

  static bool _isInactiveExecutionMode(SharedPreferences prefs) {
    final mode = prefs.getString('app_execution_mode') ?? 'unknown';
    final foreground = prefs.getBool('app_foreground') ?? false;
    return switch (mode) {
      'background_recent' || 'service_only' => true,
      'foreground' => false,
      _ => !foreground,
    };
  }

  static String _lowPowerLocationSource({
    required bool notifActive,
    required bool dismissedLowPower,
    required bool inactiveLowPower,
  }) {
    if (notifActive) return '알림 활성 절전';
    if (dismissedLowPower) return '출퇴근 확인 차단 저전력';
    if (inactiveLowPower) return '화면꺼짐 저전력';
    return '일반 감시';
  }

  static int _lowPowerLastKnownMaxAgeSeconds({
    required bool notifActive,
    required bool dismissedLowPower,
  }) {
    if (notifActive) return notificationActiveLastKnownMaxAgeSeconds;
    if (dismissedLowPower) return dismissedLastKnownMaxAgeSeconds;
    return inactiveLastKnownMaxAgeSeconds;
  }

  static double _lowPowerLastKnownMaxAccuracyMeters({
    required bool notifActive,
    required bool dismissedLowPower,
  }) {
    if (notifActive) return notificationActiveLastKnownMaxAccuracyMeters;
    if (dismissedLowPower) return dismissedLastKnownMaxAccuracyMeters;
    return inactiveLastKnownMaxAccuracyMeters;
  }

  static Future<LocationJudgment?> _judgmentFromLastKnownForLowPower({
    required double centerLat,
    required double centerLng,
    required double radius,
    required String source,
    required int maxAgeSeconds,
    required double maxAccuracyMeters,
  }) async {
    final position = await geo.Geolocator.getLastKnownPosition();
    if (position == null) {
      return null;
    }
    final ageSeconds = DateTime.now().difference(position.timestamp).inSeconds;
    if (ageSeconds < 0 || ageSeconds > maxAgeSeconds) {
      return null;
    }
    if (position.accuracy > maxAccuracyMeters) {
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
    LogFileService.log(
      '[NH알리미] 백그라운드 감시 저전력 위치 — $source, lastKnown 사용 '
      '(age:$ageSeconds초, ${judgment.decisionText})',
    );
    return judgment;
  }

  static void _logNotificationActiveLocationBackoff({
    required String source,
    required int delaySeconds,
    required String reason,
  }) {
    LogFileService.log(
      '[NH알리미] $source — 위치감시 절전 전환 '
      '($reason, 위치 재확인:$delaySeconds초, 반복 알림:30초 유지)',
    );
    LogFileService.logImportant(
      '[NH알리미] 위치감시 절전 — 알림은 30초 반복 유지, '
      '위치 재확인만 $delaySeconds초로 완화 ($reason)',
    );
  }

  static int _delayForDismissedLowPower(LocationJudgment judgment) {
    if (judgment.isOutside) {
      return dismissedOutsideIntervalSeconds;
    }
    return dismissedStableIntervalSeconds;
  }

  static Future<int> _delayForPendingEntry(
    SharedPreferences prefs,
    LocationJudgment judgment,
  ) async {
    final active = prefs.getBool(_proximityFreshCycleActiveKey) ?? false;
    final owner = prefs.getString(_proximityFreshCycleOwnerKey);
    final rechecksRemaining =
        prefs.getInt(_proximityFreshRechecksRemainingKey) ?? 0;
    if (judgment.distance > proximityFreshTriggerDistanceMeters) {
      if (active) {
        await _finishProximityFreshCycle(
          prefs,
          DateTime.now().millisecondsSinceEpoch,
        );
      }
    } else if (active &&
        owner == _proximityFreshOwnerFlutter &&
        rechecksRemaining > 0) {
      LogFileService.log(
        '[NH알리미] 근접 재확인 예약 — '
        '$proximityFreshRecheckIntervalSeconds초 후, '
        'owner:$owner, 남은횟수:$rechecksRemaining/$proximityFreshRecheckLimit',
      );
      return proximityFreshRecheckIntervalSeconds;
    } else if (active &&
        owner == _proximityFreshOwnerFlutter &&
        rechecksRemaining <= 0) {
      await _finishProximityFreshCycle(
        prefs,
        DateTime.now().millisecondsSinceEpoch,
      );
    }
    if (judgment.distance > judgment.exitThreshold &&
        judgment.distance <= approachBandMaxMeters) {
      return approachTriggerIntervalSeconds;
    }
    return pendingTriggerIntervalSeconds;
  }

  static Future<bool> _refreshApproachPendingState({
    required SharedPreferences prefs,
    required LocationJudgment judgment,
    required int nowMs,
    required bool blocked,
    required String source,
  }) async {
    if (blocked) {
      await clearApproachPendingState(prefs);
      return false;
    }

    final pendingAtMs = prefs.getInt(_approachPendingAtMsKey) ?? 0;
    final active = prefs.getBool(_approachPendingActiveKey) ?? false;
    const validMs = LocationJudgmentService.approachPendingValidSeconds * 1000;
    final expired =
        !active || pendingAtMs <= 0 || nowMs - pendingAtMs > validMs;

    if (judgment.distance >
        LocationJudgmentService.approachPendingClearDistanceMeters) {
      if (active) {
        LogFileService.log(
          '[NH알리미] $source — 접근 대기 해제 '
          '(${judgment.distance.toStringAsFixed(0)}m, 기준 '
          '${LocationJudgmentService.approachPendingClearDistanceMeters.toStringAsFixed(0)}m 초과)',
        );
      }
      await clearApproachPendingState(prefs);
      return false;
    }

    if (judgment.isApproachPendingSeed) {
      await prefs.setBool(_approachPendingActiveKey, true);
      await prefs.setInt(_approachPendingAtMsKey, nowMs);
      await prefs.setDouble(_approachPendingDistanceKey, judgment.distance);
      await prefs.setDouble(_approachPendingAccuracyKey, judgment.accuracy);
      if (expired) {
        LogFileService.log(
          '[NH알리미] $source — 접근 대기 시작 '
          '(${judgment.distance.toStringAsFixed(0)}m, '
          '정확도 ${judgment.accuracy.toStringAsFixed(0)}m, '
          '유효:${LocationJudgmentService.approachPendingValidSeconds}초)',
        );
      }
      return true;
    }

    if (expired) {
      await clearApproachPendingState(prefs);
      return false;
    }
    return true;
  }

  static Future<void> clearApproachPendingState(
    SharedPreferences prefs,
  ) async {
    await prefs.remove(_approachPendingActiveKey);
    await prefs.remove(_approachPendingAtMsKey);
    await prefs.remove(_approachPendingDistanceKey);
    await prefs.remove(_approachPendingAccuracyKey);
  }

  static Future<void> clearProximityFreshState(
    SharedPreferences prefs,
  ) async {
    await _clearProximityFreshCycleState(prefs, forceLockClear: true);
    await prefs.remove(_proximityFreshLastRequestMsKey);
    await prefs.remove(_proximityFreshCycleFinishedMsKey);
    await _clearSharedProximityFreshResult(prefs);
  }

  static Future<void> _finishProximityFreshCycle(
    SharedPreferences prefs,
    int nowMs,
  ) async {
    final active = prefs.getBool(_proximityFreshCycleActiveKey) ?? false;
    if (!active) return;
    final owner = prefs.getString(_proximityFreshCycleOwnerKey) ?? 'unknown';
    await _clearProximityFreshCycleState(prefs);
    await prefs.setInt(_proximityFreshCycleFinishedMsKey, nowMs);
    LogFileService.log(
      '[NH알리미] 근접 정밀 검증 사이클 종료 — owner:$owner',
    );
  }

  static Future<void> _clearProximityFreshCycleState(
    SharedPreferences prefs, {
    bool forceLockClear = false,
  }) async {
    final owner = prefs.getString(_proximityFreshCycleOwnerKey);
    final cycleId = prefs.getInt(_proximityFreshCycleIdKey);
    await prefs.remove(_proximityFreshCycleActiveKey);
    await prefs.remove(_proximityFreshCycleOwnerKey);
    await prefs.remove(_proximityFreshCycleIdKey);
    await prefs.remove(_proximityFreshCycleStartedMsKey);
    await prefs.remove(_proximityFreshRechecksRemainingKey);
    await _clearProximityFreshCycleLock(
      expectedOwner: owner,
      expectedCycleId: cycleId,
      force: forceLockClear,
    );
  }

  static Future<void> _clearSharedProximityFreshResult(
    SharedPreferences prefs,
  ) async {
    await prefs.remove(_proximityFreshVerifiedAtMsKey);
    await prefs.remove(_proximityFreshVerifiedDistanceMmKey);
    await prefs.remove(_proximityFreshVerifiedAccuracyMmKey);
    await prefs.remove(_proximityFreshVerifiedSourceKey);
    await prefs.remove(_proximityFreshVerifiedPayloadKey);
  }

  static String _lowPowerSuffix({
    required bool dismissedUntilExit,
    required bool inactiveLowPower,
    required int delaySeconds,
  }) {
    if (dismissedUntilExit) {
      return ', 출퇴근 확인 차단 저전력 감시 $delaySeconds초';
    }
    if (inactiveLowPower) {
      return ', 화면꺼짐 저전력 감시 $delaySeconds초';
    }
    return '';
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
    await recoverStaleGeofenceConfigUpdate(prefs);
    await prefs.setBool('monitor_active', true);
    await prefs.setInt('monitor_outside_count', 0);
    await scheduleNext(delaySeconds: initialDelaySeconds);
    LogFileService.log('[NH알리미] 백그라운드 감시 시작 — $initialDelaySeconds초 후 첫 확인');
  }

  static Future<void> stop() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('monitor_active', false);
    await prefs.setInt('monitor_outside_count', 0);
    await clearProximityFreshState(prefs);
    await AndroidAlarmManager.cancel(monitorAlarmId);
    LogFileService.log('[NH알리미] 백그라운드 감시 중지');
  }

  static Future<void> scheduleNext({
    int delaySeconds = defaultIntervalSeconds,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    await prefs.setInt('last_monitor_scheduled_ms', nowMs);
    await prefs.setInt('last_monitor_due_ms', nowMs + delaySeconds * 1000);
    await prefs.setInt('last_monitor_delay_sec', delaySeconds);
    await _recordDiagnosticDelay(prefs, delaySeconds);
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

  static Future<void> _scheduleNextIfStillActive(
    SharedPreferences prefs, {
    required String source,
    required int delaySeconds,
  }) async {
    await prefs.reload();
    final stillActive = prefs.getBool('monitor_active') ?? false;
    final stillPaused = prefs.getBool('is_paused') ?? false;
    if (shouldScheduleNextMonitor(
      monitorActive: stillActive,
      isPaused: stillPaused,
    )) {
      await scheduleNext(delaySeconds: delaySeconds);
    } else {
      LogFileService.log(
        '[NH알리미] $source 다음 예약 생략 — '
        'active:$stillActive, paused:$stillPaused',
      );
    }
  }

  static bool shouldScheduleNextMonitor({
    required bool monitorActive,
    required bool isPaused,
  }) {
    return monitorActive && !isPaused;
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
    final lastScheduled = prefs.getInt('last_monitor_scheduled_ms') ?? 0;
    final lastDue = prefs.getInt('last_monitor_due_ms') ?? 0;
    final staleSchedule = shouldRefreshSchedule(
      monitorActive: monitorActive,
      nowMs: now,
      lastScheduledMs: lastScheduled,
      lastDueMs: lastDue,
    );

    if (!monitorActive || staleSchedule) {
      await start(initialDelaySeconds: 5);
      LogFileService.log(
        '[NH알리미] 백그라운드 감시 리프레시 — '
        'active:$monitorActive, lastSchedule:${now - lastScheduled}ms, '
        'lastDue:${lastDue > 0 ? now - lastDue : 0}ms',
      );
    }
  }

  static bool shouldRefreshSchedule({
    required bool monitorActive,
    required int nowMs,
    required int lastScheduledMs,
    required int lastDueMs,
  }) {
    if (!monitorActive) return true;
    if (lastScheduledMs <= 0 || lastDueMs <= 0) return true;
    const graceMs = staleScheduleGraceSeconds * 1000;
    return nowMs - lastDueMs > graceMs;
  }

  static Future<void> _ensureDiagnosticWindow(
    SharedPreferences prefs,
  ) async {
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    if ((prefs.getInt(_diagStartedMsKey) ?? 0) <= 0) {
      await prefs.setInt(_diagStartedMsKey, nowMs);
    }
    if ((prefs.getInt(_diagLastSummaryMsKey) ?? 0) <= 0) {
      await prefs.setInt(_diagLastSummaryMsKey, nowMs);
    }
  }

  static Future<void> _incrementDiagnosticCounter(
    SharedPreferences prefs,
    String key,
  ) async {
    await prefs.setInt(key, (prefs.getInt(key) ?? 0) + 1);
  }

  static Future<void> _recordDiagnosticDelay(
    SharedPreferences prefs,
    int delaySeconds,
  ) async {
    await _ensureDiagnosticWindow(prefs);
    final minDelay = prefs.getInt(_diagMinDelaySecKey);
    final maxDelay = prefs.getInt(_diagMaxDelaySecKey);
    if (minDelay == null || delaySeconds < minDelay) {
      await prefs.setInt(_diagMinDelaySecKey, delaySeconds);
    }
    if (maxDelay == null || delaySeconds > maxDelay) {
      await prefs.setInt(_diagMaxDelaySecKey, delaySeconds);
    }
    await prefs.setInt(_diagLastDelaySecKey, delaySeconds);
  }

  static Future<void> _maybeLogDiagnosticSummary(
    SharedPreferences prefs,
  ) async {
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    await _ensureDiagnosticWindow(prefs);
    final startedMs = prefs.getInt(_diagStartedMsKey) ?? nowMs;
    final lastSummaryMs = prefs.getInt(_diagLastSummaryMsKey) ?? startedMs;
    if (nowMs - lastSummaryMs < diagnosticSummaryIntervalSeconds * 1000) {
      return;
    }

    final elapsedMinutes =
        ((nowMs - startedMs).clamp(0, 1 << 31) / 60000).round();
    final checkCount = prefs.getInt(_diagCheckCountKey) ?? 0;
    final positionRequestCount =
        prefs.getInt(_diagPositionRequestCountKey) ?? 0;
    final lastKnownCount = prefs.getInt(_diagLastKnownCountKey) ?? 0;
    final proximityFreshCount = prefs.getInt(_diagProximityFreshCountKey) ?? 0;
    final failureCount = prefs.getInt(_diagFailureCountKey) ?? 0;
    final delayedCallbackCount =
        prefs.getInt(_diagDelayedCallbackCountKey) ?? 0;
    final minDelay = prefs.getInt(_diagMinDelaySecKey) ?? 0;
    final maxDelay = prefs.getInt(_diagMaxDelaySecKey) ?? 0;
    final lastDelay = prefs.getInt(_diagLastDelaySecKey) ?? 0;

    LogFileService.logImportant(
      '[NH알리미] 사용자 진단 요약 — 최근 $elapsedMinutes분, '
      'Flutter감시:$checkCount회, 위치요청:$positionRequestCount회, '
      'lastKnown:$lastKnownCount회, 근접정밀:$proximityFreshCount회, '
      '실패/timeout:$failureCount회, '
      '실행지연:$delayedCallbackCount회, '
      '예약간격:$minDelay-$maxDelay초(last:$lastDelay초)',
    );
    await _resetDiagnosticWindow(prefs, nowMs);
  }

  static Future<void> _resetDiagnosticWindow(
    SharedPreferences prefs,
    int nowMs,
  ) async {
    await prefs.setInt(_diagStartedMsKey, nowMs);
    await prefs.setInt(_diagLastSummaryMsKey, nowMs);
    await prefs.setInt(_diagCheckCountKey, 0);
    await prefs.setInt(_diagPositionRequestCountKey, 0);
    await prefs.setInt(_diagLastKnownCountKey, 0);
    await prefs.setInt(_diagProximityFreshCountKey, 0);
    await prefs.setInt(_diagFailureCountKey, 0);
    await prefs.setInt(_diagDelayedCallbackCountKey, 0);
    await prefs.remove(_diagMinDelaySecKey);
    await prefs.remove(_diagMaxDelaySecKey);
    await prefs.remove(_diagLastDelaySecKey);
  }
}
