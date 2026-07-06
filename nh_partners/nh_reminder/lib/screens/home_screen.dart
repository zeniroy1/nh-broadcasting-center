import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:async';
import '../providers/settings_provider.dart';
import '../providers/history_provider.dart';
import '../services/geofence_service.dart';
import '../services/background_service.dart';
import '../services/log_file_service.dart';
import '../services/geofence_ui_event_service.dart';
import '../services/location_judgment_service.dart';
import '../services/monitoring_recovery_service.dart';
import 'dart:io';
import 'package:excel/excel.dart' hide Border;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../services/nh_app_launcher_service.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen>
    with SingleTickerProviderStateMixin, WidgetsBindingObserver {
  final _geoSvc = NhGeofenceService();
  final _nhAppLauncher = NhAppLauncherService();
  bool _locationUpdating = false;
  bool _resettingDefault = false;
  int _currentIndex = 0;
  DateTime _displayMonth =
      DateTime(DateTime.now().year, DateTime.now().month, 1);
  StreamSubscription<GeofenceUiEvent>? _geofenceUiSub;

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _pulseAnimation =
        Tween<double>(begin: 1.0, end: 1.1).animate(_pulseController);
    _geofenceUiSub = GeofenceUiEventService.stream.listen((event) {
      if (!mounted) return;
      if (_locationUpdating || _resettingDefault) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(event.message),
          backgroundColor: event.isWarning
              ? const Color(0xFFFF9800)
              : const Color(0xFF4DB6AC),
        ),
      );
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(historyProvider.notifier).reload();

      SharedPreferences.getInstance().then((prefs) async {
        prefs.remove('pending_history_reload');
      });
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _geofenceUiSub?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF151518),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C1C22),
        foregroundColor: Colors.white,
        title: const Text(
          'NH 알리미',
          style: TextStyle(fontWeight: FontWeight.w700, letterSpacing: 0.5),
        ),
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1.0),
          child: Container(color: Colors.white10, height: 1.0),
        ),
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildHomeTab(settings),
          _buildHistoryTab(),
          _buildSettingsTab(settings),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: const Color(0xFF1C1C22),
        selectedItemColor: const Color(0xFF4DB6AC),
        unselectedItemColor: Colors.white54,
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() => _currentIndex = index);
          if (index == 1) {
            ref.read(historyProvider.notifier).reload();
          }
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_filled), label: '홈'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: '기록'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: '설정'),
        ],
      ),
    );
  }

  Widget _buildHomeTab(settings) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (settings.isPaused) _buildPausedBanner(),
            if (settings.isPaused) const SizedBox(height: 20),
            _buildStatusCard(settings),
            const SizedBox(height: 24),
            _buildActionButtons(settings),
          ],
        ),
      ),
    );
  }

  Widget _buildPausedBanner() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF3E2723),
        border:
            Border.all(color: const Color(0xFFFF9800).withValues(alpha: 0.5)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: const Center(
        child: Row(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '알림 정지 중\n모니터링을 활성화하세요.',
              textAlign: TextAlign.center,
              style: TextStyle(
                  color: Color(0xFFFFCC80), fontSize: 13, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(settings) {
    final isActive = !settings.isPaused;
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF26262F), Color(0xFF1E1E24)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white10),
        boxShadow: const [
          BoxShadow(
              color: Colors.black26, blurRadius: 20, offset: Offset(0, 10))
        ],
      ),
      child: Column(
        children: [
          ScaleTransition(
            scale:
                isActive ? _pulseAnimation : const AlwaysStoppedAnimation(1.0),
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isActive
                    ? const Color(0xFF4DB6AC).withValues(alpha: 0.15)
                    : Colors.white10,
              ),
              child: Icon(
                isActive ? Icons.radar : Icons.location_off,
                size: 64,
                color: isActive ? const Color(0xFF80CBC4) : Colors.white54,
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            isActive ? '탐지 중' : '모니터링 중지',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: isActive ? Colors.white : Colors.white54,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            isActive
                ? ((settings.geofenceLat.toStringAsFixed(4) == '37.5660' &&
                        settings.geofenceLng.toStringAsFixed(4) == '126.9673')
                    ? '서대문역 5번출구 반경 ${settings.geofenceRadius.toInt()}m'
                    : '내 위치(보정됨) 반경 ${settings.geofenceRadius.toInt()}m')
                : '현재 지오펜스 모니터링을 중단했습니다.',
            textAlign: TextAlign.center,
            style: const TextStyle(
                fontSize: 14, color: Colors.white54, height: 1.5),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(settings) {
    final isPaused = settings.isPaused;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ElevatedButton.icon(
          onPressed: () async {
            await ref.read(settingsProvider.notifier).togglePause();
            final updated = ref.read(settingsProvider);
            if (updated.isPaused) {
              await NhBackgroundServiceManager.sendUpdate(
                isPaused: true,
                lat: updated.geofenceLat,
                lng: updated.geofenceLng,
                radius: updated.geofenceRadius,
              );
            } else {
              await MonitoringRecoveryService.reset(
                reason: '수동 모니터링 재개',
                recalibrateCurrentPosition: false,
              );
              await ref.read(settingsProvider.notifier).reload();
            }
          },
          icon:
              Icon(isPaused ? Icons.play_arrow_rounded : Icons.pause, size: 24),
          label: Text(
            isPaused ? '모니터링 재개' : '모니터링 일시정지',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          style: ElevatedButton.styleFrom(
            backgroundColor:
                isPaused ? const Color(0xFF4DB6AC) : const Color(0xFFE57373),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 18),
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            elevation: 8,
            shadowColor:
                (isPaused ? const Color(0xFF4DB6AC) : const Color(0xFFE57373))
                    .withValues(alpha: 0.5),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildSecondaryButton(
                icon: Icons.my_location,
                label: '위치 보정',
                onTap: _locationUpdating
                    ? null
                    : () => _calibrateLocation(settings),
                isLoading: _locationUpdating,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildSecondaryButton(
                icon: Icons.open_in_new,
                label: 'NH앱 실행',
                onTap: _launchNhApp,
              ),
            ),
          ],
        )
      ],
    );
  }

  Widget _buildSecondaryButton(
      {required IconData icon,
      required String label,
      VoidCallback? onTap,
      bool isLoading = false}) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        side: const BorderSide(color: Colors.white24),
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        backgroundColor: const Color(0xFF22222A),
      ),
      child: isLoading
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                  strokeWidth: 2, color: Colors.white54))
          : Column(
              children: [
                Icon(icon, size: 24, color: Colors.white70),
                const SizedBox(height: 8),
                Text(label,
                    style:
                        const TextStyle(fontSize: 13, color: Colors.white70)),
              ],
            ),
    );
  }

  Widget _buildHistoryTab() {
    final historyMap = ref.watch(historyProvider);
    final now = DateTime.now();
    final todayKey = DateTime(now.year, now.month, now.day);

    final todayRecords = historyMap[todayKey] ?? [];
    String todayIn = '미체크';
    String todayOut = '미체크';

    if (todayRecords.isNotEmpty) {
      final inTime = todayRecords.first;
      todayIn =
          '${inTime.hour.toString().padLeft(2, '0')}:${inTime.minute.toString().padLeft(2, '0')}';

      if (todayRecords.length >= 2) {
        final outTime = todayRecords.last;
        todayOut =
            '${outTime.hour.toString().padLeft(2, '0')}:${outTime.minute.toString().padLeft(2, '0')}';
      }
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF202026),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                  color: const Color(0xFF4DB6AC).withValues(alpha: 0.3),
                  width: 1.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.today, color: Color(0xFF4DB6AC)),
                    const SizedBox(width: 8),
                    Text(
                      '${now.month}월 ${now.day}일 출퇴근 현황',
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    Column(
                      children: [
                        const Text('출근 시간',
                            style:
                                TextStyle(color: Colors.white54, fontSize: 13)),
                        const SizedBox(height: 4),
                        Text(todayIn,
                            style: TextStyle(
                                color: todayIn == '미체크'
                                    ? Colors.redAccent
                                    : Colors.white,
                                fontSize: 20,
                                fontWeight: FontWeight.bold)),
                      ],
                    ),
                    Container(width: 1, height: 40, color: Colors.white10),
                    Column(
                      children: [
                        const Text('퇴근 시간',
                            style:
                                TextStyle(color: Colors.white54, fontSize: 13)),
                        const SizedBox(height: 4),
                        Text(todayOut,
                            style: TextStyle(
                                color: todayOut == '미체크'
                                    ? Colors.redAccent
                                    : Colors.white,
                                fontSize: 20,
                                fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 30),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon:
                          const Icon(Icons.chevron_left, color: Colors.white70),
                      onPressed: () {
                        setState(() {
                          _displayMonth = DateTime(
                              _displayMonth.year, _displayMonth.month - 1, 1);
                        });
                      },
                    ),
                    Flexible(
                      child: Text(
                        '${_displayMonth.year}년 ${_displayMonth.month}월 기록',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          letterSpacing: -0.4,
                        ),
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.chevron_right,
                          color: Colors.white70),
                      onPressed: () {
                        setState(() {
                          _displayMonth = DateTime(
                              _displayMonth.year, _displayMonth.month + 1, 1);
                        });
                      },
                    ),
                  ],
                ),
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: const Icon(Icons.file_download,
                        color: Color(0xFF4DB6AC)),
                    tooltip: '엑셀로 내보내기',
                    onPressed: () => _exportToExcel(),
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline,
                        color: Colors.redAccent),
                    tooltip: '해당 월 기록 삭제',
                    onPressed: () async {
                      final y = _displayMonth.year;
                      final m = _displayMonth.month;
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          backgroundColor: const Color(0xFF202026),
                          title: const Text('해당 월 기록 초기화',
                              style: TextStyle(color: Colors.white)),
                          content: Text(
                              '$y년 $m월에 기록된 모든 출퇴근 스탬프를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
                              style: const TextStyle(color: Colors.white70)),
                          actions: [
                            TextButton(
                                onPressed: () => Navigator.pop(ctx, false),
                                child: const Text('취소',
                                    style: TextStyle(color: Colors.white54))),
                            TextButton(
                                onPressed: () => Navigator.pop(ctx, true),
                                child: const Text('삭제',
                                    style: TextStyle(color: Colors.redAccent))),
                          ],
                        ),
                      );
                      if (confirm == true) {
                        await ref
                            .read(historyProvider.notifier)
                            .clearMonth(y, m);
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                              content: Text('$y년 $m월 출퇴근 스탬프가 삭제되었습니다.'),
                              backgroundColor: const Color(0xFF4DB6AC)));
                        }
                      }
                    },
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          _buildCalendarGrid(_displayMonth, historyMap),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                    color: Color(0xFF4DB6AC), shape: BoxShape.circle),
              ),
              const SizedBox(width: 4),
              const Text('출퇴근 완료',
                  style: TextStyle(color: Colors.white54, fontSize: 11)),
              const SizedBox(width: 16),
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                    color: Colors.orangeAccent, shape: BoxShape.circle),
              ),
              const SizedBox(width: 4),
              const Text('미완료',
                  style: TextStyle(color: Colors.white54, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 20),
          _buildRecordList(historyMap),
        ],
      ),
    );
  }

  Widget _buildRecordList(Map<DateTime, List<DateTime>> historyMap) {
    final y = _displayMonth.year;
    final m = _displayMonth.month;
    final daysInMonth = DateTime(y, m + 1, 0).day;
    final weekdays = ['월', '화', '수', '목', '금', '토', '일'];

    final entries = <MapEntry<DateTime, List<DateTime>>>[];
    for (int d = daysInMonth; d >= 1; d--) {
      final date = DateTime(y, m, d);
      final recs = historyMap[date] ?? [];
      if (recs.isNotEmpty) entries.add(MapEntry(date, recs));
    }

    if (entries.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF202026),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white10),
        ),
        child: const Center(
          child: Text('이번 달 기록이 없습니다.',
              style: TextStyle(color: Colors.white38, fontSize: 13)),
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF202026),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: entries.asMap().entries.map((e) {
          final idx = e.key;
          final date = e.value.key;
          final recs = e.value.value;
          final dayStr =
              '${date.month}/${date.day}(${weekdays[date.weekday - 1]})';
          final inTime =
              '${recs.first.hour.toString().padLeft(2, '0')}:${recs.first.minute.toString().padLeft(2, '0')}';
          final outTime = recs.length >= 2
              ? '${recs.last.hour.toString().padLeft(2, '0')}:${recs.last.minute.toString().padLeft(2, '0')}'
              : null;
          final isLast = idx == entries.length - 1;

          return Column(
            children: [
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    SizedBox(
                      width: 64,
                      child: Text(
                        dayStr,
                        style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 13,
                            fontWeight: FontWeight.w600),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Row(
                        children: [
                          Container(
                            width: 6,
                            height: 6,
                            decoration: const BoxDecoration(
                                color: Colors.orangeAccent,
                                shape: BoxShape.circle),
                          ),
                          const SizedBox(width: 6),
                          Text(inTime,
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 14,
                                  fontWeight: FontWeight.bold)),
                          const SizedBox(width: 4),
                          const Text('출근',
                              style: TextStyle(
                                  color: Colors.white38, fontSize: 11)),
                        ],
                      ),
                    ),
                    Expanded(
                      child: outTime != null
                          ? Row(
                              children: [
                                Container(
                                  width: 6,
                                  height: 6,
                                  decoration: const BoxDecoration(
                                      color: Color(0xFF4DB6AC),
                                      shape: BoxShape.circle),
                                ),
                                const SizedBox(width: 6),
                                Text(outTime,
                                    style: const TextStyle(
                                        color: Color(0xFF4DB6AC),
                                        fontSize: 14,
                                        fontWeight: FontWeight.bold)),
                                const SizedBox(width: 4),
                                const Text('퇴근',
                                    style: TextStyle(
                                        color: Colors.white38, fontSize: 11)),
                              ],
                            )
                          : const Text('퇴근 미기록',
                              style: TextStyle(
                                  color: Colors.orangeAccent, fontSize: 12)),
                    ),
                  ],
                ),
              ),
              if (!isLast)
                const Divider(
                    height: 1,
                    color: Colors.white10,
                    indent: 16,
                    endIndent: 16),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildCalendarGrid(
      DateTime displayMonth, Map<DateTime, List<DateTime>> historyMap) {
    final firstDayOfMonth = DateTime(displayMonth.year, displayMonth.month, 1);
    final lastDayOfMonth =
        DateTime(displayMonth.year, displayMonth.month + 1, 0);
    final firstWeekday = firstDayOfMonth.weekday;
    final emptyOffset = firstWeekday % 7;
    final rowCount = ((emptyOffset + lastDayOfMonth.day) / 7).ceil();
    final daysOfWeek = ['일', '월', '화', '수', '목', '금', '토'];
    final realNow = DateTime.now();

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF202026),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: daysOfWeek
                .map((day) => Expanded(
                      child: Center(
                        child: Text(
                          day,
                          style: TextStyle(
                            color: day == '일'
                                ? Colors.redAccent
                                : (day == '토'
                                    ? Colors.blueAccent
                                    : Colors.white54),
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ))
                .toList(),
          ),
          const SizedBox(height: 6),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: rowCount * 7,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              mainAxisExtent: 52,
              mainAxisSpacing: 2,
              crossAxisSpacing: 0,
            ),
            itemBuilder: (context, index) {
              if (index < emptyOffset ||
                  index >= emptyOffset + lastDayOfMonth.day) {
                return const SizedBox();
              }
              final day = index - emptyOffset + 1;
              final date = DateTime(displayMonth.year, displayMonth.month, day);
              final isToday = date.year == realNow.year &&
                  date.month == realNow.month &&
                  date.day == realNow.day;
              final isFuture = date
                  .isAfter(DateTime(realNow.year, realNow.month, realNow.day));
              final isWeekend = date.weekday == DateTime.saturday ||
                  date.weekday == DateTime.sunday;
              final records = historyMap[date] ?? [];

              Color stampColor = Colors.transparent;
              bool hasBoth = false;
              bool hasOne = false;
              if (!isFuture) {
                if (records.length >= 2) {
                  stampColor = const Color(0xFF4DB6AC);
                  hasBoth = true;
                } else if (records.length == 1) {
                  stampColor = Colors.orangeAccent;
                  hasOne = true;
                }
              }

              return Container(
                margin: const EdgeInsets.all(1),
                decoration: BoxDecoration(
                  color: isToday
                      ? const Color(0xFF4DB6AC).withValues(alpha: 0.18)
                      : hasBoth
                          ? const Color(0xFF4DB6AC).withValues(alpha: 0.08)
                          : hasOne
                              ? Colors.orangeAccent.withValues(alpha: 0.06)
                              : Colors.transparent,
                  borderRadius: BorderRadius.circular(6),
                  border: isToday
                      ? Border.all(color: const Color(0xFF4DB6AC), width: 1.5)
                      : null,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '$day',
                      style: TextStyle(
                        color: isWeekend
                            ? Colors.white38
                            : (isToday
                                ? const Color(0xFF4DB6AC)
                                : Colors.white70),
                        fontSize: 13,
                        fontWeight:
                            isToday ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                    const SizedBox(height: 3),
                    if (hasBoth || hasOne)
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          color: stampColor,
                          shape: BoxShape.circle,
                        ),
                      )
                    else
                      const SizedBox(height: 7),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsTab(settings) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('지오펜스 설정',
              style: TextStyle(color: Colors.white54, fontSize: 14)),
          const SizedBox(height: 12),
          _buildSettingsCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('감지 반경',
                      style: TextStyle(color: Colors.white, fontSize: 16)),
                  trailing: Text('${settings.geofenceRadius.toInt()}m',
                      style: const TextStyle(
                          color: Color(0xFF4DB6AC),
                          fontWeight: FontWeight.bold,
                          fontSize: 16)),
                  onTap: () => _showRadiusDialog(settings),
                ),
                const Divider(color: Colors.white10, height: 1),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('알림 반복 간격',
                      style: TextStyle(color: Colors.white, fontSize: 16)),
                  trailing: Text('${settings.repeatIntervalSec}초',
                      style: const TextStyle(
                          color: Color(0xFF4DB6AC),
                          fontWeight: FontWeight.bold,
                          fontSize: 16)),
                  onTap: () => _showIntervalDialog(settings),
                ),
              ],
            ),
          ),
          const Text('지오펜스 초기화',
              style: TextStyle(color: Colors.white54, fontSize: 14)),
          const SizedBox(height: 12),
          _buildSettingsCard(
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: _resettingDefault ? null : _resetToDefaultLocation,
                child: Container(
                  constraints: const BoxConstraints(minHeight: 64),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE57373).withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: const Color(0xFFE57373).withValues(alpha: 0.38),
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color:
                              const Color(0xFFE57373).withValues(alpha: 0.16),
                          shape: BoxShape.circle,
                        ),
                        child: _resettingDefault
                            ? const Padding(
                                padding: EdgeInsets.all(10),
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Color(0xFFE57373),
                                ),
                              )
                            : const Icon(Icons.refresh,
                                color: Color(0xFFE57373)),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Text(
                          _resettingDefault ? '복구 중...' : '서대문역 기본 위치로 복구',
                          style: const TextStyle(
                            color: Color(0xFFE57373),
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                      ),
                      const Icon(Icons.chevron_right, color: Color(0xFFE57373)),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Future<void> _showRadiusDialog(settings) async {
    double tempRadius = settings.geofenceRadius;
    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (dialogCtx, setDialogState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF202026),
            title:
                const Text('감지 반경 설정', style: TextStyle(color: Colors.white)),
            content: SizedBox(
              height: 100,
              child: Column(
                children: [
                  Text('${tempRadius.toInt()}m',
                      style: const TextStyle(
                          color: Color(0xFF4DB6AC),
                          fontSize: 24,
                          fontWeight: FontWeight.bold)),
                  Slider(
                    value: tempRadius,
                    min: 20,
                    max: 200,
                    divisions: 18,
                    activeColor: const Color(0xFF4DB6AC),
                    inactiveColor: Colors.white10,
                    onChanged: (v) {
                      setDialogState(() => tempRadius = v);
                    },
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('취소',
                      style: TextStyle(color: Colors.white54))),
              TextButton(
                onPressed: () async {
                  final messenger = ScaffoldMessenger.of(context);
                  Navigator.pop(ctx);
                  await ref
                      .read(settingsProvider.notifier)
                      .updateRadius(tempRadius);
                  final updated = ref.read(settingsProvider);
                  if (!updated.isPaused) {
                    final inRange = await _isCurrentlyInRange(updated);
                    await NhBackgroundServiceManager.sendUpdate(
                      isPaused: false,
                      lat: updated.geofenceLat,
                      lng: updated.geofenceLng,
                      radius: updated.geofenceRadius,
                      forceStartReminder: inRange,
                      showInitialUiEvent: false,
                    );
                    messenger.showSnackBar(SnackBar(
                      content: Text('${tempRadius.toInt()}m 반경이 적용되었습니다.'),
                      backgroundColor: const Color(0xFF4DB6AC),
                    ));
                  } else {
                    messenger.showSnackBar(SnackBar(
                      content: Text(
                          '${tempRadius.toInt()}m 반경이 저장되었습니다. (모니터링 재개 시 적용됩니다.)'),
                      backgroundColor: const Color(0xFFFF9800),
                    ));
                  }
                },
                child: const Text('확인',
                    style: TextStyle(color: Color(0xFF4DB6AC))),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _showIntervalDialog(settings) async {
    int tempInterval = settings.repeatIntervalSec;
    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (dialogCtx, setDialogState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF202026),
            title: const Text('알림 반복 간격 설정',
                style: TextStyle(color: Colors.white)),
            content: SizedBox(
              height: 100,
              child: Column(
                children: [
                  Text('$tempInterval초',
                      style: const TextStyle(
                          color: Color(0xFF4DB6AC),
                          fontSize: 24,
                          fontWeight: FontWeight.bold)),
                  Slider(
                    value: tempInterval.toDouble(),
                    min: 30,
                    max: 300,
                    divisions: 9,
                    activeColor: const Color(0xFF4DB6AC),
                    inactiveColor: Colors.white10,
                    onChanged: (v) {
                      setDialogState(() => tempInterval = v.toInt());
                    },
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('취소',
                      style: TextStyle(color: Colors.white54))),
              TextButton(
                onPressed: () async {
                  final messenger = ScaffoldMessenger.of(context);
                  Navigator.pop(ctx);
                  await ref
                      .read(settingsProvider.notifier)
                      .updateRepeatInterval(tempInterval);
                  await NhBackgroundServiceManager.sendIntervalUpdate(
                      tempInterval);
                  final updated = ref.read(settingsProvider);
                  if (!updated.isPaused) {
                    messenger.showSnackBar(SnackBar(
                      content: Text('알림 간격이 $tempInterval초로 변경되었습니다.'),
                      backgroundColor: const Color(0xFF4DB6AC),
                    ));
                  } else {
                    messenger.showSnackBar(SnackBar(
                      content: Text(
                          '알림 간격이 $tempInterval초로 저장되었습니다. (모니터링 재개 시 적용됩니다.)'),
                      backgroundColor: const Color(0xFFFF9800),
                    ));
                  }
                },
                child: const Text('확인',
                    style: TextStyle(color: Color(0xFF4DB6AC))),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSettingsCard({required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF202026),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: child,
    );
  }

  Future<void> _calibrateLocation(settings) async {
    setState(() => _locationUpdating = true);
    try {
      final result = await MonitoringRecoveryService.reset(
        reason: '수동 위치보정',
        recalibrateCurrentPosition: true,
        resumeMonitoring: !settings.isPaused,
        clearDismissalOnResume: true,
      );
      await ref.read(settingsProvider.notifier).reload();
      if (!result.positionUpdated && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              settings.isPaused
                  ? '위치보정 실패. 모니터링 중지 상태는 유지했습니다.'
                  : '위치보정 실패. 기존 위치로 모니터링을 재시작했습니다.',
            ),
            backgroundColor: Colors.red,
          ),
        );
      } else if (settings.isPaused && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('위치보정 완료. 모니터링 중지 상태는 유지했습니다.'),
            backgroundColor: Color(0xFF4DB6AC),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('위치 확인 실패: $e'), backgroundColor: Colors.red));
      }
    } finally {
      if (mounted) {
        setState(() => _locationUpdating = false);
      }
    }
  }

  Future<LocationJudgment?> _getCurrentJudgment(settings) async {
    try {
      final perm = await Geolocator.checkPermission();
      if (perm != LocationPermission.always &&
          perm != LocationPermission.whileInUse) {
        return null;
      }
      return LocationJudgmentService.fromCurrentPosition(
        centerLat: settings.geofenceLat,
        centerLng: settings.geofenceLng,
        radius: settings.geofenceRadius,
      );
    } catch (_) {
      return null;
    }
  }

  Future<bool> _isCurrentlyInRange(settings) async {
    final judgment = await _getCurrentJudgment(settings);
    return judgment?.isReliableInside ?? false;
  }

  Future<void> _resetToDefaultLocation() async {
    if (_resettingDefault) {
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _resettingDefault = true);

    try {
      await ref.read(settingsProvider.notifier).resetToDefault();
      final updated = ref.read(settingsProvider);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('dismissed_until_exit', false);
      await prefs.setInt('geofence_exit_count', 0);
      await prefs.setInt('monitor_outside_count', 0);
      await prefs.setInt('notif_outside_count', 0);
      LogFileService.log(
        '[NH알리미] 서대문역 기본 위치 복구 요청 — lat:${updated.geofenceLat}, '
        'lng:${updated.geofenceLng}, 반경:${updated.geofenceRadius}m, 차단 플래그 해제',
      );

      LocationJudgment? judgment;
      if (!updated.isPaused) {
        judgment = await _getCurrentJudgment(updated);
      }
      final inRange = judgment?.isReliableInside ?? false;
      try {
        await NhBackgroundServiceManager.sendUpdate(
          isPaused: updated.isPaused,
          lat: updated.geofenceLat,
          lng: updated.geofenceLng,
          radius: updated.geofenceRadius,
          forceStartReminder: inRange && !updated.isPaused,
          showInitialUiEvent: false,
        ).timeout(const Duration(seconds: 6));
      } catch (e) {
        LogFileService.log('[NH알리미] 서대문역 복구 후 모니터링 동기화 지연 — $e');
      }

      if (!mounted) return;
      final statusText = updated.isPaused
          ? '서대문역 위치로 복구했습니다. 모니터링 중지 상태는 유지했습니다.'
          : judgment == null
              ? '서대문역 위치로 복구했습니다. 현재 범위 상태는 확인하지 못했습니다.'
              : inRange
                  ? '현재위치는 서대문역 지오펜스 범위 안입니다.'
                  : '현재위치는 서대문역 지오펜스 범위 밖입니다.';
      messenger.showSnackBar(
        SnackBar(
          content: Text(statusText),
          backgroundColor: updated.isPaused || inRange
              ? const Color(0xFF4DB6AC)
              : const Color(0xFFFF9800),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      messenger.showSnackBar(
        SnackBar(
          content: Text('서대문역 위치 복구 실패: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _resettingDefault = false);
      }
    }
  }

  Future<void> _launchNhApp() async {
    await ref.read(historyProvider.notifier).addTimestamp(DateTime.now());
    await _geoSvc.dismissUntilExit();
    await _nhAppLauncher.launchNhApp();
  }

  Future<void> _exportToExcel() async {
    try {
      final historyMap = ref.read(historyProvider);
      var excel = Excel.createExcel();
      Sheet sheetObject = excel['Sheet1'];

      sheetObject.appendRow([
        TextCellValue('날짜'),
        TextCellValue('출근'),
        TextCellValue('퇴근'),
      ]);

      final y = _displayMonth.year;
      final m = _displayMonth.month;
      final daysInMonth = DateTime(y, m + 1, 0).day;
      final weekdays = ['월', '화', '수', '목', '금', '토', '일'];

      for (int day = 1; day <= daysInMonth; day++) {
        final date = DateTime(y, m, day);
        final weekdayStr = weekdays[date.weekday - 1];
        final dayStr = '${day.toString().padLeft(2, '0')}($weekdayStr)';

        final records = historyMap[date] ?? [];

        String inMark = '';
        String outMark = '';

        if (records.isNotEmpty) {
          final inTime = records.first;
          inMark =
              '${inTime.hour.toString().padLeft(2, '0')}:${inTime.minute.toString().padLeft(2, '0')}';
          if (records.length >= 2) {
            final outTime = records.last;
            outMark =
                '${outTime.hour.toString().padLeft(2, '0')}:${outTime.minute.toString().padLeft(2, '0')}';
          }
        }

        sheetObject.appendRow([
          TextCellValue(dayStr),
          TextCellValue(inMark),
          TextCellValue(outMark),
        ]);
      }

      final directory = await getTemporaryDirectory();
      final fileName = '${m.toString().padLeft(2, '0')}월 출퇴근 기록.xlsx';
      final filePath = '${directory.path}/$fileName';
      final fileBytes = excel.save();

      if (fileBytes != null) {
        final file = File(filePath);
        await file.writeAsBytes(fileBytes);

        if (mounted) {
          await Share.shareXFiles([XFile(filePath)],
              text: '$y년 $m월 출퇴근 기록입니다.');
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('엑셀 내보내기 실패: $e'), backgroundColor: Colors.red));
      }
    }
  }
}
