import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'background_monitor_service.dart';
import 'geofence_service.dart';
import 'log_file_service.dart';
import 'native_monitor_bridge.dart';
import 'notification_service.dart';

class MonitoringRecoveryResult {
  const MonitoringRecoveryResult({
    required this.positionUpdated,
    required this.resetStarted,
    this.error,
  });

  final bool positionUpdated;
  final bool resetStarted;
  final Object? error;
}

class MonitoringRecoveryService {
  static Future<MonitoringRecoveryResult> reset({
    required String reason,
    bool recalibrateCurrentPosition = false,
    bool syncNative = true,
    bool resumeMonitoring = true,
    bool clearDismissalOnResume = true,
    bool startFlutterGeofence = true,
  }) async {
    LogFileService.log(
      '[NH알리미] 모니터링 소프트 리셋 시작 — reason:$reason, '
      'recalibrate:$recalibrateCurrentPosition, resume:$resumeMonitoring',
    );

    Object? positionError;
    var positionUpdated = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    final resetGeneration = (prefs.getInt('monitor_reset_generation') ?? 0) + 1;
    await prefs.setInt('monitor_reset_generation', resetGeneration);
    await prefs.setBool('monitor_resetting', true);

    try {
      final wasPaused = prefs.getBool('is_paused') ?? false;
      var lat = prefs.getDouble('geofence_lat') ?? 37.56600;
      var lng = prefs.getDouble('geofence_lng') ?? 126.96730;
      final radius = prefs.getDouble('geofence_radius') ?? 30.0;

      if (recalibrateCurrentPosition) {
        try {
          final position = await _resolveCurrentPosition(
            maxAccuracyMeters: _maxCalibrationAccuracy(radius),
          );
          if (!await _isCurrentReset(prefs, resetGeneration)) {
            return _staleResetResult(
              reason: reason,
              generation: resetGeneration,
              positionUpdated: positionUpdated,
              error: positionError,
            );
          }
          lat = position.latitude;
          lng = position.longitude;
          positionUpdated = true;
          await prefs.setDouble('geofence_lat', lat);
          await prefs.setDouble('geofence_lng', lng);
          LogFileService.log(
            '[NH알리미] 소프트 리셋 위치보정 성공 — '
            'lat:$lat, lng:$lng, 정확도:${position.accuracy.toStringAsFixed(0)}m',
          );
        } catch (e) {
          positionError = e;
          LogFileService.log(
            '[NH알리미] 소프트 리셋 위치보정 실패 — 기존 위치 유지: $e',
          );
        }
      }

      if (!await _isCurrentReset(prefs, resetGeneration)) {
        return _staleResetResult(
          reason: reason,
          generation: resetGeneration,
          positionUpdated: positionUpdated,
          error: positionError,
        );
      }

      if (!resumeMonitoring) {
        await prefs.setBool('is_paused', wasPaused);
        await prefs.setBool('pending_history_reload', true);
        await NotificationService().initialize();
        await NotificationService().stopReminder();
        await NhGeofenceService().stop();
        await BackgroundMonitorService.stop();

        if (!await _isCurrentReset(prefs, resetGeneration)) {
          return _staleResetResult(
            reason: reason,
            generation: resetGeneration,
            positionUpdated: positionUpdated,
            error: positionError,
          );
        }

        if (syncNative) {
          await NativeMonitorBridge.syncConfig(
            isPaused: wasPaused,
            lat: lat,
            lng: lng,
            radius: radius,
          );
        }

        LogFileService.log(
          '[NH알리미] 위치보정만 완료 — '
          'lat:$lat, lng:$lng, 반경:${radius}m, paused:$wasPaused, '
          'positionUpdated:$positionUpdated',
        );

        return MonitoringRecoveryResult(
          positionUpdated: positionUpdated,
          resetStarted: false,
          error: positionError,
        );
      }

      await prefs.setBool('is_paused', false);
      if (clearDismissalOnResume) {
        await prefs.setBool('dismissed_until_exit', false);
      }
      await prefs.setInt('monitor_outside_count', 0);
      await prefs.setInt('geofence_exit_count', 0);
      await prefs.setInt('notif_outside_count', 0);
      await prefs.setBool('pending_history_reload', true);

      await NotificationService().initialize();
      await NotificationService().stopReminder();

      if (!await _isCurrentReset(prefs, resetGeneration)) {
        return _staleResetResult(
          reason: reason,
          generation: resetGeneration,
          positionUpdated: positionUpdated,
          error: positionError,
        );
      }

      if (syncNative) {
        await NativeMonitorBridge.syncConfig(
          isPaused: false,
          lat: lat,
          lng: lng,
          radius: radius,
        );
      }

      if (!await _isCurrentReset(prefs, resetGeneration)) {
        return _staleResetResult(
          reason: reason,
          generation: resetGeneration,
          positionUpdated: positionUpdated,
          error: positionError,
        );
      }

      final geofence = NhGeofenceService();
      await geofence.stop(clearDismissal: clearDismissalOnResume);
      if (!await _isCurrentReset(prefs, resetGeneration)) {
        return _staleResetResult(
          reason: reason,
          generation: resetGeneration,
          positionUpdated: positionUpdated,
          error: positionError,
        );
      }

      if (startFlutterGeofence) {
        await geofence.start(
          lat: lat,
          lng: lng,
          radius: radius,
          isPaused: false,
          showInitialUiEvent: false,
        );
        if (!await _isCurrentReset(prefs, resetGeneration)) {
          return _staleResetResult(
            reason: reason,
            generation: resetGeneration,
            positionUpdated: positionUpdated,
            error: positionError,
          );
        }
      } else {
        LogFileService.log(
          '[NH알리미] Flutter 지오펜스 등록 생략 — 백그라운드 자동 시작, '
          '앱 화면 진입 시 등록 예정',
        );
      }

      await prefs.setBool('monitor_resetting', false);
      if (!await _isCurrentReset(prefs, resetGeneration)) {
        return _staleResetResult(
          reason: reason,
          generation: resetGeneration,
          positionUpdated: positionUpdated,
          error: positionError,
        );
      }

      await BackgroundMonitorService.start(initialDelaySeconds: 5);
      await BackgroundMonitorService.verifyBeforeNotificationRefresh();

      if (!await _isCurrentReset(prefs, resetGeneration)) {
        return _staleResetResult(
          reason: reason,
          generation: resetGeneration,
          positionUpdated: positionUpdated,
          error: positionError,
        );
      }

      if (syncNative) {
        await NativeMonitorBridge.syncConfig(
          isPaused: false,
          lat: lat,
          lng: lng,
          radius: radius,
        );
      }

      LogFileService.log(
        '[NH알리미] 모니터링 소프트 리셋 완료 — '
        'lat:$lat, lng:$lng, 반경:${radius}m, positionUpdated:$positionUpdated',
      );

      return MonitoringRecoveryResult(
        positionUpdated: positionUpdated,
        resetStarted: true,
        error: positionError,
      );
    } finally {
      if (await _isCurrentReset(prefs, resetGeneration)) {
        await prefs.setBool('monitor_resetting', false);
      }
    }
  }

