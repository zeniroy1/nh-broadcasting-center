import 'package:flutter/services.dart';

import 'log_file_service.dart';

class UsageStatsService {
  static const _channel = MethodChannel('com.example.nh_reminder/usage_stats');
  static const _nhPackage = 'com.vus.nhpthrm';

  Future<bool> isNhAppInForeground() async {
    try {
      final result = await _channel.invokeMethod<bool>(
        'isAppInForeground',
        {'package': _nhPackage},
      );
      return result ?? false;
    } on PlatformException catch (e) {
      LogFileService.log('[NH리마인더] UsageStats 오류: ${e.message}');
      return false;
    } on MissingPluginException {
      return false;
    }
  }

  Future<bool> hasPermission() async {
    try {
      final result = await _channel.invokeMethod<bool>('hasUsagePermission');
      return result ?? false;
    } catch (_) {
      return false;
    }
  }

  Future<void> openPermissionSettings() async {
    try {
      await _channel.invokeMethod('openUsageSettings');
    } catch (e) {
      LogFileService.log('[NH리마인더] UsageStats 설정 화면 오류: $e');
    }
  }

  Future<void> launchNhApp() async {
    try {
      await _channel.invokeMethod('launchNhApp');
    } catch (e) {
      LogFileService.log('[NH알리미] NH앱 실행 실패: $e');
    }
  }
}
