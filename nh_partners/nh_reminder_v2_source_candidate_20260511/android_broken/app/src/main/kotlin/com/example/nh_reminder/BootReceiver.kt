package com.example.nh_reminder

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * 기기 재부팅 후 지오펜스 자동 재등록을 위한 BroadcastReceiver
 *
 * AndroidManifest에 BOOT_COMPLETED 권한 및 수신기 등록 필요.
 * 수신 시 앱의 백그라운드 서비스를 재시작하여 지오펜스를 다시 등록.
 */
class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == "android.intent.action.QUICKBOOT_POWERON"
        ) {
            Log.d("NHReminder", "부팅 완료 — 지오펜스 재등록 시작")

            // FlutterActivity를 통해 앱 재시작 (백그라운드 서비스 재기동)
            val launchIntent = Intent(context, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                putExtra("from_boot", true)
            }
            // 안드로이드 12+ 에서는 백그라운드 앱 시작 제한 있음
            // flutter_background_service가 대신 처리하도록 위임
            try {
                context.startForegroundService(
                    Intent(context, NhBackgroundService::class.java)
                )
            } catch (e: Exception) {
                Log.e("NHReminder", "백그라운드 서비스 시작 실패: ${e.message}")
            }
        }
    }
}
