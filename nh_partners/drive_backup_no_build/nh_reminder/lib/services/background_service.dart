import 'package:shared_preferences/shared_preferences.dart';
import 'notification_service.dart';
import 'geofence_service.dart';
import 'background_monitor_service.dart';
import 'log_file_service.dart';
import 'native_monitor_bridge.dart';

class NhBackgroundServiceManager {
  static Future<void> _updateQueue = Future.value();

  static Future<void> sendUpdate({
    required bool isPaused,
    required double lat,
    required double lng,
    required double radius,
    bool forceStartReminder = false,
    bool showInitialUiEvent = true,
  }) async {
    _updateQueue = _updateQueue.then(
      (_) => _applyUpdate(
        isPaused: isPaused,
        lat: lat,
        lng: lng,
        radius: radius,
        forceStartReminder: forceStartReminder,
        showInitialUiEvent: showInitialUiEvent,
      ),
      onError: (_) => _applyUpdate(
        isPaused: isPaused,
        lat: lat,
        lng: lng,
        radius: radius,
        forceStartReminder: forceStartReminder,
        showInitialUiEvent: showInitialUiEvent,
      ),
    );
    return _updateQueue;
  }

  static Future<void> _applyUpdate({
    required bool isPaused,
    required double lat,
    required double lng,
    required double radius,
    required bool forceStartReminder,
    required bool showInitialUiEvent,
  }) async {
    LogFileService.log(
      '[NH알리미] 설정 반영 요청 — paused:$isPaused, lat:$lat, lng:$lng, '
      '반경:${radius}m, forceStart:$forceStartReminder',
    );
    await NativeMonitorBridge.syncConfig(
      isPaused: isPaused,
      lat: lat,
      lng: lng,
      radius: radius,
    );
    final geoSvc = NhGeofenceService();
    await geoSvc.stop();

    if (!isPaused) {
      await geoSvc.start(
        lat: lat,
        lng: lng,
        radius: radius,
        isPaused: false,
        showInitialUiEvent: showInitialUiEvent,
      );
      await BackgroundMonitorService.start(initialDelaySeconds: 5);
      if (forceStartReminder && !NotificationService().isActive) {
        final prefs = await SharedPreferences.getInstance();
        final intervalSec = prefs.getInt('repeat_interval_sec') ?? 60;
        await geoSvc.startReminderAndMonitor(intervalSec);
      }
    } else {
      await BackgroundMonitorService.stop();
    }
  }

  static Future<void> sendIntervalUpdate(int intervalSec) async {
    LogFileService.log('[NH알리미] 알림 간격 변경 요청 — $intervalSec초');
    await NotificationService().restartReminderIfExists(intervalSec);
  }
}
