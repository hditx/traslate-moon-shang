package com.moonshang.translator

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewClientCompat
import com.moonshang.translator.bridge.AndroidBridge
import com.moonshang.translator.camera.CameraCaptureHelper
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import java.io.File

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader

    private var pendingPhotoCallback: ((Boolean) -> Unit)? = null
    private var pendingPermissionCallback: ((Boolean) -> Unit)? = null
    private var currentPhotoUri: Uri? = null
    private var currentPhotoFile: File? = null

    private val takePictureLauncher = registerForActivityResult(
        ActivityResultContracts.TakePicture()
    ) { success ->
        pendingPhotoCallback?.invoke(success)
        pendingPhotoCallback = null
    }

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        pendingPermissionCallback?.invoke(isGranted)
        pendingPermissionCallback = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)

        // Configurar cargador seguro de assets para evitar problemas de CORS y file:///
        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            loadWithOverviewMode = true
            useWideViewPort = true
        }

        // Registrar el puente nativo con los identificadores esperados por Vue 3: "androidApi" y "AndroidBridge"
        val bridge = AndroidBridge(
            context = this,
            onCapturePhotoRequest = { capturePhotoSync() }
        )
        webView.addJavascriptInterface(bridge, "androidApi")
        webView.addJavascriptInterface(bridge, "AndroidBridge")

        webView.webViewClient = object : WebViewClientCompat() {
            override fun shouldInterceptRequest(
                view: WebView?,
                request: WebResourceRequest?
            ): WebResourceResponse? {
                return request?.url?.let { assetLoader.shouldInterceptRequest(it) }
            }
        }

        // Manejar botón atrás nativo de Android
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    finish()
                }
            }
        })

        // Cargar frontend Vue empaquetado en assets/index.html
        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    /**
     * Invocado de manera síncrona desde el hilo de fondo de JavaScriptBridge.
     * Despacha el intent de cámara en el hilo principal y espera la respuesta del usuario.
     */
    private fun capturePhotoSync(): String? {
        val deferred = CompletableDeferred<String?>()

        runOnUiThread {
            requestCameraAndLaunch(deferred)
        }

        return runBlocking {
            withTimeoutOrNull(180_000) { // 3 minutos de timeout para captura
                deferred.await()
            }
        }
    }

    private fun requestCameraAndLaunch(deferred: CompletableDeferred<String?>) {
        val hasPermission = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED

        if (!hasPermission) {
            pendingPermissionCallback = { granted ->
                if (granted) {
                    launchCameraCapture(deferred)
                } else {
                    deferred.complete(null)
                }
            }
            requestPermissionLauncher.launch(Manifest.permission.CAMERA)
        } else {
            launchCameraCapture(deferred)
        }
    }

    private fun launchCameraCapture(deferred: CompletableDeferred<String?>) {
        try {
            val photoFile = CameraCaptureHelper.createTempImageFile(this)
            val photoUri = CameraCaptureHelper.getUriForFile(this, photoFile)
            currentPhotoFile = photoFile
            currentPhotoUri = photoUri

            pendingPhotoCallback = { success ->
                if (success && photoFile.exists() && photoFile.length() > 0L) {
                    val processedFile = CameraCaptureHelper.correctOrientationAndCompress(photoFile)
                    val result = JSONObject().apply {
                        put("filePath", processedFile.absolutePath)
                        put("filename", processedFile.name)
                    }.toString()
                    deferred.complete(result)
                } else {
                    if (photoFile.exists()) {
                        photoFile.delete()
                    }
                    deferred.complete(null)
                }
            }

            takePictureLauncher.launch(photoUri)
        } catch (e: Exception) {
            deferred.complete(null)
        }
    }
}
