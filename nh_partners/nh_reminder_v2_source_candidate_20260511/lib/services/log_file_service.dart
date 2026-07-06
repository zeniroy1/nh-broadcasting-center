import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

class UserDiagnosticLogExport {
  const UserDiagnosticLogExport({
    required this.localPath,
    required this.savedPath,
  });

  final String localPath;
  final String savedPath;
}

class LogFileService {
  static const _fileName = 'nh_reminder_runtime.txt';
  static const _backupFileName = 'nh_reminder_runtime.old.txt';
  static const _userDiagnosticFileName = 'nh_alimi_user_diagnostic.txt';
  static const _maxBytes = 8 * 1024 * 1024;
  static const _userDiagnosticRetention = Duration(days: 7);
  static const _downloadLogDir = '/storage/emulated/0/Download/nh_partners';
  static const _nativeChannel =
      MethodChannel('com.example.nh_reminder/native_monitor');

  static Future<void> _writeQueue = Future.value();
  static Directory? _cachedLogDir;

  static void log(String message) {
    debugPrint(message);
    unawaited(_enqueue(message));
  }

  static void logImportant(String message) {
    debugPrint(message);
    unawaited(_enqueue(message, forceUserDiagnostic: true));
  }

  static Future<String> logFilePath() async {
    final file = await _logFile();
    return file.path;
  }

  static Future<UserDiagnosticLogExport> exportUserDiagnosticLog() async {
    try {
      await _writeQueue;
    } catch (_) {}

    final source = await _userDiagnosticFile();
    await _pruneUserDiagnosticLog(source);

    final now = DateTime.now();
    const fileName = 'NH알리미_핵심로그.txt';

    final body = await source.exists() ? await _readTextLossy(source) : '';
    final content = StringBuffer()
      ..writeln('NH알리미 핵심 동작 로그')
      ..writeln('생성시각: ${now.toIso8601String()}')
      ..writeln('보관범위: 최근 7일')
      ..writeln('포함항목: 배터리/위치요청 요약, 지오펜스, 알림, 기록, 권한/실패')
      ..writeln('개인정보 보호: 정확한 좌표와 파일 경로는 제외 또는 마스킹')
      ..writeln('----------------------------------------');

    if (body.trim().isEmpty) {
      content.writeln('최근 7일 핵심 로그가 없습니다.');
    } else {
      content.write(body);
    }

    final text = content.toString();
    final exportFile = await _writeShareFile(fileName, text);
    final savedPath = await _saveSingleTextToDownloads(
          fileName: fileName,
          content: text,
        ) ??
        _displayPath(exportFile.path);
    return UserDiagnosticLogExport(
      localPath: exportFile.path,
      savedPath: savedPath,
    );
  }

  static Future<UserDiagnosticLogExport> exportDeveloperRuntimeLog() async {
    try {
      await _writeQueue;
    } catch (_) {}

    final source = await _logFile();
    final now = DateTime.now();
    const fileName = 'NH알리미_개발자런타임.txt';

    final body = await source.exists() ? await _readTextLossy(source) : '';
    final content = StringBuffer()
      ..writeln('NH알리미 개발자 런타임 전체 로그')
      ..writeln('생성시각: ${now.toIso8601String()}')
      ..writeln('포함항목: 전체 런타임 로그(필터링 없음)')
      ..writeln('주의사항: 좌표, 파일 경로, 기기 상태 등 상세 진단 정보가 포함될 수 있음')
      ..writeln('----------------------------------------');

    if (body.trim().isEmpty) {
      content.writeln('런타임 로그가 없습니다.');
    } else {
      content.write(body);
    }

    final text = content.toString();
    final exportFile = await _writeShareFile(fileName, text);
    final savedPath = await _saveSingleTextToDownloads(
          fileName: fileName,
          content: text,
        ) ??
        _displayPath(exportFile.path);
    return UserDiagnosticLogExport(
      localPath: exportFile.path,
      savedPath: savedPath,
    );
  }

  static Future<void> clear() async {
    final file = await _logFile();
    if (await file.exists()) {
      await file.delete();
    }
  }

  static Future<void> _enqueue(
    String message, {
    bool forceUserDiagnostic = false,
  }) async {
    _writeQueue = _writeQueue
        .catchError((_) {})
        .then((_) => _write(message, forceUserDiagnostic: forceUserDiagnostic));
    try {
      await _writeQueue;
    } catch (_) {}
  }

  static Future<void> _write(
    String message, {
    bool forceUserDiagnostic = false,
  }) async {
    final file = await _logFile();
    await _rotateIfNeeded(file);
    final timestamp = DateTime.now().toIso8601String();
    await file.writeAsString(
      '[$timestamp] $message\n',
      mode: FileMode.append,
      flush: false,
    );
    await _writeUserDiagnosticLog(
      timestamp,
      message,
      force: forceUserDiagnostic,
    );
  }

  static Future<File> _logFile() async {
    final dir = await _logDirectory();
    return File('${dir.path}${Platform.pathSeparator}$_fileName');
  }

  static Future<File> _userDiagnosticFile() async {
    final dir = await _logDirectory();
    return File(
      '${dir.path}${Platform.pathSeparator}$_userDiagnosticFileName',
    );
  }

  static Future<void> _writeUserDiagnosticLog(
    String timestamp,
    String message, {
    bool force = false,
  }) async {
    if (!force && !_isUserDiagnosticMessage(message)) return;

    final file = await _userDiagnosticFile();
    await _pruneUserDiagnosticLog(file);
    final sanitized = _sanitizeUserDiagnosticMessage(message);
    await file.writeAsString(
      '[$timestamp] $sanitized\n',
      mode: FileMode.append,
      flush: false,
    );
  }

