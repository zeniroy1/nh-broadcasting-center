import 'package:shared_preferences/shared_preferences.dart';

import 'location_judgment_service.dart';
import 'log_file_service.dart';

class ArrivalConfirmationService {
  static const int requiredConfirmCount = 2;

  static Future<bool> confirmIfNeeded({
    required SharedPreferences prefs,
    required LocationJudgment judgment,
    required String source,
  }) async {
    if (judgment.isDeepReliableInside) {
      await prefs.setInt('arrival_grace_confirm_count', 0);
      LogFileService.log(
        '[NH알리미] $source — 도착권 중심 진입, 알림 허용 '
        '(${judgment.decisionText})',
      );
      return true;
    }

    final currentCount = prefs.getInt('arrival_grace_confirm_count') ?? 0;
    if (judgment.zone != LocationZone.reliableInside &&
        !(judgment.isArrivalGraceInside && currentCount > 0)) {
      await prefs.setInt('arrival_grace_confirm_count', 0);
      return false;
    }

    final confirmCount = currentCount + 1;
    await prefs.setInt('arrival_grace_confirm_count', confirmCount);
    if (confirmCount < requiredConfirmCount) {
      LogFileService.log(
        '[NH알리미] $source — 도착권 진입 1회 보류 '
        '(${judgment.decisionText}), 다음 확인 후 알림 판단',
      );
      return false;
    }

    await prefs.setInt('arrival_grace_confirm_count', 0);
    final bridgeText = judgment.zone == LocationZone.reliableInside
        ? '도착권 2회 확인'
        : '도착권 후보 유지 후 2회 확인';
    LogFileService.log(
      '[NH알리미] $source — $bridgeText, 알림 허용 '
      '(${judgment.decisionText})',
    );
    return true;
  }
}
