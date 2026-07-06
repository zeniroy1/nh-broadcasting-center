package com.example.nh_reminder

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class ReminderActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action != ReminderActionHandler.ACTION_OPEN_NH) return

        val payload = intent.getStringExtra(ReminderActionHandler.EXTRA_PAYLOAD)
        if (payload != ReminderActionHandler.PAYLOAD_OPEN_NH) return

        Log.d("NHAlimi", "알림 클릭 수신 — 기록 저장 후 NH파트너스 실행 요청")
        UserDiagnosticLogger.append(context, "알림 버튼 클릭 감지 — 기록 저장 후 NH파트너스 실행 요청")
        ReminderActionHandler.handleOpenNh(context, "native_notification")
    }
}
