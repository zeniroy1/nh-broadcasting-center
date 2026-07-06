import 'dart:async';
import 'dart:convert';
import 'dart:ui';
import 'package:android_alarm_manager_plus/android_alarm_manager_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'nh_app_launcher_service.dart';
import 'geofence_service.dart';
import 'log_file_service.dart';
import 'location_judgment_service.dart';
import 'native_monitor_bridge.dart';

@pragma('vm:entry-point')
Future<void> notificationRepeatCallback() async {
  DartPluginRegistrant.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  await prefs.reload();
  await prefs.setInt(
    'last_notification_callback_ms',
    DateTime.now().millisecondsSinceEpoch,
  );

  if (await NotificationService._cancelRepeatIfBlocked(
    prefs,
    source: '반복 알림 콜백',
  )) {
    return;
  }

  try {
    final centerLat = prefs.getDouble('geofence_lat') ?? 37.56600;
    final centerLng = prefs.getDouble('geofence_lng') ?? 126.96730;
    final radius = prefs.getDouble('geofence_radius') ?? 30.0;

    final judgment = await LocationJudgmentService.fromCurrentPosition(
      centerLat: centerLat,
      centerLng: centerLng,
      radius: radius,
    );
    await NotificationService._saveRecentJudgment(prefs, judgment, '반복 알림 콜백');
    await prefs.setInt('notif_location_failure_defer_count', 0);

    if (judgment.isOutside) {
      final intervalSec = prefs.getInt('notif_interval_sec') ??
          prefs.getInt('repeat_interval_sec') ??
          NotificationService.defaultRepeatIntervalSeconds;
      final guardReason =
          NotificationService._repeatExitGuardReason(prefs, judgment);
      if (guardReason != null) {
        await prefs.setInt('notif_outside_count', 0);
        if (await NotificationService._cancelRepeatIfBlocked(
          prefs,
          source: '반복 알림 유지 전',
        )) {
          return;
        }
        await NotificationService().initialize();
        await NotificationService().showNotificationDirect();
        await NotificationService().scheduleNextReminder(intervalSec);
        LogFileService.log(
          '[NH알리미] 반복 알림 발송 유지 — $guardReason '
          '(${judgment.outsideText})',
        );
        return;
      }

      final outsideCount = (prefs.getInt('notif_outside_count') ?? 0) + 1;
      await prefs.setInt('notif_outside_count', outsideCount);

      if (outsideCount >= NotificationService._repeatExitRequiredCount) {
        await NotificationService().initialize();
        await NotificationService().stopReminder();
        await prefs.setInt('notif_outside_count', 0);
        LogFileService.log(
          '[NH알리미] 반복 알림 콜백 중지 — 확정 이탈 '
          '${NotificationService._repeatExitRequiredCount}회 확인 '
          '(${judgment.outsideText})',
        );
        return;
      }

      if (await NotificationService._cancelRepeatIfBlocked(
        prefs,
        source: '반복 알림 위치 튐 유예 전',
      )) {
        return;
      }
      await NotificationService().scheduleNextReminder(intervalSec);
      LogFileService.log(
        '[NH알리미] 반복 알림 위치 튐 감지 — '
        '$outsideCount/${NotificationService._repeatExitRequiredCount}회 유예 '
        '(${judgment.outsideText})',
      );
      return;
    }

    await prefs.setInt('notif_outside_count', 0);
  } catch (e) {
    final intervalSec = prefs.getInt('notif_interval_sec') ??
        prefs.getInt('repeat_interval_sec') ??
        NotificationService.defaultRepeatIntervalSeconds;
    if (await NotificationService._deferRepostAfterLocationFailure(
      prefs,
      error: e,
      intervalSeconds: intervalSec,
    )) {
      if (await NotificationService._cancelRepeatIfBlocked(
        prefs,
        source: '반복 알림 위치 실패 보류 전',
      )) {
        return;
      }
      await NotificationService().scheduleNextReminder(intervalSec);
      return;
    }
    await prefs.setInt('notif_location_failure_defer_count', 0);
    LogFileService.log('[NH알리미] 반복 알림 위치 확인 실패 — 알림 유지: $e');
  }

  if (await NotificationService._cancelRepeatIfBlocked(
    prefs,
    source: '반복 알림 재표시 전',
  )) {
    return;
  }
  await NotificationService().initialize();
  await NotificationService().showNotificationDirect();
  LogFileService.log('[NH알리미] 반복 알림 발송 (alarm callback)');

  final intervalSec = prefs.getInt('notif_interval_sec') ??
      prefs.getInt('repeat_interval_sec') ??
      NotificationService.defaultRepeatIntervalSeconds;
  await NotificationService().scheduleNextReminder(intervalSec);
}

