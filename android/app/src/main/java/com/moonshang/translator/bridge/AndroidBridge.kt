package com.moonshang.translator.bridge

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.webkit.JavascriptInterface
import com.moonshang.translator.data.LocalDictionaryHelper
import com.moonshang.translator.model.DocumentData
import com.moonshang.translator.model.PageData
import com.moonshang.translator.net.INetworkDetector
import com.moonshang.translator.net.NetworkDetector
import com.moonshang.translator.net.OperatingMode
import com.moonshang.translator.net.RemoteTranslatorClient
import com.moonshang.translator.ocr.IOcrEngine
import com.moonshang.translator.ocr.MlKitOcrEngine
import com.moonshang.translator.ocr.RemoteOcrEngine
import com.moonshang.translator.ocr.SmartHybridOcrEngine
import com.moonshang.translator.tts.AndroidSpeechManager
import com.moonshang.translator.tts.ISpeechManager
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import java.io.File

/**
 * Puente nativo expuesto a JavaScript en el WebView mediante addJavascriptInterface("androidApi").
 * Implementa el contrato esperado por IDesktopBridge en el frontend Vue 3 conectando con
 * el motor híbrido inteligente (Online con FastAPI / PaddleOCR + Offline con ML Kit / SQLite).
 */
class AndroidBridge(
    private val context: Context? = null,
    private val dictionaryHelper: LocalDictionaryHelper = LocalDictionaryHelper(context),
    val networkDetector: INetworkDetector = NetworkDetector(context),
    private val remoteTranslatorClient: RemoteTranslatorClient = RemoteTranslatorClient(),
    val ocrEngine: IOcrEngine = SmartHybridOcrEngine(
        remoteEngine = RemoteOcrEngine(),
        offlineEngine = MlKitOcrEngine(context, dictionaryHelper),
        networkDetector = networkDetector
    ),
    private val speechManager: ISpeechManager = AndroidSpeechManager(context),
    private val onOpenFileRequest: (() -> String?)? = null,
    private val onProcessPageRequest: ((String, Int) -> String)? = null,
    private val onTranslateTokenRequest: ((String) -> String)? = null,
    private val onPinyinRequest: ((String) -> String)? = null,
    private val onPlayAudioRequest: ((String) -> Boolean)? = null
) {

    @JavascriptInterface
    fun openFileDialog(): String? {
        if (onOpenFileRequest != null) {
            return onOpenFileRequest.invoke()
        }
        val candidates = listOf(
            File(context?.filesDir, "test.png"),
            File("/storage/emulated/0/Download/test.png"),
            File(context?.filesDir, "documento_chino.png"),
            File("/storage/emulated/0/Download/documento_chino.png"),
            File(context?.filesDir, "documento_chino.pdf"),
            File("/storage/emulated/0/Download/documento_chino.pdf")
        )
        val target = candidates.firstOrNull { it.exists() }
        val targetPath = target?.absolutePath ?: (context?.filesDir?.absolutePath + "/test.png")
        val targetName = target?.name ?: "test.png"

        val obj = JSONObject().apply {
            put("filePath", targetPath)
            put("filename", targetName)
        }
        return obj.toString()
    }

    @JavascriptInterface
    fun open_file_dialog(): String? = openFileDialog()

    companion object {
        val ALLOWED_EXTENSIONS = setOf("pdf", "png", "jpg", "jpeg", "webp")
        val FORBIDDEN_PREFIXES = listOf("/proc", "/sys", "/etc", "/dev")
    }

    private fun isPathSafe(filePath: String): Boolean {
        val clean = filePath.trim()
        if (clean.isBlank() || clean.contains('\u0000')) return false
        val ext = clean.substringAfterLast('.', "").lowercase()
        if (ext !in ALLOWED_EXTENSIONS) return false

        val file = java.io.File(clean)
        val canonical = try {
            file.canonicalPath
        } catch (_: Exception) {
            return false
        }

        for (prefix in FORBIDDEN_PREFIXES) {
            if (canonical.startsWith(prefix)) return false
        }
        return true
    }

    @JavascriptInterface
    fun getDocumentInfo(filePath: String): String {
        if (!isPathSafe(filePath)) {
            val emptyDoc = DocumentData(
                id = "error",
                filename = "archivo_inseguro",
                fileType = "image",
                totalPages = 1,
                currentPage = 1,
                pages = emptyList()
            )
            return emptyDoc.toJSONObject().toString()
        }
        val filename = filePath.substringAfterLast('/')
        val fileType = if (filePath.endsWith(".pdf", ignoreCase = true)) "pdf" else "image"
        val docData = DocumentData(
            id = filename,
            filename = filename,
            fileType = fileType,
            totalPages = 1,
            currentPage = 1,
            pages = emptyList()
        )
        return docData.toJSONObject().toString()
    }

    @JavascriptInterface
    fun get_document_info(filePath: String): String = getDocumentInfo(filePath)

    @JavascriptInterface
    fun processPage(filePath: String, pageNumber: Int): String {
        if (onProcessPageRequest != null) {
            return onProcessPageRequest.invoke(filePath, pageNumber)
        }
        if (!isPathSafe(filePath)) {
            return PageData(
                pageNumber = pageNumber,
                width = 800,
                height = 1200,
                imageUrl = "",
                tokens = emptyList()
            ).toJSONObject().toString()
        }
        return try {
            val pageData = runBlocking {
                ocrEngine.processImage(filePath, pageNumber)
            }
            pageData.toJSONObject().toString()
        } catch (e: Exception) {
            PageData(
                pageNumber = pageNumber,
                width = 800,
                height = 1200,
                imageUrl = filePath,
                tokens = emptyList()
            ).toJSONObject().toString()
        }
    }

    @JavascriptInterface
    fun process_page(filePath: String, pageNumber: Int): String = processPage(filePath, pageNumber)

    @JavascriptInterface
    fun translateToken(textZh: String): String {
        if (onTranslateTokenRequest != null) {
            return onTranslateTokenRequest.invoke(textZh)
        }

        val cleaned = textZh.trim().trimStart('|', ' ', '“', '”', '：', ':').trim()

        // 1. Coincidencia exacta directa en diccionario local
        val exactLocal = dictionaryHelper.getExact(cleaned)
        if (exactLocal != null) {
            return exactLocal.toJSONObject().toString()
        }

        // 2. Si hay conexión de red y no estamos en FORCE_OFFLINE, consultar motor remoto / web
        val canUseNetwork = networkDetector.mode != OperatingMode.FORCE_OFFLINE && networkDetector.isNetworkConnected()
        if (canUseNetwork) {
            val remoteResult = runBlocking {
                try { remoteTranslatorClient.translate(cleaned) } catch (_: Exception) { null }
            }
            if (remoteResult != null && remoteResult.translationEs.isNotBlank()) {
                val pinyin = if (remoteResult.pinyin.isNotBlank()) remoteResult.pinyin else dictionaryHelper.getPinyin(cleaned)
                return remoteResult.copy(textZh = cleaned, pinyin = pinyin).toJSONObject().toString()
            }
        }

        // 3. Fallback a diccionario local descompuesto
        val localResult = dictionaryHelper.translate(cleaned)
        return localResult.copy(textZh = cleaned).toJSONObject().toString()
    }

    @JavascriptInterface
    fun translate_token(textZh: String): String = translateToken(textZh)

    @JavascriptInterface
    fun copyToClipboard(text: String): Boolean {
        return try {
            if (context != null) {
                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
                val clip = ClipData.newPlainText("Traducción Moon Shang", text)
                clipboard?.setPrimaryClip(clip)
                true
            } else {
                true
            }
        } catch (e: Exception) {
            false
        }
    }

    @JavascriptInterface
    fun copy_to_clipboard(text: String): Boolean = copyToClipboard(text)

    @JavascriptInterface
    fun getPinyin(textZh: String): String {
        if (onPinyinRequest != null) {
            return onPinyinRequest.invoke(textZh)
        }

        val isOnline = runBlocking {
            try { networkDetector.isOnline() } catch (_: Exception) { false }
        }

        if (isOnline) {
            val remotePinyin = runBlocking {
                try { remoteTranslatorClient.getPinyin(textZh) } catch (_: Exception) { null }
            }
            if (!remotePinyin.isNullOrBlank()) {
                return remotePinyin
            }
        }

        return dictionaryHelper.getPinyin(textZh)
    }

    @JavascriptInterface
    fun get_pinyin(textZh: String): String = getPinyin(textZh)

    @JavascriptInterface
    fun playAudio(textZh: String): Boolean {
        if (onPlayAudioRequest != null) {
            return onPlayAudioRequest.invoke(textZh)
        }
        return speechManager.speak(textZh)
    }

    @JavascriptInterface
    fun play_audio(textZh: String): Boolean = playAudio(textZh)

    @JavascriptInterface
    fun playPronunciation(textZh: String): Boolean = playAudio(textZh)

    @JavascriptInterface
    fun play_pronunciation(textZh: String): Boolean = playAudio(textZh)

    @JavascriptInterface
    fun getOperatingMode(): String {
        return when (networkDetector.mode) {
            OperatingMode.FORCE_ONLINE -> "force_online"
            OperatingMode.FORCE_OFFLINE -> "force_offline"
            OperatingMode.AUTO -> "auto"
        }
    }

    @JavascriptInterface
    fun get_operating_mode(): String = getOperatingMode()

    @JavascriptInterface
    fun isOnline(): Boolean {
        return runBlocking {
            try { networkDetector.isOnline() } catch (_: Exception) { false }
        }
    }

    @JavascriptInterface
    fun is_online(): Boolean = isOnline()

    @JavascriptInterface
    fun setOperatingMode(modeStr: String): Boolean {
        networkDetector.mode = when (modeStr.lowercase()) {
            "online", "force_online" -> OperatingMode.FORCE_ONLINE
            "offline", "force_offline" -> OperatingMode.FORCE_OFFLINE
            else -> OperatingMode.AUTO
        }
        return true
    }

    @JavascriptInterface
    fun set_operating_mode(modeStr: String): Boolean = setOperatingMode(modeStr)
}
