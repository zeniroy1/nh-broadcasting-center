package com.hamcoding.hamshare

import android.app.Application
import android.content.Intent
import android.net.Uri
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.hamcoding.hamshare.network.HamShareClient
import com.hamcoding.hamshare.security.ReceiverConfig
import com.hamcoding.hamshare.security.SecureStore
import com.hamcoding.hamshare.transfer.TransferService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class MainUiState(
    val host: String = "",
    val port: String = "57321",
    val fingerprint: String = "",
    val pin: String = "",
    val paired: Boolean = false,
    val receiverName: String = "",
    val selectedUris: List<Uri> = emptyList(),
    val busy: Boolean = false,
    val message: String = "S23+ 핫스팟에 PC를 연결하세요."
)

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val store = SecureStore(application)
    private val mutable = MutableStateFlow(MainUiState())
    val state = mutable.asStateFlow()

    init {
        store.loadConfig()?.let { config ->
            mutable.value = mutable.value.copy(
                host = config.host, port = config.port.toString(), fingerprint = formatFingerprint(config.fingerprint),
                paired = true, receiverName = "등록된 PC", message = "PC 등록 완료 · 파일을 선택하세요."
            )
        }
    }

    fun setHost(value: String) = update { copy(host = value) }
    fun setPort(value: String) = update { copy(port = value.filter(Char::isDigit).take(5)) }
    fun setFingerprint(value: String) = update { copy(fingerprint = value.uppercase().take(23)) }
    fun setPin(value: String) = update { copy(pin = value.filter(Char::isDigit).take(6)) }

    fun setFiles(uris: List<Uri>) = update {
        copy(selectedUris = uris.distinct(), message = if (uris.isEmpty()) "파일을 선택하세요." else "${uris.size}개 파일 선택됨")
    }

    fun pair() {
        val snapshot = mutable.value
        val port = snapshot.port.toIntOrNull()
        if (snapshot.host.isBlank() || port == null || snapshot.pin.length != 6) {
            update { copy(message = "PC 주소, 포트, 6자리 PIN을 확인하세요.") }
            return
        }
        update { copy(busy = true, message = "PC 인증 중…") }
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) {
                    HamShareClient(getApplication<Application>().contentResolver).pair(
                        snapshot.host, port, snapshot.pin, snapshot.fingerprint, store.localDeviceId()
                    )
                }
            }.onSuccess { result ->
                val host = normalizeHost(snapshot.host)
                store.saveConfig(ReceiverConfig(host, port, result.fingerprint, result.receiverDeviceId, result.accessToken))
                mutable.value = mutable.value.copy(
                    host = host, fingerprint = formatFingerprint(result.fingerprint), pin = "",
                    paired = true, receiverName = result.receiverName, busy = false,
                    message = "${result.receiverName} 등록 완료"
                )
            }.onFailure { error ->
                update { copy(busy = false, message = "등록 실패: ${error.message}") }
            }
        }
    }

    fun forgetReceiver() {
        store.clearConfig()
        update { copy(paired = false, receiverName = "", pin = "", message = "PC 등록이 해제되었습니다.") }
    }

    fun startTransfer() {
        val uris = mutable.value.selectedUris
        if (store.loadConfig() == null) { update { copy(message = "먼저 PC를 등록하세요.") }; return }
        if (uris.isEmpty()) { update { copy(message = "전송할 파일을 선택하세요.") }; return }
        val intent = Intent(getApplication(), TransferService::class.java)
            .putStringArrayListExtra(TransferService.EXTRA_URIS, ArrayList(uris.map(Uri::toString)))
        ContextCompat.startForegroundService(getApplication(), intent)
        update { copy(message = "전송을 시작했습니다.") }
    }

    private fun update(block: MainUiState.() -> MainUiState) { mutable.value = mutable.value.block() }

    private fun normalizeHost(value: String) = value.trim()
        .removePrefix("https://").removePrefix("http://").substringBefore('/').substringBefore(':')

    private fun formatFingerprint(value: String): String = SecureStore.normalizeFingerprint(value)
        .chunked(2).take(6).joinToString("-")
}

