package com.moonshang.translator.integration

import com.moonshang.translator.bridge.AndroidBridge
import com.moonshang.translator.data.LocalDictionaryHelper
import com.moonshang.translator.model.BoundingBox
import com.moonshang.translator.model.DetectedToken
import com.moonshang.translator.model.PageData
import com.moonshang.translator.net.NetworkDetector
import com.moonshang.translator.ocr.IOcrEngine
import com.moonshang.translator.ocr.RemoteOcrEngine
import com.moonshang.translator.ocr.SmartHybridOcrEngine
import io.mockk.coEvery
import io.mockk.mockk
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.json.JSONObject
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.io.File

class AndroidSecurityIntegrationTest {

    private lateinit var server: MockWebServer

    @BeforeEach
    fun setUp() {
        server = MockWebServer()
        server.start()
    }

    @AfterEach
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun testRejectsPathTraversalAttacks() {
        val bridge = AndroidBridge()

        val attacks = listOf(
            "/etc/passwd.pdf",
            "/proc/version.png",
            "/sys/class/net/eth0.jpg",
            "/dev/null.pdf",
            "/storage/safe.png\u0000.exe"
        )

        for (path in attacks) {
            val pageJsonStr = bridge.processPage(path, 1)
            val json = JSONObject(pageJsonStr)
            // Debe retornar tokens vacíos y no procesar la ruta insegura
            assertEquals(0, json.getJSONArray("tokens").length())
            assertEquals("", json.getString("imageUrl"))

            val infoJsonStr = bridge.getDocumentInfo(path)
            val infoJson = JSONObject(infoJsonStr)
            assertEquals("error", infoJson.getString("id"))
            assertEquals("archivo_inseguro", infoJson.getString("filename"))
        }
    }

    @Test
    fun testRejectsDangerousFileExtensions() {
        val bridge = AndroidBridge()
        val dangerousFiles = listOf(
            "/storage/emulated/0/Download/exploit.exe",
            "/storage/emulated/0/Download/script.sh",
            "/storage/emulated/0/Download/payload.bat",
            "/storage/emulated/0/Download/hack.apk"
        )

        for (path in dangerousFiles) {
            val pageJsonStr = bridge.processPage(path, 1)
            val json = JSONObject(pageJsonStr)
            assertEquals(0, json.getJSONArray("tokens").length())
        }
    }

    @Test
    fun testEndToEndFailoverPipelineFromRemoteToOffline() {
        // Simular que el servidor FastAPI devuelve un error 500
        server.enqueue(
            MockResponse()
                .setResponseCode(500)
                .setBody("Internal Server Error")
        )

        val tempImage = File.createTempFile("sample_e2e", ".png")
        tempImage.writeBytes(byteArrayOf(0x89.toByte(), 0x50, 0x4E, 0x47))

        try {
            val baseUrl = server.url("/").toString()
            val detector = NetworkDetector(
                serverBaseUrl = baseUrl,
                connectionProvider = { true }
            )
            // Forzar modo online para probar el fallback ante fallo
            detector.mode = com.moonshang.translator.net.OperatingMode.FORCE_ONLINE

            val remoteOcr = RemoteOcrEngine(serverBaseUrl = baseUrl)
            val mockOfflineOcr = mockk<IOcrEngine>()
            val offlineFallbackData = PageData(
                pageNumber = 1,
                width = 800,
                height = 1200,
                imageUrl = tempImage.absolutePath,
                tokens = listOf(
                    DetectedToken(
                        id = "tok_fallback",
                        textZh = "学",
                        pinyin = "xué",
                        translationEs = "estudiar",
                        box = BoundingBox(10.0, 10.0, 50.0, 50.0)
                    )
                )
            )
            coEvery { mockOfflineOcr.processImage(any(), any()) } returns offlineFallbackData

            val hybridEngine = SmartHybridOcrEngine(
                remoteEngine = remoteOcr,
                offlineEngine = mockOfflineOcr,
                networkDetector = detector
            )

            val bridge = AndroidBridge(
                ocrEngine = hybridEngine,
                networkDetector = detector
            )

            // Procesar página: el servidor falla con 500 pero el hybrid engine conmuta transparentemente a offline
            val resultJsonStr = bridge.processPage(tempImage.absolutePath, 1)
            val json = JSONObject(resultJsonStr)

            assertEquals(1, json.getJSONArray("tokens").length())
            val token = json.getJSONArray("tokens").getJSONObject(0)
            assertEquals("学", token.getString("textZh"))
            assertEquals("estudiar", token.getString("translationEs"))
            assertEquals("offline_fallback", hybridEngine.lastUsedEngine)
        } finally {
            tempImage.delete()
        }
    }

    @Test
    fun testSpecialCharactersAndFuzzingInputs() {
        val dictionary = LocalDictionaryHelper()
        val bridge = AndroidBridge(dictionaryHelper = dictionary)

        // Entradas con símbolos, caracteres de control, emojis
        val edgeCases = listOf(
            "<script>alert('xss')</script>",
            "'; DROP TABLE words; --",
            "   \t\n\r   ",
            "🚀🔥💯",
            "A".repeat(2000)
        )

        for (input in edgeCases) {
            // Verificar que no lance excepciones no controladas
            val transJsonStr = bridge.translateToken(input)
            val json = JSONObject(transJsonStr)
            assertTrue(json.has("textZh"))
            assertTrue(json.has("translationEs"))
            assertTrue(json.has("pinyin"))

            val pinyin = bridge.getPinyin(input)
            if (input.isNotBlank()) {
                assertTrue(pinyin.isNotBlank())
            } else {
                assertTrue(pinyin.isBlank())
            }
        }
    }
}
