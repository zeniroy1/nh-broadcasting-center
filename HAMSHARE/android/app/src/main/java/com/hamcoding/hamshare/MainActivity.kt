package com.hamcoding.hamshare

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.app.ActivityCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.hamcoding.hamshare.transfer.TransferState
import com.hamcoding.hamshare.transfer.TransferUiState

class MainActivity : ComponentActivity() {
    private val viewModel: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleShareIntent(intent)
        if (Build.VERSION.SDK_INT >= 33 && ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 100)
        }
        setContent {
            val state by viewModel.state.collectAsStateWithLifecycle()
            val transfer by TransferState.state.collectAsState()
            HamShareTheme { HamShareScreen(state, transfer) }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleShareIntent(intent)
    }

    @Composable
    private fun HamShareScreen(state: MainUiState, transfer: TransferUiState) {
        val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
            uris.forEach { uri -> runCatching { contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION) } }
            viewModel.setFiles(uris)
        }
        Scaffold(containerColor = Color(0xFF07111F)) { padding ->
            Column(
                Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).padding(22.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text("HAMSHARE", color = Color.White, fontSize = 36.sp, fontWeight = FontWeight.ExtraBold)
                Text("Galaxy S23+ → Windows 10", color = Color(0xFF91A7C0))

                Section("1. 핫스팟") {
                    Text("S23+의 5GHz 모바일 핫스팟을 켜고 PC를 연결하세요.", color = Color(0xFFCAD8EA))
                    OutlinedButton(onClick = { startActivity(Intent("android.settings.TETHER_SETTINGS")) }) { Text("핫스팟 설정 열기") }
                }

                Section("2. PC 등록") {
                    OutlinedTextField(state.host, viewModel::setHost, label = { Text("PC IP 주소") }, placeholder = { Text("192.168.XXX.XXX") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(state.port, viewModel::setPort, label = { Text("포트") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(state.fingerprint, viewModel::setFingerprint, label = { Text("인증서 코드") }, placeholder = { Text("AA-BB-CC-DD-EE-FF") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(state.pin, viewModel::setPin, label = { Text("6자리 PIN") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Button(onClick = viewModel::pair, enabled = !state.busy) { Text(if (state.paired) "다시 등록" else "PC 등록") }
                        if (state.paired) OutlinedButton(onClick = viewModel::forgetReceiver) { Text("등록 해제") }
                    }
                    if (state.paired) Text("등록됨: ${state.receiverName}", color = Color(0xFF43D39E), fontWeight = FontWeight.Bold)
                }

                Section("3. 파일 전송") {
                    Text("선택 파일: ${state.selectedUris.size}개", color = Color.White, fontWeight = FontWeight.SemiBold)
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        OutlinedButton(onClick = { filePicker.launch(arrayOf("*/*")) }, enabled = !transfer.running) { Text("파일 선택") }
                        Button(onClick = viewModel::startTransfer, enabled = state.paired && state.selectedUris.isNotEmpty() && !transfer.running) { Text("전송 시작") }
                    }
                    if (transfer.running || transfer.completed || transfer.error != null) {
                        LinearProgressIndicator(progress = { transfer.progress }, modifier = Modifier.fillMaxWidth())
                        Text(transfer.title, color = Color.White, fontWeight = FontWeight.Bold)
                        Text(transfer.detail, color = if (transfer.error == null) Color(0xFF91A7C0) else Color(0xFFFF7B86))
                        if (transfer.bytesPerSecond > 0) Text(formatSpeed(transfer.bytesPerSecond), color = Color(0xFF55A7FF))
                    }
                }
                Text(state.message, color = Color(0xFFFFC857), modifier = Modifier.fillMaxWidth())
            }
        }
    }

    private fun handleShareIntent(intent: Intent?) {
        val uris = when (intent?.action) {
            Intent.ACTION_SEND -> listOfNotNull(intent.parcelableUri(Intent.EXTRA_STREAM))
            Intent.ACTION_SEND_MULTIPLE -> intent.parcelableUriList(Intent.EXTRA_STREAM)
            else -> emptyList()
        }
        if (uris.isNotEmpty()) viewModel.setFiles(uris)
    }
}

@Composable
private fun Section(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(
        Modifier.fillMaxWidth().background(Color(0xFF0E2034), RoundedCornerShape(18.dp)).padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp), content = {
            Text(title, color = Color(0xFF55A7FF), fontWeight = FontWeight.Bold, fontSize = 18.sp)
            content()
        }
    )
}

@Composable
private fun HamShareTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = Color(0xFF55A7FF), secondary = Color(0xFF43D39E),
            background = Color(0xFF07111F), surface = Color(0xFF0E2034), onSurface = Color.White
        ), content = content
    )
}

@Suppress("DEPRECATION")
private fun Intent.parcelableUri(key: String): Uri? =
    if (Build.VERSION.SDK_INT >= 33) getParcelableExtra(key, Uri::class.java) else getParcelableExtra(key)

@Suppress("DEPRECATION")
private fun Intent.parcelableUriList(key: String): List<Uri> =
    if (Build.VERSION.SDK_INT >= 33) getParcelableArrayListExtra(key, Uri::class.java).orEmpty()
    else getParcelableArrayListExtra<Uri>(key).orEmpty()

private fun formatSpeed(bytesPerSecond: Double): String =
    if (bytesPerSecond >= 1024 * 1024) "%.1f MB/s".format(bytesPerSecond / 1024 / 1024)
    else "%.0f KB/s".format(bytesPerSecond / 1024)
