// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    // Applied conditionally in app/build.gradle.kts — only once google-services.json exists,
    // so the build doesn't hard-fail before Firebase/FCM is configured for this app.
    alias(libs.plugins.google.services) apply false
}