package com.hamcoding.hamshare.transfer

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

data class TransferUiState(
    val running: Boolean = false,
    val title: String = "전송 준비",
    val detail: String = "파일을 선택하세요.",
    val progress: Float = 0f,
    val bytesPerSecond: Double = 0.0,
    val completed: Boolean = false,
    val error: String? = null
)

object TransferState {
    private val mutable = MutableStateFlow(TransferUiState())
    val state = mutable.asStateFlow()
    fun update(value: TransferUiState) { mutable.value = value }
}

