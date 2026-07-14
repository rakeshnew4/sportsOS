package com.sportsos.player.push

import android.util.Log
import android.webkit.CookieManager
import com.sportsos.player.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Bridges the native FCM token into the backend's device-token table by reusing the same
 * session cookie the WebView is already holding — there's no separate native login. Routed
 * through the Next.js proxy (not the FastAPI backend directly) since that's the origin the
 * "sportsos_uid" cookie is scoped to; the proxy translates it to the backend's bearer token
 * server-side exactly as it does for browser requests (see
 * web/src/app/api/proxy/[...path]/route.ts).
 */
object PushTokenRegistrar {
    private const val TAG = "PushTokenRegistrar"
    private const val SESSION_COOKIE_NAME = "sportsos_uid"

    suspend fun register(token: String): Unit = withContext(Dispatchers.IO) {
        val baseUrl = BuildConfig.SPORTS_OS_BASE_URL
        val cookie = CookieManager.getInstance().getCookie(baseUrl)
        if (cookie.isNullOrBlank() || !cookie.contains(SESSION_COOKIE_NAME)) {
            // Not logged in yet in the WebView — MainActivity retries this after every page
            // load, so it'll catch up right after the user signs in.
            return@withContext
        }
        var connection: HttpURLConnection? = null
        try {
            val url = URL("$baseUrl/api/proxy/notifications/me/device-tokens")
            connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                connectTimeout = 10_000
                readTimeout = 10_000
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Cookie", cookie)
            }
            val body = JSONObject().put("platform", "android").put("token", token)
            connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            val status = connection.responseCode
            if (status !in 200..299) {
                Log.w(TAG, "Device token registration failed: HTTP $status")
            }
        } catch (e: Exception) {
            Log.w(TAG, "Device token registration failed", e)
        } finally {
            connection?.disconnect()
        }
    }
}