enum _TimestampSaveResult { saved, duplicate, failed }

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static const _channelId = 'nh_reminder_high_v2';
  static const _channelName = '출퇴근 알림';
  static const _notifId = 1001;
  static const _notifAlarmId = 9003;
  static const _duplicateClickWindowMs = 5000;
  static const _recentJudgmentMaxAgeMs = 180000;
  static const _repeatExitStartupGraceMs = 120000;
  static const _repeatExitRequiredCount = 3;
  static const _repeatExitPoorAccuracyMeters = 80.0;
  static const _repeatExitVeryFarMeters = 600.0;
  static const defaultRepeatIntervalSeconds = 30;

  bool _isActive = false;
  bool get isActive => _isActive;

  Future<bool> startReminderOnce({
    required String source,
    int? intervalSeconds,
    bool clearDismissal = false,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();

    if (prefs.getBool('is_paused') ?? false) {
      LogFileService.log('[NH알리미] 알림 시작 생략 — 일시정지 상태, source:$source');
      return false;
    }

    if (clearDismissal) {
      await prefs.setBool('dismissed_until_exit', false);
    } else if (prefs.getBool('dismissed_until_exit') ?? false) {
      LogFileService.log(
        '[NH알리미] 알림 시작 생략 — 출퇴근 확인 차단 상태, source:$source',
      );
      return false;
    }

    final now = DateTime.now().millisecondsSinceEpoch;
    final startingAt = prefs.getInt('notification_starting_ms') ?? 0;
    final notifActive = prefs.getBool('notif_active') ?? false;
    if (_isActive || notifActive || now - startingAt < 5000) {
      LogFileService.log('[NH알리미] 알림 시작 요청 무시 — 이미 활성, source:$source');
      return false;
    }

    final interval = intervalSeconds ??
        prefs.getInt('repeat_interval_sec') ??
        defaultRepeatIntervalSeconds;
    if (!await startReminder(intervalSeconds: interval)) {
      return false;
    }
    LogFileService.log('[NH알리미] 알림 시작 — source:$source, interval:$interval초');
    return true;
  }

  static String? _repeatExitGuardReason(
    SharedPreferences prefs,
    LocationJudgment judgment,
  ) {
    final now = DateTime.now().millisecondsSinceEpoch;
    final startedAt = prefs.getInt('last_notification_started_ms') ?? 0;
    if (startedAt > 0 && now - startedAt < _repeatExitStartupGraceMs) {
      return '알림 시작 직후 GPS 안정화 보호구간';
    }

    final stopThreshold = LocationJudgmentService.confirmedExitThreshold(
      judgment.radius,
    );
    if (judgment.distance <= stopThreshold) {
      return '확정 이탈 완충권 내부';
    }

    final veryFarThreshold =
        judgment.radius + _repeatExitVeryFarMeters > _repeatExitVeryFarMeters
            ? judgment.radius + _repeatExitVeryFarMeters
            : _repeatExitVeryFarMeters;
    if (judgment.accuracy >= _repeatExitPoorAccuracyMeters &&
        judgment.distance <= veryFarThreshold) {
      return '정확도 낮은 위치값';
    }

    return null;
  }

  Future<void> initialize() async {
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    await _plugin.initialize(
      const InitializationSettings(android: androidInit),
      onDidReceiveNotificationResponse: _onNotifResponse,
    );

    final channel = AndroidNotificationChannel(
      _channelId,
      _channelName,
      description: '농협파트너스 출퇴근 버튼 클릭 확인 알림',
      importance: Importance.high,
      playSound: true,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 200, 100, 200]),
      enableLights: true,
      ledColor: const Color.fromARGB(255, 77, 182, 172),
    );

    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  Future<bool> startReminder({
    int intervalSeconds = defaultRepeatIntervalSeconds,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    final now = DateTime.now().millisecondsSinceEpoch;
    final notifActive = prefs.getBool('notif_active') ?? false;
    final startingAt = prefs.getInt('notification_starting_ms') ?? 0;
    if (_isActive || now - startingAt < 5000) {
      LogFileService.log('[NH알리미] 반복 알림 시작 요청 무시 — 이미 시작 중/활성 상태');
      return false;
    }

    final isRecoveringPersistedActive = notifActive;
    await prefs.setInt('notification_starting_ms', now);
    _isActive = true;
    await prefs.setBool('notif_active', true);
    await prefs.setInt('notif_interval_sec', intervalSeconds);
    await prefs.setInt('notif_outside_count', 0);
    await prefs.setInt('notif_location_failure_defer_count', 0);
    await prefs.setInt('last_notification_started_ms', now);
    await prefs.setInt('last_notification_callback_ms', now);
    await NativeMonitorBridge.syncNotificationActive(true);

    await showNotificationDirect();

    await scheduleNextReminder(intervalSeconds);
    if (isRecoveringPersistedActive) {
      LogFileService.log(
        '[NH알리미] 반복 알림 활성 상태 복구 — 실제 알림 재게시 '
        '($intervalSeconds초 간격, AlarmManager)',
      );
    } else {
      LogFileService.log(
          '[NH알리미] 반복 알림 시작 ($intervalSeconds초 간격, AlarmManager)');
    }
    return true;
  }

  Future<void> scheduleNextReminder(int intervalSeconds) async {
    final prefs = await SharedPreferences.getInstance();
    if (await _cancelRepeatIfBlocked(
      prefs,
      source: '반복 알림 예약 전',
    )) {
      return;
    }
    await prefs.setInt(
      'last_notification_scheduled_ms',
      DateTime.now().millisecondsSinceEpoch,
    );
    await AndroidAlarmManager.cancel(_notifAlarmId);
    await AndroidAlarmManager.oneShot(
      Duration(seconds: intervalSeconds),
      _notifAlarmId,
      notificationRepeatCallback,
      exact: true,
      wakeup: true,
      allowWhileIdle: true,
      rescheduleOnReboot: false,
    );
    LogFileService.log('[NH알리미] 다음 반복 알림 예약 → $intervalSeconds초 후');
  }

  Future<void> refreshReminderIfStale() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    if (!(prefs.getBool('notif_active') ?? false)) return;
    if (prefs.getBool('is_paused') ?? false) {
      await stopReminder();
      return;
    }

    final now = DateTime.now().millisecondsSinceEpoch;
    final lastCallback = prefs.getInt('last_notification_callback_ms') ?? 0;
    final lastScheduled = prefs.getInt('last_notification_scheduled_ms') ?? 0;
    final intervalSec = prefs.getInt('notif_interval_sec') ??
        prefs.getInt('repeat_interval_sec') ??
        defaultRepeatIntervalSeconds;
    final staleLimitMs = (intervalSec * 3 + 30) * 1000;
    final staleCallback =
        lastCallback != 0 && now - lastCallback > staleLimitMs;
    final staleSchedule =
        lastScheduled == 0 || now - lastScheduled > staleLimitMs;

    if (staleCallback || staleSchedule) {
      await scheduleNextReminder(intervalSec);
      LogFileService.log(
        '[NH알리미] 반복 알림 리프레시 — $intervalSec초 간격 재예약 '
        '(lastCallback:${now - lastCallback}ms, lastSchedule:${now - lastScheduled}ms)',
      );
    }
  }

  Future<void> stopReminder() async {
    _isActive = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('notif_active', false);
    await prefs.setInt('notif_outside_count', 0);
    await prefs.setInt('notif_location_failure_defer_count', 0);
    await prefs.setInt('notification_starting_ms', 0);
    await NativeMonitorBridge.syncNotificationActive(false);
    await AndroidAlarmManager.cancel(_notifAlarmId);
    if (!await NativeMonitorBridge.cancelReminderNotification()) {
      await _plugin.cancel(_notifId);
    }
    LogFileService.log('[NH알리미] 반복 알림 중지');
  }

  Future<void> restartReminderIfExists(int intervalSeconds) async {
    final prefs = await SharedPreferences.getInstance();
    final notifActive = prefs.getBool('notif_active') ?? false;
    if (!notifActive) {
      LogFileService.log('[NH알리미] restartReminderIfExists: 활성 알람 없음 — skip');
      return;
    }

    await AndroidAlarmManager.cancel(_notifAlarmId);
    await prefs.setInt('notif_interval_sec', intervalSeconds);
    await scheduleNextReminder(intervalSeconds);
    _isActive = true;
    LogFileService.log('[NH알리미] 알림 간격 변경 → $intervalSeconds초');
  }

  Future<bool> showNotificationDirect() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (await _cancelRepeatIfBlocked(
        prefs,
        source: '반복 알림 표시 전',
      )) {
        return false;
      }

      if (await NativeMonitorBridge.showReminderNotification()) {
        LogFileService.log('[NH알리미] 네이티브 직접 알림 발송 완료 — 본문 클릭 NH파트너스 연결');
        return true;
      }
      if (!await NativeMonitorBridge.cancelReminderNotification()) {
        await _plugin.cancel(_notifId);
      }
      await Future<void>.delayed(const Duration(milliseconds: 150));

      final androidDetails = AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: '농협파트너스 출퇴근 버튼 클릭 확인',
        importance: Importance.max,
        priority: Priority.max,
        fullScreenIntent: true,
        category: AndroidNotificationCategory.alarm,
        enableVibration: true,
        vibrationPattern: Int64List.fromList([0, 700, 200, 700, 200, 700]),
        playSound: true,
        onlyAlertOnce: false,
        autoCancel: false,
        ongoing: false,
        icon: '@mipmap/ic_launcher',
        color: const Color(0xFF005BAC),
        actions: const [
          AndroidNotificationAction(
            'open_nh',
            '📲 NH파트너스 열기',
            showsUserInterface: true,
            cancelNotification: true,
          ),
        ],
      );

      await _plugin.show(
        _notifId,
        '🔔 출퇴근 버튼을 눌렀나요?',
        '알림 본문이나 버튼을 눌러 NH파트너스를 열어주세요.',
        NotificationDetails(android: androidDetails),
        payload: 'open_nh',
      );
      LogFileService.log('[NH알리미] 팝업 알림 발송 완료 — 기존 알림 취소 후 재표시');
      return true;
    } catch (e) {
      LogFileService.log('[NH알리미] 팝업 알림 발송 실패: $e');
      return false;
    }
  }

  void _onNotifResponse(NotificationResponse response) {
    final payload = response.actionId ?? response.payload ?? '';
    if (payload == 'open_nh') {
      unawaited(_handleOpenNhResponse());
    }
  }

  Future<void> _handleOpenNhResponse() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();

    final handledAtMs = DateTime.now().millisecondsSinceEpoch;
    final lastHandledMs = prefs.getInt('last_reminder_action_handled_ms') ?? 0;
    if (_isRecentlyHandled(handledAtMs, lastHandledMs)) {
      LogFileService.log(
        '[NH알리미] 알림 클릭 중복 처리 생략 — source:플러터 알림',
      );
      await NhGeofenceService().dismissUntilExit();
      return;
    }

    await prefs.setInt('last_reminder_action_handled_ms', handledAtMs);
    final saveResult = await _saveTimestamp(handledAtMs: handledAtMs);
    if (saveResult == _TimestampSaveResult.duplicate) {
      await NhGeofenceService().dismissUntilExit();
      return;
    }

    await NhGeofenceService().dismissUntilExit();
    await NhAppLauncherService().launchNhApp();
  }

  bool _isRecentlyHandled(int nowMs, int lastHandledMs) {
    return lastHandledMs > 0 && nowMs - lastHandledMs < _duplicateClickWindowMs;
  }

  static Future<bool> _deferRepostAfterLocationFailure(
    SharedPreferences prefs, {
    required Object error,
    required int intervalSeconds,
  }) async {
    final now = DateTime.now().millisecondsSinceEpoch;
    final lastJudgmentMs = prefs.getInt('last_location_judgment_ms') ?? 0;
    if (lastJudgmentMs <= 0) return false;

    final ageMs = now - lastJudgmentMs;
    if (ageMs < 0 || ageMs > _recentJudgmentMaxAgeMs) return false;

    final zone = prefs.getString('last_location_zone') ?? '';
    final shouldDefer = zone == LocationZone.boundary.name ||
        zone == LocationZone.outside.name ||
        zone == LocationZone.farOutside.name;
    if (!shouldDefer) return false;

    final distance = prefs.getDouble('last_location_distance_m') ?? -1;
    final accuracy = prefs.getDouble('last_location_accuracy_m') ?? -1;
    final radius = prefs.getDouble('last_location_radius_m') ??
        prefs.getDouble('geofence_radius') ??
        30.0;
    final failureGuardReason = _repeatFailureGuardReason(
      prefs,
      distance: distance,
      accuracy: accuracy,
      radius: radius,
    );
    if (failureGuardReason != null) {
      await prefs.setInt('notif_location_failure_defer_count', 0);
      final source = prefs.getString('last_location_source') ?? 'unknown';
      final ageSec = (ageMs / 1000).round();
      LogFileService.log(
        '[NH알리미] 반복 알림 위치 확인 실패 — 알림 유지: '
        '$failureGuardReason, 최근 위치 판정:$zone, source:$source, '
        'age:$ageSec초, 거리:${distance.toStringAsFixed(0)}m, '
        '정확도:${accuracy.toStringAsFixed(0)}m: $error',
      );
      return false;
    }

    final deferCount =
        (prefs.getInt('notif_location_failure_defer_count') ?? 0) + 1;
    await prefs.setInt('notif_location_failure_defer_count', deferCount);
    final source = prefs.getString('last_location_source') ?? 'unknown';
    final ageSec = (ageMs / 1000).round();
    LogFileService.log(
      '[NH알리미] 반복 알림 위치 확인 실패 — 최근 위치 판정:$zone, '
      'source:$source, age:$ageSec초, '
      '거리:${distance.toStringAsFixed(0)}m, 정확도:${accuracy.toStringAsFixed(0)}m, '
      '알림 재표시 보류 $deferCount회, 다음:$intervalSeconds초: $error',
    );
    return true;
  }

  static String? _repeatFailureGuardReason(
    SharedPreferences prefs, {
    required double distance,
    required double accuracy,
    required double radius,
  }) {
    final now = DateTime.now().millisecondsSinceEpoch;
    final startedAt = prefs.getInt('last_notification_started_ms') ?? 0;
    if (startedAt > 0 && now - startedAt < _repeatExitStartupGraceMs) {
      return '알림 시작 직후 GPS 안정화 보호구간';
    }

    if (distance >= 0 &&
        distance <= LocationJudgmentService.confirmedExitThreshold(radius)) {
      return '확정 이탈 완충권 내부';
    }

    final veryFarThreshold = radius + _repeatExitVeryFarMeters;
    if (accuracy >= _repeatExitPoorAccuracyMeters &&
        distance >= 0 &&
        distance <= veryFarThreshold) {
      return '정확도 낮은 위치값';
    }

    return null;
  }

  static Future<bool> _cancelRepeatIfBlocked(
    SharedPreferences prefs, {
    required String source,
  }) async {
    await prefs.reload();
    final reason = _repeatBlockReason(prefs);
    if (reason == null) {
      return false;
    }

    NotificationService()._isActive = false;
    await prefs.setBool('notif_active', false);
    await prefs.setInt('notif_outside_count', 0);
    await prefs.setInt('notif_location_failure_defer_count', 0);
    await AndroidAlarmManager.cancel(_notifAlarmId);
    await NativeMonitorBridge.syncNotificationActive(false);
    LogFileService.log('[NH알리미] $source 종료 — $reason');
    return true;
  }

  static String? _repeatBlockReason(SharedPreferences prefs) {
    if (!(prefs.getBool('notif_active') ?? false)) {
      return 'notif_active=false';
    }
    if (prefs.getBool('is_paused') ?? false) {
      return '일시정지 상태';
    }
    if (prefs.getBool('dismissed_until_exit') ?? false) {
      return '출퇴근 확인 차단 상태';
    }
    return null;
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

  Future<_TimestampSaveResult> _saveTimestamp({
    required int handledAtMs,
  }) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.reload();
      final jsonString = prefs.getString('commute_history_raw');
      List<DateTime> timestamps = [];
      if (jsonString != null) {
        final List<dynamic> decoded = jsonDecode(jsonString);
        timestamps = decoded.map((e) => DateTime.parse(e.toString())).toList();
      }
      final timestamp = DateTime.fromMillisecondsSinceEpoch(handledAtMs);
      if (timestamps.isNotEmpty &&
          timestamp.difference(timestamps.last).inMilliseconds.abs() <
              _duplicateClickWindowMs) {
        await prefs.setInt('last_reminder_action_handled_ms', handledAtMs);
        LogFileService.log(
          '[NH알리미] 출퇴근 기록 중복 저장 생략 — source:플러터 알림, '
          'last:${timestamps.last.toIso8601String()}',
        );
        return _TimestampSaveResult.duplicate;
      }

      timestamps.add(timestamp);
      await prefs.setString(
        'commute_history_raw',
        jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
      );
      await prefs.setBool('pending_history_reload', true);
      LogFileService.log(
        '[NH알리미] 출퇴근 기록 저장 완료 — source:플러터 알림, '
        'timestamp:${timestamps.last.toIso8601String()}',
      );
      return _TimestampSaveResult.saved;
    } catch (e) {
      LogFileService.log('[NH알리미] 기록 저장 실패: $e');
      return _TimestampSaveResult.failed;
    }
  }
}
