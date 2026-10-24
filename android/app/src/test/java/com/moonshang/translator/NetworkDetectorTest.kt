package com.moonshang.translator

import com.moonshang.translator.net.NetworkDetector
import com.moonshang.translator.net.OperatingMode
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class NetworkDetectorTest {

    private lateinit var server: MockWebServer
    private lateinit var detector: NetworkDetector

    @BeforeEach
    fun setUp() {
        server = MockWebServer()
        server.start()
        val baseUrl = server.url("/").toString()
        detector = NetworkDetector(
            serverBaseUrl = baseUrl,
            connectionProvider = { true }
        )
    }

    @AfterEach
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun testServerReachableWhenHealthy() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"status": "healthy", "paddle_ocr_available": true}""")
        )

        assertTrue(detector.isServerReachable())
    }

    @Test
    fun testServerUnreachableWhenErrorOrDown() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(500)
                .setBody("Internal Server Error")
        )

        assertFalse(detector.isServerReachable())
    }

    @Test
    fun testIsOnlineWithAutoMode() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"status": "healthy"}""")
        )

        detector.mode = OperatingMode.AUTO
        assertTrue(detector.isOnline())
    }

    @Test
    fun testIsOnlineWhenNetworkDisconnected() = runTest {
        val disconnectedDetector = NetworkDetector(
            serverBaseUrl = server.url("/").toString(),
            connectionProvider = { false }
        )
        disconnectedDetector.mode = OperatingMode.AUTO
        assertFalse(disconnectedDetector.isOnline())
    }

    @Test
    fun testForcedModes() = runTest {
        // En FORCE_OFFLINE debe retornar false incluso si el servidor responde
        detector.mode = OperatingMode.FORCE_OFFLINE
        assertFalse(detector.isOnline())

        // En FORCE_ONLINE debe retornar true
        detector.mode = OperatingMode.FORCE_ONLINE
        assertTrue(detector.isOnline())
    }

    @Test
    fun testInitialProperties() {
        assertEquals(OperatingMode.AUTO, detector.mode)
        assertTrue(detector.isNetworkConnected())
    }
}
