package com.example.nh_reminder

import android.content.Context
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object UserDiagnosticLogger {
    private const val USER_DIAGNOSTIC_FILE = "nh_alimi_user_diagnostic.txt"

    fun append(context: Context, message: String) {
        try {
            val dir = context.getExternalFilesDir(null) ?: context.filesDir
            if (!dir.exists()) dir.mkdirs()

            val timestamp = SimpleDateFormat(
                "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
                Locale.US
            ).format(Date())
            File(dir, USER_DIAGNOSTIC_FILE).appendText(
                "[$timestamp] [NH알리미] $message\n",
                Charsets.UTF_8
            )
        } catch (_: Exception) {
        }
    }
}
