package com.moonshang.translator

import android.speech.tts.TextToSpeech
import com.moonshang.translator.tts.AndroidSpeechManager
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.util.Locale

class AndroidSpeechManagerTest {

    @Test
    fun testInitializationSuccessWithChineseLocale() {
        val mockTts = mockk<TextToSpeech>(relaxed = true)
        every { mockTts.setLanguage(Locale.SIMPLIFIED_CHINESE) } returns TextToSpeech.LANG_AVAILABLE

        lateinit var listener: TextToSpeech.OnInitListener
        val manager = AndroidSpeechManager(
            textToSpeechFactory = {
                listener = it
                mockTts
            }
        )

        // Simular callback de inicialización de Android TTS
        listener.onInit(TextToSpeech.SUCCESS)

        assertTrue(manager.isInitialized)
        assertTrue(manager.isChineseSupported)
        assertTrue(manager.isLanguageAvailable())
    }

    @Test
    fun testSpeakSuccessWhenInitialized() {
        val mockTts = mockk<TextToSpeech>(relaxed = true)
        every { mockTts.setLanguage(any()) } returns TextToSpeech.LANG_AVAILABLE
        every { mockTts.speak(any(), any(), any(), any()) } returns TextToSpeech.SUCCESS

        lateinit var listener: TextToSpeech.OnInitListener
        val manager = AndroidSpeechManager(
            textToSpeechFactory = {
                listener = it
                mockTts
            }
        )
        listener.onInit(TextToSpeech.SUCCESS)

        val result = manager.speak("你好")
        assertTrue(result)
        verify { mockTts.speak("你好", TextToSpeech.QUEUE_FLUSH, null, any()) }
    }

    @Test
    fun testSpeakBlankReturnsFalse() {
        val manager = AndroidSpeechManager()
        assertFalse(manager.speak(""))
        assertFalse(manager.speak("   "))
    }

    @Test
    fun testStopAndShutdown() {
        val mockTts = mockk<TextToSpeech>(relaxed = true)
        lateinit var listener: TextToSpeech.OnInitListener
        val manager = AndroidSpeechManager(
            textToSpeechFactory = {
                listener = it
                mockTts
            }
        )
        listener.onInit(TextToSpeech.SUCCESS)

        manager.stop()
        verify { mockTts.stop() }

        manager.shutdown()
        verify { mockTts.shutdown() }
        assertFalse(manager.isInitialized)
    }
}
