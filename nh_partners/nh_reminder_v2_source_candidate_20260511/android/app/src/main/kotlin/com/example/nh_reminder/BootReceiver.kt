package com.example.nh_reminder

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == "android.intent.action.QUICKBOOT_POWERON"
        ) {
            Log.d("NHReminder", "부팅 완료 — 지오펜스 재등록 시작")
            NativeServiceScheduler.schedule(context)

            try {
                if (NativeServiceScheduler.isMonitoringHours()) {
                    context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
                        .edit()
                        .putBoolean("flutter.is_paused", false)
                        .putBoolean("flutter.user_paused", false)
                        .putBoolean("flutter.dismissed_until_exit", false)
                        .putBoolean("flutter.notif_active", false)
                        .putLong("flutter.monitor_outside_count", 0L)
                        .putLong("flutter.geofence_exit_count", 0L)
                        .putLong("flutter.notif_outside_count", 0L)
                        .apply()
                    context.getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
                        .edit()
                        .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, false)
                        .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, false)
                        .putBoolean(NhBackgroundService.KEY_NATIVE_REPEAT_OWNER, false)
                        .apply()
                    NhBackgroundService.start(context)
                    Log.d("NHReminder", "부팅 후 모니터링 시간대 — 수동정지 해제 및 서비스 시작")
                }
            } catch (e: Exception) {
                Log.e("NHReminder", "백그라운드 서비스 시작 실패: ${e.message}")
            }
        }
    }
}
