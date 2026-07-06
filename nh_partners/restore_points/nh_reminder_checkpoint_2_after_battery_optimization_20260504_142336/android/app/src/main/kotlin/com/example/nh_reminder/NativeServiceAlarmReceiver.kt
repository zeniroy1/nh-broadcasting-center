package com.example.nh_reminder

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class NativeServiceAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        when (intent?.action) {
            NativeServiceScheduler.ACTION_START_MONITORING -> {
                try {
                    if (isUserPaused(context)) {
                        NhBackgroundService.stop(context)
                        Log.d("NHAlimi", "06:00 네이티브 서비스 시작 생략 — 사용자 모니터링 OFF 상태")
                        NativeServiceScheduler.schedule(context)
                        return
                    }

                    context.getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
                        .edit()
                        .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, false)
                        .apply()
                    NhBackgroundService.start(context)
                    Log.d("NHAlimi", "06:00 네이티브 포그라운드 서비스 시작")
                } catch (e: Exception) {
                    Log.e("NHAlimi", "06:00 네이티브 서비스 시작 실패: ${e.message}")
                }
            }

            NativeServiceScheduler.ACTION_STOP_MONITORING -> {
                try {
                    context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
                        .edit()
                        .putBoolean("flutter.is_paused", true)
                        .putBoolean("flutter.notif_active", false)
                        .apply()
                    context.getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
                        .edit()
                        .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, true)
                        .putBoolean(NhBackgroundService.KEY_NATIVE_NOTIF_ACTIVE, false)
                        .apply()
                    context.getSystemService(NotificationManager::class.java)?.cancel(1001)
                    NhBackgroundService.stop(context)
                    Log.d("NHAlimi", "19:00 네이티브 포그라운드 서비스 종료")
                } catch (e: Exception) {
                    Log.e("NHAlimi", "19:00 네이티브 서비스 종료 실패: ${e.message}")
                }
            }
        }

        NativeServiceScheduler.schedule(context)
    }

    private fun isUserPaused(context: Context): Boolean {
        return context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            .getBoolean("flutter.user_paused", false)
    }
}
