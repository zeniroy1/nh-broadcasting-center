import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

final historyProvider = StateNotifierProvider<HistoryNotifier, List<Map<String, dynamic>>>((ref) {
  return HistoryNotifier();
});

class HistoryNotifier extends StateNotifier<List<Map<String, dynamic>>> {
  HistoryNotifier() : super([]) {
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('commute_history');
    if (jsonString != null) {
      final List<dynamic> decoded = jsonDecode(jsonString);
      state = decoded.map((e) => e as Map<String, dynamic>).toList();
    } else {
      // 초기 프리셋용 더미 데이터 제공
      state = [
        {'time': DateTime.now().subtract(const Duration(hours: 0, minutes: 5)).toIso8601String(), 'desc': '퇴근 체크 완료 (자동 감지 종료)'},
        {'time': DateTime.now().subtract(const Duration(hours: 9, minutes: 12)).toIso8601String(), 'desc': '출근 구역 진입 (알림 발생)'},
      ];
    }
  }

  Future<void> addRecord(String description) async {
    final newRecord = {
      'time': DateTime.now().toIso8601String(),
      'desc': description,
    };
    final newState = [newRecord, ...state];
    state = newState;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('commute_history', jsonEncode(newState));
  }
}
