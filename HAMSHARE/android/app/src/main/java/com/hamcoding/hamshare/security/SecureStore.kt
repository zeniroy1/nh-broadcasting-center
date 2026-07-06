package com.hamcoding.hamshare.security

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import java.util.UUID
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

data class ReceiverConfig(
    val host: String,
    val port: Int,
    val fingerprint: String,
    val deviceId: String,
    val token: String
)

class SecureStore(context: Context) {
    private val preferences = context.getSharedPreferences("hamshare", Context.MODE_PRIVATE)
    private val keyAlias = "hamshare-token-key"

    fun localDeviceId(): String {
        val existing = preferences.getString("local_device_id", null)
        if (existing != null) return existing
        return UUID.randomUUID().toString().replace("-", "").also {
            preferences.edit().putString("local_device_id", it).apply()
        }
    }

    fun loadConfig(): ReceiverConfig? {
        val host = preferences.getString("host", null) ?: return null
        val fingerprint = preferences.getString("fingerprint", null) ?: return null
        val receiverDeviceId = preferences.getString("receiver_device_id", null) ?: return null
        val encryptedToken = preferences.getString("token", null) ?: return null
        return runCatching {
            ReceiverConfig(host, preferences.getInt("port", 57321), fingerprint, receiverDeviceId, decrypt(encryptedToken))
        }.getOrNull()
    }

    fun saveConfig(config: ReceiverConfig) {
        preferences.edit()
            .putString("host", config.host)
            .putInt("port", config.port)
            .putString("fingerprint", normalizeFingerprint(config.fingerprint))
            .putString("receiver_device_id", config.deviceId)
            .putString("token", encrypt(config.token))
            .apply()
    }

    fun clearConfig() = preferences.edit()
        .remove("host").remove("port").remove("fingerprint")
        .remove("receiver_device_id").remove("token").apply()

    private fun encrypt(value: String): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        val payload = cipher.iv + cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(payload, Base64.NO_WRAP)
    }

    private fun decrypt(value: String): String {
        val payload = Base64.decode(value, Base64.NO_WRAP)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), GCMParameterSpec(128, payload.copyOfRange(0, 12)))
        return cipher.doFinal(payload.copyOfRange(12, payload.size)).toString(Charsets.UTF_8)
    }

    private fun getOrCreateKey(): SecretKey {
        val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (keyStore.getKey(keyAlias, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").run {
            init(KeyGenParameterSpec.Builder(
                keyAlias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .build())
            generateKey()
        }
    }

    companion object {
        fun normalizeFingerprint(value: String): String = value.filter(Char::isLetterOrDigit).uppercase()
    }
}

