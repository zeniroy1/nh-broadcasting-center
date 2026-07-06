import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

class LogFileService {
  static const _fileName = 'nh_reminder_runtime.txt';
  static const _backupFileName = 'nh_reminder_runtime.old.txt';
  static const _devMaxBytes = 8 * 1024 * 1024;
  static const _releaseMaxBytes = 1024 * 1024;
  static const _downloadLogDir = '/storage/emulated/0/Download/nh_partners';

  static Future<void> _writeQueue = Future.value();
  static Directory? _cachedLogDir;

  static void log(String message) {
    debugPrint(message);
    if (!_shouldPersist(message)) return;
    unawaited(_enqueue(message));
  }

  static String get policyLabel => kDebugMode
      ? 'dev:Download/nh_partners, max 8MB + backup'
      : 'release:app-private, max 1MB + backup';

  static Future<String> logFilePath() async {
    final file = await _logFile();
    return file.path;
  }

  static Future<void> clear() async {
    final file = await _logFile();
    if (await file.exists()) {
      await file.delete();
    }
  }

  static Future<void> _enqueue(String message) async {
    _writeQueue = _writeQueue.then((_) => _write(message));
    try {
      await _writeQueue;
    } catch (_) {
      // File logging must never break reminder logic.
    }
  }

  static Future<void> _write(String message) async {
    final file = await _logFile();
    await _rotateIfNeeded(file);
    final timestamp = DateTime.now().toIso8601String();
    await file.writeAsString(
      '[$timestamp] $message\n',
      mode: FileMode.append,
      flush: false,
    );
  }

  static Future<File> _logFile() async {
    final dir = await _logDirectory();
    return File('${dir.path}${Platform.pathSeparator}$_fileName');
  }

  static Future<Directory> _logDirectory() async {
    final cached = _cachedLogDir;
    if (cached != null && await cached.exists()) {
      return cached;
    }

    if (kDebugMode && Platform.isAndroid) {
      final downloadsDir = Directory(_downloadLogDir);
      if (await _canWriteTo(downloadsDir)) {
        _cachedLogDir = downloadsDir;
        return downloadsDir;
      }
    }

    final fallback = await getExternalStorageDirectory() ??
        await getApplicationDocumentsDirectory();
    if (!await fallback.exists()) {
      await fallback.create(recursive: true);
    }
    _cachedLogDir = fallback;
    return fallback;
  }

  static Future<bool> _canWriteTo(Directory dir) async {
    try {
      if (!await dir.exists()) {
        await dir.create(recursive: true);
      }
      final probe = File('${dir.path}${Platform.pathSeparator}.write_test');
      await probe.writeAsString('ok', flush: true);
      await probe.delete();
      return true;
    } catch (_) {
      return false;
    }
  }

  static Future<void> _rotateIfNeeded(File file) async {
    if (!await file.exists()) return;
    final length = await file.length();
    const maxBytes = kDebugMode ? _devMaxBytes : _releaseMaxBytes;
    if (length < maxBytes) return;

    final backup =
        File('${file.parent.path}${Platform.pathSeparator}$_backupFileName');
    if (await backup.exists()) {
      await backup.delete();
    }
    await file.rename(backup.path);
  }

  static bool _shouldPersist(String message) {
    if (kDebugMode) return true;

    const releaseKeepKeywords = [
      '파일 로그 시작',
      '자동 시작 알람 예약',
      '자동 종료 알람 예약',
      '06:00',
      '19:00',
      '초기 설정 로드',
      '모니터링 소프트 리셋',
      '수동 모니터링 재개',
      '수동 위치보정',
      '위치보정',
      '서대문역',
      '보정 구간',
      '범위 밖 2회',
      '범위 밖 1회',
      '차단 유지',
      '지오펜스 시작',
      '지오펜스 시작 실패',
      'ENTER',
      'EXIT',
      '알림 시작',
      '반복 알림 시작',
      '반복 알림 중지',
      '반복 알림 위치 확인 실패',
      '알림 재표시 보류',
      '팝업 알림',
      '네이티브 직접 알림',
      '네이티브 보조 팝업',
      'NH파트너스 앱 감지',
      '출퇴근 확인 완료',
      '출퇴근 기록 저장',
      '오류',
      '실패',
      '권한 없음',
    ];

    return releaseKeepKeywords.any(message.contains);
  }
}
