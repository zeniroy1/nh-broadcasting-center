import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/app_state.dart';
import '../services/background_monitor_service.dart';

const _kIsPaused = 'is_paused';
const _kUserPaused = 'user_paused';
const _kGeofenceLat = 'geofence_lat';
const _kGeofenceLng = 'geofence_lng';
const _kGeofenceRadius = 'geofence_radius';
const _kRepeatInterval = 'repeat_interval_sec';

class SettingsNotifier extends StateNotifier<AppSettings> {
  SettingsNotifier({AppSettings? initialSettings})
      : super(initialSettings ?? const AppSettings()) {
    if (initialSettings == null) {
      _load();
    }
  }

  static Future<AppSettings> loadFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final rawRadius =
        prefs.getDouble(_kGeofenceRadius) ?? AppSettings.defaultGeofenceRadius;
    final radius = AppSettings.clampGeofenceRadius(rawRadius);
    if (radius != rawRadius) {
      await prefs.setDouble(_kGeofenceRadius, radius);
    }
    return AppSettings(
      isPaused: prefs.getBool(_kIsPaused) ?? false,
      geofenceLat:
          prefs.getDouble(_kGeofenceLat) ?? AppSettings.defaultGeofenceLat,
      geofenceLng:
          prefs.getDouble(_kGeofenceLng) ?? AppSettings.defaultGeofenceLng,
      geofenceRadius: radius,
      repeatIntervalSec: prefs.getInt(_kRepeatInterval) ??
          AppSettings.defaultRepeatIntervalSec,
    );
  }

  Future<void> _load() async {
    state = await loadFromPrefs();
  }

  Future<void> togglePause() async {
    final prefs = await SharedPreferences.getInstance();
    final next = !state.isPaused;
    await prefs.setBool(_kIsPaused, next);
    await prefs.setBool(_kUserPaused, next);
    state = state.copyWith(isPaused: next);
  }

  Future<void> updateGeofenceLocation(double lat, double lng) async {
    final prefs = await SharedPreferences.getInstance();
    final generation =
        await BackgroundMonitorService.beginGeofenceConfigUpdate(prefs);
    try {
      await prefs.setDouble(_kGeofenceLat, lat);
      await prefs.setDouble(_kGeofenceLng, lng);
      await BackgroundMonitorService.clearApproachPendingState(prefs);
    } finally {
      await BackgroundMonitorService.finishGeofenceConfigUpdate(
        prefs,
        generation,
      );
    }
    state = state.copyWith(geofenceLat: lat, geofenceLng: lng);
  }

  Future<void> resetToDefault() async {
    final prefs = await SharedPreferences.getInstance();
    const defaultLat = AppSettings.defaultGeofenceLat;
    const defaultLng = AppSettings.defaultGeofenceLng;
    final generation =
        await BackgroundMonitorService.beginGeofenceConfigUpdate(prefs);
    try {
      await prefs.setDouble(_kGeofenceLat, defaultLat);
      await prefs.setDouble(_kGeofenceLng, defaultLng);
      await BackgroundMonitorService.clearApproachPendingState(prefs);
    } finally {
      await BackgroundMonitorService.finishGeofenceConfigUpdate(
        prefs,
        generation,
      );
    }
    state = state.copyWith(geofenceLat: defaultLat, geofenceLng: defaultLng);
  }

  Future<void> reload() async => _load();

  Future<void> updateRadius(double radius) async {
    final prefs = await SharedPreferences.getInstance();
    final clampedRadius = AppSettings.clampGeofenceRadius(radius);
    final generation =
        await BackgroundMonitorService.beginGeofenceConfigUpdate(prefs);
    try {
      await prefs.setDouble(_kGeofenceRadius, clampedRadius);
      await BackgroundMonitorService.clearApproachPendingState(prefs);
    } finally {
      await BackgroundMonitorService.finishGeofenceConfigUpdate(
        prefs,
        generation,
      );
    }
    state = state.copyWith(geofenceRadius: clampedRadius);
  }

  Future<void> updateRepeatInterval(int seconds) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_kRepeatInterval, seconds);
    state = state.copyWith(repeatIntervalSec: seconds);
  }
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, AppSettings>(
  (ref) => SettingsNotifier(),
);
