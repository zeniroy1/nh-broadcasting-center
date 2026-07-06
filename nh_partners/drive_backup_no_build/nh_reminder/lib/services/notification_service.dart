import 'dart:convert';
import 'dart:ui';
import 'package:android_alarm_manager_plus/android_alarm_manager_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'usage_stats_service.dart';
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

  if (!(prefs.getBool('notif_active') ?? false)) {
    await AndroidAlarmManager.cancel(NotificationService._notifAlarmId);
    LogFileService.log('[NH알리미] 반복 알림 콜백 종료 — notif_active=false');
    return;
  }
  if (prefs.getBool('is_paused') ?? false) {
    await AndroidAlarmManager.cancel(NotificationService._notifAlarmId);
    LogFileService.log('[NH알리미] 반복 알림 콜백 종료 — 일시정지 상태');
    return;
  }
  if (prefs.getBool('dismissed_until_exit') ?? false) {
    await AndroidAlarmManager.cancel(NotificationService._notifAlarmId);
    LogFileService.log('[NH알리미] 반복 알림 콜백 종료 — 이탈 전 차단 상태');
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

    if (judgment.isOutside) {
      final outsideCount = (prefs.getInt('notif_outside_count') ?? 0) + 1;
      await prefs.setInt('notif_outside_count', outsideCount);

      if (outsideCount >= 2) {
        await NotificationService().initialize();
        await NotificationService().stopReminder();
        await prefs.setInt('notif_outside_count', 0);
        LogFileService.log(
          '[NH알리미] 반복 알림 콜백 중지 — 범위 밖 2회 확인 '
          '(${judgment.outsideText})',
        );
        return;
      }

      final intervalSec = prefs.getInt('notif_interval_sec') ??
          prefs.getInt('repeat_interval_sec') ??
          60;
      await NotificationService().scheduleNextReminder(intervalSec);
      LogFileService.log(
        '[NH알리미] 반복 알림 위치 튐 감지 — 1회 유예 '
        '(${judgment.outsideText})',
      );
      return;
    }

    await prefs.setInt('notif_outside_count', 0);
  } catch (e) {
    LogFileService.log('[NH알리미] 반복 알림 위치 확인 실패 — 알림 유지: $e');
  }

  await NotificationService().initialize();
  await NotificationService().showNotificationDirect();
  LogFileService.log('[NH알리미] 반복 알림 발송 (alarm callback)');

  final intervalSec = prefs.getInt('notif_interval_sec') ??
      prefs.getInt('repeat_interval_sec') ??
      60;
  await NotificationService().scheduleNextReminder(intervalSec);
}

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static const _channelId = 'nh_reminder_high_v1';
  static const _channelName = '출퇴근 알림';
  static const _notifId = 1001;
  static const _notifAlarmId = 9003;

  bool _isActive = false;
  bool get isActive => _isActive;

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

  Future<void> startReminder({int intervalSeconds = 60}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    final now = DateTime.now().millisecondsSinceEpoch;
    final notifActive = prefs.getBool('notif_active') ?? false;
    final startingAt = prefs.getInt('notification_starting_ms') ?? 0;
    if (_isActive || notifActive || now - startingAt < 5000) {
      LogFileService.log('[NH알리미] 반복 알림 시작 요청 무시 — 이미 시작 중/활성 상태');
      return;
    }

    await prefs.setInt('notification_starting_ms', now);
    _isActive = true;
    await prefs.setBool('notif_active', true);
    await prefs.setInt('notif_interval_sec', intervalSeconds);
    await prefs.setInt('notif_outside_count', 0);
    await prefs.setInt('last_notification_started_ms', now);
    await prefs.setInt('last_notification_callback_ms', now);
    await NativeMonitorBridge.syncNotificationActive(true);

    await showNotificationDirect();

    await scheduleNextReminder(intervalSeconds);
    LogFileService.log('[NH알리미] 반복 알림 시작 ($intervalSeconds초 간격, AlarmManager)');
  }

  Future<void> scheduleNextReminder(int intervalSeconds) async {
    final prefs = await SharedPreferences.getInstance();
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
        60;
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
    await prefs.setInt('notification_starting_ms', 0);
    await NativeMonitorBridge.syncNotificationActive(false);
    await AndroidAlarmManager.cancel(_notifAlarmId);
    await _plugin.cancel(_notifId);
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

  Future<void> showNotificationDirect() async {
    try {
      if (await NativeMonitorBridge.showReminderNotification()) {
        LogFileService.log('[NH알리미] 네이티브 직접 알림 발송 완료 — 본문 클릭 NH파트너스 연결');
        return;
      }

      // Samsung/Android가 같은 ID 갱신을 조용히 처리하는 경우가 있어 재게시한다.
      await _plugin.cancel(_notifId);
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
    } catch (e) {
      LogFileService.log('[NH알리미] 팝업 알림 발송 실패: $e');
    }
  }

  void _onNotifResponse(NotificationResponse response) {
    final payload = response.actionId ?? response.payload ?? '';
    if (payload == 'open_nh') {
      _saveTimestamp();
      NhGeofenceService().dismissUntilExit();
      UsageStatsService().launchNhApp();
    }
  }

  Future<void> _saveTimestamp() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonString = prefs.getString('commute_history_raw');
      List<DateTime> timestamps = [];
      if (jsonString != null) {
        final List<dynamic> decoded = jsonDecode(jsonString);
        timestamps = decoded.map((e) => DateTime.parse(e.toString())).toList();
      }
      timestamps.add(DateTime.now());
      await prefs.setString(
        'commute_history_raw',
        jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
      );
      await prefs.setBool('pending_history_reload', true);
    } catch (e) {
      LogFileService.log('[NH알리미] 기록 저장 실패: $e');
    }
  }
}
