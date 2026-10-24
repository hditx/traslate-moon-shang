package com.moonshang.translator.tts

interface ISpeechManager {
    fun speak(textZh: String): Boolean
    fun stop()
    fun shutdown()
    fun isLanguageAvailable(): Boolean
}
