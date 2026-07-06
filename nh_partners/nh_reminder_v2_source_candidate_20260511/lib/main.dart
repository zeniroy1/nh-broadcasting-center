import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/home_screen.dart';
import 'services/notification_service.dart';
import 'services/geofence_service.dart';
import 'services/alarm_scheduler.dart';
import 'services/background_monitor_service.dart';
import 'services/log_file_service.dart';
import 'services/native_monitor_bridge.dart';
import 'models/app_state.dart';
import 'providers/settings_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  LogFileService.log(
      '[NH알리미] 파일 로그 시작 — ${await LogFileService.logFilePath()}');

  await NotificationService().initialize();
  await DailyAlarmScheduler.schedule();
  final initialSettings = await SettingsNotifier.loadFromPrefs();
  LogFileService.log(
    '[NH알리미] 초기 설정 로드 — lat:${initialSettings.geofenceLat}, '
    'lng:${initialSettings.geofenceLng}, 반경:${initialSettings.geofenceRadius}m, '
    'paused:${initialSettings.isPaused}',
  );
  await NativeMonitorBridge.syncFromSettings(initialSettings);

  runApp(
    ProviderScope(
      overrides: [
        settingsProvider.overrideWith(
          (ref) => SettingsNotifier(initialSettings: initialSettings),
        ),
      ],
      child: const NhReminderApp(),
    ),
  );
}

class NhReminderApp extends ConsumerWidget {
  const NhReminderApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: 'NH 알리미',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4DB6AC),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF151518),
        useMaterial3: true,
        fontFamily: 'pretendard',
      ),
      home: const PermissionGateway(),
    );
  }
}

class PermissionGateway extends ConsumerStatefulWidget {
  const PermissionGateway({super.key});

  @override
  ConsumerState<PermissionGateway> createState() => _PermissionGatewayState();
}

