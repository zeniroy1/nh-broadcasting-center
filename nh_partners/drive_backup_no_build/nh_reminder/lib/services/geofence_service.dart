import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:geofence_service/geofence_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'notification_service.dart';
import 'usage_stats_service.dart';
import 'log_file_service.dart';
import 'location_judgment_service.dart';
import 'geofence_ui_event_service.dart';

class NhGeofenceService {
  static final NhGeofenceService _instance = NhGeofenceService._internal();
  factory NhGeofenceService() => _instance;
  NhGeofenceService._internal();

  final _notif = NotificationService();
  final _usage = UsageStatsService();

  GeofenceService? _geoService;
  bool _isRunning = false;
  Timer? _nhAppCheckTimer;
  bool _dismissedUntilExit = false;
  Future<void> _operationQueue = Future.value();

  Future<void> start({
    required double lat,
    required double lng,
    required double radius,
    required bool isPaused,
    bool showInitialUiEvent = true,
  }) async {
    return _enqueueOperation(
      () => _startInternal(
        lat: lat,
        lng: lng,
        radius: radius,
        isPaused: isPaused,
        showInitialUiEvent: showInitialUiEvent,
      ),
    );
  }

  Future<void> _startInternal({
    required double lat,
    required double lng,
    required double radius,
    required bool isPaused,
    required bool showInitialUiEvent,
  }) async {
    if (_isRunning) {
      await _stopInternal();
    }
    if (isPaused) {
      LogFileService.log('[NH알리미] 일시정지 상태 — 지오펜스 시작 안 함');
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    _dismissedUntilExit = prefs.getBool('dismissed_until_exit') ?? false;
    await prefs.setInt('geofence_exit_count', 0);

    _geoService = GeofenceService.instance.setup(
      interval: 5000,
      accuracy: 100,
      loiteringDelayMs: 0,
      statusChangeDelayMs: 0,
      useActivityRecognition: false,
      allowMockLocations: true,
      printDevLog: kDebugMode,
      geofenceRadiusSortType: GeofenceRadiusSortType.DESC,
    );

    final geofence = Geofence(
      id: 'nh_workplace',
      latitude: lat,
      longitude: lng,
      radius: [GeofenceRadius(id: 'r_${radius.toInt()}m', length: radius)],
    );

    _geoService!.addGeofenceStatusChangeListener(_onGeofenceStatusChange);
    _geoService!.addStreamErrorListener(_onError);

    try {
      await _geoService!.start([geofence]);
      _isRunning = true;
      LogFileService.log('[NH알리미] 지오펜스 시작 — lat:$lat, lng:$lng, 반경:${radius}m');

      await _checkIfAlreadyInside(
        lat,
        lng,
        radius,
        prefs,
        showUiEvent: showInitialUiEvent,
      );
    } catch (e) {
      LogFileService.log('[NH알리미] 지오펜스 시작 실패: $e');
    }
  }

  Future<void> _checkIfAlreadyInside(
    double lat,
    double lng,
    double radius,
    SharedPreferences prefs, {
    required bool showUiEvent,
  }) async {
    try {
      final judgment = await LocationJudgmentService.fromCurrentPosition(
        centerLat: lat,
        centerLng: lng,
        radius: radius,
      );
      LogFileService.log(
          '[NH알리미] 현재 위치 확인 — 거리: ${judgment.distance.toStringAsFixed(0)}m, 정확도:${judgment.accuracy.toStringAsFixed(0)}m');

      if (judgment.zone == LocationZone.reliableInside) {
        if (_dismissedUntilExit) {
          LogFileService.log('[NH알리미] 이미 범위 안 — 차단 플래그 ON, 알림 없음');
          return;
        }
        if (_notif.isActive) {
          LogFileService.log('[NH알리미] 이미 범위 안 — 알림 이미 활성 중');
          return;
        }
        LogFileService.log(
            '[NH알리미] 시작 시 이미 범위 안 → 즉시 알림 시작 (${judgment.distance.toStringAsFixed(0)}m)');
        if (showUiEvent) {
          GeofenceUiEventService.show('지오펜스 범위 안입니다. 알림 모니터링이 시작됩니다.');
        }
        final intervalSec = prefs.getInt('repeat_interval_sec') ?? 60;
        await _notif.stopReminder();
        await _notif.startReminder(intervalSeconds: intervalSec);
        _startNhAppCheck();
      } else if (judgment.zone == LocationZone.unreliableInside) {
        LogFileService.log('[NH알리미] 시작 시 범위 안 보류 — GPS 정확도 낮음 '
            '(${judgment.decisionText})');
        if (showUiEvent) {
          GeofenceUiEventService.show(
            '지오펜스 범위 안이지만 GPS 정확도가 낮아 재확인 중입니다.',
            isWarning: true,
          );
        }
      } else {
        LogFileService.log(
            '[NH알리미] 시작 시 범위 밖 (${judgment.distance.toStringAsFixed(0)}m) — ENTER 대기');
        if (showUiEvent) {
          GeofenceUiEventService.show('현재 위치는 지오펜스 범위 밖입니다.', isWarning: true);
        }
      }
    } catch (e) {
      LogFileService.log('[NH알리미] 시작 시 위치 확인 실패: $e');
    }
  }

  Future<void> stop() async {
    return _enqueueOperation(_stopInternal);
  }

  Future<void> _stopInternal() async {
    _geoService?.removeGeofenceStatusChangeListener(_onGeofenceStatusChange);
    _geoService?.removeStreamErrorListener(_onError);
    await _geoService?.stop();
    _geoService = null;
    _isRunning = false;
    _stopNhAppCheck();
    await _notif.stopReminder();
    _dismissedUntilExit = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('dismissed_until_exit', false);
    LogFileService.log('[NH알리미] 지오펜스 중지 완료');
  }

  Future<void> _enqueueOperation(Future<void> Function() operation) {
    _operationQueue = _operationQueue.then(
      (_) => operation(),
      onError: (_) => operation(),
    );
    return _operationQueue;
  }

  bool get isRunning => _isRunning;

  Future<void> startReminderAndMonitor(int intervalSec) async {
    _dismissedUntilExit = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('dismissed_until_exit', false);
    await _notif.stopReminder();
    await _notif.startReminder(intervalSeconds: intervalSec);
    _startNhAppCheck();
    LogFileService.log('[NH알리미] 강제 알림 시작 ($intervalSec초 간격)');
  }

  Future<void> dismissUntilExit() async {
    _dismissedUntilExit = true;
    await _notif.stopReminder();
    _stopNhAppCheck();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('dismissed_until_exit', true);
    LogFileService.log('[NH알리미] 출퇴근 확인 완료 — 이탈 전까지 알림 차단');
  }

  Future<void> _onGeofenceStatusChange(
    Geofence geofence,
    GeofenceRadius radius,
    GeofenceStatus status,
    Location location,
  ) async {
    LogFileService.log('[NH알리미] 지오펜스 이벤트: ${status.name}');

    if (status == GeofenceStatus.ENTER) {
      final prefs = await SharedPreferences.getInstance();
      _dismissedUntilExit = prefs.getBool('dismissed_until_exit') ?? false;
      await prefs.setInt('geofence_exit_count', 0);

      if (_dismissedUntilExit) {
        LogFileService.log('[NH알리미] ENTER — 차단 플래그 ON, 무시');
        return;
      }
      if (prefs.getBool('is_paused') ?? false) {
        LogFileService.log('[NH알리미] ENTER — 일시정지 중, 무시');
        return;
      }
      if (_notif.isActive) {
        LogFileService.log('[NH알리미] ENTER — 알림 이미 활성 중, 무시');
        return;
      }
      if (!await _isWithinConfiguredRadius(prefs)) {
        return;
      }

      LogFileService.log('[NH알리미] ENTER — 알림 시작!');
      final intervalSec = prefs.getInt('repeat_interval_sec') ?? 60;
      await _notif.startReminder(intervalSeconds: intervalSec);
      _startNhAppCheck();
    }

    if (status == GeofenceStatus.EXIT) {
      _verifyAndHandleExit();
    }
  }

  Future<bool> _isWithinConfiguredRadius(SharedPreferences prefs) async {
    try {
      await prefs.reload();
      final centerLat = prefs.getDouble('geofence_lat') ?? 37.56600;
      final centerLng = prefs.getDouble('geofence_lng') ?? 126.96730;
      final radius = prefs.getDouble('geofence_radius') ?? 30.0;
      final judgment = await LocationJudgmentService.fromCurrentPosition(
        centerLat: centerLat,
        centerLng: centerLng,
        radius: radius,
      );

      if (judgment.zone == LocationZone.reliableInside) {
        LogFileService.log('[NH알리미] ENTER 검증 통과 — ${judgment.decisionText}');
        GeofenceUiEventService.show('지오펜스 범위로 들어왔습니다.');
        return true;
      }

      if (judgment.zone == LocationZone.unreliableInside) {
        LogFileService.log('[NH알리미] ENTER 검증 보류 — GPS 정확도 낮음 '
            '(${judgment.decisionText}), 알림 시작 안 함');
        GeofenceUiEventService.show('지오펜스 진입 신호가 있지만 GPS 정확도가 낮아 재확인 중입니다.',
            isWarning: true);
        return false;
      }

      LogFileService.log(
          '[NH알리미] ENTER 검증 — ${judgment.zoneLabel} (${judgment.outsideText}), 알림 시작 안 함');
      return false;
    } catch (e) {
      LogFileService.log('[NH알리미] ENTER 검증 실패 — 알림 시작 안 함: $e');
      return false;
    }
  }

  Future<void> _verifyAndHandleExit() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final centerLat = prefs.getDouble('geofence_lat') ?? 37.56600;
      final centerLng = prefs.getDouble('geofence_lng') ?? 126.96730;
      final radius = prefs.getDouble('geofence_radius') ?? 30.0;

      final judgment = await LocationJudgmentService.fromCurrentPosition(
        centerLat: centerLat,
        centerLng: centerLng,
        radius: radius,
      );

      if (judgment.isOutside) {
        final exitCount = (prefs.getInt('geofence_exit_count') ?? 0) + 1;

        if (_dismissedUntilExit &&
            !LocationJudgmentService.isConfirmedExitAfterDismissal(judgment)) {
          await prefs.setInt('geofence_exit_count', 0);
          LogFileService.log(
              '[NH알리미] EXIT — 출퇴근 확인 차단 유지 (${judgment.outsideText}, 확정이탈 기준 ${LocationJudgmentService.confirmedExitThreshold(radius).toStringAsFixed(0)}m)');
        } else {
          await prefs.setInt('geofence_exit_count', exitCount);

          if (exitCount >= 2) {
            await _notif.stopReminder();
            _stopNhAppCheck();
            _dismissedUntilExit = false;
            await prefs.setBool('dismissed_until_exit', false);
            await prefs.setInt('geofence_exit_count', 0);
            LogFileService.log(
                '[NH알리미] EXIT 2회 확인 (${judgment.outsideText}) — 알림 중지, 플래그 초기화');
            GeofenceUiEventService.show('지오펜스 범위를 벗어났습니다.', isWarning: true);
          } else {
            LogFileService.log(
                '[NH알리미] EXIT 위치 튐 감지 — 1회 유예 (${judgment.outsideText})');
          }
        }
      } else {
        await prefs.setInt('geofence_exit_count', 0);
        LogFileService.log(
            '[NH알리미] GPS 흔들림 (${judgment.distance.toStringAsFixed(0)}m, 기준 ${judgment.exitThreshold.toStringAsFixed(0)}m) — 무시');
      }
    } catch (e) {
      LogFileService.log('[NH알리미] EXIT 검증 실패: $e');
    }
  }

  void _onError(dynamic error) {
    LogFileService.log('[NH알리미] 지오펜스 오류: $error');
  }

  void _startNhAppCheck() {
    _nhAppCheckTimer?.cancel();
    _nhAppCheckTimer = Timer.periodic(
      const Duration(seconds: 10),
      (_) async {
        if (!_notif.isActive) {
          _stopNhAppCheck();
          return;
        }
        final hasPerm = await _usage.hasPermission();
        if (!hasPerm) return;

        final isRunning = await _usage.isNhAppInForeground();
        if (isRunning) {
          LogFileService.log('[NH알리미] NH파트너스 앱 감지 → 알림 종료');
          await dismissUntilExit();
        }
      },
    );
  }

  void _stopNhAppCheck() {
    _nhAppCheckTimer?.cancel();
    _nhAppCheckTimer = null;
  }
}
