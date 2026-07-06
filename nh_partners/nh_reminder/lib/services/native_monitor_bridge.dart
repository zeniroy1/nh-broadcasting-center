import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/app_state.dart';
import 'log_file_service.dart';

class NativeMonitorBridge {
  static const MethodChannel _channel =
      MethodChannel('com.example.nh_reminder/native_monitor');

  static Future<void> syncFromSettings(AppSettings settings) {
    return syncConfig(
      isPaused: settings.isPaused,
      lat: settings.geofenceLat,
      lng: settings.geofenceLng,
      radius: settings.geofenceRadius,
    );
  }

  static Future<void> syncConfig({
    required bool isPaused,
    required double lat,
    required double lng,
    required double radius,
  }) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await _channel.invokeMethod<void>('updateConfig', {
        'paused': isPaused,
        'lat': lat,
        'lng': lng,
        'radius': radius,
        'notifActive': prefs.getBool('notif_active') ?? false,
      });
      LogFileService.log(
        '[NH알리미] 네이티브 보조 감시 설정 동기화 — '
        'paused:$isPaused, lat:$lat, lng:$lng, 반경:${radius}m',
      );
    } catch (e) {
      if (e is MissingPluginException) {
        return;
      }
      LogFileService.log('[NH알리미] 네이티브 보조 감시 설정 동기화 실패: $e');
    }
  }

  static Future<void> syncNotificationActive(bool isActive) async {
    try {
      await _channel.invokeMethod<void>('updateNotificationActive', {
        'notifActive': isActive,
      });
      LogFileService.log('[NH알리미] 네이티브 보조 감시 알림상태 동기화 — active:$isActive');
    } catch (e) {
      if (e is MissingPluginException) {
        return;
      }
      LogFileService.log('[NH알리미] 네이티브 보조 감시 알림상태 동기화 실패: $e');
    }
  }

  static Future<bool> showReminderNotification() async {
    try {
      await _channel.invokeMethod<void>('showReminderNotification');
      return true;
    } catch (e) {
      if (e is MissingPluginException) {
        return false;
      }
      LogFileService.log('[NH알리미] 네이티브 직접 알림 발송 실패: $e');
      return false;
    }
  }

  static Future<bool> cancelReminderNotification() async {
    try {
      await _channel.invokeMethod<void>('cancelReminderNotification');
      return true;
    } catch (e) {
      if (e is MissingPluginException) {
        return false;
      }
      LogFileService.log('[NH알리미] 네이티브 직접 알림 취소 실패: $e');
      return false;
    }
  }

  static Future<void> stopService() async {
    try {
      await _channel.invokeMethod<void>('stopService');
      LogFileService.log('[NH알리미] 네이티브 포그라운드 서비스 종료 요청 완료');
    } catch (e) {
      if (e is MissingPluginException) {
        return;
      }
      LogFileService.log('[NH알리미] 네이티브 포그라운드 서비스 종료 요청 실패: $e');
    }
  }
}
