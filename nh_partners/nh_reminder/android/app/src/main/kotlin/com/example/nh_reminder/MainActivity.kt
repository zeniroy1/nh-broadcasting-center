package com.example.nh_reminder

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    private val CHANNEL = "com.example.nh_reminder/nh_app_launcher"
    private val NATIVE_MONITOR_CHANNEL = "com.example.nh_reminder/native_monitor"
    private val NH_PACKAGE = "com.vus.nhpthrm"
    private val REMINDER_CHANNEL_ID = "nh_reminder_high_v2"
    private val REMINDER_NOTIF_ID = 1001

    override fun onCreate(savedInstanceState: android.os.Bundle?) {
        super.onCreate(savedInstanceState)
        NativeServiceScheduler.schedule(this)

        // ✅ 모니터링 시간대에는 포그라운드 서비스 시작/복구
        try {
            if (isUserPaused()) {
                NhBackgroundService.stop(this)
                Log.d("NHAlimi", "사용자 모니터링 OFF — 포그라운드 서비스 시작 생략")
            } else if (NativeServiceScheduler.isMonitoringHours()) {
                setNativePaused(false)
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
                        if (paused) {
                            NhBackgroundService.stop(this)
                            Log.d("NHAlimi", "모니터링 일시정지 반영 — 포그라운드 서비스 중지")
                        } else if (NativeServiceScheduler.isMonitoringHours()) {
                            NhBackgroundService.start(this)
                            Log.d("NHAlimi", "모니터링 재개 반영 — 포그라운드 서비스 시작/복구")
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
                    "cancelReminderNotification" -> {
                        getSystemService(NotificationManager::class.java)?.cancel(REMINDER_NOTIF_ID)
                        Log.d("NHAlimi", "네이티브 직접 알림 취소")
                        result.success(null)
                    }
                    "stopService" -> {
                        getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
                            .edit()
                            .putBoolean("flutter.is_paused", true)
                            .putBoolean("flutter.notif_active", false)
                            .apply()
                        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
                            .edit()
                            .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, true)
                            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, false)
                            .apply()
                        getSystemService(NotificationManager::class.java)?.cancel(REMINDER_NOTIF_ID)
                        NhBackgroundService.stop(this)
                        Log.d("NHAlimi", "Flutter 요청 — 네이티브 포그라운드 서비스 종료")
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

    private fun isUserPaused(): Boolean {
        val flutterPrefs = getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
        return flutterPrefs.getBoolean("flutter.user_paused", false)
    }

    private fun setNativePaused(paused: Boolean) {
        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, paused)
            .apply()
    }

    private fun handleReminderNotificationIntent(intent: Intent?) {
        if (!hasOpenNhPayload(intent)) return

        Log.d("NHAlimi", "알림 본문 클릭 감지 — 기록 저장 후 NH파트너스 실행")
        ReminderActionHandler.handleOpenNh(this, "flutter_notification")
    }

    private fun hasOpenNhPayload(intent: Intent?): Boolean {
        val extras = intent?.extras ?: return false
        return extras.keySet().any { key -> extras.get(key)?.toString() == "open_nh" }
    }

    private fun showDirectReminderNotification() {
        createReminderChannel()

        val actionIntent = Intent(this, ReminderActionReceiver::class.java).apply {
            action = ReminderActionHandler.ACTION_OPEN_NH
            putExtra(ReminderActionHandler.EXTRA_PAYLOAD, ReminderActionHandler.PAYLOAD_OPEN_NH)
        }

        val pendingIntent = PendingIntent.getBroadcast(
            this,
            REMINDER_NOTIF_ID,
            actionIntent,
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
            .setDefaults(Notification.DEFAULT_VIBRATE)
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
                vibrationPattern = longArrayOf(0, 700, 200, 700, 200, 700)
            }
            getSystemService(NotificationManager::class.java)?.createNotificationChannel(channel)
        }
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
