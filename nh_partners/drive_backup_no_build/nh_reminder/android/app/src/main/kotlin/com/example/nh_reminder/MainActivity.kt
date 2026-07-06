package com.example.nh_reminder

import android.app.AppOpsManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Process
import android.provider.Settings
import android.util.Log
import androidx.core.app.NotificationCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    private val CHANNEL = "com.example.nh_reminder/usage_stats"
    private val NATIVE_MONITOR_CHANNEL = "com.example.nh_reminder/native_monitor"
    private val NH_PACKAGE = "com.vus.nhpthrm"
    private val REMINDER_CHANNEL_ID = "nh_reminder_high_v1"
    private val REMINDER_NOTIF_ID = 1001

    override fun onCreate(savedInstanceState: android.os.Bundle?) {
        super.onCreate(savedInstanceState)
        NativeServiceScheduler.schedule(this)

        // ✅ 모니터링 시간대에는 포그라운드 서비스 시작/복구
        try {
            if (NativeServiceScheduler.isMonitoringHours()) {
                NhBackgroundService.start(this)
                Log.d("NHAlimi", "포그라운드 서비스 시작/복구 요청")
            } else {
                NhBackgroundService.stop(this)
                Log.d("NHAlimi", "모니터링 시간 외 — 포그라운드 서비스 중지")
            }
        } catch (e: Exception) {
            Log.e("NHAlimi", "서비스 시작 실패: ${e.message}")
        }

        handleReminderNotificationIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleReminderNotificationIntent(intent)
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "isAppInForeground" -> {
                        val pkg = call.argument<String>("package") ?: NH_PACKAGE
                        result.success(isAppInForeground(pkg))
                    }
                    "hasUsagePermission" -> {
                        result.success(hasUsagePermission())
                    }
                    "openUsageSettings" -> {
                        openUsageSettings()
                        result.success(null)
                    }
                    "launchNhApp" -> {
                        launchNhApp()
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, NATIVE_MONITOR_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "updateConfig" -> {
                        val paused = call.argument<Boolean>("paused") ?: false
                        val lat = call.argument<Double>("lat") ?: 37.56600
                        val lng = call.argument<Double>("lng") ?: 126.96730
                        val radius = call.argument<Double>("radius") ?: 30.0
                        val notifActive = call.argument<Boolean>("notifActive") ?: false
                        updateNativeMonitorConfig(paused, lat, lng, radius, notifActive)
                        if (NativeServiceScheduler.isMonitoringHours()) {
                            NhBackgroundService.start(this)
                        }
                        result.success(null)
                    }
                    "updateNotificationActive" -> {
                        val notifActive = call.argument<Boolean>("notifActive") ?: false
                        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
                            .edit()
                            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, notifActive)
                            .apply()
                        result.success(null)
                    }
                    "showReminderNotification" -> {
                        showDirectReminderNotification()
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
    }

    private fun updateNativeMonitorConfig(
        paused: Boolean,
        lat: Double,
        lng: Double,
        radius: Double,
        notifActive: Boolean
    ) {
        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, paused)
            .putLong(NhBackgroundService.KEY_NATIVE_LAT, lat.toBits())
            .putLong(NhBackgroundService.KEY_NATIVE_LNG, lng.toBits())
            .putLong(NhBackgroundService.KEY_NATIVE_RADIUS, radius.toBits())
            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, notifActive)
            .apply()

        Log.d(
            "NHAlimi",
            "네이티브 보조 감시 설정 반영: paused=$paused, lat=$lat, lng=$lng, " +
                    "radius=$radius, notifActive=$notifActive"
        )
    }

    private fun handleReminderNotificationIntent(intent: Intent?) {
        if (!hasOpenNhPayload(intent)) return

        Log.d("NHAlimi", "알림 본문 클릭 감지 — NH파트너스 실행")
        markReminderHandledFromNotification()
        launchNhApp()
    }

    private fun hasOpenNhPayload(intent: Intent?): Boolean {
        val extras = intent?.extras ?: return false
        return extras.keySet().any { key -> extras.get(key)?.toString() == "open_nh" }
    }

    private fun markReminderHandledFromNotification() {
        getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            .edit()
            .putBoolean("flutter.notif_active", false)
            .putBoolean("flutter.dismissed_until_exit", true)
            .apply()

        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, false)
            .apply()

        getSystemService(NotificationManager::class.java)?.cancel(1001)
    }

    private fun showDirectReminderNotification() {
        createReminderChannel()

        val nhIntent = packageManager.getLaunchIntentForPackage(NH_PACKAGE)
            ?: Intent(Intent.ACTION_VIEW, android.net.Uri.parse("market://details?id=$NH_PACKAGE"))
        nhIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

        val pendingIntent = PendingIntent.getActivity(
            this,
            REMINDER_NOTIF_ID,
            nhIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, REMINDER_CHANNEL_ID)
            .setContentTitle("🔔 출퇴근 버튼을 눌렀나요?")
            .setContentText("알림 본문이나 버튼을 눌러 NH파트너스를 열어주세요.")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setContentIntent(pendingIntent)
            .setAutoCancel(false)
            .setOngoing(false)
            .setVibrate(longArrayOf(0, 700, 200, 700, 200, 700))
            .addAction(0, "📲 NH파트너스 열기", pendingIntent)
            .build()

        getSystemService(NotificationManager::class.java)?.notify(REMINDER_NOTIF_ID, notification)
        Log.d("NHAlimi", "네이티브 직접 알림 발송 — 본문 클릭 NH파트너스 연결")
    }

    private fun createReminderChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                REMINDER_CHANNEL_ID,
                "출퇴근 알림",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "농협파트너스 출퇴근 버튼 클릭 확인 알림"
                enableVibration(true)
            }
            getSystemService(NotificationManager::class.java)?.createNotificationChannel(channel)
        }
    }

    /** NH파트너스 앱이 지금 포그라운드에 있는지 확인 */
    private fun isAppInForeground(targetPackage: String): Boolean {
        if (!hasUsagePermission()) return false
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return false

        val usm = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val now = System.currentTimeMillis()
        // 최근 10초 이내 사용 통계 조회
        val stats = usm.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            now - 10_000L,
            now
        )
        if (stats.isNullOrEmpty()) return false

        // 가장 최근에 사용된 앱이 NH파트너스인지 확인
        val recentStat = stats.maxByOrNull { it.lastTimeUsed }
        return recentStat?.packageName == targetPackage
    }

    /** PACKAGE_USAGE_STATS 권한 보유 여부 */
    private fun hasUsagePermission(): Boolean {
        return try {
            val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
            val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                appOps.unsafeCheckOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    packageName
                )
            } else {
                @Suppress("DEPRECATION")
                appOps.checkOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    packageName
                )
            }
            mode == AppOpsManager.MODE_ALLOWED
        } catch (e: Exception) {
            false
        }
    }

    /** 사용 내역 권한 설정 화면 열기 */
    private fun openUsageSettings() {
        startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
    }

    /** NH파트너스 앱 100% 강제 실행 */
    private fun launchNhApp() {
        val launchIntent = packageManager.getLaunchIntentForPackage(NH_PACKAGE)
        if (launchIntent != null) {
            startActivity(launchIntent)
        } else {
            val marketIntent = Intent(Intent.ACTION_VIEW, android.net.Uri.parse("market://details?id=$NH_PACKAGE"))
            startActivity(marketIntent)
        }
    }
}
