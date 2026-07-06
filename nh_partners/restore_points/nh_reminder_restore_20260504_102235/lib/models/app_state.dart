/// NH 리마인더 앱 전역 상태 모델
class AppSettings {
  /// 일시정지 여부 (true = 알림 안 울림)
  final bool isPaused;

  /// 지오펜스 중심 위도
  final double geofenceLat;

  /// 지오펜스 중심 경도
  final double geofenceLng;

  /// 지오펜스 반경 (미터)
  final double geofenceRadius;

  /// 알림 반복 간격 (초, 기본 30초)
  final int repeatIntervalSec;

  const AppSettings({
    this.isPaused = false,
    this.geofenceLat = 37.56580,   // 서대문역 5번 출구 부근 (초기값)
    this.geofenceLng = 126.96640,
    this.geofenceRadius = 30.0,
    this.repeatIntervalSec = 30,
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
