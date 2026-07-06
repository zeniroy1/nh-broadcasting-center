import 'package:flutter/services.dart';

import 'log_file_service.dart';

/// NH알리미에서 인정한 클릭 경로로 NH파트너스 앱을 실행한다.
class NhAppLauncherService {
  static const _channel =
      MethodChannel('com.example.nh_reminder/nh_app_launcher');

  /// NH 앱 네이티브 실행
  Future<void> launchNhApp() async {
    try {
      await _channel.invokeMethod('launchNhApp');
    } catch (e) {
      LogFileService.log('[NH알리미] NH앱 실행 실패: $e');
    }
  }
}
