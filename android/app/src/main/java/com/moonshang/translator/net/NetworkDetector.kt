package com.moonshang.translator.net

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Detector de red y disponibilidad del servidor backend FastAPI.
 * Permite alternancia automática e inteligente entre modo Online y Offline.
 */
class NetworkDetector(
    private val context: Context? = null,
    var serverBaseUrl: String = "http://10.0.2.2:8000",
    private val httpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(1500, TimeUnit.MILLISECONDS)
        .readTimeout(1500, TimeUnit.MILLISECONDS)
        .build(),
    private val connectionProvider: (() -> Boolean)? = null
) : INetworkDetector {

    override var mode: OperatingMode = OperatingMode.AUTO

    /**
     * Comprueba si el dispositivo tiene una interfaz de red activa con salida a Internet.
     */
    override fun isNetworkConnected(): Boolean {
        if (connectionProvider != null) {
            return connectionProvider.invoke()
        }

        if (context == null) return true

        val connectivityManager =
            context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
                ?: return false

        val activeNetwork = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(activeNetwork) ?: return false

        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    /**
     * Realiza un health-check rápido contra el endpoint /health del servidor backend.
     */
    override suspend fun isServerReachable(): Boolean = withContext(Dispatchers.IO) {
        val healthUrl = "${serverBaseUrl.trimEnd('/')}/health"
        val request = Request.Builder()
            .url(healthUrl)
            .get()
            .build()

        try {
            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val bodyStr = response.body?.string() ?: ""
                    val json = JSONObject(bodyStr)
                    json.optString("status") == "healthy"
                } else {
                    false
                }
            }
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Determina si la aplicación debe operar en modo Online considerando el modo configurado,
     * la conexión de red y la respuesta del servidor.
     */
    override suspend fun isOnline(): Boolean {
        return when (mode) {
            OperatingMode.FORCE_OFFLINE -> false
            OperatingMode.FORCE_ONLINE -> true
            OperatingMode.AUTO -> isNetworkConnected() && isServerReachable()
        }
    }
}
