package com.hamcoding.hamshare.transfer

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.net.Uri
import android.os.IBinder
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import com.hamcoding.hamshare.MainActivity
import com.hamcoding.hamshare.R
import com.hamcoding.hamshare.network.HamShareClient
import com.hamcoding.hamshare.security.SecureStore
import java.util.concurrent.Executors
import kotlin.math.roundToInt

class TransferService : Service() {
    private val executor = Executors.newSingleThreadExecutor()
    private val notificationManager by lazy { getSystemService(NotificationManager::class.java) }

    override fun onCreate() {
        super.onCreate()
        notificationManager.createNotificationChannel(NotificationChannel(
            CHANNEL_ID, "HAMSHARE 파일 전송", NotificationManager.IMPORTANCE_LOW
        ))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val uriStrings = intent?.getStringArrayListExtra(EXTRA_URIS).orEmpty()
        if (uriStrings.isEmpty()) { stopSelf(); return START_NOT_STICKY }
        startForeground(NOTIFICATION_ID, notification("파일 준비 중", 0, true))
        executor.execute { transfer(uriStrings.map(Uri::parse)) }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        executor.shutdownNow()
        super.onDestroy()
    }

    private fun transfer(uris: List<Uri>) {
        val started = SystemClock.elapsedRealtime()
        try {
            val store = SecureStore(this)
            val config = store.loadConfig() ?: error("먼저 PC를 등록하세요.")
            val client = HamShareClient(contentResolver)
            TransferState.update(TransferUiState(true, "파일 검사 중", "SHA-256 계산 중", 0f))
            val files = client.inspectFiles(uris) { index, total, message ->
                val progress = if (total == 0) 0f else index.toFloat() / total * 0.1f
                TransferState.update(TransferUiState(true, "파일 검사 중", message, progress))
                notificationManager.notify(NOTIFICATION_ID, notification(message, (progress * 100).roundToInt(), true))
            }
            val totalBytes = files.sumOf { it.size }.coerceAtLeast(1)
            val localDeviceId = store.localDeviceId()
            val transferId = client.beginTransfer(config, localDeviceId, files)
            var completedBytes = 0L
            files.forEachIndexed { index, file ->
                client.uploadFile(config, localDeviceId, transferId, index, file) { currentFileBytes ->
                    val sent = completedBytes + currentFileBytes
                    val elapsedSeconds = ((SystemClock.elapsedRealtime() - started) / 1000.0).coerceAtLeast(0.1)
                    val progress = sent.toFloat() / totalBytes
                    val state = TransferUiState(
                        true, "${index + 1}/${files.size} 전송 중", file.name,
                        progress, sent / elapsedSeconds
                    )
                    TransferState.update(state)
                    notificationManager.notify(NOTIFICATION_ID, notification(file.name, (progress * 100).roundToInt(), false))
                }
                completedBytes += file.size
            }
            TransferState.update(TransferUiState(
                running = false, title = "전송 완료", detail = "${files.size}개 파일 전송 완료",
                progress = 1f, completed = true
            ))
            notificationManager.notify(NOTIFICATION_ID, notification("${files.size}개 파일 전송 완료", 100, false))
        } catch (error: Throwable) {
            TransferState.update(TransferUiState(
                running = false, title = "전송 실패", detail = error.message ?: "알 수 없는 오류",
                error = error.message ?: "알 수 없는 오류"
            ))
            notificationManager.notify(NOTIFICATION_ID, notification("전송 실패: ${error.message}", 0, false))
        } finally {
            stopForeground(STOP_FOREGROUND_DETACH)
            stopSelf()
        }
    }

    private fun notification(text: String, progress: Int, indeterminate: Boolean): Notification {
        val openIntent = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_hamshare)
            .setContentTitle("HAMSHARE")
            .setContentText(text)
            .setContentIntent(openIntent)
            .setOnlyAlertOnce(true)
            .setOngoing(progress in 1..99)
            .setProgress(100, progress.coerceIn(0, 100), indeterminate)
            .build()
    }

    companion object {
        const val EXTRA_URIS = "uris"
        private const val CHANNEL_ID = "hamshare-transfer"
        private const val NOTIFICATION_ID = 57321
    }
}
