import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/settings_provider.dart';
import '../providers/history_provider.dart';
import '../services/geofence_service.dart';
import '../services/notification_service.dart';
import '../services/usage_stats_service.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> with SingleTickerProviderStateMixin {
  final _geoSvc = NhGeofenceService();
  final _notifSvc = NotificationService();
  final _usageSvc = UsageStatsService();
  bool _locationUpdating = false;
  int _currentIndex = 0;

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.1).animate(_pulseController);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF151518), // 다크 메탈릭 테마 배경
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C1C22),
        foregroundColor: Colors.white,
        title: const Text(
          'NH 리마인더',
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
        selectedItemColor: const Color(0xFF4DB6AC), // 파스텔톤 민트
        unselectedItemColor: Colors.white54,
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_filled), label: '홈'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: '기록'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: '설정'),
        ],
      ),
    );
  }

  // ==========================================
  // 홈 탭
  // ==========================================
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
        border: Border.all(color: const Color(0xFFFF9800).withOpacity(0.5)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: const [
          Icon(Icons.pause_circle_filled, color: Color(0xFFFFB74D), size: 28),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              '알림 정지 중\n출퇴근 시 재개하여 모니터링을 활성화하세요.',
              style: TextStyle(color: Color(0xFFFFCC80), fontSize: 13, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusCard(settings) {
    final isActive = !settings.isPaused;
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [const Color(0xFF26262F), const Color(0xFF1E1E24)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white10),
        boxShadow: const [
          BoxShadow(color: Colors.black26, blurRadius: 20, offset: Offset(0, 10))
        ],
      ),
      child: Column(
        children: [
          ScaleTransition(
            scale: isActive ? _pulseAnimation : const AlwaysStoppedAnimation(1.0),
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isActive ? const Color(0xFF4DB6AC).withOpacity(0.15) : Colors.white10,
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
                ? '서대문역 5번 출구 반경 ${settings.geofenceRadius.toInt()}m'
                : '현재 지오펜스 모니터링을 중단했습니다.',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 14, color: Colors.white54, height: 1.5),
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
              await _geoSvc.stop();
            } else {
              await _geoSvc.start(
                lat: updated.geofenceLat,
                lng: updated.geofenceLng,
                radius: updated.geofenceRadius,
                isPaused: false,
              );
            }
          },
          icon: Icon(isPaused ? Icons.play_arrow_rounded : Icons.pause, size: 24),
          label: Text(
            isPaused ? '모니터링 재개' : '모니터링 일시정지',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          style: ElevatedButton.styleFrom(
            backgroundColor: isPaused ? const Color(0xFF4DB6AC) : const Color(0xFFE57373),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 18),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            elevation: 8,
            shadowColor: (isPaused ? const Color(0xFF4DB6AC) : const Color(0xFFE57373)).withOpacity(0.5),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildSecondaryButton(
                icon: Icons.my_location,
                label: '위치 보정',
                onTap: _locationUpdating ? null : () => _calibrateLocation(settings),
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

  Widget _buildSecondaryButton({required IconData icon, required String label, VoidCallback? onTap, bool isLoading = false}) {
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
          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white54))
          : Column(
              children: [
                Icon(icon, size: 24, color: Colors.white70),
                const SizedBox(height: 8),
                Text(label, style: const TextStyle(fontSize: 13, color: Colors.white70)),
              ],
            ),
    );
  }

  // ==========================================
  // 기록 탭 (SharedPreferences 기반 실제 기록)
  // ==========================================
  Widget _buildHistoryTab() {
    final history = ref.watch(historyProvider);
    
    if (history.isEmpty) {
      return const Center(
        child: Text('출퇴근 기록이 없습니다.', style: TextStyle(color: Colors.white54)),
      );
    }
    
    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: history.length,
      itemBuilder: (context, index) {
        final record = history[index];
        final time = DateTime.tryParse(record['time'] ?? '')?.toLocal() ?? DateTime.now();
        final desc = record['desc'] ?? '기록 없음';
        
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF202026),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white10),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF4DB6AC).withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check_circle, color: Color(0xFF4DB6AC), size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      desc,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${time.year}년 ${time.month}월 ${time.day}일 ${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}',
                      style: const TextStyle(color: Colors.white54, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  // ==========================================
  // 설정 탭
  // ==========================================
  Widget _buildSettingsTab(settings) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('지오펜스 설정', style: TextStyle(color: Colors.white54, fontSize: 14)),
          const SizedBox(height: 12),
          _buildSettingsCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('감지 반경', style: TextStyle(color: Colors.white, fontSize: 16)),
                    Text('${settings.geofenceRadius.toInt()}m', style: const TextStyle(color: Color(0xFF4DB6AC), fontWeight: FontWeight.bold)),
                  ],
                ),
                Slider(
                  value: settings.geofenceRadius,
                  min: 20, max: 200, divisions: 18,
                  activeColor: const Color(0xFF4DB6AC),
                  inactiveColor: Colors.white10,
                  onChanged: (v) => ref.read(settingsProvider.notifier).updateRadius(v),
                ),
                const Divider(color: Colors.white10, height: 30),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('알림 반복 간격', style: TextStyle(color: Colors.white, fontSize: 16)),
                    Text('${settings.repeatIntervalSec}초', style: const TextStyle(color: Color(0xFF4DB6AC), fontWeight: FontWeight.bold)),
                  ],
                ),
                Slider(
                  value: settings.repeatIntervalSec.toDouble(),
                  min: 30, max: 300, divisions: 9,
                  activeColor: const Color(0xFF4DB6AC),
                  inactiveColor: Colors.white10,
                  onChanged: (v) => ref.read(settingsProvider.notifier).updateRepeatInterval(v.toInt()),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const Text('시스템 권한', style: TextStyle(color: Colors.white54, fontSize: 14)),
          const SizedBox(height: 12),
          _buildSettingsCard(
            child: ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.security, color: Colors.white70),
              title: const Text('권한 설정 관리', style: TextStyle(color: Colors.white)),
              trailing: const Icon(Icons.chevron_right, color: Colors.white54),
              onTap: () async {
                 await _usageSvc.openPermissionSettings();
              },
            ),
          ),
          const Text('지오펜스 초기화', style: TextStyle(color: Colors.white54, fontSize: 14)),
          const SizedBox(height: 12),
          _buildSettingsCard(
            child: ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.refresh, color: Color(0xFFE57373)),
              title: const Text('서대문역 기본 위치로 복구', style: TextStyle(color: Color(0xFFE57373), fontWeight: FontWeight.bold)),
              onTap: () async {
                await ref.read(settingsProvider.notifier).resetToDefault();
                final updated = ref.read(settingsProvider);
                await _geoSvc.stop();
                await _geoSvc.start(
                  lat: updated.geofenceLat,
                  lng: updated.geofenceLng,
                  radius: updated.geofenceRadius,
                  isPaused: updated.isPaused,
                );
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('지오펜스 중심이 서대문역으로 초기화되었습니다.'), backgroundColor: Color(0xFF4DB6AC)));
                }
              },
            ),
          ),
          const SizedBox(height: 40),
        ],
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

  // ==========================================
  // 로직
  // ==========================================
  Future<void> _calibrateLocation(settings) async {
    setState(() => _locationUpdating = true);
    try {
      LocationPermission perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.always || perm == LocationPermission.whileInUse) {
        final pos = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
        await ref.read(settingsProvider.notifier).updateGeofenceLocation(pos.latitude, pos.longitude);

        final updated = ref.read(settingsProvider);
        await _geoSvc.stop();
        await _geoSvc.start(
          lat: updated.geofenceLat,
          lng: updated.geofenceLng,
          radius: updated.geofenceRadius,
          isPaused: updated.isPaused,
        );

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('위치를 성공적으로 보정했습니다.'), backgroundColor: Color(0xFF4DB6AC)));
        }
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('위치 확인 실패: $e'), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _locationUpdating = false);
    }
  }

  Future<void> _launchNhApp() async {
    final uri = Uri.parse('intent://launch#Intent;package=com.vus.nhpthrm;scheme=nhpartners;end');
    final storeUri = Uri.parse('https://play.google.com/store/apps/details?id=com.vus.nhpthrm');

    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      await launchUrl(storeUri, mode: LaunchMode.externalApplication);
    }
  }
}
