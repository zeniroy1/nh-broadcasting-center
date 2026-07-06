class AppSettings {
  static const defaultGeofenceLat = 37.56600;
  static const defaultGeofenceLng = 126.96730;
  static const defaultGeofenceRadius = 30.0;
  static const defaultRepeatIntervalSec = 30;

  final bool isPaused;
  final double geofenceLat;
  final double geofenceLng;
  final double geofenceRadius;
  final int repeatIntervalSec;

  const AppSettings({
    this.isPaused = false,
    this.geofenceLat = defaultGeofenceLat,
    this.geofenceLng = defaultGeofenceLng,
    this.geofenceRadius = defaultGeofenceRadius,
    this.repeatIntervalSec = defaultRepeatIntervalSec,
  });

  AppSettings copyWith({
    bool? isPaused,
    double? geofenceLat,
    double? geofenceLng,
    double? geofenceRadius,
    int? repeatIntervalSec,
  }) {
    return AppSettings(
      isPaused: isPaused ?? this.isPaused,
      geofenceLat: geofenceLat ?? this.geofenceLat,
      geofenceLng: geofenceLng ?? this.geofenceLng,
      geofenceRadius: geofenceRadius ?? this.geofenceRadius,
      repeatIntervalSec: repeatIntervalSec ?? this.repeatIntervalSec,
    );
  }
}
