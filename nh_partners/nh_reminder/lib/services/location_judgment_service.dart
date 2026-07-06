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
    required this.looseAccuracyThreshold,
    required this.exitThreshold,
    required this.isArrivalGraceInside,
  });

  final LocationZone zone;
  final double distance;
  final double radius;
  final double accuracy;
  final double deepInsideThreshold;
  final double accuracyThreshold;
  final double looseAccuracyThreshold;
  final double exitThreshold;
  final bool isArrivalGraceInside;

  bool get isReliableInside => zone == LocationZone.reliableInside;
  bool get isDeepReliableInside =>
      zone == LocationZone.reliableInside && distance <= deepInsideThreshold;
  bool get isInside =>
      zone == LocationZone.reliableInside ||
      zone == LocationZone.unreliableInside;
  bool get isOutside =>
      zone == LocationZone.outside || zone == LocationZone.farOutside;

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
        '통과기준: 확실권 ${deepInsideThreshold.toStringAsFixed(0)}m 이내(정확도 ${looseAccuracyThreshold.toStringAsFixed(0)}m 이하) '
        '또는 경계권 정확도 ${accuracyThreshold.toStringAsFixed(0)}m 이하, '
        '이탈기준: ${exitThreshold.toStringAsFixed(0)}m 초과, '
        '판정:${passed ? '통과' : '보류'}';
  }

  String get outsideText =>
      '${distance.toStringAsFixed(0)}m, 기준 ${exitThreshold.toStringAsFixed(0)}m, '
      '정확도 ${accuracy.toStringAsFixed(0)}m';
}

class LocationJudgmentService {
  static const double insideAccuracyFloorMeters = 35.0;
  static const double deepInsideFloorMeters = 10.0;
  static const double deepInsideRadiusRatio = 2 / 3;
  static const double looseInsideAccuracyMeters = 120.0;
  static const double arrivalGraceMeters = 20.0;
  static const double exitBufferMeters = 25.0;
  static const double minimumExitThresholdMeters = 60.0;
  static const double farOutsideBufferMeters = 500.0;
  static const double confirmedExitBufferMeters = 120.0;
  static const double minimumConfirmedExitThresholdMeters = 150.0;

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
    final deepInsideThreshold = (radius * deepInsideRadiusRatio)
        .clamp(deepInsideFloorMeters, radius)
        .toDouble();
    final accuracyThreshold =
        radius > insideAccuracyFloorMeters ? radius : insideAccuracyFloorMeters;
    const looseAccuracyThreshold = looseInsideAccuracyMeters;
    final arrivalThreshold = radius + arrivalGraceMeters;
    final exitThreshold = radius + exitBufferMeters > minimumExitThresholdMeters
        ? radius + exitBufferMeters
        : minimumExitThresholdMeters;

    final LocationZone zone;
    final reliableCoreInside =
        distance <= deepInsideThreshold && accuracy <= looseAccuracyThreshold;
    final reliableEdgeInside = distance > deepInsideThreshold &&
        distance <= radius &&
        accuracy <= accuracyThreshold;
    final reliableWithinRadius = reliableCoreInside || reliableEdgeInside;
    final reliableArrivalGraceSignal = distance > radius &&
        distance <= arrivalThreshold &&
        accuracy <= accuracyThreshold;

    if (reliableWithinRadius) {
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
      looseAccuracyThreshold: looseAccuracyThreshold,
      exitThreshold: exitThreshold,
      isArrivalGraceInside: reliableArrivalGraceSignal,
    );
  }

  static double confirmedExitThreshold(double radius) {
    final threshold = radius + confirmedExitBufferMeters;
    return threshold > minimumConfirmedExitThresholdMeters
        ? threshold
        : minimumConfirmedExitThresholdMeters;
  }

  static double dismissalResetExitThreshold(double radius) {
    final threshold = radius + exitBufferMeters;
    return threshold > minimumExitThresholdMeters
        ? threshold
        : minimumExitThresholdMeters;
  }

  static bool isConfirmedExitAfterDismissal(LocationJudgment judgment) {
    return judgment.distance > dismissalResetExitThreshold(judgment.radius);
  }
}