class _PermissionGatewayState extends ConsumerState<PermissionGateway>
    with WidgetsBindingObserver {
  bool _ready = false;
  String _status = '권한 확인 중...';
  AppLifecycleState _lastLifecycleState = AppLifecycleState.resumed;
  int _lastAppStateLogMs = 0;
  static const Duration _appStateLogInterval = Duration(minutes: 10);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _lastLifecycleState =
        WidgetsBinding.instance.lifecycleState ?? AppLifecycleState.resumed;
    unawaited(_persistAppLifecycleState(
      _lastLifecycleState,
      reason: 'init',
      logNow: true,
    ));
    _checkAndStart();
  }

  Timer? _pollingTimer;

  Future<void> _checkAndStart() async {
    setState(() => _status = '위치 권한 확인 중...');
    await Permission.locationAlways.request();
    await Permission.notification.request();
    await Permission.ignoreBatteryOptimizations.request();

    setState(() => _status = '서비스 시작 중...');
    await Future.delayed(const Duration(milliseconds: 300));

    final settings = ref.read(settingsProvider);
    await NhGeofenceService().start(
      lat: settings.geofenceLat,
      lng: settings.geofenceLng,
      radius: settings.geofenceRadius,
      isPaused: settings.isPaused,
    );
    if (!settings.isPaused) {
      await BackgroundMonitorService.start(initialDelaySeconds: 10);
    } else {
      await BackgroundMonitorService.stop();
    }
    await _refreshHealthChecks(verifyPositionFirst: true);

    _startPolling();

    if (mounted) setState(() => _ready = true);
  }

  void _startPolling() {
    _pollingTimer?.cancel();
    bool lastPaused = ref.read(settingsProvider).isPaused;

    _pollingTimer = Timer.periodic(const Duration(seconds: 30), (_) async {
      try {
        await _persistAppLifecycleState(
          _lastLifecycleState,
          reason: 'polling',
        );
        final prefs = await SharedPreferences.getInstance();
        final isPaused = prefs.getBool('is_paused') ?? false;
        if (isPaused == lastPaused) {
          if (_lastLifecycleState != AppLifecycleState.resumed) {
            return;
          }
          await _refreshHealthChecks();
          return;
        }
        lastPaused = isPaused;

        LogFileService.log('[NH알리미] polling: is_paused 변경 → $isPaused');
        final providerPaused = ref.read(settingsProvider).isPaused;
        if (providerPaused == isPaused) {
          LogFileService.log(
            '[NH알리미] polling: 앱 내 상태 변경은 이미 처리됨 — 추가 재시작 생략',
          );
          await _refreshHealthChecks(verifyPositionFirst: !isPaused);
          return;
        }

        await ref.read(settingsProvider.notifier).reload();
        final geoSvc = NhGeofenceService();
        if (isPaused) {
          await geoSvc.stop();
          await BackgroundMonitorService.stop();
        } else {
          final lat =
              prefs.getDouble('geofence_lat') ?? AppSettings.defaultGeofenceLat;
          final lng =
              prefs.getDouble('geofence_lng') ?? AppSettings.defaultGeofenceLng;
          final radius = AppSettings.clampGeofenceRadius(
            prefs.getDouble('geofence_radius') ??
                AppSettings.defaultGeofenceRadius,
          );
          await geoSvc.stop();
          await geoSvc.start(
              lat: lat, lng: lng, radius: radius, isPaused: false);
          await BackgroundMonitorService.start(initialDelaySeconds: 5);
          LogFileService.log('[NH알리미] polling: 06:00 지오펜스 재시작');
        }
        await _refreshHealthChecks(verifyPositionFirst: !isPaused);
      } catch (e) {
        LogFileService.log('[NH알리미] polling 오류: $e');
      }
    });
  }

  Future<void> _refreshHealthChecks({bool verifyPositionFirst = false}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.reload();
    final isPaused = prefs.getBool('is_paused') ?? false;
    final notifActive = prefs.getBool('notif_active') ?? false;
    var allowNotificationRefresh = true;
    if (!isPaused && (verifyPositionFirst || notifActive)) {
      allowNotificationRefresh =
          await BackgroundMonitorService.verifyBeforeNotificationRefresh();
    }
    await BackgroundMonitorService.refreshIfStale();
    if (notifActive && allowNotificationRefresh) {
      await NotificationService().refreshReminderIfStale();
    } else if (notifActive) {
      LogFileService.log('[NH알리미] 리프레시 순서 제어 — 위치 확인 전/범위 밖 상태라 알림 리프레시 보류');
    }
  }

  Future<void> _persistAppLifecycleState(
    AppLifecycleState state, {
    required String reason,
    bool logNow = false,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    final isForeground = state == AppLifecycleState.resumed;
    final executionMode = _executionModeForLifecycle(state);
    await prefs.setString('app_lifecycle_state', state.name);
    await prefs.setString('app_execution_mode', executionMode);
    await prefs.setBool('app_foreground', isForeground);
    await prefs.setBool('app_activity_visible', isForeground);
    await prefs.setBool('app_activity_alive', executionMode != 'service_only');
    await prefs.setInt('last_app_lifecycle_ms', nowMs);

    if (!logNow &&
        nowMs - _lastAppStateLogMs < _appStateLogInterval.inMilliseconds) {
      return;
    }
    _lastAppStateLogMs = nowMs;

    final isPaused = prefs.getBool('is_paused') ?? false;
    final notifActive = prefs.getBool('notif_active') ?? false;
    final monitorActive = prefs.getBool('monitor_active') ?? false;
    final dismissedUntilExit = prefs.getBool('dismissed_until_exit') ?? false;
    LogFileService.log(
      '[NH알리미] 앱 실행상태 스냅샷 — mode:$executionMode, state:${state.name}, '
      'foreground:$isForeground, paused:$isPaused, notifActive:$notifActive, '
      'monitorActive:$monitorActive, dismissedUntilExit:$dismissedUntilExit, '
      'reason:$reason',
    );
  }

  String _executionModeForLifecycle(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) return 'foreground';
    if (state == AppLifecycleState.detached) return 'service_only';
    return 'background_recent';
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _pollingTimer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _lastLifecycleState = state;
    unawaited(_persistAppLifecycleState(
      state,
      reason: 'lifecycle',
      logNow: true,
    ));
    if (state == AppLifecycleState.resumed) {
      _refreshHealthChecks(verifyPositionFirst: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_ready) return const HomeScreen();

    return Scaffold(
      backgroundColor: const Color(0xFF151518),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.notifications_active,
                size: 80, color: Color(0xFF4DB6AC)),
            const SizedBox(height: 24),
            const Text(
              'NH 알리미',
              style: TextStyle(
                color: Colors.white,
                fontSize: 32,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              '농협파트너스 출퇴근 알림',
              style: TextStyle(color: Colors.white70, fontSize: 16),
            ),
            const SizedBox(height: 40),
            const CircularProgressIndicator(color: Colors.white),
            const SizedBox(height: 16),
            Text(
              _status,
              style: const TextStyle(color: Colors.white70, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
