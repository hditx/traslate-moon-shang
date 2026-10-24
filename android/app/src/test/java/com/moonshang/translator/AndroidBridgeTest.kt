package com.moonshang.translator

import com.moonshang.translator.bridge.AndroidBridge
import com.moonshang.translator.data.LocalDictionaryHelper
import com.moonshang.translator.model.BoundingBox
import com.moonshang.translator.model.DetectedToken
import com.moonshang.translator.model.PageData
import com.moonshang.translator.ocr.IOcrEngine
import com.moonshang.translator.tts.ISpeechManager
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.json.JSONObject
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class AndroidBridgeTest {

    @Test
    fun testOpenFileDialogReturnsValidJson() {
        val bridge = AndroidBridge()
        val jsonStr = bridge.openFileDialog()

        assertNotNull(jsonStr)
        val json = JSONObject(jsonStr!!)
        assertTrue(json.has("filePath"))
        assertTrue(json.has("filename"))
        assertTrue(json.getString("filename").isNotEmpty())

        // Verificar alias snake_case
        assertEquals(jsonStr, bridge.open_file_dialog())
    }

    @Test
    fun testGetDocumentInfoDetectsFileType() {
        val bridge = AndroidBridge()

        val pdfJsonStr = bridge.getDocumentInfo("/path/to/test.pdf")
        val pdfJson = JSONObject(pdfJsonStr)
        assertEquals("test.pdf", pdfJson.getString("filename"))
        assertEquals("pdf", pdfJson.getString("fileType"))

        val imgJsonStr = bridge.getDocumentInfo("/path/to/image.png")
        val imgJson = JSONObject(imgJsonStr)
        assertEquals("image", imgJson.getString("fileType"))
    }

    @Test
    fun testProcessPageReturnsValidStructure() {
        val mockOcr = mockk<IOcrEngine>()
        val expectedPage = PageData(
            pageNumber = 2,
            width = 1000,
            height = 1500,
            imageUrl = "/path/doc.png",
            tokens = listOf(
                DetectedToken(
                    id = "tok_1",
                    textZh = "月",
                    pinyin = "yuè",
                    translationEs = "luna, mes",
                    box = BoundingBox(10.0, 20.0, 50.0, 60.0)
                )
            )
        )
        kotlinx.coroutines.runBlocking {
            every { kotlinx.coroutines.runBlocking { mockOcr.processImage(any(), any()) } } returns expectedPage
        }

        val bridge = AndroidBridge(ocrEngine = mockOcr)
        val jsonStr = bridge.processPage("/path/doc.png", 2)

        val json = JSONObject(jsonStr)
        assertEquals(2, json.getInt("pageNumber"))
        assertEquals(1000, json.getInt("width"))
        assertEquals(1500, json.getInt("height"))
        val tokens = json.getJSONArray("tokens")
        assertEquals(1, tokens.length())
        assertEquals("月", tokens.getJSONObject(0).getString("textZh"))
    }

    @Test
    fun testTranslateTokenAndPinyinWithLocalDictionary() {
        val dictionary = LocalDictionaryHelper()
        val bridge = AndroidBridge(dictionaryHelper = dictionary)

        assertEquals("jiào", bridge.getPinyin("窖"))
        assertEquals("nǐ", bridge.getPinyin("你"))
        assertEquals("hǎo", bridge.getPinyin("好"))

        val transJsonStr = bridge.translateToken("你好")
        val json = JSONObject(transJsonStr)
        assertEquals("你好", json.getString("textZh"))
        assertEquals("hola", json.getString("translationEs"))
        assertEquals("nǐ hǎo", json.getString("pinyin"))
        assertTrue(json.getBoolean("fromCache"))
    }

    @Test
    fun testCustomHandlersInjection() {
        val bridge = AndroidBridge(
            onOpenFileRequest = {
                JSONObject().put("filePath", "/custom/file.pdf").toString()
            },
            onPinyinRequest = { "custom_pinyin" }
        )

        val fileJson = JSONObject(bridge.openFileDialog()!!)
        assertEquals("/custom/file.pdf", fileJson.getString("filePath"))
        assertEquals("custom_pinyin", bridge.getPinyin("cualquiera"))
    }

    @Test
    fun testAudioAndClipboardMethods() {
        val mockSpeech = mockk<ISpeechManager>(relaxed = true)
        every { mockSpeech.speak("你好") } returns true

        val bridge = AndroidBridge(speechManager = mockSpeech)
        assertTrue(bridge.copyToClipboard("Hola"))
        assertTrue(bridge.playAudio("你好"))
        verify { mockSpeech.speak("你好") }
        assertTrue(bridge.playPronunciation("你好"))
    }

    @Test
    fun testOperatingModeAndOnlineStatus() {
        val bridge = AndroidBridge()
        assertEquals("auto", bridge.getOperatingMode())
        assertEquals("auto", bridge.get_operating_mode())

        bridge.setOperatingMode("offline")
        assertEquals("force_offline", bridge.getOperatingMode())
        assertEquals(false, bridge.isOnline())
        assertEquals(false, bridge.is_online())

        bridge.setOperatingMode("online")
        assertEquals("force_online", bridge.getOperatingMode())
        assertEquals(true, bridge.isOnline())
    }
}
