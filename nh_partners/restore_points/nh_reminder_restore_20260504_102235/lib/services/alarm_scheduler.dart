import 'dart:ui';

import 'package:android_alarm_manager_plus/android_alarm_manager_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'notification_service.dart';
import 'background_monitor_service.dart';
import 'geofence_service.dart';
import 'log_file_service.dart';
import 'monitoring_recovery_service.dart';
import 'native_monitor_bridge.dart';

class DailyAlarmScheduler {
  static const int _startAlarmId = 9001;
  static const int _stopAlarmId = 9002;

  static Future<void> schedule() async {
    await AndroidAlarmManager.initialize();

    final now = DateTime.now();

    DateTime nextStart = DateTime(now.year, now.month, now.day, 6, 0, 0);
    if (now.isAfter(nextStart)) {
      nextStart = nextStart.add(const Duration(days: 1));
    }

    await AndroidAlarmManager.oneShotAt(
      nextStart,
      _startAlarmId,
      _onStartAlarm,
      exact: true,
      wakeup: true,
      rescheduleOnReboot: true,
    );
    LogFileService.log('[NH리마인더] 자동 시작 알람 예약: $nextStart');

    DateTime nextStop = DateTime(now.year, now.month, now.day, 19, 0, 0);
    if (now.isAfter(nextStop)) {
      nextStop = nextStop.add(const Duration(days: 1));
    }

    await AndroidAlarmManager.oneShotAt(
      nextStop,
      _stopAlarmId,
      _onStopAlarm,
      exact: true,
      wakeup: true,
      rescheduleOnReboot: true,
    );
    LogFileService.log('[NH리마인더] 자동 종료 알람 예약: $nextStop');
  }

  static Future<void> cancelAll() async {
    await AndroidAlarmManager.cancel(_startAlarmId);
    await AndroidAlarmManager.cancel(_stopAlarmId);
  }
}

@pragma('vm:entry-point')
Future<void> _onStartAlarm() async {
  DartPluginRegistrant.ensureInitialized();
  LogFileService.log('[NH알리미] ⏰ 06:00 자동 모니터링 시작');
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    final userPaused = prefs.getBool('user_paused') ?? false;
    if (userPaused) {
      LogFileService.log('[NH알리미] 06:00 — 사용자 모니터링 OFF 유지, 자동 시작 생략');
      await DailyAlarmScheduler.schedule();
      return;
    }

    await prefs.setBool('is_paused', false);
    await prefs.setBool('dismissed_until_exit', false);
    await prefs.setBool('pending_history_reload', true);
    await MonitoringRecoveryService.reset(
      reason: '06:00 자동 모니터링 시작',
      syncNative: false,
      startFlutterGeofence: false,
    );
    LogFileService.log('[NH알리미] 06:00 — 모니터링 소프트 리셋 완료');
  } catch (e) {
    LogFileService.log('[NH알리미] 06:00 시작 오류: $e');
  }
  await DailyAlarmScheduler.schedule();
}

@pragma('vm:entry-point')
Future<void> _onStopAlarm() async {
  DartPluginRegistrant.ensureInitialized();
  LogFileService.log('[NH알리미] ⏰ 19:00 자동 모니터링 종료');
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    await prefs.setBool('is_paused', true);
    await BackgroundMonitorService.stop();
    await NhGeofenceService().stop();
    await NotificationService().initialize();
    await NotificationService().stopReminder();
    await NativeMonitorBridge.stopService();
    LogFileService.log(
      '[NH알리미] 19:00 — 시간표 종료 상태 저장 완료, '
      '지오펜스/백그라운드 감시/알림/네이티브 서비스 중지',
    );
  } catch (e) {
    LogFileService.log('[NH알리미] 19:00 종료 오류: $e');
  }
  await DailyAlarmScheduler.schedule();
}
