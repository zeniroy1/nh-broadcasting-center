package com.example.nh_reminder

import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Process
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    private val CHANNEL = "com.example.nh_reminder/usage_stats"
    private val NH_PACKAGE = "com.vus.nhpthrm"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "isAppInForeground" -> {
                        val pkg = call.argument<String>("package") ?: NH_PACKAGE
                        result.success(isAppInForeground(pkg))
                    }
                    "hasUsagePermission" -> {
                        result.success(hasUsagePermission())
                    }
                    "openUsageSettings" -> {
                        openUsageSettings()
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
    }

    /** NH파트너스 앱이 지금 포그라운드에 있는지 확인 */
    private fun isAppInForeground(targetPackage: String): Boolean {
        if (!hasUsagePermission()) return false
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return false

        val usm = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val now = System.currentTimeMillis()
        // 최근 10초 이내 사용 통계 조회
        val stats = usm.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            now - 10_000L,
            now
        )
        if (stats.isNullOrEmpty()) return false

        // 가장 최근에 사용된 앱이 NH파트너스인지 확인
        val recentStat = stats.maxByOrNull { it.lastTimeUsed }
        return recentStat?.packageName == targetPackage
    }

    /** PACKAGE_USAGE_STATS 권한 보유 여부 */
    private fun hasUsagePermission(): Boolean {
        return try {
            val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
            val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                appOps.unsafeCheckOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    packageName
                )
            } else {
                @Suppress("DEPRECATION")
                appOps.checkOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    packageName
                )
            }
            mode == AppOpsManager.MODE_ALLOWED
        } catch (e: Exception) {
            false
        }
    }

    /** 사용 내역 권한 설정 화면 열기 */
    private fun openUsageSettings() {
        startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
    }
}
