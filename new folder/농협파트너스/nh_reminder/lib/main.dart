import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';
import 'screens/home_screen.dart';
import 'services/notification_service.dart';
import 'services/geofence_service.dart';
import 'providers/settings_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 알림 서비스 초기화 (앱 시작 시 한 번)
  await NotificationService().initialize();

  runApp(
    const ProviderScope(
      child: NhReminderApp(),
    ),
  );
}

class NhReminderApp extends ConsumerWidget {
  const NhReminderApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: 'NH 리마인더',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4DB6AC),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF151518),
        useMaterial3: true,
        fontFamily: 'pretendard',  // 없으면 기본 폰트 사용
      ),
      home: const PermissionGateway(),
    );
  }
}

/// 권한 확인 → 지오펜스 시작 → 홈 화면 진입
class PermissionGateway extends ConsumerStatefulWidget {
  const PermissionGateway({super.key});

  @override
  ConsumerState<PermissionGateway> createState() => _PermissionGatewayState();
}

class _PermissionGatewayState extends ConsumerState<PermissionGateway> {
  bool _ready = false;
  String _status = '권한 확인 중...';

  @override
  void initState() {
    super.initState();
    _checkAndStart();
  }

  Future<void> _checkAndStart() async {
    // 1. 위치 권한 요청
    setState(() => _status = '위치 권한 확인 중...');
    final loc = await Permission.locationAlways.request();

    // 2. 알림 권한 요청 (Android 13+)
    await Permission.notification.request();

    // 3. 배터리 최적화 예외 요청
    await Permission.ignoreBatteryOptimizations.request();

    // 4. 설정 로드 후 지오펜스 시작
    setState(() => _status = '서비스 시작 중...');
    await Future.delayed(const Duration(milliseconds: 300)); // 설정 로드 대기

    final settings = ref.read(settingsProvider);
    await NhGeofenceService().start(
      lat: settings.geofenceLat,
      lng: settings.geofenceLng,
      radius: settings.geofenceRadius,
      isPaused: settings.isPaused,
    );

    if (mounted) setState(() => _ready = true);
  }

  @override
  Widget build(BuildContext context) {
    if (_ready) return const HomeScreen();

    // 로딩 화면
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
              'NH 리마인더',
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
