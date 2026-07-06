package com.hamcoding.hamshare.network

import android.content.ContentResolver
import android.net.Uri
import android.provider.OpenableColumns
import com.hamcoding.hamshare.security.ReceiverConfig
import com.hamcoding.hamshare.security.SecureStore
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.net.URL
import java.security.MessageDigest
import java.security.SecureRandom
import java.security.cert.X509Certificate
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager

data class LocalFile(
    val uri: Uri,
    val name: String,
    val size: Long,
    val sha256: String,
    val mimeType: String?
)

data class PairResult(
    val receiverDeviceId: String,
    val receiverName: String,
    val accessToken: String,
    val fingerprint: String
)

class HamShareClient(private val resolver: ContentResolver) {
    fun pair(host: String, port: Int, pin: String, fingerprintCode: String, localDeviceId: String): PairResult {
        require(pin.length == 6) { "PIN은 6자리여야 합니다." }
        require(SecureStore.normalizeFingerprint(fingerprintCode).length >= 12) { "인증서 코드는 12자리 이상이어야 합니다." }
        val body = JSONObject()
            .put("deviceId", localDeviceId)
            .put("deviceName", android.os.Build.MODEL)
            .put("pin", pin)
            .toString()
        val connection = open(host, port, "/api/v1/pair", "POST", fingerprintCode)
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
        connection.doOutput = true
        connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
        val response = readJson(connection)
        return PairResult(
            response.getString("deviceId"), response.getString("deviceName"),
            response.getString("accessToken"), response.getString("certificateFingerprint")
        )
    }

    fun inspectFiles(uris: List<Uri>, onProgress: (Int, Int, String) -> Unit): List<LocalFile> = uris.mapIndexed { index, uri ->
        val name = queryDisplayName(uri)
        onProgress(index, uris.size, "검사 중: $name")
        val digest = MessageDigest.getInstance("SHA-256")
        var actualSize = 0L
        resolver.openInputStream(uri)?.use { input ->
            BufferedInputStream(input, 1024 * 1024).use { buffered ->
                val buffer = ByteArray(1024 * 1024)
                while (true) {
                    val count = buffered.read(buffer)
                    if (count < 0) break
                    digest.update(buffer, 0, count)
                    actualSize += count
                }
            }
        } ?: error("파일을 열 수 없습니다: $name")
        LocalFile(uri, name, actualSize, digest.digest().toHex(), resolver.getType(uri))
    }

    fun beginTransfer(config: ReceiverConfig, localDeviceId: String, files: List<LocalFile>): String {
        val array = JSONArray()
        files.forEachIndexed { index, file ->
            array.put(JSONObject()
                .put("index", index).put("name", file.name).put("size", file.size)
                .put("sha256", file.sha256).put("mimeType", file.mimeType ?: JSONObject.NULL))
        }
        val body = JSONObject().put("deviceId", localDeviceId).put("files", array).toString()
        val connection = authenticated(config, localDeviceId, "/api/v1/transfers", "POST")
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
        connection.doOutput = true
        connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
        return readJson(connection).getString("transferId")
    }

    fun uploadFile(
        config: ReceiverConfig,
        localDeviceId: String,
        transferId: String,
        index: Int,
        file: LocalFile,
        onBytes: (Long) -> Unit
    ) {
        val path = "/api/v1/transfers/$transferId/files/$index"
        val connection = authenticated(config, localDeviceId, path, "PUT")
        connection.setRequestProperty("Content-Type", file.mimeType ?: "application/octet-stream")
        connection.setFixedLengthStreamingMode(file.size)
        connection.doOutput = true
        resolver.openInputStream(file.uri)?.use { input ->
            BufferedInputStream(input, 1024 * 1024).use { source ->
                BufferedOutputStream(connection.outputStream, 1024 * 1024).use { destination ->
                    val buffer = ByteArray(1024 * 1024)
                    var sent = 0L
                    while (true) {
                        val count = source.read(buffer)
                        if (count < 0) break
                        destination.write(buffer, 0, count)
                        sent += count
                        onBytes(sent)
                    }
                }
            }
        } ?: error("파일을 열 수 없습니다: ${file.name}")
        readJson(connection)
    }

    private fun authenticated(config: ReceiverConfig, localDeviceId: String, path: String, method: String): HttpsURLConnection =
        open(config.host, config.port, path, method, config.fingerprint).apply {
            setRequestProperty("Authorization", "Bearer ${config.token}")
            setRequestProperty("X-HAMSHARE-DEVICE-ID", localDeviceId)
        }

    private fun open(host: String, port: Int, path: String, method: String, fingerprint: String): HttpsURLConnection {
        val normalizedHost = host.trim().removePrefix("https://").removePrefix("http://").substringBefore('/').substringBefore(':')
        val connection = URL("https://$normalizedHost:$port$path").openConnection() as HttpsURLConnection
        val expected = SecureStore.normalizeFingerprint(fingerprint)
        val trustManager = object : X509TrustManager {
            override fun getAcceptedIssuers(): Array<X509Certificate> = emptyArray()
            override fun checkClientTrusted(chain: Array<X509Certificate>?, authType: String?) = Unit
            override fun checkServerTrusted(chain: Array<X509Certificate>?, authType: String?) {
                val certificate = chain?.firstOrNull() ?: error("서버 인증서가 없습니다.")
                val actual = MessageDigest.getInstance("SHA-256").digest(certificate.encoded).toHex()
                if (expected.length < 12 || !actual.startsWith(expected)) throw java.security.cert.CertificateException("인증서 코드가 일치하지 않습니다.")
            }
        }
        SSLContext.getInstance("TLS").apply { init(null, arrayOf<TrustManager>(trustManager), SecureRandom()) }.also {
            connection.sslSocketFactory = it.socketFactory
        }
        connection.hostnameVerifier = javax.net.ssl.HostnameVerifier { _, _ -> true }
        connection.requestMethod = method
        connection.connectTimeout = 10_000
        connection.readTimeout = 120_000
        connection.useCaches = false
        return connection
    }

    private fun readJson(connection: HttpsURLConnection): JSONObject {
        val code = connection.responseCode
        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
        val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
        if (code !in 200..299) {
            val message = runCatching { JSONObject(text).optString("message") }.getOrNull().orEmpty()
            error(if (message.isBlank()) "서버 오류 HTTP $code" else message)
        }
        return JSONObject(text)
    }

    private fun queryDisplayName(uri: Uri): String {
        var name = "shared-file"
        runCatching {
            resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME).takeIf { it >= 0 }?.let { index ->
                        cursor.getString(index)?.let { value -> if (value.isNotBlank()) name = value }
                    }
                }
            }
        }
        return name
    }
}

private fun ByteArray.toHex(): String = joinToString("") { "%02X".format(it) }
