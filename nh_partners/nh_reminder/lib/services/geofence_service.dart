import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:geofence_service/geofence_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'notification_service.dart';
import 'log_file_service.dart';
import 'location_judgment_service.dart';
import 'arrival_confirmation_service.dart';
import 'geofence_ui_event_service.dart';

class NhGeofenceService {
  static final NhGeofenceService _instance = NhGeofenceService._internal();
  factory NhGeofenceService() => _instance;
  NhGeofenceService._internal();

  final _notif = NotificationService();
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
      await _stopInternal(
        clearDismissal: false,
        stopReminder: isPaused,
      );
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
      await _saveRecentJudgment(prefs, judgment, '지오펜스 시작 위치 확인');
      LogFileService.log(
          '[NH알리미] 현재 위치 확인 — 거리: ${judgment.distance.toStringAsFixed(0)}m, 정확도:${judgment.accuracy.toStringAsFixed(0)}m');

      if (judgment.zone == LocationZone.reliableInside) {
        if (_dismissedUntilExit) {
          LogFileService.log('[NH알리미] 이미 범위 안 — 차단 플래그 ON, 알림 없음');
          return;
        }
        if (await _isReminderActive(prefs)) {
          _startNhAppCheck();
          LogFileService.log('[NH알리미] 이미 범위 안 — 알림 이미 활성 중, 새 알림 시작 생략');
          return;
        }
        if (!await ArrivalConfirmationService.confirmIfNeeded(
          prefs: prefs,
          judgment: judgment,
          source: '시작 시 위치 확인',
        )) {
          return;
        }
        LogFileService.log(
            '[NH알리미] 시작 시 이미 범위 안 → 즉시 알림 시작 (${judgment.distance.toStringAsFixed(0)}m)');
        if (showUiEvent) {
          GeofenceUiEventService.show('지오펜스 범위 안입니다. 알림 모니터링이 시작됩니다.');
        }
        final intervalSec = prefs.getInt('repeat_interval_sec') ??
            NotificationService.defaultRepeatIntervalSeconds;
        if (await _notif.startReminderOnce(
          source: '시작 시 위치 확인',
          intervalSeconds: intervalSec,
        )) {
          _startNhAppCheck();
        }
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

  Future<void> stop({
    bool clearDismissal = true,
    bool stopReminder = true,
  }) async {
    return _enqueueOperation(
      () => _stopInternal(
        clearDismissal: clearDismissal,
        stopReminder: stopReminder,
      ),
    );
  }

  Future<void> _stopInternal({
    required bool clearDismissal,
    bool stopReminder = true,
  }) async {
    _geoService?.removeGeofenceStatusChangeListener(_onGeofenceStatusChange);
    _geoService?.removeStreamErrorListener(_onError);
    await _geoService?.stop();
    _geoService = null;
    _isRunning = false;
    _stopNhAppCheck();
    if (stopReminder) {
      await _notif.stopReminder();
    }
    if (clearDismissal) {
      _dismissedUntilExit = false;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('dismissed_until_exit', false);
      LogFileService.log('[NH알리미] 지오펜스 중지 완료 — 차단 플래그 해제');
    } else {
      final reminderText = stopReminder ? '' : ', 반복 알림 보존';
      LogFileService.log('[NH알리미] 지오펜스 재시작 준비 완료 — 차단 플래그 유지$reminderText');
    }
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
    if (await _notif.startReminderOnce(
      source: '강제 알림 시작',
      intervalSeconds: intervalSec,
      clearDismissal: true,
    )) {
      _startNhAppCheck();
      LogFileService.log('[NH알리미] 강제 알림 시작 ($intervalSec초 간격)');
    }
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
      if (await _isReminderActive(prefs)) {
        _startNhAppCheck();
        LogFileService.log('[NH알리미] ENTER — 알림 이미 활성 중, 새 알림 시작 생략');
        return;
      }
      if (!await _isWithinConfiguredRadius(prefs)) {
        return;
      }

      final intervalSec = prefs.getInt('repeat_interval_sec') ??
          NotificationService.defaultRepeatIntervalSeconds;
      if (await _notif.startReminderOnce(
        source: 'ENTER 검증',
        intervalSeconds: intervalSec,
      )) {
        LogFileService.log('[NH알리미] ENTER — 알림 시작!');
        _startNhAppCheck();
      }
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
      await _saveRecentJudgment(prefs, judgment, 'ENTER 검증');

      if (judgment.zone == LocationZone.reliableInside ||
          judgment.isArrivalGraceInside) {
        if (judgment.zone != LocationZone.reliableInside) {
          LogFileService.log('[NH알리미] ENTER 검증 — 도착 후보 경계 신호 '
              '(${judgment.decisionText})');
        }
        if (!await ArrivalConfirmationService.confirmIfNeeded(
          prefs: prefs,
          judgment: judgment,
          source: 'ENTER 검증',
        )) {
          return false;
        }
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
      await _saveRecentJudgment(prefs, judgment, 'EXIT 검증');

      if (judgment.isOutside) {
        await prefs.setInt('arrival_grace_confirm_count', 0);
        final reminderActive = await _isReminderActive(prefs);

        if (reminderActive) {
          final activeExitThreshold =
              LocationJudgmentService.confirmedExitThreshold(radius);
          if (judgment.distance <= activeExitThreshold) {
            await prefs.setInt('geofence_exit_count', 0);
            LogFileService.log(
              '[NH알리미] EXIT — 범위 밖이지만 알림 활성 보호구간 유지 '
              '(${judgment.outsideText}, 알림중지 기준 '
              '${activeExitThreshold.toStringAsFixed(0)}m)',
            );
          } else {
            final exitCount = (prefs.getInt('geofence_exit_count') ?? 0) + 1;
            await prefs.setInt('geofence_exit_count', exitCount);
            if (exitCount >= 2) {
              await _notif.stopReminder();
              _stopNhAppCheck();
              _dismissedUntilExit = false;
              await prefs.setBool('dismissed_until_exit', false);
              await prefs.setInt('geofence_exit_count', 0);
              LogFileService.log(
                '[NH알리미] EXIT 2회 확인 '
                '(${judgment.outsideText}, 알림중지 기준 '
                '${activeExitThreshold.toStringAsFixed(0)}m) — 알림 중지',
              );
              GeofenceUiEventService.show('지오펜스 범위를 벗어났습니다.', isWarning: true);
            } else {
              LogFileService.log(
                '[NH알리미] EXIT 알림 활성 이탈 후보 — 1회 유예 '
                '(${judgment.outsideText}, 알림중지 기준 '
                '${activeExitThreshold.toStringAsFixed(0)}m)',
              );
            }
          }
        } else if (_dismissedUntilExit &&
            !LocationJudgmentService.isConfirmedExitAfterDismissal(judgment)) {
          await prefs.setInt('geofence_exit_count', 0);
          LogFileService.log(
              '[NH알리미] EXIT — 출퇴근 확인 차단 유지 (${judgment.outsideText}, 차단해제 기준 ${LocationJudgmentService.dismissalResetExitThreshold(radius).toStringAsFixed(0)}m)');
        } else {
          final exitCount = (prefs.getInt('geofence_exit_count') ?? 0) + 1;
          await prefs.setInt('geofence_exit_count', exitCount);

          if (exitCount >= 2) {
            _stopNhAppCheck();
            _dismissedUntilExit = false;
            await prefs.setBool('dismissed_until_exit', false);
            await prefs.setInt('geofence_exit_count', 0);
            LogFileService.log(
                '[NH알리미] EXIT 2회 확인 (${judgment.outsideText}) — 차단 플래그 초기화');
            GeofenceUiEventService.show('지오펜스 범위를 벗어났습니다.', isWarning: true);
          } else {
            LogFileService.log(
                '[NH알리미] EXIT 위치 튐 감지 — 1회 유예 (${judgment.outsideText})');
          }
        }
      } else {
        await prefs.setInt('geofence_exit_count', 0);
        if (!judgment.isArrivalGraceInside) {
          await prefs.setInt('arrival_grace_confirm_count', 0);
        }
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
    // 출퇴근 확인은 NH알리미 알림/버튼 클릭만 인정한다.
    // NH파트너스 앱을 사용자가 직접 여는 동작은 기록하거나 감시하지 않는다.
    _nhAppCheckTimer?.cancel();
    _nhAppCheckTimer = null;
  }

  void _stopNhAppCheck() {
    _nhAppCheckTimer?.cancel();
    _nhAppCheckTimer = null;
  }

  Future<bool> _isReminderActive([SharedPreferences? prefs]) async {
    final store = prefs ?? await SharedPreferences.getInstance();
    await store.reload();
    return _notif.isActive || (store.getBool('notif_active') ?? false);
  }

  Future<void> _saveRecentJudgment(
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
}
