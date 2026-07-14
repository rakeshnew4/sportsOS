package com.sportsos.player

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.webkit.CookieManager
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.core.content.edit
import androidx.lifecycle.lifecycleScope
import com.google.firebase.FirebaseApp
import com.google.firebase.messaging.FirebaseMessaging
import com.sportsos.player.push.PushTokenRegistrar
import com.sportsos.player.ui.theme.SportsosTheme
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

private enum class NotificationPromptAction { REQUEST_PERMISSION, OPEN_SETTINGS }

private const val PREFS_NAME = "sportsos_prefs"
private const val KEY_PERMISSION_EVER_REQUESTED = "notif_permission_requested"

// POST_NOTIFICATIONS is API 33+; every reference to it below is already runtime-guarded
// behind an SDK_INT >= TIRAMISU check, so the constant itself is safe on older devices.
@SuppressLint("InlinedApi")
class MainActivity : ComponentActivity() {

    private var webViewRef: WebView? = null
    private var pendingBookingId: String? = null
    private lateinit var permissionLauncher: ActivityResultLauncher<String>

    // Drives the in-app nudge dialog. Compose state so a permission-check result triggers
    // recomposition regardless of which lifecycle callback (onCreate vs onResume) found it.
    private val promptAction = mutableStateOf<NotificationPromptAction?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pendingBookingId = intent.getStringExtra(EXTRA_BOOKING_ID)

        // Must be registered before STARTED — do this ahead of setContent.
        permissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) fetchAndRegisterPushToken()
        }

        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    val webView = webViewRef
                    if (webView != null && webView.canGoBack()) {
                        webView.goBack()
                    } else {
                        isEnabled = false
                        onBackPressedDispatcher.onBackPressed()
                    }
                }
            }
        )

        enableEdgeToEdge()
        setContent {
            SportsosTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    AndroidView(
                        modifier = Modifier.fillMaxSize().padding(innerPadding),
                        factory = { context -> buildWebView(context) },
                    )
                }

                val action by promptAction
                if (action != null) {
                    NotificationPromptDialog(
                        action = action!!,
                        onDismiss = { promptAction.value = null },
                        onConfirm = {
                            promptAction.value = null
                            when (action) {
                                NotificationPromptAction.REQUEST_PERMISSION -> {
                                    markPermissionRequested()
                                    permissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                                }
                                NotificationPromptAction.OPEN_SETTINGS -> openAppNotificationSettings()
                                null -> Unit
                            }
                        }
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        checkNotificationsEnabled()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        val bookingId = intent.getStringExtra(EXTRA_BOOKING_ID) ?: return
        webViewRef?.loadUrl("${BuildConfig.SPORTS_OS_BASE_URL}/bookings/$bookingId")
    }

    /** Checks whether notifications are enabled for this app (covers both the runtime
     * permission on API 33+ and the plain Settings toggle on older versions) and asks again
     * if not — a real system prompt while one is still available, otherwise an in-app nudge
     * pointing at Settings, since the system dialog stops appearing after it's been denied. */
    private fun checkNotificationsEnabled() {
        if (NotificationManagerCompat.from(this).areNotificationsEnabled()) {
            fetchAndRegisterPushToken()
            return
        }

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            // No runtime permission pre-Android 13 — only the Settings toggle controls this.
            promptAction.value = NotificationPromptAction.OPEN_SETTINGS
            return
        }

        val permission = Manifest.permission.POST_NOTIFICATIONS
        promptAction.value = when {
            ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED ->
                // Permission granted but notifications still report disabled (e.g. channel
                // blocked) — re-requesting the permission won't fix that.
                NotificationPromptAction.OPEN_SETTINGS
            shouldShowRequestPermissionRationale(permission) -> NotificationPromptAction.REQUEST_PERMISSION
            !hasRequestedPermissionBefore() -> {
                // First ever launch — go straight to the system dialog, no need for our own
                // rationale first.
                markPermissionRequested()
                permissionLauncher.launch(permission)
                null
            }
            else -> NotificationPromptAction.OPEN_SETTINGS
        }
    }

    private fun hasRequestedPermissionBefore(): Boolean =
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE).getBoolean(KEY_PERMISSION_EVER_REQUESTED, false)

    private fun markPermissionRequested() {
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE).edit {
            putBoolean(KEY_PERMISSION_EVER_REQUESTED, true)
        }
    }

    private fun openAppNotificationSettings() {
        // minSdk is 30, which is already past the API 26 cutoff for ACTION_APP_NOTIFICATION_SETTINGS.
        val settingsIntent = Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
            .putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
        startActivity(settingsIntent)
    }

    private fun fetchAndRegisterPushToken() {
        if (FirebaseApp.getApps(this).isEmpty()) return // Firebase not configured — no-op.
        lifecycleScope.launch {
            try {
                val token = FirebaseMessaging.getInstance().token.await()
                PushTokenRegistrar.register(token)
            } catch (e: Exception) {
                // Best-effort — a failed registration just means no push until the next
                // successful attempt (next resume/page load).
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun buildWebView(context: Context): WebView {
        CookieManager.getInstance().setAcceptCookie(true)
        return WebView(context).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)

            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                    val uri = request.url
                    if (uri.scheme == "http" || uri.scheme == "https") return false
                    return try {
                        startActivity(Intent(Intent.ACTION_VIEW, uri))
                        true
                    } catch (e: Exception) {
                        true // no app can handle it (e.g. tel:/mailto: on a device without one) — swallow
                    }
                }

                override fun onPageFinished(view: WebView, url: String?) {
                    super.onPageFinished(view, url)
                    CookieManager.getInstance().flush()
                    // A session cookie may only just have been set by a fresh login — try
                    // registering the push token again now that one might exist.
                    fetchAndRegisterPushToken()
                }
            }

            webViewRef = this
            val startUrl = pendingBookingId?.let { "${BuildConfig.SPORTS_OS_BASE_URL}/bookings/$it" }
                ?: BuildConfig.SPORTS_OS_BASE_URL
            pendingBookingId = null
            loadUrl(startUrl)
        }
    }

    companion object {
        const val EXTRA_BOOKING_ID = "booking_id"
    }
}

@Composable
private fun NotificationPromptDialog(
    action: NotificationPromptAction,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Turn on notifications") },
        text = {
            Text(
                if (action == NotificationPromptAction.REQUEST_PERMISSION)
                    "Get notified about match invites, booking updates, and open slots."
                else
                    "Notifications are off for SportsOS. Enable them in Settings to get match invites, booking updates, and open slots."
            )
        },
        confirmButton = {
            Button(onClick = onConfirm) {
                Text(if (action == NotificationPromptAction.REQUEST_PERMISSION) "Allow" else "Open Settings")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Not now") }
        }
    )
}
