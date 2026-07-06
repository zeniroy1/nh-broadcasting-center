import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/log_file_service.dart';

final historyProvider =
    StateNotifierProvider<HistoryNotifier, Map<DateTime, List<DateTime>>>(
  (ref) => HistoryNotifier(),
);

class HistoryNotifier extends StateNotifier<Map<DateTime, List<DateTime>>> {
  static const _manualDuplicateWindow = Duration(minutes: 2);

  HistoryNotifier() : super({}) {
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('commute_history_raw');
    List<DateTime> timestamps = [];

    if (jsonString != null && jsonString != '[]') {
      final List<dynamic> decoded = jsonDecode(jsonString);
      timestamps = decoded.map((e) => DateTime.parse(e.toString())).toList();
    } else if (jsonString == null) {
      timestamps = [
        DateTime(2026, 4, 1, 18, 10),
        DateTime(2026, 4, 2, 8, 50),
        DateTime(2026, 4, 6, 8, 50),
        DateTime(2026, 4, 6, 18, 10),
        DateTime(2026, 4, 7, 8, 50),
        DateTime(2026, 4, 8, 8, 50),
        DateTime(2026, 4, 9, 8, 50),
        DateTime(2026, 4, 10, 8, 50),
        DateTime(2026, 4, 10, 18, 10),
        DateTime(2026, 4, 13, 8, 50),
        DateTime(2026, 4, 13, 18, 10),
        DateTime(2026, 4, 14, 8, 50),
        DateTime(2026, 4, 14, 18, 10),
        DateTime(2026, 4, 15, 8, 50),
        DateTime(2026, 4, 15, 18, 10),
        DateTime(2026, 4, 16, 8, 50),
        DateTime(2026, 4, 16, 18, 10),
        DateTime(2026, 4, 17, 8, 50),
        DateTime(2026, 4, 17, 18, 10),
        DateTime(2026, 4, 20, 8, 50),
        DateTime(2026, 4, 20, 18, 10),
        DateTime(2026, 4, 21, 8, 50),
        DateTime(2026, 4, 21, 18, 10),
        DateTime(2026, 4, 22, 8, 50),
        DateTime(2026, 4, 23, 8, 50),
      ];
      await prefs.setString(
        'commute_history_raw',
        jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
      );
    }

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

  Future<void> reload() async {
    await _loadHistory();
  }

  Future<void> clearMonth(int year, int month) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('commute_history_raw');
    if (jsonString == null) return;

    final List<dynamic> decoded = jsonDecode(jsonString);
    final timestamps =
        decoded.map((e) => DateTime.parse(e.toString())).toList();
    timestamps.removeWhere((ts) => ts.year == year && ts.month == month);

    await prefs.setString(
      'commute_history_raw',
      jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
    );

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

  Future<void> addTimestamp(DateTime ts) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('commute_history_raw');
    List<DateTime> timestamps = [];

    if (jsonString != null) {
      final List<dynamic> decoded = jsonDecode(jsonString);
      timestamps = decoded.map((e) => DateTime.parse(e.toString())).toList();
    }

    if (timestamps.isNotEmpty &&
        ts.difference(timestamps.last).abs() < _manualDuplicateWindow) {
      LogFileService.logImportant(
        '[NH알리미] 출퇴근 기록 중복 저장 생략 — source:앱 버튼, '
        'last:${timestamps.last.toIso8601String()}',
      );
      return;
    }

    timestamps.add(ts);

    await prefs.setString(
      'commute_history_raw',
      jsonEncode(timestamps.map((e) => e.toIso8601String()).toList()),
    );
    LogFileService.log(
      '[NH알리미] 출퇴근 기록 저장 완료 — source:앱 버튼, '
      'timestamp:${ts.toIso8601String()}',
    );

    await _loadHistory();
  }
}
