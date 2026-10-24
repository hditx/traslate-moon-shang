package com.moonshang.translator

import com.moonshang.translator.ocr.RemoteOcrEngine
import com.moonshang.translator.ocr.RemoteOcrException
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.io.File

class RemoteOcrEngineTest {

    private lateinit var server: MockWebServer
    private lateinit var engine: RemoteOcrEngine
    private lateinit var tempFile: File

    @BeforeEach
    fun setUp() {
        server = MockWebServer()
        server.start()
        engine = RemoteOcrEngine(serverBaseUrl = server.url("/").toString())

        tempFile = File.createTempFile("sample_zh", ".png")
        tempFile.writeBytes(byteArrayOf(0x89.toByte(), 0x50, 0x4E, 0x47))
    }

    @AfterEach
    fun tearDown() {
        server.shutdown()
        if (tempFile.exists()) tempFile.delete()
    }

    @Test
    fun testProcessImageSuccessWithFastApiContract() = runTest {
        val mockResponseBody = """
            {
                "pageNumber": 1,
                "width": 1024,
                "height": 768,
                "imageUrl": "/storage/mock_page_1.png",
                "tokens": [
                    {
                        "id": "tok_1",
                        "textZh": "中国",
                        "pinyin": "zhōng guó",
                        "translationEs": "China",
                        "box": {
                            "x1": 10.0,
                            "y1": 20.0,
                            "x2": 150.0,
                            "y2": 70.0
                        },
                        "confidence": 0.99
                    }
                ]
            }
        """.trimIndent()

        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(mockResponseBody)
        )

        val pageData = engine.processImage(tempFile.absolutePath, 1)

        val recordedRequest = server.takeRequest()
        assertEquals("POST", recordedRequest.method)
        assertEquals("/api/process-page", recordedRequest.path)
        assertTrue(recordedRequest.headers["Content-Type"]?.startsWith("multipart/form-data") == true)

        assertEquals(1, pageData.pageNumber)
        assertEquals(1024, pageData.width)
        assertEquals(768, pageData.height)
        assertEquals(1, pageData.tokens.size)

        val token = pageData.tokens.first()
        assertEquals("中国", token.textZh)
        assertEquals("zhōng guó", token.pinyin)
        assertEquals("China", token.translationEs)
        assertEquals(10.0, token.box.x1)
        assertEquals(140.0, token.box.width)
    }

    @Test
    fun testProcessImageThrowsRemoteOcrExceptionOnServerError() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(500)
                .setBody("""{"detail": "PaddleOCR execution failed"}""")
        )

        assertThrows(RemoteOcrException::class.java) {
            kotlinx.coroutines.runBlocking {
                engine.processImage(tempFile.absolutePath, 1)
            }
        }
    }

    @Test
    fun testProcessImageNonExistentFileThrows() = runTest {
        assertThrows(RemoteOcrException::class.java) {
            kotlinx.coroutines.runBlocking {
                engine.processImage("/non/existent/image.png", 1)
            }
        }
    }
}
