import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

class LogFileService {
  static const _fileName = 'nh_reminder_runtime.txt';
  static const _backupFileName = 'nh_reminder_runtime.old.txt';
  static const _maxBytes = 8 * 1024 * 1024;
  static const _downloadLogDir = '/storage/emulated/0/Download/nh_partners';

  static Future<void> _writeQueue = Future.value();
  static Directory? _cachedLogDir;

  static void log(String message) {
    debugPrint(message);
    unawaited(_enqueue(message));
  }

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

    if (Platform.isAndroid) {
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
    if (length < _maxBytes) return;

    final backup =
        File('${file.parent.path}${Platform.pathSeparator}$_backupFileName');
    if (await backup.exists()) {
      await backup.delete();
    }
    await file.rename(backup.path);
  }
}