  static Future<Directory> _logDirectory() async {
    final cached = _cachedLogDir;
    if (cached != null && await cached.exists()) {
      return cached;
    }

    final fallback = await getExternalStorageDirectory() ??
        await getApplicationDocumentsDirectory();
    if (!await fallback.exists()) {
      await fallback.create(recursive: true);
    }
    _cachedLogDir = fallback;
    return fallback;
  }

  static Future<void> _rotateIfNeeded(File file) async {
    if (!await file.exists()) return;
    final length = await file.length();
    if (length < _maxBytes) return;

    final backup =
        File('${file.parent.path}${Platform.pathSeparator}$_backupFileName');
    if (await backup.exists()) {
      await backup.delete();
    }
    await file.rename(backup.path);
  }

  static Future<void> _pruneUserDiagnosticLog(File file) async {
    if (!await file.exists()) return;

    final cutoff = DateTime.now().subtract(_userDiagnosticRetention);
    final lines = const LineSplitter().convert(await _readTextLossy(file));
    final kept = <String>[];

    for (final line in lines) {
      final timestamp = _extractTimestamp(line);
      if (timestamp == null || !timestamp.isBefore(cutoff)) {
        kept.add(line);
      }
    }

    final trimmed =
        kept.length > 2000 ? kept.sublist(kept.length - 2000) : kept;
    if (trimmed.length != lines.length) {
      await file.writeAsString(
        trimmed.isEmpty ? '' : '${trimmed.join('\n')}\n',
        flush: true,
      );
    }
  }

  static Future<File> _writeShareFile(String fileName, String content) async {
    final directory = await getTemporaryDirectory();
    if (!await directory.exists()) {
      await directory.create(recursive: true);
    }
    final file = File('${directory.path}${Platform.pathSeparator}$fileName');
    await file.writeAsString(content, flush: true);
    return file;
  }

  static Future<String?> _saveSingleTextToDownloads({
    required String fileName,
    required String content,
  }) async {
    if (!Platform.isAndroid) return null;

    try {
      return await _nativeChannel.invokeMethod<String>('saveTextToDownloads', {
        'fileName': fileName,
        'content': content,
      });
    } catch (_) {
      return null;
    }
  }

  static Future<String> _readTextLossy(File file) async {
    final bytes = await file.readAsBytes();
    return utf8.decode(bytes, allowMalformed: true);
  }

  static String _displayPath(String path) {
    if (path.startsWith(_downloadLogDir)) {
      return 'Download/nh_partners/${path.split(Platform.pathSeparator).last}';
    }
    return path;
  }

  static DateTime? _extractTimestamp(String line) {
    final match = RegExp(r'^\[(.+?)\]').firstMatch(line);
    if (match == null) return null;
    return DateTime.tryParse(match.group(1) ?? '');
  }

  static bool _isUserDiagnosticMessage(String message) {
    const excludeKeywords = [
      '파일 로그 시작',
      'UsageStats',
      '설정 화면 오류',
      'DevTools',
      '다음 백그라운드 감시 예약',
      '반복 알림 발송',
      '팝업 알림 발송 완료',
      '범위 밖, ENTER 대기',
      '범위 안 보류',
      '범위 안이지만 알림 활성 상태라 새 알림 시작 생략',
      '범위 밖 감지지만 초기 진입 알림 유지',
      '경계 흔들림',
    ];
    if (excludeKeywords.any(message.contains)) return false;
    if (message.contains('네이티브 보조 감시 — 범위 ') ||
        message.contains('네이티브 보조 감시 — 경계/보류')) {
      return false;
    }

    if (message.contains('사용자 진단 요약')) return true;

    const importantKeywords = [
      '06:00',
      '19:00',
      '지오펜스',
      'ENTER',
      'EXIT',
      'DWELL',
      '백그라운드 감시 시작',
      '백그라운드 감시 중지',
      '백그라운드 감시 리프레시',
      '백그라운드 감시 실행 지연',
      '백그라운드 감시 위치 확인 실패',
      '모니터링 소프트 리셋',
      '반복 알림',
      '네이티브 반복 알림',
      '네이티브 보조 팝업',
      '알림 시작',
      '알림 중지',
      '위치보정',
      '위치 확인 실패',
      '위치 권한 없음',
      '저전력',
      '위치감시 절전',
      'lastKnown',
      '출퇴근 확인',
      '출퇴근 기록',
      'NH파트너스',
      '배터리',
      '앱 상태',
      '앱 실행상태',
      '실행 상태',
      '포그라운드 서비스',
      '네이티브 보조 감시 위치 확인 실패',
      '네이티브 보조 감시 종료',
      '네이티브 보조 감시 — 위치 권한 없음',
    ];
    return importantKeywords.any(message.contains);
  }

  static String _sanitizeUserDiagnosticMessage(String message) {
    var text = message;
    text = text.replaceAll(
      RegExp(r'lat[:=][^,\s]+,\s*lng[:=][^,\s]+'),
      '위치:마스킹',
    );
    text = text.replaceAll(
      RegExp(r'/storage/[^\s)]+'),
      '경로:마스킹',
    );
    text = text.replaceAll(
      RegExp(r'[A-Z]:\\[^\s)]+'),
      '경로:마스킹',
    );
    return text;
  }
}
