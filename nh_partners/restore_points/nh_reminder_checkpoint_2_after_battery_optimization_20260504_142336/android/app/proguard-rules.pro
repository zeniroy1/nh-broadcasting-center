# flutter_local_notifications uses Gson TypeToken for cached notification data.
# Preserve generic signatures if release shrinking is enabled later.
-keepattributes Signature
-keep class com.google.gson.reflect.TypeToken { *; }
-keep class * extends com.google.gson.reflect.TypeToken
-keep class com.dexterous.flutterlocalnotifications.models.** { *; }
