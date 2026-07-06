package com.example.nh_reminder

import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import org.json.JSONArray
import java.text.SimpleDateFormat
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Date
import java.util.Locale
import kotlin.math.abs

object ReminderActionHandler {
    const val ACTION_OPEN_NH = "com.example.nh_reminder.OPEN_NH"
    const val EXTRA_PAYLOAD = "payload"
    const val EXTRA_SOURCE = "source"
    const val PAYLOAD_OPEN_NH = "open_nh"

    private const val FLUTTER_PREFS = "FlutterSharedPreferences"
    private const val NH_PACKAGE = "com.vus.nhpthrm"
    private const val REMINDER_NOTIF_ID = 1001
    private const val KEY_LAST_ACTION_HANDLED_MS = "flutter.last_reminder_action_handled_ms"
    private const val DUPLICATE_WINDOW_MS = 120_000L

    fun handleOpenNh(context: Context, source: String) {
        val handledAtMs = System.currentTimeMillis()
        if (isRecentlyHandled(context, handledAtMs)) {
            Log.d("NHAlimi", "알림 클릭 중복 처리 생략 — source:$source")
            UserDiagnosticLogger.append(context, "알림 클릭 중복 처리 생략 — source:$source")
            markReminderHandled(context)
            launchNhApp(context, source)
            return
        }

        when (saveTimestamp(context, source, handledAtMs)) {
            SaveResult.Saved -> {
                markReminderHandled(context)
                launchNhApp(context, source)
            }
            SaveResult.Duplicate -> {
                markReminderHandled(context)
                launchNhApp(context, source)
            }
            SaveResult.Failed -> {
                if (!markActionHandled(context, handledAtMs)) {
                    Log.w("NHAlimi", "알림 클릭 처리 마커 저장 실패 — source:$source")
                }
                UserDiagnosticLogger.append(context, "출퇴근 기록 저장 실패 후 알림 처리 계속 — source:$source")
                markReminderHandled(context)
                launchNhApp(context, source)
            }
        }
    }

    private fun isRecentlyHandled(context: Context, nowMs: Long): Boolean {
        val prefs = context.getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
        val lastHandledMs = prefs.getLong(KEY_LAST_ACTION_HANDLED_MS, 0L)
        return lastHandledMs > 0L && nowMs - lastHandledMs < DUPLICATE_WINDOW_MS
    }

    private fun markActionHandled(context: Context, handledAtMs: Long): Boolean {
        return context.getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putLong(KEY_LAST_ACTION_HANDLED_MS, handledAtMs)
            .commit()
    }

    private fun saveTimestamp(context: Context, source: String, handledAtMs: Long): SaveResult {
        try {
            val prefs = context.getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            val raw = prefs.getString("flutter.commute_history_raw", null)
            val timestamps = if (raw.isNullOrBlank()) JSONArray() else JSONArray(raw)
            if (hasRecentTimestamp(timestamps, handledAtMs)) {
                markActionHandled(context, handledAtMs)
                Log.d("NHAlimi", "출퇴근 기록 중복 저장 생략 — source:$source")
                UserDiagnosticLogger.append(context, "출퇴근 기록 중복 저장 생략 — source:$source")
                return SaveResult.Duplicate
            }

            val timestamp = SimpleDateFormat(
                "yyyy-MM-dd'T'HH:mm:ss.SSS",
                Locale.US
            ).format(Date(handledAtMs))

            timestamps.put(timestamp)
            val committed = prefs.edit()
                .putLong(KEY_LAST_ACTION_HANDLED_MS, handledAtMs)
                .putString("flutter.commute_history_raw", timestamps.toString())
                .putBoolean("flutter.pending_history_reload", true)
                .commit()

            if (!committed) {
                Log.e("NHAlimi", "출퇴근 기록 저장 커밋 실패 — source:$source")
                UserDiagnosticLogger.append(context, "출퇴근 기록 저장 커밋 실패 — source:$source")
                return SaveResult.Failed
            }

            Log.d("NHAlimi", "출퇴근 기록 저장 완료 — source:$source, timestamp:$timestamp")
            UserDiagnosticLogger.append(
                context,
                "출퇴근 기록 저장 완료 — source:$source, timestamp:$timestamp"
            )
            return SaveResult.Saved
        } catch (e: Exception) {
            Log.e("NHAlimi", "출퇴근 기록 저장 실패 — source:$source, ${e.message}")
            UserDiagnosticLogger.append(context, "출퇴근 기록 저장 실패 — source:$source")
            return SaveResult.Failed
        }
    }

    private fun hasRecentTimestamp(timestamps: JSONArray, nowMs: Long): Boolean {
        if (timestamps.length() == 0) return false

        val lastTimestamp = timestamps.optString(timestamps.length() - 1, "")
        val lastMs = parseTimestampMs(lastTimestamp) ?: return false
        return abs(nowMs - lastMs) < DUPLICATE_WINDOW_MS
    }

    private fun parseTimestampMs(timestamp: String): Long? {
        return try {
            LocalDateTime.parse(timestamp, DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                .atZone(ZoneId.systemDefault())
                .toInstant()
                .toEpochMilli()
        } catch (e: Exception) {
            null
        }
    }

    private enum class SaveResult {
        Saved,
        Duplicate,
        Failed,
    }

    private fun markReminderHandled(context: Context) {
        context.getSharedPreferences(FLUTTER_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean("flutter.notif_active", false)
            .putBoolean("flutter.dismissed_until_exit", true)
            .apply()

        context.getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, false)
            .putBoolean(NhBackgroundService.KEY_NATIVE_REPEAT_OWNER, false)
            .apply()

        context.getSystemService(NotificationManager::class.java)
            ?.cancel(REMINDER_NOTIF_ID)

        UserDiagnosticLogger.append(
            context,
            "알림 클릭 처리 완료 — 반복 알림 중지, 출퇴근 확인 차단 진입"
        )
    }

    private fun launchNhApp(context: Context, source: String) {
        try {
            val launchIntent = context.packageManager.getLaunchIntentForPackage(NH_PACKAGE)
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                Log.d("NHAlimi", "NH파트너스 실행 요청 — source:$source")
                UserDiagnosticLogger.append(context, "NH파트너스 실행 요청 — source:$source")
                context.startActivity(launchIntent)
                UserDiagnosticLogger.append(context, "NH파트너스 실행 인텐트 전달 완료 — source:$source")
            } else {
                val marketIntent = Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse("market://details?id=$NH_PACKAGE")
                ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                Log.w("NHAlimi", "NH파트너스 패키지 없음 — Play 스토어 이동 요청")
                UserDiagnosticLogger.append(context, "NH파트너스 패키지 없음 — Play 스토어 이동 요청")
                context.startActivity(marketIntent)
            }
        } catch (e: Exception) {
            Log.e("NHAlimi", "NH파트너스 실행 요청 실패 — source:$source, ${e.message}")
            UserDiagnosticLogger.append(
                context,
                "NH파트너스 실행 요청 실패 — source:$source, reason:${e.javaClass.simpleName}"
            )
        }
    }
}
