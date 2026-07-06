import 'package:flutter/services.dart';

import 'log_file_service.dart';

/// Android UsageStatsManager를 통해
/// NH파트너스 앱(com.vus.nhpthrm) 포그라운드 실행 여부를 확인
///
/// iOS에서는 사용 불가 → 항상 false 반환
class UsageStatsService {
  static const _channel = MethodChannel('com.example.nh_reminder/usage_stats');
  static const _nhPackage = 'com.vus.nhpthrm';

  /// NH파트너스 앱이 현재 포그라운드에 있는지 확인
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
      // iOS나 UsageStats 권한 없을 때
      return false;
    }
  }

  /// PACKAGE_USAGE_STATS 권한 보유 여부 확인
  Future<bool> hasPermission() async {
    try {
      final result = await _channel.invokeMethod<bool>('hasUsagePermission');
      return result ?? false;
    } catch (_) {
      return false;
    }
  }

  /// 권한 설정 화면으로 이동
  Future<void> openPermissionSettings() async {
    try {
      await _channel.invokeMethod('openUsageSettings');
    } catch (e) {
      LogFileService.log('[NH리마인더] UsageStats 설정 화면 오류: $e');
    }
  }

  /// NH 앱 네이티브 실행
  Future<void> launchNhApp() async {
    try {
      await _channel.invokeMethod('launchNhApp');
    } catch (e) {
      LogFileService.log('[NH알리미] NH앱 실행 실패: $e');
    }
  }
}