  static Future<bool> _isCurrentReset(
    SharedPreferences prefs,
    int generation,
  ) async {
    await prefs.reload();
    return (prefs.getInt('monitor_reset_generation') ?? 0) == generation;
  }

  static MonitoringRecoveryResult _staleResetResult({
    required String reason,
    required int generation,
    required bool positionUpdated,
    required Object? error,
  }) {
    LogFileService.log(
      '[NH알리미] 모니터링 소프트 리셋 취소 — 더 최신 작업이 시작됨 '
      '(reason:$reason, generation:$generation)',
    );
    return MonitoringRecoveryResult(
      positionUpdated: positionUpdated,
      resetStarted: false,
      error: error,
    );
  }

  static double _maxCalibrationAccuracy(double radius) {
    if (radius < 100) {
      return 100;
    }
    return radius;
  }

  static double _fallbackCalibrationAccuracy(double maxAccuracyMeters) {
    final fallback = maxAccuracyMeters * 1.8;
    if (fallback < 180) {
      return 180;
    }
    if (fallback > 300) {
      return 300;
    }
    return fallback;
  }

  static Future<Position> _resolveCurrentPosition({
    required double maxAccuracyMeters,
  }) async {
    await _ensureLocationServiceReady();
    Position? fallbackCandidate;

    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 10),
      );
      if (_isAccurateEnough(position, maxAccuracyMeters)) {
        return position;
      }
      fallbackCandidate = _betterPosition(fallbackCandidate, position);
      LogFileService.log(
        '[NH알리미] 위치보정 1차 보류 — 정확도 낮음 '
        '(${position.accuracy.toStringAsFixed(0)}m, 기준:${maxAccuracyMeters.toStringAsFixed(0)}m)',
      );
    } catch (e) {
      LogFileService.log('[NH알리미] 위치보정 1차 실패 — high 정확도: $e');
    }

    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium,
        timeLimit: const Duration(seconds: 10),
      );
      if (_isAccurateEnough(position, maxAccuracyMeters)) {
        return position;
      }
      fallbackCandidate = _betterPosition(fallbackCandidate, position);
      LogFileService.log(
        '[NH알리미] 위치보정 2차 보류 — 정확도 낮음 '
        '(${position.accuracy.toStringAsFixed(0)}m, 기준:${maxAccuracyMeters.toStringAsFixed(0)}m)',
      );
    } catch (e) {
      LogFileService.log('[NH알리미] 위치보정 2차 실패 — medium 정확도: $e');
    }

    final lastKnown = await Geolocator.getLastKnownPosition();
    if (lastKnown != null && _isUsableLastKnown(lastKnown, maxAccuracyMeters)) {
      LogFileService.log(
        '[NH알리미] 위치보정 대체 성공 — lastKnown 사용 '
        '(정확도:${lastKnown.accuracy.toStringAsFixed(0)}m)',
      );
      return lastKnown;
    }

    final fallbackAccuracyMeters =
        _fallbackCalibrationAccuracy(maxAccuracyMeters);
    if (fallbackCandidate != null &&
        _isAccurateEnough(fallbackCandidate, fallbackAccuracyMeters)) {
      LogFileService.log(
        '[NH알리미] 위치보정 저정확도 허용 — '
        '정확도:${fallbackCandidate.accuracy.toStringAsFixed(0)}m, '
        '허용기준:${fallbackAccuracyMeters.toStringAsFixed(0)}m',
      );
      return fallbackCandidate;
    }

    throw StateError(
      '현재 위치 정확도가 낮아 위치보정 기준점으로 저장하지 않았습니다.',
    );
  }

  static Future<void> _ensureLocationServiceReady() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw StateError('기기 위치 서비스가 꺼져 있습니다.');
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      permission = await Geolocator.requestPermission();
    }

    if (permission != LocationPermission.always &&
        permission != LocationPermission.whileInUse) {
      throw StateError('위치 권한이 허용되지 않았습니다.');
    }
  }

  static bool _isAccurateEnough(Position position, double maxAccuracyMeters) {
    return position.accuracy <= maxAccuracyMeters;
  }

  static bool _isUsableLastKnown(Position position, double maxAccuracyMeters) {
    final timestamp = position.timestamp;
    final age = DateTime.now().difference(timestamp);
    return age <= const Duration(minutes: 10) &&
        _isAccurateEnough(position, maxAccuracyMeters);
  }

  static Position _betterPosition(Position? current, Position candidate) {
    if (current == null) {
      return candidate;
    }
    return candidate.accuracy < current.accuracy ? candidate : current;
  }
}
