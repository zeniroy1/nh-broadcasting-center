package com.example.nh_reminder

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class NativeServiceAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        when (intent?.action) {
            NativeServiceScheduler.ACTION_START_MONITORING -> {
                try {
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
                    context.getSharedPreferences(NhBackgroundService.NATIVE_PREFS, Context.MODE_PRIVATE)
                        .edit()
                        .putBoolean(NhBackgroundService.KEY_NATIVE_PAUSED, true)
                        .apply()
                    NhBackgroundService.stop(context)
                    Log.d("NHAlimi", "19:00 네이티브 포그라운드 서비스 종료")
                } catch (e: Exception) {
                    Log.e("NHAlimi", "19:00 네이티브 서비스 종료 실패: ${e.message}")
                }
            }
        }

        NativeServiceScheduler.schedule(context)
    }
}
