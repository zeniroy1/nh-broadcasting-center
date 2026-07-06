package com.example.nh_reminder

import android.app.AppOpsManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.usage.UsageStatsManager
import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Environment
import android.os.Process
import android.provider.MediaStore
import android.provider.Settings
import android.util.Log
import androidx.core.app.NotificationCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : FlutterActivity() {

    private val CHANNEL = "com.example.nh_reminder/usage_stats"
    private val NATIVE_MONITOR_CHANNEL = "com.example.nh_reminder/native_monitor"
    private val NH_PACKAGE = "com.vus.nhpthrm"
    private val REMINDER_CHANNEL_ID = "nh_reminder_high_v2"
    private val REMINDER_NOTIF_ID = 1001
    private val FLUTTER_PREFS = "FlutterSharedPreferences"
    private val MODE_FOREGROUND = "foreground"
    private val MODE_BACKGROUND_RECENT = "background_recent"
    private val MODE_SERVICE_ONLY = "service_only"

    override fun onCreate(savedInstanceState: android.os.Bundle?) {
        super.onCreate(savedInstanceState)
        persistAppExecutionState(
            mode = MODE_BACKGROUND_RECENT,
            activityVisible = false,
            activityAlive = true
        )
        NativeServiceScheduler.schedule(this)

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

    override fun onResume() {
        super.onResume()
        persistAppExecutionState(
            mode = MODE_FOREGROUND,
            activityVisible = true,
            activityAlive = true
        )
    }

    override fun onStop() {
        persistAppExecutionState(
            mode = MODE_BACKGROUND_RECENT,
            activityVisible = false,
            activityAlive = true
        )
        super.onStop()
    }

    override fun onDestroy() {
        persistAppExecutionState(
            mode = MODE_SERVICE_ONLY,
            activityVisible = false,
            activityAlive = false
        )
        appendServiceOnlySnapshot(reason = "activity_destroy")
        super.onDestroy()
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
                        val lat = call.argument<Double>("lat") ?: NhBackgroundService.DEFAULT_GEOFENCE_LAT
                        val lng = call.argument<Double>("lng") ?: NhBackgroundService.DEFAULT_GEOFENCE_LNG
                        val radius = call.argument<Double>("radius") ?: NhBackgroundService.DEFAULT_GEOFENCE_RADIUS
                        val notifActive = call.argument<Boolean>("notifActive") ?: false
                        val configGeneration = call.argument<Number>("configGeneration")?.toLong() ?: 0L
                        updateNativeMonitorConfig(paused, lat, lng, radius, notifActive, configGeneration)
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
                        val editor = getSharedPreferences(
                            NhBackgroundService.NATIVE_PREFS,
                            Context.MODE_PRIVATE
                        ).edit()
                            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, notifActive)
                        if (!notifActive) {
                            editor.putBoolean(NhBackgroundService.KEY_NATIVE_REPEAT_OWNER, false)
                        }
                        editor
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
                        getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
                            .edit()
                            .putBoolean("flutter.is_paused", true)
                            .putBoolean("flutter.notif_active", false)
                            .apply()
                        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
                            .edit()
                            .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, true)
                            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, false)
                            .putBoolean(NhBackgroundService.KEY_NATIVE_REPEAT_OWNER, false)
                            .apply()
                        getSystemService(NotificationManager::class.java)?.cancel(REMINDER_NOTIF_ID)
                        NhBackgroundService.stop(this)
                        Log.d("NHAlimi", "Flutter 요청 — 네이티브 포그라운드 서비스 종료")
                        result.success(null)
                    }
                    "saveTextToDownloads" -> {
                        try {
                            val fileName = call.argument<String>("fileName") ?: "NH알리미_핵심로그.txt"
                            val content = call.argument<String>("content") ?: ""
                            result.success(saveTextToDownloads(fileName, content))
                        } catch (e: Exception) {
                            result.error("SAVE_FAILED", e.message, null)
                        }
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
        notifActive: Boolean,
        configGeneration: Long
    ) {
        val safeRadius = radius.coerceIn(
            NhBackgroundService.MIN_GEOFENCE_RADIUS,
            NhBackgroundService.MAX_GEOFENCE_RADIUS
        )
        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, paused)
            .putLong(NhBackgroundService.KEY_NATIVE_LAT, lat.toBits())
            .putLong(NhBackgroundService.KEY_NATIVE_LNG, lng.toBits())
            .putLong(NhBackgroundService.KEY_NATIVE_RADIUS, safeRadius.toBits())
            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, notifActive)
            .putLong(NhBackgroundService.KEY_NATIVE_CONFIG_GENERATION, configGeneration)
            .apply()

        Log.d(
            "NHAlimi",
            "네이티브 보조 감시 설정 반영: paused=$paused, lat=$lat, lng=$lng, " +
                    "radius=$safeRadius, notifActive=$notifActive"
        )
    }

    private fun isUserPaused(): Boolean {
        val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        return flutterPrefs.getBoolean("flutter.user_paused", false)
    }

    private fun persistAppExecutionState(
        mode: String,
        activityVisible: Boolean,
        activityAlive: Boolean
    ) {
        getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString("flutter.app_execution_mode", mode)
            .putBoolean("flutter.app_activity_visible", activityVisible)
            .putBoolean("flutter.app_activity_alive", activityAlive)
            .putLong("flutter.last_activity_state_ms", System.currentTimeMillis())
            .apply()
    }

    private fun appendServiceOnlySnapshot(reason: String) {
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val lifecycle = prefs.getString("flutter.app_lifecycle_state", "unknown")
        val notifActive = prefs.getBoolean("flutter.notif_active", false)
        val paused = prefs.getBoolean("flutter.is_paused", false) ||
            prefs.getBoolean("flutter.user_paused", false)
        val message = "[NH알리미] 앱 실행상태 스냅샷 — " +
            "mode:$MODE_SERVICE_ONLY, source:activity, lifecycle:$lifecycle, " +
            "activityVisible:false, activityAlive:false, serviceActive:true, " +
            "notifActive:$notifActive, paused:$paused, reason:$reason"

        appendTextLog("nh_reminder_runtime.txt", message)
        appendTextLog("nh_alimi_user_diagnostic.txt", message)
    }

    private fun appendTextLog(fileName: String, message: String) {
        try {
            val timestamp = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS", Locale.KOREA)
                .format(Date())
            val logDir = getExternalFilesDir(null) ?: filesDir
            if (!logDir.exists()) {
                logDir.mkdirs()
            }
            File(logDir, fileName).appendText("[$timestamp] $message\n")
        } catch (e: Exception) {
            Log.e("NHAlimi", "Activity 파일 로그 실패: ${e.message}")
        }
    }

    private fun setNativePaused(paused: Boolean) {
        getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, paused)
            .apply()
    }

    private fun handleReminderNotificationIntent(intent: Intent?) {
        if (!hasOpenNhPayload(intent)) return

        val source = intent?.getStringExtra(ReminderActionHandler.EXTRA_SOURCE)
            ?: "flutter_notification"
        Log.d("NHAlimi", "알림 본문 클릭 감지 — 기록 저장 후 NH파트너스 실행 요청")
        UserDiagnosticLogger.append(
            this,
            "알림 본문 클릭 감지 — 기록 저장 후 NH파트너스 실행 요청, source:$source"
        )
        intent?.removeExtra(ReminderActionHandler.EXTRA_PAYLOAD)
        intent?.removeExtra(ReminderActionHandler.EXTRA_SOURCE)
        ReminderActionHandler.handleOpenNh(this, source)
    }

    private fun hasOpenNhPayload(intent: Intent?): Boolean {
        val extras = intent?.extras ?: return false
        return extras.keySet().any { key -> extras.get(key)?.toString() == "open_nh" }
    }

    private fun showDirectReminderNotification() {
        val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        if (flutterPrefs.getBoolean("flutter.is_paused", false) ||
            flutterPrefs.getBoolean("flutter.user_paused", false) ||
            flutterPrefs.getBoolean("flutter.dismissed_until_exit", false)
        ) {
            getSystemService(NotificationManager::class.java)?.cancel(REMINDER_NOTIF_ID)
            Log.d("NHAlimi", "네이티브 직접 알림 생략 — 차단 상태")
            return
        }
        createReminderChannel()

        val actionIntent = Intent(this, MainActivity::class.java).apply {
            action = ReminderActionHandler.ACTION_OPEN_NH
            putExtra(ReminderActionHandler.EXTRA_PAYLOAD, ReminderActionHandler.PAYLOAD_OPEN_NH)
            putExtra(ReminderActionHandler.EXTRA_SOURCE, "native_notification")
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
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
        Log.d("NHAlimi", "네이티브 직접 알림 발송 — 본문 클릭 Activity 경유 NH파트너스 연결")
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

    private fun saveTextToDownloads(fileName: String, content: String): String {
        val safeName = fileName.replace(Regex("""[\\/:*?"<>|]"""), "_")
        val relativeDir = "${Environment.DIRECTORY_DOWNLOADS}/nh_partners"

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            deleteExistingDownload(relativeDir, safeName)

            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, safeName)
                put(MediaStore.MediaColumns.MIME_TYPE, "text/plain")
                put(MediaStore.MediaColumns.RELATIVE_PATH, relativeDir)
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val uri = contentResolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                values
            ) ?: throw IllegalStateException("Download 파일 생성 실패")

            contentResolver.openOutputStream(uri)?.use { stream ->
                stream.write(content.toByteArray(Charsets.UTF_8))
            } ?: throw IllegalStateException("Download 파일 쓰기 실패")

            values.clear()
            values.put(MediaStore.MediaColumns.IS_PENDING, 0)
            contentResolver.update(uri, values, null, null)
            return "Download/nh_partners/$safeName"
        }

        @Suppress("DEPRECATION")
        val dir = File(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
            "nh_partners"
        )
        if (!dir.exists()) dir.mkdirs()
        val file = File(dir, safeName)
        file.writeText(content, Charsets.UTF_8)
        return file.absolutePath
    }

    private fun deleteExistingDownload(relativeDir: String, safeName: String) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return

        val collection = MediaStore.Downloads.EXTERNAL_CONTENT_URI
        val projection = arrayOf(MediaStore.MediaColumns._ID)
        val selection =
            "${MediaStore.MediaColumns.DISPLAY_NAME}=? AND ${MediaStore.MediaColumns.RELATIVE_PATH}=?"
        val selectionArgs = arrayOf(safeName, "$relativeDir/")

        contentResolver.query(
            collection,
            projection,
            selection,
            selectionArgs,
            null
        )?.use { cursor ->
            val idColumn = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns._ID)
            while (cursor.moveToNext()) {
                val uri = ContentUris.withAppendedId(collection, cursor.getLong(idColumn))
                contentResolver.delete(uri, null, null)
            }
        }
    }

    private fun isAppInForeground(targetPackage: String): Boolean {
        if (!hasUsagePermission()) return false
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return false

        val usm = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val now = System.currentTimeMillis()
        val stats = usm.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            now - 10_000L,
            now
        )
        if (stats.isNullOrEmpty()) return false

        val recentStat = stats.maxByOrNull { it.lastTimeUsed }
        return recentStat?.packageName == targetPackage
    }

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

    private fun openUsageSettings() {
        startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
    }

    private fun launchNhApp() {
        try {
            val launchIntent = packageManager.getLaunchIntentForPackage(NH_PACKAGE)
            if (launchIntent != null) {
                Log.d("NHAlimi", "NH파트너스 실행 요청 — source:앱 버튼")
                UserDiagnosticLogger.append(this, "NH파트너스 실행 요청 — source:앱 버튼")
                startActivity(launchIntent)
                UserDiagnosticLogger.append(this, "NH파트너스 실행 인텐트 전달 완료 — source:앱 버튼")
            } else {
                val marketIntent = Intent(
                    Intent.ACTION_VIEW,
                    android.net.Uri.parse("market://details?id=$NH_PACKAGE")
                )
                Log.w("NHAlimi", "NH파트너스 패키지 없음 — Play 스토어 이동 요청")
                UserDiagnosticLogger.append(this, "NH파트너스 패키지 없음 — Play 스토어 이동 요청")
                startActivity(marketIntent)
            }
        } catch (e: Exception) {
            Log.e("NHAlimi", "NH파트너스 실행 요청 실패 — source:앱 버튼, ${e.message}")
            UserDiagnosticLogger.append(
                this,
                "NH파트너스 실행 요청 실패 — source:앱 버튼, reason:${e.javaClass.simpleName}"
            )
        }
    }
}
