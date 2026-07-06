import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/app_state.dart';

// SharedPreferences 키
const _kIsPaused = 'is_paused';
const _kGeofenceLat = 'geofence_lat';
const _kGeofenceLng = 'geofence_lng';
const _kGeofenceRadius = 'geofence_radius';
const _kRepeatInterval = 'repeat_interval_sec';

/// 설정값을 SharedPreferences에서 불러오고 저장하는 Notifier
class SettingsNotifier extends StateNotifier<AppSettings> {
  SettingsNotifier() : super(const AppSettings()) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = AppSettings(
      isPaused: prefs.getBool(_kIsPaused) ?? false,
      geofenceLat: prefs.getDouble(_kGeofenceLat) ?? 37.56580,
      geofenceLng: prefs.getDouble(_kGeofenceLng) ?? 126.96640,
      geofenceRadius: prefs.getDouble(_kGeofenceRadius) ?? 30.0,
      repeatIntervalSec: prefs.getInt(_kRepeatInterval) ?? 60,
    );
  }

  /// 일시정지 토글
  Future<void> togglePause() async {
    final prefs = await SharedPreferences.getInstance();
    final next = !state.isPaused;
    await prefs.setBool(_kIsPaused, next);
    state = state.copyWith(isPaused: next);
  }

  /// 지오펜스 위치 업데이트 (온보딩에서 현재 위치로 설정)
  Future<void> updateGeofenceLocation(double lat, double lng) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_kGeofenceLat, lat);
    await prefs.setDouble(_kGeofenceLng, lng);
    state = state.copyWith(geofenceLat: lat, geofenceLng: lng);
  }

  /// 반경 업데이트
  /// 서대문역(기본값)으로 지오펜스 위치 초기화
  Future<void> resetToDefault() async {
    final prefs = await SharedPreferences.getInstance();
    const defaultLat = 37.56580;
    const defaultLng = 126.96640;
    await prefs.setDouble(_kGeofenceLat, defaultLat);
    await prefs.setDouble(_kGeofenceLng, defaultLng);
    state = state.copyWith(geofenceLat: defaultLat, geofenceLng: defaultLng);
  }

  Future<void> updateRadius(double radius) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_kGeofenceRadius, radius);
    state = state.copyWith(geofenceRadius: radius);
  }

  /// 반복 간격 업데이트
  Future<void> updateRepeatInterval(int seconds) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_kRepeatInterval, seconds);
    state = state.copyWith(repeatIntervalSec: seconds);
  }
}

final settingsProvider =
    StateNotifierProvider<SettingsNotifier, AppSettings>(
  (ref) => SettingsNotifier(),
);
