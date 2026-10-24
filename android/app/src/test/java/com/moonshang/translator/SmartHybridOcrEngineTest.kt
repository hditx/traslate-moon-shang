package com.moonshang.translator

import com.moonshang.translator.model.BoundingBox
import com.moonshang.translator.model.DetectedToken
import com.moonshang.translator.model.PageData
import com.moonshang.translator.net.INetworkDetector
import com.moonshang.translator.ocr.IOcrEngine
import com.moonshang.translator.ocr.RemoteOcrException
import com.moonshang.translator.ocr.SmartHybridOcrEngine
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class SmartHybridOcrEngineTest {

    private lateinit var remoteEngine: IOcrEngine
    private lateinit var offlineEngine: IOcrEngine
    private lateinit var networkDetector: INetworkDetector
    private lateinit var hybridEngine: SmartHybridOcrEngine

    private val remotePageData = PageData(
        pageNumber = 1,
        width = 1200,
        height = 1600,
        imageUrl = "/remote/path.png",
        tokens = listOf(
            DetectedToken(
                id = "tok_remote_1",
                textZh = "商朝",
                pinyin = "shāng cháo",
                translationEs = "Dinastía Shang",
                box = BoundingBox(10.0, 10.0, 100.0, 50.0)
            )
        )
    )

    private val offlinePageData = PageData(
        pageNumber = 1,
        width = 800,
        height = 1200,
        imageUrl = "/local/path.png",
        tokens = listOf(
            DetectedToken(
                id = "tok_offline_1",
                textZh = "商",
                pinyin = "shāng",
                translationEs = "comercio",
                box = BoundingBox(10.0, 10.0, 50.0, 50.0)
            )
        )
    )

    @BeforeEach
    fun setUp() {
        remoteEngine = mockk()
        offlineEngine = mockk()
        networkDetector = mockk()
        hybridEngine = SmartHybridOcrEngine(
            remoteEngine = remoteEngine,
            offlineEngine = offlineEngine,
            networkDetector = networkDetector
        )
    }

    @Test
    fun testUsesRemoteEngineWhenOnlineAndSuccessful() = runTest {
        coEvery { networkDetector.isOnline() } returns true
        coEvery { remoteEngine.processImage(any(), any()) } returns remotePageData

        val result = hybridEngine.processImage("/path/doc.pdf", 1)

        assertEquals("remote", hybridEngine.lastUsedEngine)
        assertEquals(1, result.pageNumber)
        assertEquals("tok_remote_1", result.tokens.first().id)
        assertEquals("Dinastía Shang", result.tokens.first().translationEs)

        coVerify(exactly = 1) { remoteEngine.processImage("/path/doc.pdf", 1) }
        coVerify(exactly = 0) { offlineEngine.processImage(any(), any()) }
    }

    @Test
    fun testFallsBackToOfflineEngineWhenRemoteFails() = runTest {
        coEvery { networkDetector.isOnline() } returns true
        coEvery { remoteEngine.processImage(any(), any()) } throws RemoteOcrException("Server 500 error")
        coEvery { offlineEngine.processImage(any(), any()) } returns offlinePageData

        val result = hybridEngine.processImage("/path/doc.pdf", 1)

        assertEquals("offline_fallback", hybridEngine.lastUsedEngine)
        assertEquals("tok_offline_1", result.tokens.first().id)
        assertEquals("comercio", result.tokens.first().translationEs)

        coVerify(exactly = 1) { remoteEngine.processImage("/path/doc.pdf", 1) }
        coVerify(exactly = 1) { offlineEngine.processImage("/path/doc.pdf", 1) }
    }

    @Test
    fun testUsesOfflineEngineDirectlyWhenOffline() = runTest {
        coEvery { networkDetector.isOnline() } returns false
        coEvery { offlineEngine.processImage(any(), any()) } returns offlinePageData

        val result = hybridEngine.processImage("/path/doc.pdf", 1)

        assertEquals("offline", hybridEngine.lastUsedEngine)
        assertEquals("tok_offline_1", result.tokens.first().id)

        coVerify(exactly = 0) { remoteEngine.processImage(any(), any()) }
        coVerify(exactly = 1) { offlineEngine.processImage("/path/doc.pdf", 1) }
    }
}
