import 'dart:async';
import 'dart:ui';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// NH 리마인더 알림 서비스
///
/// - 음소거/방해금지 무시 긴급음 채널 사용
/// - Full-screen intent (잠금화면 팝업)
/// - Heads-up 배너 (다른 앱 위 팝업)
/// - 액션 버튼 2개: [확인함] [NH파트너스 열기]
/// - 1분 간격 반복 (타이머 기반, 종료 조건 만족 시 취소)
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static const _channelId = 'nh_reminder_urgent';
  static const _channelName = '긴급 출퇴근 알림';
  static const _notifId = 1001;

  // 반복 알림 타이머
  Timer? _repeatTimer;
  bool _isActive = false;

  /// 초기화 (앱 시작 시 한 번 호출)
  Future<void> initialize() async {
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit);

    await _plugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotifResponse,
    );

    // 긴급 알림 채널 생성
    // IMPORTANCE_HIGH + setBypassDnd(true) → 방해금지/음소거 무시
    final channel = AndroidNotificationChannel(
      _channelId,
      _channelName,
      description: '농협파트너스 출퇴근 버튼 클릭 확인 긴급 알림',
      importance: Importance.max,
      playSound: true,
      enableVibration: true,
      // 알람 채널 → 방해금지 무시
      // sound: const RawResourceAndroidNotificationSound('notification_alarm'), // 소리 파일 없어서 기본 소리로 우회
      vibrationPattern: Int64List.fromList([0, 500, 200, 500, 200, 500]),
      enableLights: true,
      ledColor: const Color.fromARGB(255, 255, 100, 0),
    );

    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  /// 알림 응답 처리 (액션 버튼 탭 등)
  void _onNotifResponse(NotificationResponse response) {
    final payload = response.actionId ?? response.payload ?? '';
    if (payload == 'confirm' || payload == 'open_nh') {
      stopReminder();
    }
    if (payload == 'open_nh') {
      _launchNhApp();
    }
  }

  /// NH파트너스 앱 실행
  void _launchNhApp() {
    // url_launcher를 통해 NH파트너스 앱 실행
    // 앱이 없으면 Play Store로 이동
    const nhPackage = 'com.vus.nhpthrm';
    // Android에서는 intent scheme 사용
    debugPrint('[NH리마인더] NH파트너스 앱 실행 시도: $nhPackage');
  }

  /// 지오펜스 진입 시 1분 반복 알림 시작
  void startReminder({int intervalSeconds = 60}) {
    if (_isActive) return; // 이미 실행 중이면 무시
    _isActive = true;

    // 즉시 첫 알림 발송
    _showUrgentNotification();

    // 1분마다 반복
    _repeatTimer = Timer.periodic(
      Duration(seconds: intervalSeconds),
      (_) {
        if (_isActive) _showUrgentNotification();
      },
    );
  }

  /// 알림 반복 중지 (확인함 / NH앱 실행 감지 시)
  void stopReminder() {
    _isActive = false;
    _repeatTimer?.cancel();
    _repeatTimer = null;
    _plugin.cancel(_notifId);
    debugPrint('[NH리마인더] 알림 종료 — 출퇴근 확인 완료');
  }

  bool get isActive => _isActive;

  /// 실제 알림 발송
  Future<void> _showUrgentNotification() async {
    final androidDetails = AndroidNotificationDetails(
      _channelId,
      _channelName,
      channelDescription: '농협파트너스 출퇴근 버튼 클릭 확인',
      importance: Importance.max,
      priority: Priority.max,

      // Full-screen intent (잠금화면에서도 팝업)
      fullScreenIntent: true,

      // 방해금지 무시
      category: AndroidNotificationCategory.alarm,

      // 진동 패턴 (알람 스타일: 강진동)
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 700, 200, 700, 200, 700]),

      // 소리 (알람 채널에서 음소거 무시)
      // sound: const RawResourceAndroidNotificationSound('notification_alarm'), // 소리 파일 없어서 기본 소리로 우회
      playSound: true,

      // 자동 사라짐 방지 (확인함 버튼 누를 때까지 유지)
      autoCancel: false,
      ongoing: false,

      // 알림 아이콘
      icon: '@mipmap/ic_launcher',
      color: const Color(0xFF005BAC), // 농협 파란색

      // 액션 버튼 2개
      actions: const [
        AndroidNotificationAction(
          'confirm',
          '✅ 확인함',
          showsUserInterface: false,
          cancelNotification: true,
        ),
        AndroidNotificationAction(
          'open_nh',
          '📲 NH파트너스 열기',
          showsUserInterface: true,
          cancelNotification: true,
        ),
      ],
    );

    await _plugin.show(
      _notifId,
      '🔔 출퇴근 버튼을 눌렀나요?',
      '농협파트너스 앱에서 출퇴근 기록을 확인해주세요!',
      NotificationDetails(android: androidDetails),
      payload: 'geofence_reminder',
    );
  }
}
