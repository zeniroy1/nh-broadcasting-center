import 'package:geolocator/geolocator.dart' as geo;

enum LocationZone {
  reliableInside,
  unreliableInside,
  boundary,
  outside,
  farOutside,
}

class LocationJudgment {
  const LocationJudgment({
    required this.zone,
    required this.distance,
    required this.radius,
    required this.accuracy,
    required this.deepInsideThreshold,
    required this.accuracyThreshold,
    required this.exitThreshold,
    required this.initialAlertThreshold,
  });

  final LocationZone zone;
  final double distance;
  final double radius;
  final double accuracy;
  final double deepInsideThreshold;
  final double accuracyThreshold;
  final double exitThreshold;
  final double initialAlertThreshold;

  bool get isReliableInside => zone == LocationZone.reliableInside;
  bool get isInside =>
      zone == LocationZone.reliableInside ||
      zone == LocationZone.unreliableInside;
  bool get isOutside =>
      zone == LocationZone.outside || zone == LocationZone.farOutside;
  bool get isInitialAlertCandidate =>
      distance <= initialAlertThreshold &&
      accuracy <= LocationJudgmentService.initialAlertAccuracyThresholdMeters;
  bool get isStrongInitialAlertCandidate =>
      distance <= LocationJudgmentService.strongInitialAlertDistanceMeters &&
      accuracy <= LocationJudgmentService.strongInitialAlertAccuracyMeters;
  bool get isApproachPendingSeed =>
      distance >= LocationJudgmentService.approachPendingMinMeters &&
      distance <= LocationJudgmentService.approachPendingMaxMeters &&
      accuracy <= LocationJudgmentService.approachPendingAccuracyMeters;

  String get zoneLabel {
    switch (zone) {
      case LocationZone.reliableInside:
        return '범위 안';
      case LocationZone.unreliableInside:
        return '범위 안 보류';
      case LocationZone.boundary:
        return '경계 흔들림';
      case LocationZone.outside:
        return '범위 밖';
      case LocationZone.farOutside:
        return '먼 범위 밖';
    }
  }

  String get decisionText {
    final passed = zone == LocationZone.reliableInside;
    return '거리 ${distance.toStringAsFixed(0)}m / 반경 ${radius.toStringAsFixed(0)}m, '
        '정확도 ${accuracy.toStringAsFixed(0)}m, '
        '통과기준: 중심권 ${deepInsideThreshold.toStringAsFixed(0)}m 이내 또는 정확도 ${accuracyThreshold.toStringAsFixed(0)}m 이하, '
        '이탈기준: ${exitThreshold.toStringAsFixed(0)}m 초과, '
        '판정:${passed ? '통과' : '보류'}';
  }

  String get outsideText =>
      '${distance.toStringAsFixed(0)}m, 기준 ${exitThreshold.toStringAsFixed(0)}m, '
      '정확도 ${accuracy.toStringAsFixed(0)}m';

  String get initialAlertText => '거리 ${distance.toStringAsFixed(0)}m / 초기알림기준 '
      '${initialAlertThreshold.toStringAsFixed(0)}m, '
      '정확도 ${accuracy.toStringAsFixed(0)}m / 기준 '
      '${LocationJudgmentService.initialAlertAccuracyThresholdMeters.toStringAsFixed(0)}m';
}

class LocationJudgmentService {
  static const double insideAccuracyFloorMeters = 35.0;
  static const double initialAlertAccuracyThresholdMeters = 120.0;
  static const double initialAlertBufferMeters = 40.0;
  static const double minimumInitialAlertThresholdMeters = 60.0;
  static const double maximumInitialAlertThresholdMeters = 60.0;
  static const double strongInitialAlertDistanceMeters = 50.0;
  static const double strongInitialAlertAccuracyMeters = 80.0;
  static const double approachPendingMinMeters = 60.0;
  static const double approachPendingMaxMeters = 80.0;
  static const double approachPendingAccuracyMeters = 30.0;
  static const int approachPendingValidSeconds = 5 * 60;
  static const double approachPendingClearDistanceMeters = 120.0;
  static const double deepInsideFloorMeters = 10.0;
  static const double exitBufferMeters = 15.0;
  static const double minimumExitThresholdMeters = 50.0;
  static const double farOutsideBufferMeters = 500.0;

  static Future<LocationJudgment> fromCurrentPosition({
    required double centerLat,
    required double centerLng,
    required double radius,
    geo.LocationAccuracy desiredAccuracy = geo.LocationAccuracy.medium,
    Duration timeout = const Duration(seconds: 10),
  }) async {
    final pos = await geo.Geolocator.getCurrentPosition(
      desiredAccuracy: desiredAccuracy,
    ).timeout(timeout);

    final distance = geo.Geolocator.distanceBetween(
      pos.latitude,
      pos.longitude,
      centerLat,
      centerLng,
    );

    return judge(
      distance: distance,
      radius: radius,
      accuracy: pos.accuracy,
    );
  }

  static LocationJudgment judge({
    required double distance,
    required double radius,
    required double accuracy,
  }) {
    final deepInsideThreshold =
        (radius * 0.5).clamp(deepInsideFloorMeters, radius).toDouble();
    final accuracyThreshold =
        radius > insideAccuracyFloorMeters ? radius : insideAccuracyFloorMeters;
    final exitThreshold = radius + exitBufferMeters > minimumExitThresholdMeters
        ? radius + exitBufferMeters
        : minimumExitThresholdMeters;
    final initialAlertThreshold = (radius + initialAlertBufferMeters)
        .clamp(
          minimumInitialAlertThresholdMeters,
          maximumInitialAlertThresholdMeters,
        )
        .toDouble();

    final LocationZone zone;
    if (distance <= radius &&
        (distance <= deepInsideThreshold || accuracy <= accuracyThreshold)) {
      zone = LocationZone.reliableInside;
    } else if (distance <= radius) {
      zone = LocationZone.unreliableInside;
    } else if (distance <= exitThreshold) {
      zone = LocationZone.boundary;
    } else if (distance <= radius + farOutsideBufferMeters) {
      zone = LocationZone.outside;
    } else {
      zone = LocationZone.farOutside;
    }

    return LocationJudgment(
      zone: zone,
      distance: distance,
      radius: radius,
      accuracy: accuracy,
      deepInsideThreshold: deepInsideThreshold,
      accuracyThreshold: accuracyThreshold,
      exitThreshold: exitThreshold,
      initialAlertThreshold: initialAlertThreshold,
    );
  }
}
