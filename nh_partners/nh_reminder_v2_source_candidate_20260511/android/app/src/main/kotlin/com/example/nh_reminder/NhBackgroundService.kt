package com.example.nh_reminder

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.os.BatteryManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.core.app.NotificationCompat
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import org.json.JSONObject
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin
import kotlin.math.sqrt

class NhBackgroundService : Service() {

    companion object {
        const val ACTION_START = "com.example.nh_reminder.action.START_BG_SERVICE"
        const val ACTION_STOP = "com.example.nh_reminder.action.STOP_BG_SERVICE"
        const val CHANNEL_ID = "nh_reminder_bg_service_v2"
        const val NOTIF_ID = 2001
        const val NATIVE_PREFS = "nh_native_monitor"
        const val KEY_NATIVE_PAUSED = "paused"
        const val KEY_NATIVE_LAT = "lat"
        const val KEY_NATIVE_LNG = "lng"
        const val KEY_NATIVE_RADIUS = "radius"
        const val KEY_NATIVE_NOTIF_ACTIVE = "notif_active"
        const val KEY_NATIVE_REPEAT_OWNER = "native_repeat_owner"
        const val KEY_NATIVE_CONFIG_GENERATION = "config_generation"
        const val DEFAULT_GEOFENCE_LAT = 37.566
        const val DEFAULT_GEOFENCE_LNG = 126.9673
        const val DEFAULT_GEOFENCE_RADIUS = 30.0
        const val MIN_GEOFENCE_RADIUS = 20.0
        const val MAX_GEOFENCE_RADIUS = 50.0
        private const val REMINDER_CHANNEL_ID = "nh_reminder_high_v2"
        private const val REMINDER_NOTIF_ID = 1001
        private const val FLUTTER_PREFS = "FlutterSharedPreferences"
        private const val MODE_FOREGROUND = "foreground"
        private const val MODE_BACKGROUND_RECENT = "background_recent"
        private const val MODE_SERVICE_ONLY = "service_only"
        private const val BATTERY_LOG_INTERVAL_MS = 15 * 60 * 1000L
        private const val APP_STATE_LOG_INTERVAL_MS = 10 * 60 * 1000L
        private const val NATIVE_LOCATION_TIMEOUT_MS = 12 * 1000L
        private const val NATIVE_POPUP_COOLDOWN_MS = 30 * 1000L
        private const val NATIVE_REMINDER_INTERVAL_MS = 30 * 1000L
        private const val NATIVE_DEFAULT_INTERVAL_MS = 120 * 1000L
        private const val NATIVE_NOTIF_ACTIVE_LOW_POWER_INTERVAL_MS = 300 * 1000L
        private const val NATIVE_PENDING_TRIGGER_INTERVAL_MS = 120 * 1000L
        private const val NATIVE_APPROACH_TRIGGER_INTERVAL_MS = 60 * 1000L
        private const val NATIVE_PROXIMITY_FRESH_RECHECK_INTERVAL_MS = 30 * 1000L
        private const val NATIVE_PROXIMITY_FRESH_COOLDOWN_MS = 3 * 60 * 1000L
        private const val NATIVE_PROXIMITY_FRESH_RECHECK_LIMIT = 2
        private const val NATIVE_PROXIMITY_FRESH_TRIGGER_METERS = 300.0
        private const val NATIVE_PROXIMITY_FRESH_CYCLE_MAX_MS = 2 * 60 * 1000L
        private const val NATIVE_PROXIMITY_FRESH_SHARED_RESULT_MAX_AGE_MS = 45 * 1000L
        private const val GEOFENCE_CONFIG_UPDATE_STALE_MS = 10 * 1000L
        private const val PROXIMITY_FRESH_CYCLE_LOCK_FILE =
            "nh_proximity_fresh_cycle.lock"
        private const val NATIVE_DISMISSED_OUTSIDE_INTERVAL_MS = 300 * 1000L
        private const val NATIVE_DISMISSED_STABLE_INTERVAL_MS = 300 * 1000L
        private const val NATIVE_FAR_METERS = 500.0
        private const val NATIVE_INITIAL_ALERT_BUFFER_METERS = 40.0
        private const val NATIVE_INITIAL_ALERT_MIN_METERS = 60.0
        private const val NATIVE_INITIAL_ALERT_MAX_METERS = 60.0
        private const val NATIVE_INITIAL_ALERT_MAX_ACCURACY_METERS = 120.0
        private const val NATIVE_STRONG_INITIAL_ALERT_DISTANCE_METERS = 50.0
        private const val NATIVE_STRONG_INITIAL_ALERT_ACCURACY_METERS = 80.0
        private const val NATIVE_APPROACH_PENDING_MIN_METERS = 60.0
        private const val NATIVE_APPROACH_PENDING_MAX_METERS = 80.0
        private const val NATIVE_APPROACH_PENDING_ACCURACY_METERS = 30.0
        private const val NATIVE_APPROACH_PENDING_VALID_MS = 5 * 60 * 1000L
        private const val NATIVE_APPROACH_PENDING_CLEAR_METERS = 120.0
        private const val NATIVE_NOTIF_ACTIVE_LAST_KNOWN_MAX_AGE_MS = 5 * 60 * 1000L
        private const val NATIVE_NOTIF_ACTIVE_LAST_KNOWN_MAX_ACCURACY_METERS = 150.0
        private const val NATIVE_INACTIVE_LAST_KNOWN_MAX_AGE_MS = 3 * 60 * 1000L
        private const val NATIVE_INACTIVE_LAST_KNOWN_MAX_ACCURACY_METERS = 150.0
        private const val NATIVE_DISMISSED_EXIT_THRESHOLD_METERS = 100.0
        private const val NATIVE_APPROACH_BAND_MAX_METERS = 80.0
        private const val NATIVE_DISMISSED_LAST_KNOWN_MAX_AGE_MS = 5 * 60 * 1000L
        private const val NATIVE_DISMISSED_LAST_KNOWN_MAX_ACCURACY_METERS = 120.0
        private const val BATTERY_PREFS = "nh_battery_usage"
        private const val KEY_ACTIVE = "active"
        private const val KEY_START_PERCENT = "start_percent"
        private const val KEY_START_ELAPSED_MS = "start_elapsed_ms"
        private const val KEY_HAD_CHARGING = "had_charging"
        private const val KEY_APPROACH_PENDING_ACTIVE = "flutter.approach_pending_active"
        private const val KEY_APPROACH_PENDING_AT_MS = "flutter.approach_pending_at_ms"
        private const val KEY_APPROACH_PENDING_DISTANCE = "flutter.approach_pending_distance_m"
        private const val KEY_APPROACH_PENDING_ACCURACY = "flutter.approach_pending_accuracy_m"
        private const val KEY_PROXIMITY_FRESH_LAST_REQUEST_MS =
            "flutter.proximity_fresh_last_request_ms"
        private const val KEY_PROXIMITY_FRESH_CYCLE_ACTIVE =
            "flutter.proximity_fresh_cycle_active"
        private const val KEY_PROXIMITY_FRESH_CYCLE_OWNER =
            "flutter.proximity_fresh_cycle_owner"
        private const val KEY_PROXIMITY_FRESH_CYCLE_ID =
            "flutter.proximity_fresh_cycle_id"
        private const val KEY_PROXIMITY_FRESH_CYCLE_STARTED_MS =
            "flutter.proximity_fresh_cycle_started_ms"
        private const val KEY_PROXIMITY_FRESH_CYCLE_FINISHED_MS =
            "flutter.proximity_fresh_cycle_finished_ms"
        private const val KEY_PROXIMITY_FRESH_RECHECKS_REMAINING =
            "flutter.proximity_fresh_rechecks_remaining"
        private const val KEY_PROXIMITY_FRESH_VERIFIED_AT_MS =
            "flutter.proximity_fresh_verified_at_ms"
        private const val KEY_PROXIMITY_FRESH_VERIFIED_DISTANCE_MM =
            "flutter.proximity_fresh_verified_distance_mm"
        private const val KEY_PROXIMITY_FRESH_VERIFIED_ACCURACY_MM =
            "flutter.proximity_fresh_verified_accuracy_mm"
        private const val KEY_PROXIMITY_FRESH_VERIFIED_SOURCE =
            "flutter.proximity_fresh_verified_source"
        private const val KEY_PROXIMITY_FRESH_VERIFIED_PAYLOAD =
            "flutter.proximity_fresh_verified_payload"
        private const val KEY_GEOFENCE_CONFIG_GENERATION =
            "flutter.geofence_config_generation"
        private const val KEY_GEOFENCE_CONFIG_UPDATE_STARTED_MS =
            "flutter.geofence_config_update_started_ms"
        private const val PROXIMITY_FRESH_OWNER_NATIVE = "native"

        fun hasLocationPermission(context: Context): Boolean {
            val fine = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)
            val coarse = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION)
            return fine == PackageManager.PERMISSION_GRANTED || coarse == PackageManager.PERMISSION_GRANTED
        }

        fun start(context: Context) {
            syncNativeConfigFromFlutter(context)
            if (!hasLocationPermission(context)) {
                Log.w("NHAlimi", "포그라운드 서비스 시작 생략 — 위치 권한 없음")
                return
            }

            val intent = Intent(context, NhBackgroundService::class.java).apply {
                action = ACTION_START
            }
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(intent)
                } else {
                    context.startService(intent)
                }
            } catch (e: Exception) {
                Log.e("NHAlimi", "포그라운드 서비스 시작 실패: ${e.message}")
            }
        }

        fun syncNativeConfigFromFlutter(context: Context) {
            val flutterPrefs = context.getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            val nativePrefs = context.getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
            recoverStaleFlutterGeofenceConfigUpdate(context, flutterPrefs)
            val lat = readFlutterDoublePreference(
                flutterPrefs,
                "flutter.geofence_lat",
                Double.fromBits(nativePrefs.getLong(KEY_NATIVE_LAT, DEFAULT_GEOFENCE_LAT.toBits()))
            )
            val lng = readFlutterDoublePreference(
                flutterPrefs,
                "flutter.geofence_lng",
                Double.fromBits(nativePrefs.getLong(KEY_NATIVE_LNG, DEFAULT_GEOFENCE_LNG.toBits()))
            )
            val radius = readFlutterDoublePreference(
                flutterPrefs,
                "flutter.geofence_radius",
                Double.fromBits(
                    nativePrefs.getLong(KEY_NATIVE_RADIUS, DEFAULT_GEOFENCE_RADIUS.toBits())
                )
            ).coerceIn(MIN_GEOFENCE_RADIUS, MAX_GEOFENCE_RADIUS)
            val configGeneration = readFlutterLongPreference(
                flutterPrefs,
                KEY_GEOFENCE_CONFIG_GENERATION,
                nativePrefs.getLong(KEY_NATIVE_CONFIG_GENERATION, 0L)
            )
            val paused = flutterPrefs.getBoolean(
                "flutter.is_paused",
                nativePrefs.getBoolean(KEY_NATIVE_PAUSED, false)
            )
            val notifActive = flutterPrefs.getBoolean(
                "flutter.notif_active",
                nativePrefs.getBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
            )
            val editor = nativePrefs.edit()
                .putBoolean(KEY_NATIVE_PAUSED, paused)
                .putLong(KEY_NATIVE_LAT, lat.toBits())
                .putLong(KEY_NATIVE_LNG, lng.toBits())
                .putLong(KEY_NATIVE_RADIUS, radius.toBits())
                .putBoolean(KEY_NATIVE_NOTIF_ACTIVE, notifActive)
                .putLong(KEY_NATIVE_CONFIG_GENERATION, configGeneration)
            if (!notifActive) {
                editor.putBoolean(KEY_NATIVE_REPEAT_OWNER, false)
            }
            editor.commit()
        }

        private fun recoverStaleFlutterGeofenceConfigUpdate(
            context: Context,
            flutterPrefs: android.content.SharedPreferences
        ) {
            val configGeneration = readFlutterLongPreference(
                flutterPrefs,
                KEY_GEOFENCE_CONFIG_GENERATION,
                0L
            )
            if (configGeneration % 2L == 0L) return
            val updateStartedMs = readFlutterLongPreference(
                flutterPrefs,
                KEY_GEOFENCE_CONFIG_UPDATE_STARTED_MS,
                0L
            )
            val nowMs = System.currentTimeMillis()
            if (updateStartedMs > 0L &&
                nowMs >= updateStartedMs &&
                nowMs - updateStartedMs < GEOFENCE_CONFIG_UPDATE_STALE_MS
            ) {
                return
            }
            try {
                File(context.filesDir, PROXIMITY_FRESH_CYCLE_LOCK_FILE).delete()
            } catch (_: Exception) {
            }
            val recovered = flutterPrefs.edit()
                .remove(KEY_PROXIMITY_FRESH_LAST_REQUEST_MS)
                .remove(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE)
                .remove(KEY_PROXIMITY_FRESH_CYCLE_OWNER)
                .remove(KEY_PROXIMITY_FRESH_CYCLE_ID)
                .remove(KEY_PROXIMITY_FRESH_CYCLE_STARTED_MS)
                .remove(KEY_PROXIMITY_FRESH_CYCLE_FINISHED_MS)
                .remove(KEY_PROXIMITY_FRESH_RECHECKS_REMAINING)
                .remove(KEY_PROXIMITY_FRESH_VERIFIED_AT_MS)
                .remove(KEY_PROXIMITY_FRESH_VERIFIED_DISTANCE_MM)
                .remove(KEY_PROXIMITY_FRESH_VERIFIED_ACCURACY_MM)
                .remove(KEY_PROXIMITY_FRESH_VERIFIED_SOURCE)
                .remove(KEY_PROXIMITY_FRESH_VERIFIED_PAYLOAD)
                .putLong(KEY_GEOFENCE_CONFIG_GENERATION, configGeneration + 1L)
                .remove(KEY_GEOFENCE_CONFIG_UPDATE_STARTED_MS)
                .commit()
            if (recovered) {
                Log.w(
                    "NHAlimi",
                    "Interrupted geofence config update recovered: " +
                            "$configGeneration->${configGeneration + 1L}"
                )
            }
        }

        private fun readFlutterDoublePreference(
            prefs: android.content.SharedPreferences,
            key: String,
            defaultValue: Double
        ): Double {
            return when (val value = prefs.all[key]) {
                is Number -> value.toDouble()
                is String -> Regex("""[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$""")
                    .find(value.trim())
                    ?.value
                    ?.toDoubleOrNull()
                    ?: defaultValue
                else -> defaultValue
            }
        }

        private fun readFlutterLongPreference(
            prefs: android.content.SharedPreferences,
            key: String,
            defaultValue: Long
        ): Long {
            return when (val value = prefs.all[key]) {
                is Number -> value.toLong()
                is String -> value.toLongOrNull() ?: defaultValue
                else -> defaultValue
            }
        }

        fun stop(context: Context) {
            context.getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_NATIVE_PAUSED, true)
                .putBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
                .putBoolean(KEY_NATIVE_REPEAT_OWNER, false)
                .apply()
            context.getSystemService(NotificationManager::class.java)?.cancel(NOTIF_ID)
            context.getSystemService(NotificationManager::class.java)?.cancel(REMINDER_NOTIF_ID)
            context.stopService(Intent(context, NhBackgroundService::class.java))
        }
    }

    private val handler = Handler(Looper.getMainLooper())
    private var nativeMonitoringActive = false
    private var nativeMonitorGeneration = 0L
    private var nativeCheckRunning = false
    private var nativeCheckCount = 0L
    private var nativeLocationRequestCount = 0L
    private var nativeLocationTimeoutCount = 0L
    private var nativeLastKnownUseCount = 0L
    private var nativeProximityFreshRequestCount = 0L
    private var nativePopupCount = 0L
    private var lastNativeZone = "unknown"
    private var lastNativePopupAtMs = 0L
    private var nativeReminderGeneration = 0L

    private val batteryLogger = object : Runnable {
        override fun run() {
            logBatterySnapshot("포그라운드 서비스 배터리 샘플")
            handler.postDelayed(this, BATTERY_LOG_INTERVAL_MS)
        }
    }
    private val appStateLogger = object : Runnable {
        override fun run() {
            appendRuntimeLog(buildExecutionStateLog("native_service_periodic"))
            handler.postDelayed(this, APP_STATE_LOG_INTERVAL_MS)
        }
    }
    private val nativeMonitor = object : Runnable {
        override fun run() {
            runNativeMonitorCheck(nativeMonitorGeneration)
        }
    }
    private val nativeReminder = object : Runnable {
        override fun run() {
            runNativeReminderTick(nativeReminderGeneration)
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.d("NHAlimi", "포그라운드 서비스 생성")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            removeForegroundServiceNotification()
            stopAppStateLogging("native_service_stop")
            logBatterySnapshot("포그라운드 서비스 종료 전 배터리")
            finishBatteryLogging()
            stopNativeMonitoring()
            clearNativeProximityFreshStateOnStop()
            stopNativeReminderRepeat(clearActive = false)
            stopSelf()
            Log.d("NHAlimi", "포그라운드 서비스 중지 요청")
            return START_NOT_STICKY
        }

        if (isUserPaused()) {
            appendRuntimeLog("[NH알리미] 포그라운드 서비스 시작 생략 — 사용자 모니터링 OFF 상태")
            stopServiceNow()
            return START_NOT_STICKY
        }

        if (!NativeServiceScheduler.isMonitoringHours()) {
            appendRuntimeLog("[NH알리미] 포그라운드 서비스 시작 생략 — 모니터링 시간 외")
            stopServiceNow()
            return START_NOT_STICKY
        }

        if (!promoteToForeground()) {
            return START_NOT_STICKY
        }
        startBatteryLogging()
        startAppStateLogging()
        startNativeMonitoring(initialDelayMs = 3_000L)
        recoverNativeReminderRepeatIfNeeded()
        Log.d("NHAlimi", "포그라운드 서비스 시작/복구")
        return START_STICKY
    }

    private fun promoteToForeground(): Boolean {
        if (!hasLocationPermission()) {
            appendRuntimeLog("[NH알리미] 포그라운드 서비스 시작 중단 — 위치 권한 없음")
            stopServiceNow()
            return false
        }

        createServiceChannel()
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                startForeground(NOTIF_ID, buildNotification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
            } else {
                startForeground(NOTIF_ID, buildNotification())
            }
            true
        } catch (e: Exception) {
            appendRuntimeLog("[NH알리미] 포그라운드 서비스 승격 실패 — ${e.javaClass.simpleName}: ${e.message}")
            stopServiceNow()
            false
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun stopServiceNow() {
        removeForegroundServiceNotification()
        stopAppStateLogging("native_service_stop_now")
        stopBatteryLogging()
        finishBatteryLogging()
        stopNativeMonitoring()
        clearNativeProximityFreshStateOnStop()
        stopNativeReminderRepeat(clearActive = false)
        stopSelf()
    }

    override fun onDestroy() {
        logBatterySnapshot("포그라운드 서비스 종료")
        removeForegroundServiceNotification()
        stopAppStateLogging("native_service_destroy")
        finishBatteryLogging()
        stopNativeMonitoring()
        clearNativeProximityFreshStateOnStop()
        stopNativeReminderRepeat(clearActive = false)
        super.onDestroy()
        Log.d("NHAlimi", "포그라운드 서비스 종료")
    }

    private fun removeForegroundServiceNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        getSystemService(NotificationManager::class.java)?.cancel(NOTIF_ID)
    }

    private fun createServiceChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "NH알리미 실행 중",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "출퇴근 위치 모니터링 중"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java)?.createNotificationChannel(channel)
        }
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

    private fun isUserPaused(): Boolean {
        val flutterPrefs = getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
        return flutterPrefs.getBoolean("flutter.user_paused", false)
    }

    private fun buildNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("NH알리미 실행 중")
            .setContentText("출퇴근 위치 모니터링 중...")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }

    private fun startBatteryLogging() {
        handler.removeCallbacks(batteryLogger)
        ensureBatterySessionStarted()
        logBatterySnapshot("포그라운드 서비스 배터리 시작/복구")
        handler.postDelayed(batteryLogger, BATTERY_LOG_INTERVAL_MS)
    }

    private fun stopBatteryLogging() {
        handler.removeCallbacks(batteryLogger)
    }

    private fun startAppStateLogging() {
        handler.removeCallbacks(appStateLogger)
        appendRuntimeLog(buildExecutionStateLog("native_service_start"))
        handler.postDelayed(appStateLogger, APP_STATE_LOG_INTERVAL_MS)
    }

    private fun stopAppStateLogging(reason: String) {
        handler.removeCallbacks(appStateLogger)
        appendRuntimeLog(buildExecutionStateLog(reason))
    }

    private fun buildExecutionStateLog(reason: String): String {
        val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val nativePrefs = getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
        val activityVisible = flutterPrefs.getBoolean("flutter.app_activity_visible", false)
        val activityAlive = flutterPrefs.getBoolean("flutter.app_activity_alive", false)
        val lifecycleState = flutterPrefs.getString("flutter.app_lifecycle_state", "unknown")
        val flutterMode = flutterPrefs.getString("flutter.app_execution_mode", "unknown")
        val mode = when {
            activityVisible -> MODE_FOREGROUND
            activityAlive -> MODE_BACKGROUND_RECENT
            else -> MODE_SERVICE_ONLY
        }
        val notifActive = nativePrefs.getBoolean(KEY_NATIVE_NOTIF_ACTIVE, false) ||
                flutterPrefs.getBoolean("flutter.notif_active", false)
        val paused = nativePrefs.getBoolean(KEY_NATIVE_PAUSED, false) ||
                flutterPrefs.getBoolean("flutter.is_paused", false) ||
                flutterPrefs.getBoolean("flutter.user_paused", false)

        return "[NH알리미] 앱 실행상태 스냅샷 — mode:$mode, source:native_service, " +
                "flutterMode:$flutterMode, lifecycle:$lifecycleState, " +
                "activityVisible:$activityVisible, activityAlive:$activityAlive, " +
                "serviceActive:$nativeMonitoringActive, notifActive:$notifActive, " +
                "paused:$paused, interval:10분, reason:$reason"
    }

    private fun finishBatteryLogging() {
        stopBatteryLogging()
        getSharedPreferences(BATTERY_PREFS, Context.MODE_PRIVATE)
            .edit()
            .clear()
            .apply()
    }

    private fun ensureBatterySessionStarted() {
        val prefs = getSharedPreferences(BATTERY_PREFS, Context.MODE_PRIVATE)
        if (prefs.getBoolean(KEY_ACTIVE, false)) return

        val battery = readBatteryState()
        prefs.edit()
            .putBoolean(KEY_ACTIVE, true)
            .putInt(KEY_START_PERCENT, battery.percent)
            .putLong(KEY_START_ELAPSED_MS, SystemClock.elapsedRealtime())
            .putBoolean(KEY_HAD_CHARGING, battery.charging)
            .apply()

        appendRuntimeLog(
            "[NH알리미] 배터리 사용량 측정 시작 — 시작:${battery.percent}%, " +
                    "charging:${battery.charging}, plugged:${battery.pluggedText}"
        )
    }

    private fun logBatterySnapshot(label: String) {
        try {
            val battery = readBatteryState()
            val prefs = getSharedPreferences(BATTERY_PREFS, Context.MODE_PRIVATE)
            if (battery.charging) {
                prefs.edit().putBoolean(KEY_HAD_CHARGING, true).apply()
            }
            val usageSummary = buildBatteryUsageSummary(battery)

            appendRuntimeLog(
                "[NH알리미] $label — battery:${battery.percent}%, " +
                        "charging:${battery.charging}, plugged:${battery.pluggedText}, $usageSummary"
            )
        } catch (e: Exception) {
            Log.e("NHAlimi", "배터리 로그 실패: ${e.message}")
        }
    }

    private data class BatteryState(
        val percent: Int,
        val charging: Boolean,
        val pluggedText: String
    )

    private fun readBatteryState(): BatteryState {
        val batteryIntent = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = batteryIntent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryIntent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        val percent = if (level >= 0 && scale > 0) level * 100 / scale else -1
        val status = batteryIntent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val plugged = batteryIntent?.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0) ?: 0
        val charging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                status == BatteryManager.BATTERY_STATUS_FULL
        val pluggedText = when (plugged) {
            BatteryManager.BATTERY_PLUGGED_AC -> "AC"
            BatteryManager.BATTERY_PLUGGED_USB -> "USB"
            BatteryManager.BATTERY_PLUGGED_WIRELESS -> "WIRELESS"
            0 -> "NONE"
            else -> "UNKNOWN"
        }
        return BatteryState(percent, charging, pluggedText)
    }

    private fun buildBatteryUsageSummary(current: BatteryState): String {
        val prefs = getSharedPreferences(BATTERY_PREFS, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(KEY_ACTIVE, false)) {
            return "사용량:측정 세션 없음"
        }

        val startPercent = prefs.getInt(KEY_START_PERCENT, current.percent)
        val startElapsedMs = prefs.getLong(KEY_START_ELAPSED_MS, SystemClock.elapsedRealtime())
        val elapsedMs = (SystemClock.elapsedRealtime() - startElapsedMs).coerceAtLeast(0L)
        val usedPercent = if (startPercent >= 0 && current.percent >= 0) {
            (startPercent - current.percent).coerceAtLeast(0)
        } else {
            -1
        }
        val hadCharging = prefs.getBoolean(KEY_HAD_CHARGING, false) || current.charging
        val reliability = if (hadCharging) "충전 포함, 참고값" else "비충전 기준"
        val usedText = if (usedPercent >= 0) {
            "총 배터리 약 ${usedPercent}% 사용"
        } else {
            "사용량 계산 불가"
        }

        return "사용량:$usedText, 시작:${startPercent}%, 현재:${current.percent}%, " +
                "경과:${formatElapsed(elapsedMs)}, 기준:$reliability, " +
                "네이티브감시:위치체크 ${nativeCheckCount}회, 위치요청 ${nativeLocationRequestCount}회, " +
                "timeout ${nativeLocationTimeoutCount}회, lastKnown ${nativeLastKnownUseCount}회, " +
                "근접정밀 ${nativeProximityFreshRequestCount}회, " +
                "보조팝업 ${nativePopupCount}회"
    }

    private fun formatElapsed(elapsedMs: Long): String {
        val totalMinutes = elapsedMs / 60000L
        val hours = totalMinutes / 60L
        val minutes = totalMinutes % 60L
        return if (hours > 0) {
            "${hours}시간 ${minutes}분"
        } else {
            "${minutes}분"
        }
    }

    private fun appendRuntimeLog(message: String) {
        val timestamp = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS", Locale.KOREA)
            .format(Date())
        val line = "[$timestamp] $message\n"

        try {
            val logDir = getExternalFilesDir(null) ?: filesDir
            if (!logDir.exists()) logDir.mkdirs()
            File(logDir, "nh_reminder_runtime.txt").appendText(line)
        } catch (e: Exception) {
            try {
                File(filesDir, "nh_reminder_runtime.txt").appendText(line)
            } catch (ignored: Exception) {
                Log.e("NHAlimi", "파일 로그 실패: ${e.message}")
            }
        }

        appendUserDiagnosticLog(timestamp, message)
    }

    private fun appendUserDiagnosticLog(timestamp: String, message: String) {
        if (!isUserDiagnosticMessage(message)) return

        val sanitized = sanitizeUserDiagnosticMessage(message)
        val line = "[$timestamp] $sanitized\n"

        try {
            val logDir = getExternalFilesDir(null) ?: filesDir
            if (!logDir.exists()) logDir.mkdirs()
            val file = File(logDir, "nh_alimi_user_diagnostic.txt")
            pruneUserDiagnosticLog(file)
            file.appendText(line)
        } catch (e: Exception) {
            try {
                val file = File(filesDir, "nh_alimi_user_diagnostic.txt")
                pruneUserDiagnosticLog(file)
                file.appendText(line)
            } catch (ignored: Exception) {
                Log.e("NHAlimi", "사용자 로그 실패: ${e.message}")
            }
        }
    }

    private fun isUserDiagnosticMessage(message: String): Boolean {
        val excludeKeywords = listOf(
            "파일 로그 시작",
            "UsageStats",
            "설정 화면 오류",
            "DevTools",
            "다음 백그라운드 감시 예약",
            "반복 알림 발송",
            "팝업 알림 발송 완료",
            "범위 밖, ENTER 대기",
            "범위 안 보류",
            "범위 안이지만 알림 활성 상태라 새 알림 시작 생략",
            "범위 밖 감지지만 초기 진입 알림 유지",
            "경계 흔들림",
            "저전력 위치"
        )
        if (excludeKeywords.any { message.contains(it) }) return false
        if (
            message.contains("네이티브 보조 감시 — 범위 ") ||
            message.contains("네이티브 보조 감시 — 경계/보류")
        ) {
            return false
        }

        if (message.contains("사용자 진단 요약")) return true

        val importantKeywords = listOf(
            "06:00",
            "19:00",
            "지오펜스",
            "ENTER",
            "EXIT",
            "DWELL",
            "백그라운드 감시 시작",
            "백그라운드 감시 중지",
            "백그라운드 감시 리프레시",
            "백그라운드 감시 실행 지연",
            "백그라운드 감시 위치 확인 실패",
            "모니터링 소프트 리셋",
            "반복 알림",
            "네이티브 반복 알림",
            "알림 시작",
            "알림 중지",
            "위치보정",
            "위치 확인 실패",
            "위치 권한 없음",
            "저전력",
            "위치감시 절전",
            "절전",
            "lastKnown",
            "출퇴근 확인",
            "출퇴근 기록",
            "NH파트너스",
            "배터리",
            "포그라운드 서비스",
            "네이티브 보조 감시 위치 확인 실패",
            "네이티브 보조 감시 종료",
            "네이티브 보조 감시 — 위치 권한 없음",
            "네이티브 보조 팝업"
        )

        return importantKeywords.any { message.contains(it) }
    }

    private fun sanitizeUserDiagnosticMessage(message: String): String {
        return message
            .replace(Regex("""lat[:=][^,\s]+,\s*lng[:=][^,\s]+"""), "위치:마스킹")
            .replace(Regex("""/storage/[^\s)]+"""), "경로:마스킹")
            .replace(Regex("""[A-Z]:\\[^\s)]+"""), "경로:마스킹")
    }

    private fun pruneUserDiagnosticLog(file: File) {
        if (!file.exists()) return

        val formatter = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS", Locale.KOREA)
        val cutoff = formatter.format(Date(System.currentTimeMillis() - 7L * 24L * 60L * 60L * 1000L))
        val original = file.readLines()
        val kept = original.filter { line ->
            val timestamp = line.substringAfter("[", "").substringBefore("]", "")
            timestamp.isEmpty() || timestamp >= cutoff
        }.let { lines ->
            if (lines.size > 2000) lines.takeLast(2000) else lines
        }

        if (kept.size != original.size) {
            file.writeText(if (kept.isEmpty()) "" else kept.joinToString("\n") + "\n")
        }
    }

    private data class NativeConfig(
        val paused: Boolean,
        val lat: Double,
        val lng: Double,
        val radius: Double,
        val notifActive: Boolean,
        val dismissedUntilExit: Boolean,
        val executionMode: String,
        val configGeneration: Long
    )

    private data class NativeJudgment(
        val zone: String,
        val distance: Double,
        val accuracy: Double,
        val exitThreshold: Double,
        val initialAlertThreshold: Double,
        val reliableInside: Boolean,
        val initialAlertCandidate: Boolean
    ) {
        val isOutside: Boolean
            get() = zone == "outside" || zone == "farOutside"
        val strongInitialAlertCandidate: Boolean
            get() = distance <= NATIVE_STRONG_INITIAL_ALERT_DISTANCE_METERS &&
                    accuracy <= NATIVE_STRONG_INITIAL_ALERT_ACCURACY_METERS
        val approachPendingSeed: Boolean
            get() = distance >= NATIVE_APPROACH_PENDING_MIN_METERS &&
                    distance <= NATIVE_APPROACH_PENDING_MAX_METERS &&
                    accuracy <= NATIVE_APPROACH_PENDING_ACCURACY_METERS

        fun decisionText(radius: Double): String {
            val centerThreshold = max(10.0, radius * 0.5)
            val accuracyThreshold = max(radius, 35.0)
            val result = if (reliableInside) "통과" else "보류"
            return "거리 ${distance.toInt()}m / 반경 ${radius.toInt()}m, " +
                    "정확도 ${accuracy.toInt()}m, 통과기준: 중심권 ${centerThreshold.toInt()}m 이내 " +
                    "또는 정확도 ${accuracyThreshold.toInt()}m 이하, " +
                    "이탈기준: ${exitThreshold.toInt()}m 초과, 판정:$result"
        }

        fun initialAlertText(): String {
            return "거리 ${distance.toInt()}m / 초기알림기준 ${initialAlertThreshold.toInt()}m, " +
                    "정확도 ${accuracy.toInt()}m / 기준 ${NATIVE_INITIAL_ALERT_MAX_ACCURACY_METERS.toInt()}m"
        }
    }

    private enum class NativeProximityFreshAction {
        NONE,
        START_CYCLE,
        RECHECK,
        CONSUME_SHARED
    }

    private fun startNativeMonitoring(initialDelayMs: Long) {
        nativeMonitoringActive = true
        nativeMonitorGeneration += 1
        nativeCheckRunning = false
        handler.removeCallbacks(nativeMonitor)
        handler.postDelayed(nativeMonitor, initialDelayMs)
    }

    private fun stopNativeMonitoring() {
        nativeMonitoringActive = false
        nativeMonitorGeneration += 1
        handler.removeCallbacks(nativeMonitor)
        nativeCheckRunning = false
    }

    private fun scheduleNativeMonitoring(delayMs: Long) {
        if (!nativeMonitoringActive) return
        handler.removeCallbacks(nativeMonitor)
        handler.postDelayed(nativeMonitor, delayMs)
    }

    private fun runNativeMonitorCheck(generation: Long) {
        if (!isCurrentNativeMonitor(generation)) return

        if (nativeCheckRunning) {
            return
        }

        val config = readNativeConfig()
        if (!isCurrentNativeConfig(config)) {
            syncNativeConfigFromFlutter(this)
            appendRuntimeLog("[NH알리미] 네이티브 설정 snapshot 복구 — 3초 후 재확인")
            scheduleNativeMonitoring(3_000L)
            return
        }
        if (config.paused) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 감시 종료 — paused=true")
            stopServiceNow()
            return
        }

        if (!NativeServiceScheduler.isMonitoringHours()) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 감시 종료 — 모니터링 시간 외")
            stopServiceNow()
            return
        }

        if (!hasLocationPermission()) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 감시 — 위치 권한 없음")
            scheduleNativeMonitoring(NATIVE_DEFAULT_INTERVAL_MS)
            return
        }

        nativeCheckRunning = true
        nativeCheckCount += 1
        requestNativeLocation(config, generation)
    }

    private fun isCurrentNativeMonitor(generation: Long): Boolean {
        return nativeMonitoringActive && generation == nativeMonitorGeneration
    }

    private fun readNativeConfig(): NativeConfig {
        val prefs = getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
        val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val nativeNotifActive = prefs.getBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
        val flutterNotifActive = flutterPrefs.getBoolean("flutter.notif_active", false)
        val activityVisible = flutterPrefs.getBoolean("flutter.app_activity_visible", false)
        val activityAlive = flutterPrefs.getBoolean("flutter.app_activity_alive", false)
        val executionMode = when {
            activityVisible -> MODE_FOREGROUND
            activityAlive -> MODE_BACKGROUND_RECENT
            else -> MODE_SERVICE_ONLY
        }
        return NativeConfig(
            paused = prefs.getBoolean(KEY_NATIVE_PAUSED, false),
            lat = Double.fromBits(prefs.getLong(KEY_NATIVE_LAT, DEFAULT_GEOFENCE_LAT.toBits())),
            lng = Double.fromBits(prefs.getLong(KEY_NATIVE_LNG, DEFAULT_GEOFENCE_LNG.toBits())),
            radius = Double.fromBits(
                prefs.getLong(KEY_NATIVE_RADIUS, DEFAULT_GEOFENCE_RADIUS.toBits())
            ).coerceIn(MIN_GEOFENCE_RADIUS, MAX_GEOFENCE_RADIUS),
            notifActive = nativeNotifActive || flutterNotifActive,
            dismissedUntilExit = flutterPrefs.getBoolean("flutter.dismissed_until_exit", false),
            executionMode = executionMode,
            configGeneration = prefs.getLong(KEY_NATIVE_CONFIG_GENERATION, 0L)
        )
    }

    private fun isCurrentNativeConfig(config: NativeConfig): Boolean {
        val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val nativePrefs = getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
        val flutterGeneration = getLongPreference(
            flutterPrefs,
            KEY_GEOFENCE_CONFIG_GENERATION,
            0L
        )
        val nativeGeneration = nativePrefs.getLong(KEY_NATIVE_CONFIG_GENERATION, 0L)
        return config.configGeneration % 2L == 0L &&
                config.configGeneration == flutterGeneration &&
                config.configGeneration == nativeGeneration
    }

    private fun hasLocationPermission(): Boolean {
        return hasLocationPermission(this)
    }

    @Suppress("MissingPermission")
    private fun requestNativeLocation(config: NativeConfig, generation: Long) {
        val locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val bestLastKnown = bestLastKnownLocation(locationManager)
        when (resolveNativeProximityFreshAction(config, bestLastKnown)) {
            NativeProximityFreshAction.START_CYCLE -> {
                startNativeProximityFreshRequest(
                    locationManager,
                    config,
                    generation,
                    bestLastKnown,
                    "startCycle"
                )
                return
            }
            NativeProximityFreshAction.RECHECK -> {
                startNativeProximityFreshRequest(
                    locationManager,
                    config,
                    generation,
                    bestLastKnown,
                    "recheck"
                )
                return
            }
            NativeProximityFreshAction.CONSUME_SHARED -> {
                sharedProximityFreshLocation(config, bestLastKnown)?.let {
                    finishNativeLocationCheck(
                        config,
                        it,
                        timedOut = false,
                        note = "shared 근접 검증",
                        generation = generation
                    )
                    return
                }
            }
            NativeProximityFreshAction.NONE -> Unit
        }
        sharedProximityFreshLocation(config, bestLastKnown)?.let {
            finishNativeLocationCheck(
                config,
                it,
                timedOut = false,
                note = "shared 근접 검증",
                generation = generation
            )
            return
        }
        if (shouldUseLastKnownForLocationLowPower(config, bestLastKnown)) {
            finishNativeLocationCheck(
                config,
                bestLastKnown,
                timedOut = false,
                note = if (config.notifActive) {
                    "lastKnown 알림활성 절전"
                } else if (isInactiveLowPower(config)) {
                    "lastKnown 화면꺼짐 저전력"
                } else {
                    "lastKnown 저전력"
                },
                generation = generation
            )
            return
        }
        val provider = selectProvider(locationManager)

        if (provider == null) {
            finishNativeLocationCheck(
                config,
                bestLastKnown,
                timedOut = true,
                note = "provider 없음",
                generation = generation
            )
            return
        }

        requestNativeProviderLocation(
            locationManager = locationManager,
            config = config,
            generation = generation,
            fallbackLocation = bestLastKnown,
            provider = provider,
            note = provider,
            allowNetworkFallback = false,
            allowProximityUpgrade = true
        )
    }

    @Suppress("MissingPermission")
    private fun requestNativeProviderLocation(
        locationManager: LocationManager,
        config: NativeConfig,
        generation: Long,
        fallbackLocation: Location?,
        provider: String,
        note: String,
        allowNetworkFallback: Boolean,
        allowProximityUpgrade: Boolean
    ) {
        if (!locationManager.isProviderEnabled(provider)) {
            if (allowNetworkFallback) {
                requestNativeNetworkFallback(
                    locationManager,
                    config,
                    generation,
                    fallbackLocation,
                    "provider 비활성:$provider"
                )
            } else {
                finishNativeLocationCheck(
                    config,
                    fallbackLocation,
                    timedOut = true,
                    note = "provider 비활성:$provider",
                    generation = generation
                )
            }
            return
        }

        nativeLocationRequestCount += 1
        var completed = false
        lateinit var listener: LocationListener
        val timeout = Runnable {
            if (completed) return@Runnable
            completed = true
            try {
                locationManager.removeUpdates(listener)
            } catch (_: Exception) {
            }
            if (!isCurrentNativeMonitor(generation)) return@Runnable
            if (allowNetworkFallback) {
                nativeLocationTimeoutCount += 1
                requestNativeNetworkFallback(
                    locationManager,
                    config,
                    generation,
                    fallbackLocation,
                    "timeout:$provider"
                )
            } else {
                finishNativeLocationCheck(
                    config,
                    fallbackLocation,
                    timedOut = true,
                    note = "위치 요청 timeout:$provider",
                    generation = generation
                )
            }
        }

        listener = object : LocationListener {
            override fun onLocationChanged(location: Location) {
                if (completed) return
                completed = true
                handler.removeCallbacks(timeout)
                try {
                    locationManager.removeUpdates(this)
                } catch (_: Exception) {
                }
                if (!isCurrentNativeMonitor(generation)) return
                if (allowProximityUpgrade) {
                    when (resolveNativeProximityFreshAction(config, location)) {
                        NativeProximityFreshAction.START_CYCLE -> {
                            startNativeProximityFreshRequest(
                                locationManager,
                                config,
                                generation,
                                location,
                                "startCycle"
                            )
                            return
                        }
                        NativeProximityFreshAction.RECHECK -> {
                            startNativeProximityFreshRequest(
                                locationManager,
                                config,
                                generation,
                                location,
                                "recheck"
                            )
                            return
                        }
                        NativeProximityFreshAction.CONSUME_SHARED -> {
                            sharedProximityFreshLocation(config, location)?.let {
                                finishNativeLocationCheck(
                                    config,
                                    it,
                                    timedOut = false,
                                    note = "shared 근접 검증",
                                    generation = generation
                                )
                                return
                            }
                        }
                        NativeProximityFreshAction.NONE -> Unit
                    }
                }
                finishNativeLocationCheck(
                    config,
                    location,
                    timedOut = false,
                    note = note,
                    generation = generation
                )
            }

            @Deprecated("Deprecated in Java")
            override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {
            }

            override fun onProviderEnabled(provider: String) {
            }

            override fun onProviderDisabled(provider: String) {
            }
        }

        try {
            locationManager.requestSingleUpdate(provider, listener, Looper.getMainLooper())
            handler.postDelayed(timeout, NATIVE_LOCATION_TIMEOUT_MS)
        } catch (e: Exception) {
            handler.removeCallbacks(timeout)
            if (allowNetworkFallback) {
                requestNativeNetworkFallback(
                    locationManager,
                    config,
                    generation,
                    fallbackLocation,
                    "요청 실패:$provider:${e.message}"
                )
            } else {
                finishNativeLocationCheck(
                    config,
                    fallbackLocation,
                    timedOut = true,
                    note = "위치 요청 실패:$provider:${e.message}",
                    generation = generation
                )
            }
        }
    }

    private fun startNativeProximityFreshRequest(
        locationManager: LocationManager,
        config: NativeConfig,
        generation: Long,
        fallbackLocation: Location?,
        action: String
    ) {
        if (!ownsNativeProximityFreshCycle()) {
            appendRuntimeLog("[NH알리미] 근접 정밀 측정 양보 — owner 변경 감지, 공유값 재사용")
            finishNativeLocationCheck(
                config,
                sharedProximityFreshLocation(config, fallbackLocation) ?: fallbackLocation,
                timedOut = false,
                note = "근접 정밀 owner 양보",
                generation = generation
            )
            return
        }
        markNativeProximityFreshRequested(config, fallbackLocation, action)
        requestNativeProviderLocation(
            locationManager = locationManager,
            config = config,
            generation = generation,
            fallbackLocation = fallbackLocation,
            provider = LocationManager.GPS_PROVIDER,
            note = "gps 근접 정밀",
            allowNetworkFallback = true,
            allowProximityUpgrade = false
        )
    }

    private fun requestNativeNetworkFallback(
        locationManager: LocationManager,
        config: NativeConfig,
        generation: Long,
        fallbackLocation: Location?,
        reason: String
    ) {
        val provider = selectProvider(locationManager)
        if (provider == null) {
            appendRuntimeLog("[NH알리미] 근접 정밀 측정 fallback 실패 — $reason, provider 없음")
            finishNativeLocationCheck(
                config,
                fallbackLocation,
                timedOut = true,
                note = "근접 정밀 fallback 실패:$reason",
                generation = generation
            )
            return
        }

        appendRuntimeLog(
            "[NH알리미] 근접 정밀 측정 fallback — $reason, provider:$provider"
        )
        requestNativeProviderLocation(
            locationManager = locationManager,
            config = config,
            generation = generation,
            fallbackLocation = fallbackLocation,
            provider = provider,
            note = "$provider 근접 fallback",
            allowNetworkFallback = false,
            allowProximityUpgrade = false
        )
    }

    @Suppress("MissingPermission")
    private fun bestLastKnownLocation(locationManager: LocationManager): Location? {
        if (!hasLocationPermission()) return null

        val providers = listOf(
            LocationManager.GPS_PROVIDER,
            LocationManager.NETWORK_PROVIDER,
            LocationManager.PASSIVE_PROVIDER
        )
        return providers.mapNotNull { provider ->
            try {
                locationManager.getLastKnownLocation(provider)
            } catch (_: Exception) {
                null
            }
        }.minWithOrNull(
            compareBy<Location> { locationAgeMs(it) }
                .thenBy { if (it.hasAccuracy()) it.accuracy else 9999f }
        )
    }

    private fun selectProvider(locationManager: LocationManager): String? {
        return when {
            locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER) -> LocationManager.NETWORK_PROVIDER
            locationManager.isProviderEnabled(LocationManager.PASSIVE_PROVIDER) -> LocationManager.PASSIVE_PROVIDER
            else -> null
        }
    }

    private fun resolveNativeProximityFreshAction(
        config: NativeConfig,
        location: Location?
    ): NativeProximityFreshAction {
        if (!isCurrentNativeConfig(config)) {
            return NativeProximityFreshAction.NONE
        }
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val nowMs = System.currentTimeMillis()
        expireNativeProximityFreshCycleIfNeeded(prefs, nowMs)

        if (config.notifActive ||
            config.dismissedUntilExit ||
            !isInactiveLowPower(config)
        ) {
            if (prefs.getBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, false)) {
                finishNativeProximityFreshCycle(prefs, nowMs)
            }
            return NativeProximityFreshAction.NONE
        }

        if (prefs.getBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, false)) {
            if (!isWithinNativeProximityFreshTrigger(config, location)) {
                if (isUsableNativeProximityFreshTriggerLocation(location)) {
                    finishNativeProximityFreshCycle(prefs, nowMs)
                }
                return NativeProximityFreshAction.NONE
            }
            val owner = prefs.getString(KEY_PROXIMITY_FRESH_CYCLE_OWNER, null)
            val remaining = getLongPreference(
                prefs,
                KEY_PROXIMITY_FRESH_RECHECKS_REMAINING,
                0L
            )
            if (owner == PROXIMITY_FRESH_OWNER_NATIVE && remaining > 0) {
                prefs.edit()
                    .putLong(KEY_PROXIMITY_FRESH_RECHECKS_REMAINING, remaining - 1L)
                    .commit()
                return NativeProximityFreshAction.RECHECK
            }
            return if (hasRecentSharedProximityFreshResult(prefs, nowMs)) {
                NativeProximityFreshAction.CONSUME_SHARED
            } else {
                NativeProximityFreshAction.NONE
            }
        }

        if (!isWithinNativeProximityFreshTrigger(config, location)) {
            return NativeProximityFreshAction.NONE
        }
        if (hasRecentSharedProximityFreshResult(prefs, nowMs)) {
            return NativeProximityFreshAction.CONSUME_SHARED
        }
        val lastFinishedMs = prefs.getLong(KEY_PROXIMITY_FRESH_CYCLE_FINISHED_MS, 0L)
        if (lastFinishedMs > 0L && nowMs - lastFinishedMs < NATIVE_PROXIMITY_FRESH_COOLDOWN_MS) {
            return NativeProximityFreshAction.NONE
        }

        val cycleId = nowMs
        if (!tryAcquireNativeProximityFreshCycleLock(cycleId)) {
            return if (hasRecentSharedProximityFreshResult(prefs, nowMs)) {
                NativeProximityFreshAction.CONSUME_SHARED
            } else {
                NativeProximityFreshAction.NONE
            }
        }
        val committed = prefs.edit()
            .putBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, true)
            .putString(KEY_PROXIMITY_FRESH_CYCLE_OWNER, PROXIMITY_FRESH_OWNER_NATIVE)
            .putLong(KEY_PROXIMITY_FRESH_CYCLE_ID, cycleId)
            .putLong(KEY_PROXIMITY_FRESH_CYCLE_STARTED_MS, nowMs)
            .putLong(
                KEY_PROXIMITY_FRESH_RECHECKS_REMAINING,
                NATIVE_PROXIMITY_FRESH_RECHECK_LIMIT.toLong()
            )
            .commit()
        if (!committed || !ownsNativeProximityFreshCycle(cycleId)
        ) {
            clearNativeProximityFreshCycleLock(
                expectedOwner = PROXIMITY_FRESH_OWNER_NATIVE,
                expectedCycleId = cycleId
            )
            return NativeProximityFreshAction.NONE
        }
        appendRuntimeLog(
            "[NH알리미] 근접 정밀 검증 사이클 시작 — " +
                    "owner:$PROXIMITY_FRESH_OWNER_NATIVE, id:$cycleId, " +
                    "재확인:${NATIVE_PROXIMITY_FRESH_RECHECK_LIMIT}회"
        )
        return NativeProximityFreshAction.START_CYCLE
    }

    private fun ownsNativeProximityFreshCycle(expectedCycleId: Long? = null): Boolean {
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val cycleId = prefs.getLong(KEY_PROXIMITY_FRESH_CYCLE_ID, 0L)
        return prefs.getBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, false) &&
                prefs.getString(KEY_PROXIMITY_FRESH_CYCLE_OWNER, null) ==
                PROXIMITY_FRESH_OWNER_NATIVE &&
                cycleId > 0L &&
                (expectedCycleId == null || cycleId == expectedCycleId) &&
                ownsNativeProximityFreshCycleLock(cycleId)
    }

    private fun getLongPreference(
        prefs: android.content.SharedPreferences,
        key: String,
        defaultValue: Long
    ): Long {
        return when (val value = prefs.all[key]) {
            is Long -> value
            is Int -> value.toLong()
            else -> defaultValue
        }
    }

    private fun nativeProximityFreshCycleLockFile(): File =
        File(filesDir, PROXIMITY_FRESH_CYCLE_LOCK_FILE)

    private fun nativeProximityFreshCycleLockToken(owner: String, cycleId: Long): String =
        "$owner:$cycleId"

    private fun tryAcquireNativeProximityFreshCycleLock(cycleId: Long): Boolean {
        val file = nativeProximityFreshCycleLockFile()
        clearExpiredNativeProximityFreshCycleLock(file)
        return try {
            if (!file.createNewFile()) return false
            file.writeText(nativeProximityFreshCycleLockToken(PROXIMITY_FRESH_OWNER_NATIVE, cycleId))
            true
        } catch (e: Exception) {
            file.delete()
            appendRuntimeLog("[NH알리미] 근접 정밀 lock 확보 실패 — error:$e")
            false
        }
    }

    private fun ownsNativeProximityFreshCycleLock(cycleId: Long): Boolean {
        val file = nativeProximityFreshCycleLockFile()
        return try {
            file.exists() &&
                    file.readText().trim() ==
                    nativeProximityFreshCycleLockToken(PROXIMITY_FRESH_OWNER_NATIVE, cycleId)
        } catch (_: Exception) {
            false
        }
    }

    private fun clearExpiredNativeProximityFreshCycleLock(file: File) {
        try {
            if (file.exists() &&
                System.currentTimeMillis() - file.lastModified() >
                NATIVE_PROXIMITY_FRESH_CYCLE_MAX_MS
            ) {
                file.delete()
            }
        } catch (_: Exception) {
            return
        }
    }

    private fun clearNativeProximityFreshCycleLock(
        expectedOwner: String? = null,
        expectedCycleId: Long? = null,
        force: Boolean = false
    ) {
        try {
            val file = nativeProximityFreshCycleLockFile()
            if (!file.exists()) return
            if (force ||
                (expectedOwner != null &&
                        expectedCycleId != null &&
                        file.readText().trim() ==
                        nativeProximityFreshCycleLockToken(expectedOwner, expectedCycleId))
            ) {
                file.delete()
            }
        } catch (_: Exception) {
            return
        }
    }

    private fun isWithinNativeProximityFreshTrigger(
        config: NativeConfig,
        location: Location?
    ): Boolean {
        if (!isUsableNativeProximityFreshTriggerLocation(location)) return false
        val triggerLocation = location ?: return false
        return distanceMeters(
            config.lat,
            config.lng,
            triggerLocation.latitude,
            triggerLocation.longitude
        ) <= NATIVE_PROXIMITY_FRESH_TRIGGER_METERS
    }

    private fun isUsableNativeProximityFreshTriggerLocation(location: Location?): Boolean {
        if (location == null) return false
        val age = locationAgeMs(location)
        if (age < 0L || age > NATIVE_INACTIVE_LAST_KNOWN_MAX_AGE_MS) return false
        val accuracy = if (location.hasAccuracy()) location.accuracy.toDouble() else 999.0
        return accuracy <= NATIVE_INACTIVE_LAST_KNOWN_MAX_ACCURACY_METERS
    }

    private fun markNativeProximityFreshRequested(
        config: NativeConfig,
        fallbackLocation: Location?,
        action: String
    ) {
        val nowMs = System.currentTimeMillis()
        getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putLong(KEY_PROXIMITY_FRESH_LAST_REQUEST_MS, nowMs)
            .apply()
        nativeProximityFreshRequestCount += 1

        val distanceText = if (fallbackLocation == null) {
            "unknown"
        } else {
            distanceMeters(
                config.lat,
                config.lng,
                fallbackLocation.latitude,
                fallbackLocation.longitude
            ).toInt().toString()
        }
        val fine = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) ==
                PackageManager.PERMISSION_GRANTED
        val coarse = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) ==
                PackageManager.PERMISSION_GRANTED
        val background = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION) ==
                    PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
        appendRuntimeLog(
            "[NH알리미] 근접 정밀 측정 요청 — provider:gps, action:$action, 거리:${distanceText}m, " +
                    "timeout:${NATIVE_LOCATION_TIMEOUT_MS / 1000}초"
        )
        appendRuntimeLog(
            "[NH알리미] 위치 권한 상태 — fine:$fine, coarse:$coarse, background:$background"
        )
    }

    private fun expireNativeProximityFreshCycleIfNeeded(
        prefs: android.content.SharedPreferences,
        nowMs: Long
    ) {
        if (!prefs.getBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, false)) return
        val startedMs = prefs.getLong(KEY_PROXIMITY_FRESH_CYCLE_STARTED_MS, 0L)
        if (startedMs <= 0L || nowMs - startedMs > NATIVE_PROXIMITY_FRESH_CYCLE_MAX_MS) {
            finishNativeProximityFreshCycle(prefs, nowMs)
        }
    }

    private fun finishNativeProximityFreshCycle(
        prefs: android.content.SharedPreferences,
        nowMs: Long = System.currentTimeMillis()
    ) {
        if (!prefs.getBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, false)) return
        val owner = prefs.getString(KEY_PROXIMITY_FRESH_CYCLE_OWNER, "unknown")
        val cycleId = prefs.getLong(KEY_PROXIMITY_FRESH_CYCLE_ID, 0L)
        prefs.edit()
            .remove(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE)
            .remove(KEY_PROXIMITY_FRESH_CYCLE_OWNER)
            .remove(KEY_PROXIMITY_FRESH_CYCLE_ID)
            .remove(KEY_PROXIMITY_FRESH_CYCLE_STARTED_MS)
            .remove(KEY_PROXIMITY_FRESH_RECHECKS_REMAINING)
            .putLong(KEY_PROXIMITY_FRESH_CYCLE_FINISHED_MS, nowMs)
            .apply()
        clearNativeProximityFreshCycleLock(
            expectedOwner = owner,
            expectedCycleId = cycleId
        )
        appendRuntimeLog("[NH알리미] 근접 정밀 검증 사이클 종료 — owner:$owner")
    }

    private fun clearNativeProximityFreshStateOnStop() {
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        if (prefs.getBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, false)) {
            finishNativeProximityFreshCycle(prefs)
        }
        clearNativeProximityFreshCycleLock(force = true)
    }

    private data class SharedProximityFreshPayload(
        val verifiedAtMs: Long,
        val distanceMm: Long,
        val accuracyMm: Long,
        val source: String,
        val configGeneration: Long
    )

    private fun readSharedProximityFreshPayload(
        prefs: android.content.SharedPreferences,
        nowMs: Long = System.currentTimeMillis()
    ): SharedProximityFreshPayload? {
        val encoded = prefs.getString(KEY_PROXIMITY_FRESH_VERIFIED_PAYLOAD, null) ?: return null
        return try {
            val json = JSONObject(encoded)
            if (!json.has("verifiedAtMs") ||
                !json.has("distanceMm") ||
                !json.has("accuracyMm") ||
                !json.has("source") ||
                !json.has("configGeneration")
            ) {
                return null
            }
            val payload = SharedProximityFreshPayload(
                verifiedAtMs = json.getLong("verifiedAtMs"),
                distanceMm = json.getLong("distanceMm"),
                accuracyMm = json.getLong("accuracyMm"),
                source = json.getString("source"),
                configGeneration = json.getLong("configGeneration")
            )
            val currentConfigGeneration = getLongPreference(
                prefs,
                KEY_GEOFENCE_CONFIG_GENERATION,
                0L
            )
            if (payload.verifiedAtMs <= 0L ||
                payload.distanceMm < 0L ||
                payload.accuracyMm < 0L ||
                payload.configGeneration % 2L != 0L ||
                payload.configGeneration != currentConfigGeneration ||
                nowMs < payload.verifiedAtMs ||
                nowMs - payload.verifiedAtMs >
                NATIVE_PROXIMITY_FRESH_SHARED_RESULT_MAX_AGE_MS
            ) {
                null
            } else {
                payload
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun hasRecentSharedProximityFreshResult(
        prefs: android.content.SharedPreferences,
        nowMs: Long = System.currentTimeMillis()
    ): Boolean {
        return readSharedProximityFreshPayload(prefs, nowMs) != null
    }

    private fun sharedProximityFreshLocation(
        config: NativeConfig,
        triggerLocation: Location?
    ): Location? {
        if (!isWithinNativeProximityFreshTrigger(config, triggerLocation)) return null
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val nowMs = System.currentTimeMillis()
        val payload = readSharedProximityFreshPayload(prefs, nowMs) ?: return null
        val ageMs = (nowMs - payload.verifiedAtMs).coerceAtLeast(0L)
        return Location("shared proximity fresh").apply {
            latitude = config.lat + (payload.distanceMm / 1000.0) / 111_320.0
            longitude = config.lng
            accuracy = (payload.accuracyMm / 1000.0).toFloat()
            time = payload.verifiedAtMs
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
                elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos() - ageMs * 1_000_000L
            }
        }
    }

    private fun storeSharedNativeProximityFreshResult(
        judgment: NativeJudgment,
        source: String,
        configGeneration: Long
    ): Boolean {
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val currentConfigGeneration = getLongPreference(
            prefs,
            KEY_GEOFENCE_CONFIG_GENERATION,
            0L
        )
        if (configGeneration % 2L != 0L ||
            configGeneration != currentConfigGeneration
        ) {
            appendRuntimeLog(
                "[NH알리미] 근접 정밀 측정 결과 폐기 — 설정 변경 감지:" +
                        "$configGeneration->$currentConfigGeneration"
            )
            return false
        }
        val payload = JSONObject()
            .put("verifiedAtMs", System.currentTimeMillis())
            .put("distanceMm", (judgment.distance * 1000).toLong())
            .put("accuracyMm", (judgment.accuracy * 1000).toLong())
            .put("source", source)
            .put("configGeneration", configGeneration)
            .toString()
        prefs.edit()
            .putString(KEY_PROXIMITY_FRESH_VERIFIED_PAYLOAD, payload)
            .remove(KEY_PROXIMITY_FRESH_VERIFIED_AT_MS)
            .remove(KEY_PROXIMITY_FRESH_VERIFIED_DISTANCE_MM)
            .remove(KEY_PROXIMITY_FRESH_VERIFIED_ACCURACY_MM)
            .remove(KEY_PROXIMITY_FRESH_VERIFIED_SOURCE)
            .apply()
        return true
    }

    private fun finishNativeLocationCheck(
        config: NativeConfig,
        location: Location?,
        timedOut: Boolean,
        note: String,
        generation: Long
    ) {
        if (!isCurrentNativeMonitor(generation)) return
        nativeCheckRunning = false
        if (!isCurrentNativeConfig(config)) {
            syncNativeConfigFromFlutter(this)
            appendRuntimeLog("[NH알리미] 네이티브 위치 응답 폐기 — 설정 변경 감지")
            scheduleNativeMonitoring(3_000L)
            return
        }

        if (location == null) {
            if (timedOut) {
                nativeLocationTimeoutCount += 1
            }
            val delayMs = nextNativeFailureDelay(config)
            appendRuntimeLog(
                "[NH알리미] 네이티브 보조 감시 위치 확인 실패 — $note, " +
                        "다음:${delayMs / 1000}초"
            )
            if (config.notifActive) {
                appendRuntimeLog(
                    "[NH알리미] 네이티브 위치감시 절전 — 위치 실패/timeout, " +
                            "위치 재확인:${delayMs / 1000}초, 반복 알림:${NATIVE_REMINDER_INTERVAL_MS / 1000}초 유지"
                )
            }
            scheduleNativeMonitoring(delayMs)
            return
        }

        val judgment = judgeNativeLocation(config, location)
        if (note == "gps 근접 정밀") {
            storeSharedNativeProximityFreshResult(
                judgment,
                PROXIMITY_FRESH_OWNER_NATIVE,
                config.configGeneration
            )
            appendRuntimeLog(
                "[NH알리미] 근접 정밀 측정 성공 — provider:gps, " +
                        "거리:${judgment.distance.toInt()}m, 정확도:${judgment.accuracy.toInt()}m"
            )
        } else if (note.contains("근접 fallback")) {
            storeSharedNativeProximityFreshResult(
                judgment,
                "nativeFallback",
                config.configGeneration
            )
            appendRuntimeLog(
                "[NH알리미] 근접 정밀 측정 fallback 성공 — source:$note, " +
                        "거리:${judgment.distance.toInt()}m, 정확도:${judgment.accuracy.toInt()}m"
            )
        }
        if (timedOut) {
            nativeLocationTimeoutCount += 1
        }
        if (note.contains("lastKnown")) {
            nativeLastKnownUseCount += 1
        }
        handleDismissedNativeExit(config, judgment)
        val delayMs = nextNativeDelay(config, judgment)
        val delaySec = delayMs / 1000
        val age = locationAgeMs(location)
        val timeoutText = if (timedOut) ", timeout후 lastKnown 사용" else ""
        val dismissedLowPower = config.dismissedUntilExit &&
                (judgment.reliableInside || !judgment.isOutside)
        val dismissedLowPowerText =
            if (dismissedLowPower) ", 출퇴근 확인 차단 저전력" else ""
        val notifLowPowerText =
            if (config.notifActive) ", 알림 활성 위치절전(반복 알림 ${NATIVE_REMINDER_INTERVAL_MS / 1000}초 유지)" else ""
        val inactiveLowPowerText =
            if (isInactiveLowPower(config) && !config.notifActive && !config.dismissedUntilExit) {
                ", 화면꺼짐 저전력(${config.executionMode})"
            } else {
                ""
            }

        refreshNativeApproachPendingState(config, judgment)
        val weakInitialAlertCandidate = judgment.initialAlertCandidate &&
                !judgment.strongInitialAlertCandidate &&
                !isVerifiedNativeProximityResult(note)
        val initialAlertCandidate = !config.dismissedUntilExit &&
                !config.notifActive &&
                judgment.initialAlertCandidate &&
                (judgment.strongInitialAlertCandidate ||
                        isVerifiedNativeProximityResult(note))
        if (weakInitialAlertCandidate) {
            appendRuntimeLog(
                "[NH알리미] 네이티브 약한 초기 알림 후보 보류 — " +
                        "${judgment.initialAlertText()}, 검증된 fresh 위치 필요"
            )
        }

        if (judgment.reliableInside && lastNativeZone != "inside" && config.dismissedUntilExit) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 팝업 생략 — 출퇴근 확인 차단 상태")
        } else if ((judgment.reliableInside || initialAlertCandidate) &&
            lastNativeZone != "inside" &&
            !config.notifActive
        ) {
            if (initialAlertCandidate && !judgment.reliableInside) {
                appendRuntimeLog(
                    "[NH알리미] 네이티브 초기 알림 후보 통과 — " +
                            "${judgment.initialAlertText()}, zone:${judgment.zone}"
                )
            }
            clearNativeApproachPendingState()
            showNativeEntryPopup(config, judgment)
        } else if (judgment.reliableInside && lastNativeZone != "inside" && config.notifActive) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 팝업 생략 — 반복 알림 이미 활성 중")
        }

        lastNativeZone = when {
            judgment.reliableInside || initialAlertCandidate -> "inside"
            judgment.isOutside -> "outside"
            else -> "boundary"
        }

        val status = when {
            judgment.reliableInside -> "범위 안"
            initialAlertCandidate -> "초기 알림 후보"
            judgment.isOutside -> "범위 밖"
            else -> "경계/보류"
        }
        appendRuntimeLog(
            "[NH알리미] 네이티브 보조 감시 — $status " +
                    "(${judgment.decisionText(config.radius)}, age:${age}ms, source:$note$timeoutText$dismissedLowPowerText$notifLowPowerText$inactiveLowPowerText), " +
                    "다음:${delaySec}초"
        )
        if (config.notifActive && delayMs >= NATIVE_NOTIF_ACTIVE_LOW_POWER_INTERVAL_MS) {
            appendRuntimeLog(
                "[NH알리미] 네이티브 위치감시 절전 — 알림 활성 상태, " +
                        "위치 재확인:${delaySec}초, 반복 알림:${NATIVE_REMINDER_INTERVAL_MS / 1000}초 유지"
            )
        } else if (isInactiveLowPower(config)) {
            appendRuntimeLog(
                "[NH알리미] 네이티브 백그라운드 트리거 — 화면꺼짐 상태(${config.executionMode}), " +
                        "저전력 위치확인:${delaySec}초"
            )
        }
        scheduleNativeMonitoring(delayMs)
    }

    private fun judgeNativeLocation(config: NativeConfig, location: Location): NativeJudgment {
        val distance = distanceMeters(config.lat, config.lng, location.latitude, location.longitude)
        val accuracy = if (location.hasAccuracy()) location.accuracy.toDouble() else 999.0
        val centerThreshold = max(10.0, config.radius * 0.5)
        val accuracyThreshold = max(config.radius, 35.0)
        val exitThreshold = max(config.radius + 15.0, 50.0)
        val initialAlertThreshold = max(
            NATIVE_INITIAL_ALERT_MIN_METERS,
            minOf(config.radius + NATIVE_INITIAL_ALERT_BUFFER_METERS, NATIVE_INITIAL_ALERT_MAX_METERS)
        )
        val reliableInside = distance <= config.radius &&
                (distance <= centerThreshold || accuracy <= accuracyThreshold)
        val initialAlertCandidate = distance <= initialAlertThreshold &&
                accuracy <= NATIVE_INITIAL_ALERT_MAX_ACCURACY_METERS
        val zone = when {
            reliableInside -> "inside"
            distance <= config.radius -> "unreliableInside"
            distance <= exitThreshold -> "boundary"
            distance <= config.radius + NATIVE_FAR_METERS -> "outside"
            else -> "farOutside"
        }
        return NativeJudgment(
            zone,
            distance,
            accuracy,
            exitThreshold,
            initialAlertThreshold,
            reliableInside,
            initialAlertCandidate
        )
    }

    private fun shouldUseLastKnownForLocationLowPower(config: NativeConfig, location: Location?): Boolean {
        if ((!config.dismissedUntilExit && !config.notifActive && !isInactiveLowPower(config)) || location == null) {
            return false
        }
        val age = locationAgeMs(location)
        if (age < 0 || age > lastKnownMaxAgeMs(config)) return false
        val accuracy = if (location.hasAccuracy()) location.accuracy.toDouble() else 999.0
        return accuracy <= lastKnownMaxAccuracyMeters(config)
    }

    private fun lastKnownMaxAgeMs(config: NativeConfig): Long {
        return when {
            config.notifActive -> NATIVE_NOTIF_ACTIVE_LAST_KNOWN_MAX_AGE_MS
            config.dismissedUntilExit -> NATIVE_DISMISSED_LAST_KNOWN_MAX_AGE_MS
            else -> NATIVE_INACTIVE_LAST_KNOWN_MAX_AGE_MS
        }
    }

    private fun lastKnownMaxAccuracyMeters(config: NativeConfig): Double {
        return when {
            config.notifActive -> NATIVE_NOTIF_ACTIVE_LAST_KNOWN_MAX_ACCURACY_METERS
            config.dismissedUntilExit -> NATIVE_DISMISSED_LAST_KNOWN_MAX_ACCURACY_METERS
            else -> NATIVE_INACTIVE_LAST_KNOWN_MAX_ACCURACY_METERS
        }
    }

    private fun isVerifiedNativeProximityResult(note: String): Boolean {
        return note == "gps 근접 정밀" ||
                note == "shared 근접 검증" ||
                note.endsWith(" 근접 fallback")
    }

    private fun refreshNativeApproachPendingState(
        config: NativeConfig,
        judgment: NativeJudgment
    ): Boolean {
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        if (config.dismissedUntilExit || config.notifActive) {
            clearNativeApproachPendingState()
            return false
        }

        val nowMs = System.currentTimeMillis()
        val active = prefs.getBoolean(KEY_APPROACH_PENDING_ACTIVE, false)
        val pendingAtMs = prefs.getLong(KEY_APPROACH_PENDING_AT_MS, 0L)
        val expired = !active ||
                pendingAtMs <= 0L ||
                nowMs - pendingAtMs > NATIVE_APPROACH_PENDING_VALID_MS

        if (judgment.distance > NATIVE_APPROACH_PENDING_CLEAR_METERS) {
            if (active) {
                appendRuntimeLog(
                    "[NH알리미] 네이티브 접근 대기 해제 — " +
                            "${judgment.distance.toInt()}m, 기준 " +
                            "${NATIVE_APPROACH_PENDING_CLEAR_METERS.toInt()}m 초과"
                )
            }
            clearNativeApproachPendingState()
            return false
        }

        if (judgment.approachPendingSeed) {
            prefs.edit()
                .putBoolean(KEY_APPROACH_PENDING_ACTIVE, true)
                .putLong(KEY_APPROACH_PENDING_AT_MS, nowMs)
                .remove(KEY_APPROACH_PENDING_DISTANCE)
                .remove(KEY_APPROACH_PENDING_ACCURACY)
                .apply()
            if (expired) {
                appendRuntimeLog(
                    "[NH알리미] 네이티브 접근 대기 시작 — " +
                            "${judgment.distance.toInt()}m, 정확도 " +
                            "${judgment.accuracy.toInt()}m, 유효:" +
                            "${NATIVE_APPROACH_PENDING_VALID_MS / 1000}초"
                )
            }
            return true
        }

        if (expired) {
            clearNativeApproachPendingState()
            return false
        }
        return true
    }

    private fun clearNativeApproachPendingState() {
        getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .remove(KEY_APPROACH_PENDING_ACTIVE)
            .remove(KEY_APPROACH_PENDING_AT_MS)
            .remove(KEY_APPROACH_PENDING_DISTANCE)
            .remove(KEY_APPROACH_PENDING_ACCURACY)
            .apply()
    }

    private fun handleDismissedNativeExit(config: NativeConfig, judgment: NativeJudgment) {
        if (!config.dismissedUntilExit) {
            return
        }

        if (!judgment.isOutside) {
            return
        }

        if (judgment.distance > NATIVE_DISMISSED_EXIT_THRESHOLD_METERS) {
            getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean("flutter.dismissed_until_exit", false)
                .apply()
            appendRuntimeLog(
                "[NH알리미] 네이티브 보조 감시 — 출퇴근 확인 차단 해제 " +
                        "(${judgment.distance.toInt()}m, 기준 ${judgment.exitThreshold.toInt()}m, " +
                        "정확도 ${judgment.accuracy.toInt()}m, 차단 해제 기준 " +
                        "${NATIVE_DISMISSED_EXIT_THRESHOLD_METERS.toInt()}m 초과)"
            )
        } else {
            appendRuntimeLog(
                "[NH알리미] 네이티브 보조 감시 — 출퇴근 확인 차단 유지 " +
                        "(${judgment.distance.toInt()}m, 기준 ${judgment.exitThreshold.toInt()}m, " +
                        "정확도 ${judgment.accuracy.toInt()}m, 차단 해제 기준 " +
                        "${NATIVE_DISMISSED_EXIT_THRESHOLD_METERS.toInt()}m 초과)"
            )
        }
    }

    private fun nextNativeDelay(config: NativeConfig, judgment: NativeJudgment): Long {
        val prefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        if (config.dismissedUntilExit) {
            finishNativeProximityFreshCycle(prefs)
            if (judgment.isOutside) {
                return NATIVE_DISMISSED_OUTSIDE_INTERVAL_MS
            }
            return NATIVE_DISMISSED_STABLE_INTERVAL_MS
        }

        if (config.notifActive) {
            finishNativeProximityFreshCycle(prefs)
            return NATIVE_NOTIF_ACTIVE_LOW_POWER_INTERVAL_MS
        }

        if (isInactiveLowPower(config)) {
            val active = prefs.getBoolean(KEY_PROXIMITY_FRESH_CYCLE_ACTIVE, false)
            val owner = prefs.getString(KEY_PROXIMITY_FRESH_CYCLE_OWNER, null)
            val remaining = getLongPreference(
                prefs,
                KEY_PROXIMITY_FRESH_RECHECKS_REMAINING,
                0L
            )
            if (judgment.distance > NATIVE_PROXIMITY_FRESH_TRIGGER_METERS) {
                finishNativeProximityFreshCycle(prefs)
            } else if (active &&
                owner == PROXIMITY_FRESH_OWNER_NATIVE &&
                remaining > 0
            ) {
                appendRuntimeLog(
                    "[NH알리미] 근접 재확인 예약 — " +
                            "${NATIVE_PROXIMITY_FRESH_RECHECK_INTERVAL_MS / 1000}초 후, " +
                            "owner:$owner, 남은횟수:$remaining/" +
                            "$NATIVE_PROXIMITY_FRESH_RECHECK_LIMIT"
                )
                return NATIVE_PROXIMITY_FRESH_RECHECK_INTERVAL_MS
            } else if (active &&
                owner == PROXIMITY_FRESH_OWNER_NATIVE &&
                remaining <= 0
            ) {
                finishNativeProximityFreshCycle(prefs)
            }
            if (judgment.distance > judgment.exitThreshold &&
                judgment.distance <= NATIVE_APPROACH_BAND_MAX_METERS
            ) {
                return NATIVE_APPROACH_TRIGGER_INTERVAL_MS
            }
            return NATIVE_PENDING_TRIGGER_INTERVAL_MS
        }

        return NATIVE_PENDING_TRIGGER_INTERVAL_MS
    }

    private fun isInactiveLowPower(config: NativeConfig): Boolean =
        config.executionMode == MODE_BACKGROUND_RECENT || config.executionMode == MODE_SERVICE_ONLY

    private fun nextNativeFailureDelay(config: NativeConfig): Long {
        if (config.notifActive) {
            return NATIVE_NOTIF_ACTIVE_LOW_POWER_INTERVAL_MS
        }
        if (config.dismissedUntilExit) {
            return NATIVE_DISMISSED_STABLE_INTERVAL_MS
        }
        if (isInactiveLowPower(config)) {
            return NATIVE_PENDING_TRIGGER_INTERVAL_MS
        }
        return NATIVE_DEFAULT_INTERVAL_MS
    }

    private fun showNativeEntryPopup(config: NativeConfig, judgment: NativeJudgment) {
        val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val nativePrefs = getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
        val blockReason = nativeEntryPopupBlockReason(config, flutterPrefs, nativePrefs)
        if (blockReason != null) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 팝업 생략 — $blockReason")
            return
        }
        val now = SystemClock.elapsedRealtime()
        if (now - lastNativePopupAtMs < NATIVE_POPUP_COOLDOWN_MS) {
            return
        }
        lastNativePopupAtMs = now
        nativePopupCount += 1

        finishNativeProximityFreshCycle(
            getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        )
        markNativeReminderActive()
        createReminderChannel()
        postNativeReminderNotification()
        appendRuntimeLog(
            "[NH알리미] 네이티브 보조 팝업 발송 — " +
                    "${judgment.distance.toInt()}m, 정확도 ${judgment.accuracy.toInt()}m"
        )
        startNativeReminderRepeat()
    }

    private fun nativeEntryPopupBlockReason(
        config: NativeConfig,
        flutterPrefs: android.content.SharedPreferences,
        nativePrefs: android.content.SharedPreferences
    ): String? {
        if (!isCurrentNativeConfig(config)) return "설정 변경 감지"
        if (flutterPrefs.getBoolean("flutter.notif_active", false) ||
            nativePrefs.getBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
        ) {
            return "공유 알림 활성 상태"
        }
        if (flutterPrefs.getBoolean("flutter.is_paused", false) ||
            flutterPrefs.getBoolean("flutter.user_paused", false) ||
            nativePrefs.getBoolean(KEY_NATIVE_PAUSED, false)
        ) {
            return "일시정지 상태"
        }
        if (flutterPrefs.getBoolean("flutter.dismissed_until_exit", false)) {
            return "출퇴근 확인 차단 상태"
        }
        if (!NativeServiceScheduler.isMonitoringHours()) {
            return "모니터링 시간 외"
        }
        return null
    }

    private fun markNativeReminderActive() {
        val nowMs = System.currentTimeMillis()
        getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean("flutter.notif_active", true)
            .putInt("flutter.notif_interval_sec", (NATIVE_REMINDER_INTERVAL_MS / 1000).toInt())
            .putLong("flutter.notification_starting_ms", nowMs)
            .putLong("flutter.last_notification_started_ms", nowMs)
            .putLong("flutter.last_notification_callback_ms", nowMs)
            .putLong("flutter.last_notification_scheduled_ms", nowMs)
            .putLong("flutter.notif_outside_count", 0L)
            .apply()
        getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_NATIVE_NOTIF_ACTIVE, true)
            .putBoolean(KEY_NATIVE_REPEAT_OWNER, true)
            .apply()
    }

    private fun startNativeReminderRepeat() {
        nativeReminderGeneration += 1
        handler.removeCallbacks(nativeReminder)
        handler.postDelayed(nativeReminder, NATIVE_REMINDER_INTERVAL_MS)
        appendRuntimeLog(
            "[NH알리미] 네이티브 반복 알림 시작 — " +
                    "${NATIVE_REMINDER_INTERVAL_MS / 1000}초 간격"
        )
        appendRuntimeLog(
            "[NH알리미] 다음 네이티브 반복 알림 예약 → " +
                    "${NATIVE_REMINDER_INTERVAL_MS / 1000}초 후"
        )
    }

    private fun stopNativeReminderRepeat(clearActive: Boolean) {
        nativeReminderGeneration += 1
        handler.removeCallbacks(nativeReminder)
        if (clearActive) {
            getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean("flutter.notif_active", false)
                .putLong("flutter.notif_outside_count", 0L)
                .apply()
            getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
                .putBoolean(KEY_NATIVE_REPEAT_OWNER, false)
                .apply()
        }
    }

    private fun recoverNativeReminderRepeatIfNeeded() {
        val nativePrefs = getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
        if (!nativePrefs.getBoolean(KEY_NATIVE_REPEAT_OWNER, false)) {
            return
        }
        if (!nativePrefs.getBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)) {
            return
        }
        val blockReason = nativeReminderBlockReason()
        if (blockReason != null) {
            appendRuntimeLog("[NH알리미] 네이티브 반복 알림 복구 생략 — $blockReason")
            return
        }

        createReminderChannel()
        postNativeReminderNotification()
        nativeReminderGeneration += 1
        handler.removeCallbacks(nativeReminder)
        handler.postDelayed(nativeReminder, NATIVE_REMINDER_INTERVAL_MS)
        appendRuntimeLog(
            "[NH알리미] 네이티브 반복 알림 활성 상태 복구 — " +
                    "${NATIVE_REMINDER_INTERVAL_MS / 1000}초 간격 재예약"
        )
        appendRuntimeLog(
            "[NH알리미] 다음 네이티브 반복 알림 예약 → " +
                    "${NATIVE_REMINDER_INTERVAL_MS / 1000}초 후"
        )
    }

    private fun runNativeReminderTick(generation: Long) {
        if (generation != nativeReminderGeneration) return

        val blockReason = nativeReminderBlockReason()
        if (blockReason != null) {
            stopNativeReminderRepeat(clearActive = blockReason != "notif_active=false")
            appendRuntimeLog("[NH알리미] 네이티브 반복 알림 종료 — $blockReason")
            return
        }

        postNativeReminderNotification()
        val nowMs = System.currentTimeMillis()
        getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putLong("flutter.last_notification_callback_ms", nowMs)
            .putLong("flutter.last_notification_scheduled_ms", nowMs)
            .apply()

        appendRuntimeLog("[NH알리미] 네이티브 반복 알림 발송")
        handler.postDelayed(nativeReminder, NATIVE_REMINDER_INTERVAL_MS)
        appendRuntimeLog(
            "[NH알리미] 다음 네이티브 반복 알림 예약 → " +
                    "${NATIVE_REMINDER_INTERVAL_MS / 1000}초 후"
        )
    }

    private fun nativeReminderBlockReason(): String? {
        val flutterPrefs = getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val nativePrefs = getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
        val flutterActive = flutterPrefs.getBoolean("flutter.notif_active", false)
        val nativeActive = nativePrefs.getBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
        if (!flutterActive && !nativeActive) return "notif_active=false"
        if (flutterPrefs.getBoolean("flutter.is_paused", false) ||
            flutterPrefs.getBoolean("flutter.user_paused", false) ||
            nativePrefs.getBoolean(KEY_NATIVE_PAUSED, false)
        ) {
            return "일시정지 상태"
        }
        if (flutterPrefs.getBoolean("flutter.dismissed_until_exit", false)) {
            return "출퇴근 확인 차단 상태"
        }
        if (!NativeServiceScheduler.isMonitoringHours()) {
            return "모니터링 시간 외"
        }
        return null
    }

    private fun postNativeReminderNotification() {
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

        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager?.cancel(REMINDER_NOTIF_ID)
        notificationManager?.notify(REMINDER_NOTIF_ID, notification)
    }

    private fun distanceMeters(lat1: Double, lng1: Double, lat2: Double, lng2: Double): Double {
        val earthRadius = 6371000.0
        val dLat = Math.toRadians(lat2 - lat1)
        val dLng = Math.toRadians(lng2 - lng1)
        val a = sin(dLat / 2) * sin(dLat / 2) +
                cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) *
                sin(dLng / 2) * sin(dLng / 2)
        val c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return earthRadius * c
    }

    private fun locationAgeMs(location: Location): Long {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            ((SystemClock.elapsedRealtimeNanos() - location.elapsedRealtimeNanos) / 1_000_000L)
                .coerceAtLeast(0L)
        } else {
            Long.MAX_VALUE
        }
    }
}
