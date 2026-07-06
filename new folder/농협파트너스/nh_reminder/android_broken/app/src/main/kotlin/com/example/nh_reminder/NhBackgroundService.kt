package com.example.nh_reminder

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat

/**
 * NH 리마인더 포그라운드 서비스
 *
 * 앱이 백그라운드에 있어도 지오펜스 모니터링을 유지하기 위한 서비스.
 * flutter_background_service 패키지가 이 서비스를 래핑하여 Dart 코드 실행.
 */
class NhBackgroundService : Service() {

    companion object {
        const val CHANNEL_ID = "nh_reminder_bg_service"
        const val NOTIF_ID = 2001
    }

    override fun onCreate() {
        super.onCreate()
        createServiceChannel()
        startForeground(NOTIF_ID, buildServiceNotification())
        Log.d("NHReminder", "백그라운드 서비스 시작")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // 서비스가 강제 종료되어도 자동 재시작
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        Log.d("NHReminder", "백그라운드 서비스 종료")
    }

    private fun createServiceChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "NH 리마인더 실행 중",
                NotificationManager.IMPORTANCE_LOW  // 상태바에 조용히 표시
            ).apply {
                description = "위치 모니터링 서비스 실행 중"
                setShowBadge(false)
            }
            val nm = getSystemService(NotificationManager::class.java)
            nm?.createNotificationChannel(channel)
        }
    }

    private fun buildServiceNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("NH 리마인더 실행 중")
            .setContentText("출퇴근 위치 모니터링 중...")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }
}
