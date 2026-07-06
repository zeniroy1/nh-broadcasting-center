import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:geofence_service/geofence_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'notification_service.dart';
import 'usage_stats_service.dart';

/// NH 리마인더 지오펜싱 서비스
///
/// - 서대문역 5번 출구 반경 30m 진입 감지
/// - ENTER 이벤트 발생 시 1분 반복 알림 시작
/// - GeofencingClient + FusedLocationProvider 기반
/// - BOOT_COMPLETED 후 자동 재등록
class NhGeofenceService {
  static final NhGeofenceService _instance = NhGeofenceService._internal();
  factory NhGeofenceService() => _instance;
  NhGeofenceService._internal();

  final _notif = NotificationService();
  final _usage = UsageStatsService();

  GeofenceService? _geoService;
  bool _isRunning = false;

  // NH앱 포그라운드 감지 폴링 타이머
  Timer? _nhAppCheckTimer;

  /// 지오펜스 서비스 초기화 및 시작
  ///
  /// [lat], [lng]: 지오펜스 중심 좌표
  /// [radius]: 반경 (미터, 기본 30m)
  /// [isPaused]: 일시정지 상태이면 시작하지 않음
  Future<void> start({
    required double lat,
    required double lng,
    required double radius,
    required bool isPaused,
  }) async {
    if (_isRunning) return;
    if (isPaused) {
      debugPrint('[NH리마인더] 일시정지 상태 — 지오펜스 시작 안 함');
      return;
    }

    _geoService = GeofenceService.instance.setup(
      interval: 5000,                        // 5초마다 위치 갱신
      accuracy: 100,                          // 100m 이내 정확도 허용
      loiteringDelayMs: 0,                    // 진입 즉시 이벤트
      statusChangeDelayMs: 0,
      useActivityRecognition: false,
      allowMockLocations: false,
      printDevLog: kDebugMode,
      geofenceRadiusSortType: GeofenceRadiusSortType.DESC,
    );

    // 지오펜스 정의
    final geofence = Geofence(
      id: 'nh_workplace',
      latitude: lat,
      longitude: lng,
      radius: [
        GeofenceRadius(id: 'r_${radius.toInt()}m', length: radius),
      ],
    );

    // ENTER 이벤트 리스너
    _geoService!.addGeofenceStatusChangeListener(_onGeofenceStatusChange);
    _geoService!.addStreamErrorListener(_onError);

    try {
      await _geoService!.start([geofence]);
      _isRunning = true;
      debugPrint('[NH리마인더] 지오펜스 시작 — lat:$lat, lng:$lng, 반경:${radius}m');
    } catch (e) {
      debugPrint('[NH리마인더] 지오펜스 시작 실패: $e');
    }
  }

  /// 지오펜스 서비스 중지
  Future<void> stop() async {
    _geoService?.removeGeofenceStatusChangeListener(_onGeofenceStatusChange);
    await _geoService?.stop();
    _isRunning = false;
    _stopNhAppCheck();
    debugPrint('[NH리마인더] 지오펜스 중지');
  }

  bool get isRunning => _isRunning;

  /// 지오펜스 상태 변경 핸들러
  Future<void> _onGeofenceStatusChange(
    Geofence geofence,
    GeofenceRadius radius,
    GeofenceStatus status,
    Location location,
  ) async {
    debugPrint('[NH리마인더] 지오펜스 이벤트: ${status.name}');

    if (status == GeofenceStatus.ENTER) {
      // 일시정지 상태 재확인
      final prefs = await SharedPreferences.getInstance();
      final isPaused = prefs.getBool('is_paused') ?? false;
      if (isPaused) {
        debugPrint('[NH리마인더] 일시정지 중 — 진입 알림 무시');
        return;
      }

      // 이미 알림 활성 중이면 무시
      if (_notif.isActive) return;

      debugPrint('[NH리마인더] 지정 구역 진입! 알림 시작');
      final intervalSec = prefs.getInt('repeat_interval_sec') ?? 60;
      _notif.startReminder(intervalSeconds: intervalSec);

      // NH앱 포그라운드 감지 폴링 시작 (Android UsageStats)
      _startNhAppCheck();
    }

    // EXIT는 무시 (알림 종료 조건이 아님)
  }

  void _onError(dynamic error) {
    debugPrint('[NH리마인더] 지오펜스 오류: $error');
  }

  /// NH파트너스 앱 포그라운드 실행 감지 (Android UsageStatsManager)
  void _startNhAppCheck() {
    _nhAppCheckTimer?.cancel();
    _nhAppCheckTimer = Timer.periodic(
      const Duration(seconds: 10), // 10초마다 확인
      (_) async {
        if (!_notif.isActive) {
          _stopNhAppCheck();
          return;
        }
        final isRunning = await _usage.isNhAppInForeground();
        if (isRunning) {
          debugPrint('[NH리마인더] NH파트너스 앱 실행 감지 → 알림 종료');
          _notif.stopReminder();
          _stopNhAppCheck();
        }
      },
    );
  }

  void _stopNhAppCheck() {
    _nhAppCheckTimer?.cancel();
    _nhAppCheckTimer = null;
  }
}
