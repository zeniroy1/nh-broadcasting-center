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
        private const val REMINDER_CHANNEL_ID = "nh_reminder_high_v2"
        private const val REMINDER_NOTIF_ID = 1001
        private const val BATTERY_LOG_INTERVAL_MS = 15 * 60 * 1000L
        private const val NATIVE_LOCATION_TIMEOUT_MS = 12 * 1000L
        private const val NATIVE_POPUP_COOLDOWN_MS = 30 * 1000L
        private const val NATIVE_INSIDE_INTERVAL_MS = 15 * 1000L
        private const val NATIVE_NEAR_INTERVAL_MS = 30 * 1000L
        private const val NATIVE_DEFAULT_INTERVAL_MS = 60 * 1000L
        private const val NATIVE_FAR_INTERVAL_MS = 120 * 1000L
        private const val NATIVE_ENTRY_NEAR_METERS = 150.0
        private const val NATIVE_FAR_METERS = 500.0
        private const val BATTERY_PREFS = "nh_battery_usage"
        private const val KEY_ACTIVE = "active"
        private const val KEY_START_PERCENT = "start_percent"
        private const val KEY_START_ELAPSED_MS = "start_elapsed_ms"
        private const val KEY_HAD_CHARGING = "had_charging"

        fun hasLocationPermission(context: Context): Boolean {
            val fine = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)
            val coarse = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION)
            return fine == PackageManager.PERMISSION_GRANTED || coarse == PackageManager.PERMISSION_GRANTED
        }

        fun start(context: Context) {
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

        fun stop(context: Context) {
            context.getSharedPreferences(NATIVE_PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_NATIVE_PAUSED, true)
                .putBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
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
    private var nativePopupCount = 0L
    private var lastNativeZone = "unknown"
    private var lastNativePopupAtMs = 0L

    private val batteryLogger = object : Runnable {
        override fun run() {
            logBatterySnapshot("포그라운드 서비스 배터리 샘플")
            handler.postDelayed(this, BATTERY_LOG_INTERVAL_MS)
        }
    }
    private val nativeMonitor = object : Runnable {
        override fun run() {
            runNativeMonitorCheck(nativeMonitorGeneration)
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.d("NHAlimi", "포그라운드 서비스 생성")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            removeForegroundServiceNotification()
            logBatterySnapshot("포그라운드 서비스 종료 전 배터리")
            finishBatteryLogging()
            stopNativeMonitoring()
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
        startNativeMonitoring(initialDelayMs = 3_000L)
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
        stopBatteryLogging()
        finishBatteryLogging()
        stopNativeMonitoring()
        stopSelf()
    }

    override fun onDestroy() {
        logBatterySnapshot("포그라운드 서비스 종료")
        removeForegroundServiceNotification()
        finishBatteryLogging()
        stopNativeMonitoring()
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
            val downloadDir = File("/storage/emulated/0/Download/nh_partners")
            if (!downloadDir.exists()) downloadDir.mkdirs()
            File(downloadDir, "nh_reminder_runtime.txt").appendText(line)
        } catch (e: Exception) {
            try {
                val fallbackDir = getExternalFilesDir(null) ?: filesDir
                File(fallbackDir, "nh_reminder_runtime.txt").appendText(line)
            } catch (ignored: Exception) {
                Log.e("NHAlimi", "파일 로그 실패: ${e.message}")
            }
        }
    }

    private data class NativeConfig(
        val paused: Boolean,
        val lat: Double,
        val lng: Double,
        val radius: Double,
        val notifActive: Boolean,
        val dismissedUntilExit: Boolean
    )

    private data class NativeJudgment(
        val zone: String,
        val distance: Double,
        val accuracy: Double,
        val exitThreshold: Double,
        val reliableInside: Boolean
    ) {
        val isOutside: Boolean
            get() = zone == "outside" || zone == "farOutside"

        fun decisionText(radius: Double): String {
            val centerThreshold = max(10.0, radius * 0.5)
            val accuracyThreshold = max(radius, 35.0)
            val result = if (reliableInside) "통과" else "보류"
            return "거리 ${distance.toInt()}m / 반경 ${radius.toInt()}m, " +
                    "정확도 ${accuracy.toInt()}m, 통과기준: 중심권 ${centerThreshold.toInt()}m 이내 " +
                    "또는 정확도 ${accuracyThreshold.toInt()}m 이하, " +
                    "이탈기준: ${exitThreshold.toInt()}m 초과, 판정:$result"
        }
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
        val flutterPrefs = getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
        val nativeNotifActive = prefs.getBoolean(KEY_NATIVE_NOTIF_ACTIVE, false)
        val flutterNotifActive = flutterPrefs.getBoolean("flutter.notif_active", false)
        return NativeConfig(
            paused = prefs.getBoolean(KEY_NATIVE_PAUSED, false),
            lat = Double.fromBits(prefs.getLong(KEY_NATIVE_LAT, 37.56600.toBits())),
            lng = Double.fromBits(prefs.getLong(KEY_NATIVE_LNG, 126.96730.toBits())),
            radius = Double.fromBits(prefs.getLong(KEY_NATIVE_RADIUS, 30.0.toBits())),
            notifActive = nativeNotifActive || flutterNotifActive,
            dismissedUntilExit = flutterPrefs.getBoolean("flutter.dismissed_until_exit", false)
        )
    }

    private fun hasLocationPermission(): Boolean {
        return hasLocationPermission(this)
    }

    @Suppress("MissingPermission")
    private fun requestNativeLocation(config: NativeConfig, generation: Long) {
        val locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val bestLastKnown = bestLastKnownLocation(locationManager)
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
            finishNativeLocationCheck(
                config,
                bestLastKnown,
                timedOut = true,
                note = "위치 요청 timeout",
                generation = generation
            )
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
                finishNativeLocationCheck(
                    config,
                    location,
                    timedOut = false,
                    note = provider,
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
            finishNativeLocationCheck(
                config,
                bestLastKnown,
                timedOut = true,
                note = "위치 요청 실패:${e.message}",
                generation = generation
            )
        }
    }

    private fun bestLastKnownLocation(locationManager: LocationManager): Location? {
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
            locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER) -> LocationManager.GPS_PROVIDER
            locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER) -> LocationManager.NETWORK_PROVIDER
            locationManager.isProviderEnabled(LocationManager.PASSIVE_PROVIDER) -> LocationManager.PASSIVE_PROVIDER
            else -> null
        }
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

        if (location == null) {
            appendRuntimeLog(
                "[NH알리미] 네이티브 보조 감시 위치 확인 실패 — $note, " +
                        "다음:${NATIVE_DEFAULT_INTERVAL_MS / 1000}초"
            )
            scheduleNativeMonitoring(NATIVE_DEFAULT_INTERVAL_MS)
            return
        }

        val judgment = judgeNativeLocation(config, location)
        val delayMs = nextNativeDelay(config.radius, judgment.distance, judgment.zone)
        val delaySec = delayMs / 1000
        val age = locationAgeMs(location)
        val timeoutText = if (timedOut) ", timeout후 lastKnown 사용" else ""

        if (judgment.reliableInside && lastNativeZone != "inside" && config.dismissedUntilExit) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 팝업 생략 — 출퇴근 확인 차단 상태")
        } else if (judgment.reliableInside && lastNativeZone != "inside" && !config.notifActive) {
            showNativeEntryPopup(judgment)
        } else if (judgment.reliableInside && lastNativeZone != "inside" && config.notifActive) {
            appendRuntimeLog("[NH알리미] 네이티브 보조 팝업 생략 — 반복 알림 이미 활성 중")
        }

        lastNativeZone = when {
            judgment.reliableInside -> "inside"
            judgment.isOutside -> "outside"
            else -> "boundary"
        }

        val status = when {
            judgment.reliableInside -> "범위 안"
            judgment.isOutside -> "범위 밖"
            else -> "경계/보류"
        }
        appendRuntimeLog(
            "[NH알리미] 네이티브 보조 감시 — $status " +
                    "(${judgment.decisionText(config.radius)}, age:${age}ms, source:$note$timeoutText), " +
                    "다음:${delaySec}초"
        )
        scheduleNativeMonitoring(delayMs)
    }

    private fun judgeNativeLocation(config: NativeConfig, location: Location): NativeJudgment {
        val distance = distanceMeters(config.lat, config.lng, location.latitude, location.longitude)
        val accuracy = if (location.hasAccuracy()) location.accuracy.toDouble() else 999.0
        val centerThreshold = max(10.0, config.radius * 0.5)
        val accuracyThreshold = max(config.radius, 35.0)
        val exitThreshold = max(config.radius + 15.0, 50.0)
        val reliableInside = distance <= config.radius &&
                (distance <= centerThreshold || accuracy <= accuracyThreshold)
        val zone = when {
            reliableInside -> "inside"
            distance <= config.radius -> "unreliableInside"
            distance <= exitThreshold -> "boundary"
            distance <= config.radius + NATIVE_FAR_METERS -> "outside"
            else -> "farOutside"
        }
        return NativeJudgment(zone, distance, accuracy, exitThreshold, reliableInside)
    }

    private fun nextNativeDelay(radius: Double, distance: Double, zone: String): Long {
        if (zone == "inside" || zone == "unreliableInside" || zone == "boundary") {
            return NATIVE_INSIDE_INTERVAL_MS
        }
        val outsideDistance = distance - radius
        return when {
            outsideDistance <= 30.0 -> NATIVE_INSIDE_INTERVAL_MS
            outsideDistance <= NATIVE_ENTRY_NEAR_METERS -> NATIVE_NEAR_INTERVAL_MS
            outsideDistance <= NATIVE_FAR_METERS -> NATIVE_DEFAULT_INTERVAL_MS
            else -> NATIVE_FAR_INTERVAL_MS
        }
    }

    private fun showNativeEntryPopup(judgment: NativeJudgment) {
        val now = SystemClock.elapsedRealtime()
        if (now - lastNativePopupAtMs < NATIVE_POPUP_COOLDOWN_MS) {
            return
        }
        lastNativePopupAtMs = now
        nativePopupCount += 1

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
        appendRuntimeLog(
            "[NH알리미] 네이티브 보조 팝업 발송 — " +
                    "${judgment.distance.toInt()}m, 정확도 ${judgment.accuracy.toInt()}m"
        )
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
