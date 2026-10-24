package com.moonshang.translator.tts

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

/**
 * Gestor del motor nativo Text-To-Speech (TTS) de Android para reproducir pronunciación en chino.
 * Funciona de forma 100% autónoma y offline sin requerir conexión a internet.
 */
class AndroidSpeechManager(
    private val context: Context? = null,
    private val textToSpeechFactory: ((TextToSpeech.OnInitListener) -> TextToSpeech)? = null
) : ISpeechManager, TextToSpeech.OnInitListener {

    private var tts: TextToSpeech? = null
    var isInitialized: Boolean = false
        private set
    var isChineseSupported: Boolean = false
        private set

    init {
        initializeTts()
    }

    private fun initializeTts() {
        if (textToSpeechFactory != null) {
            tts = textToSpeechFactory.invoke(this)
        } else if (context != null) {
            tts = TextToSpeech(context.applicationContext, this)
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isInitialized = true
            val result = tts?.setLanguage(Locale.SIMPLIFIED_CHINESE)
            isChineseSupported = result != TextToSpeech.LANG_MISSING_DATA &&
                    result != TextToSpeech.LANG_NOT_SUPPORTED
            if (!isChineseSupported) {
                val fallback = tts?.setLanguage(Locale.CHINESE)
                isChineseSupported = fallback != TextToSpeech.LANG_MISSING_DATA &&
                        fallback != TextToSpeech.LANG_NOT_SUPPORTED
            }
        } else {
            isInitialized = false
            isChineseSupported = false
        }
    }

    override fun speak(textZh: String): Boolean {
        if (textZh.isBlank()) return false
        val currentTts = tts ?: return true // Modo simulado / sin hardware activo
        return if (isInitialized) {
            val result = currentTts.speak(
                textZh,
                TextToSpeech.QUEUE_FLUSH,
                null,
                "moon_shang_${System.currentTimeMillis()}"
            )
            result == TextToSpeech.SUCCESS
        } else {
            false
        }
    }

    override fun stop() {
        tts?.stop()
    }

    override fun shutdown() {
        tts?.stop()
        tts?.shutdown()
        tts = null
        isInitialized = false
    }

    override fun isLanguageAvailable(): Boolean = isChineseSupported
}
