package com.example.nh_reminder

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import java.util.Calendar

object NativeServiceScheduler {
    private const val START_REQUEST_CODE = 9101
    private const val STOP_REQUEST_CODE = 9102

    const val ACTION_START_MONITORING = "com.example.nh_reminder.action.START_MONITORING_SERVICE"
    const val ACTION_STOP_MONITORING = "com.example.nh_reminder.action.STOP_MONITORING_SERVICE"

    fun schedule(context: Context) {
        scheduleOne(context, true)
        scheduleOne(context, false)
    }

    fun isMonitoringHours(): Boolean {
        val now = Calendar.getInstance()
        val hour = now.get(Calendar.HOUR_OF_DAY)
        return hour in 6 until 19
    }

    private fun scheduleOne(context: Context, start: Boolean) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val target = nextAt(if (start) 6 else 19)
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            if (start) START_REQUEST_CODE else STOP_REQUEST_CODE,
            Intent(context, NativeServiceAlarmReceiver::class.java).apply {
                action = if (start) ACTION_START_MONITORING else ACTION_STOP_MONITORING
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                target.timeInMillis,
                pendingIntent
            )
        } else {
            alarmManager.setExact(AlarmManager.RTC_WAKEUP, target.timeInMillis, pendingIntent)
        }

        Log.d(
            "NHAlimi",
            "네이티브 서비스 ${if (start) "시작" else "종료"} 알람 예약: ${target.time}"
        )
    }

    private fun nextAt(hour: Int): Calendar {
        val now = Calendar.getInstance()
        return Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, hour)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
            if (!after(now)) {
                add(Calendar.DAY_OF_YEAR, 1)
            }
        }
    }
}
