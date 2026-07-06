import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

// Map: 날짜(자정 기준) -> 해당 날짜의 타임스탬프 목록
final historyProvider = StateNotifierProvider<HistoryNotifier, Map<DateTime, List<DateTime>>>((ref) {
  return HistoryNotifier();
});

class HistoryNotifier extends StateNotifier<Map<DateTime, List<DateTime>>> {
  HistoryNotifier() : super({}) {
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('commute_history_raw');
    List<DateTime> timestamps = [];

    if (jsonString != null && jsonString != '[]') {
      // 저장된 기록이 있으면 그대로 불러옴
      final List<dynamic> decoded = jsonDecode(jsonString);
      timestamps = decoded.map((e) => DateTime.parse(e.toString())).toList();
    } else if (jsonString == null) {
      // 완전 신규 설치 시에만 4월 기본 기록 삽입
      timestamps = [
        DateTime(2026, 4, 1, 18, 10),  // 1일  퇴근
        DateTime(2026, 4, 2, 8, 50),   // 2일  출근
        DateTime(2026, 4, 6, 8, 50),   // 6일  출근
        DateTime(2026, 4, 6, 18, 10),  // 6일  퇴근
        DateTime(2026, 4, 7, 8, 50),   // 7일  출근
        DateTime(2026, 4, 8, 8, 50),   // 8일  출근
        DateTime(2026, 4, 9, 8, 50),   // 9일  출근
        DateTime(2026, 4, 10, 8, 50),  // 10일 출근
        DateTime(2026, 4, 10, 18, 10), // 10일 퇴근
        DateTime(2026, 4, 13, 8, 50),  // 13일 출근
        DateTime(2026, 4, 13, 18, 10), // 13일 퇴근
        DateTime(2026, 4, 14, 8, 50),  // 14일 출근
        DateTime(2026, 4, 14, 18, 10), // 14일 퇴근
        DateTime(2026, 4, 15, 8, 50),  // 15일 출근
        DateTime(2026, 4, 15, 18, 10), // 15일 퇴근
        DateTime(2026, 4, 16, 8, 50),  // 16일 출근
        DateTime(2026, 4, 16, 18, 10), // 16일 퇴근
        DateTime(2026, 4, 17, 8, 50),  // 17일 출근
        DateTime(2026, 4, 17, 18, 10), // 17일 퇴근
        DateTime(2026, 4, 20, 8, 50),   // 20일 출근
        DateTime(2026, 4, 20, 18, 10),  // 20일 퇴근
        DateTime(2026, 4, 21, 8, 50),   // 21일 출근
        DateTime(2026, 4, 21, 18, 10),  // 21일 퇴근
        DateTime(2026, 4, 22, 8, 50),   // 22일 출근
        DateTime(2026, 4, 23, 8, 50),   // 23일 출근
      ];
      // SharedPreferences에 영구 저장
      await prefs.setString(
        'commute_history_raw',
        jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
      );
    }

    final Map<DateTime, List<DateTime>> grouped = {};
    for (var ts in timestamps) {
      final dateKey = DateTime(ts.year, ts.month, ts.day);
      if (!grouped.containsKey(dateKey)) {
        grouped[dateKey] = [];
      }
      grouped[dateKey]!.add(ts);
    }

    // 시간 오름차순 정렬
    for (var list in grouped.values) {
      list.sort((a, b) => a.compareTo(b));
    }

    state = grouped;
  }

  /// 강제 리로드 (홈 화면 등에서 호출 가능)
  Future<void> reload() async {
    await _loadHistory();
  }

  /// 특정 달의 기록만 삭제
  Future<void> clearMonth(int year, int month) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('commute_history_raw');
    if (jsonString == null) return;

    final List<dynamic> decoded = jsonDecode(jsonString);
    final timestamps = decoded.map((e) => DateTime.parse(e.toString())).toList();

    // 지정된 연/월에 해당하는 타임스탬프만 제거
    timestamps.removeWhere((ts) => ts.year == year && ts.month == month);

    // 다시 저장 (빈 배열이어도 그대로 저장 — 기본 데이터 재삽입 방지)
    await prefs.setString(
      'commute_history_raw',
      jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
    );

    // _loadHistory 호출 없이 상태 직접 업데이트
    final Map<DateTime, List<DateTime>> grouped = {};
    for (var ts in timestamps) {
      final dateKey = DateTime(ts.year, ts.month, ts.day);
      grouped.putIfAbsent(dateKey, () => []).add(ts);
    }
    for (var list in grouped.values) {
      list.sort((a, b) => a.compareTo(b));
    }
    state = grouped;
  }

  /// NH파트너스 앱 실행 버튼 클릭 시 현재 시각을 출퇴근 기록으로 저장
  Future<void> addTimestamp(DateTime ts) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('commute_history_raw');
    List<DateTime> timestamps = [];

    if (jsonString != null) {
      final List<dynamic> decoded = jsonDecode(jsonString);
      timestamps = decoded.map((e) => DateTime.parse(e.toString())).toList();
    }

    timestamps.add(ts);

    await prefs.setString(
      'commute_history_raw',
      jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
    );

    // 상태 즉시 반영
    await _loadHistory();
  }
}
