package com.moonshang.translator

import com.moonshang.translator.data.LocalDictionaryHelper
import com.moonshang.translator.ocr.MlKitOcrEngine
import com.moonshang.translator.ocr.RawOcrElement
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class MlKitOcrEngineTest {

    private lateinit var dictionary: LocalDictionaryHelper
    private lateinit var engine: MlKitOcrEngine

    @BeforeEach
    fun setUp() {
        dictionary = LocalDictionaryHelper()
        engine = MlKitOcrEngine(dictionaryHelper = dictionary)
    }

    @Test
    fun testMapRawElementsToTokensEnrichment() {
        val elements = listOf(
            RawOcrElement(
                text = "你好",
                x1 = 50.0,
                y1 = 100.0,
                x2 = 200.0,
                y2 = 180.0,
                confidence = 0.98
            ),
            RawOcrElement(
                text = "学习中文",
                x1 = 50.0,
                y1 = 220.0,
                x2 = 350.0,
                y2 = 300.0,
                confidence = 0.95
            ),
            RawOcrElement(
                text = "   ", // Blanco, debe descartarse
                x1 = 0.0,
                y1 = 0.0,
                x2 = 10.0,
                y2 = 10.0
            )
        )

        val tokens = engine.mapRawElementsToTokens(elements, dictionary)
        assertEquals(2, tokens.size)

        val token1 = tokens[0]
        assertEquals("tok_1", token1.id)
        assertEquals("你好", token1.textZh)
        assertEquals("nǐ hǎo", token1.pinyin)
        assertEquals("hola", token1.translationEs)
        assertEquals(50.0, token1.box.x1)
        assertEquals(100.0, token1.box.y1)
        assertEquals(200.0, token1.box.x2)
        assertEquals(180.0, token1.box.y2)
        assertEquals(150.0, token1.box.width)
        assertEquals(80.0, token1.box.height)
        assertEquals(0.98, token1.confidence)

        val token2 = tokens[1]
        assertEquals("tok_2", token2.id)
        assertEquals("学习中文", token2.textZh)
        assertEquals("xué xí zhōng wén", token2.pinyin)
        assertTrue(token2.translationEs.contains("estudiar") || token2.translationEs.contains("chino"))
    }

    @Test
    fun testProcessImageWithCustomExtractor() = runTest {
        val customEngine = MlKitOcrEngine(
            dictionaryHelper = dictionary,
            customExtractor = { path, page ->
                listOf(
                    RawOcrElement(
                        text = "中国",
                        x1 = 10.0,
                        y1 = 20.0,
                        x2 = 110.0,
                        y2 = 70.0
                    )
                )
            }
        )

        val pageData = customEngine.processImage("/storage/dummy.png", 1)
        assertEquals(1, pageData.pageNumber)
        assertEquals(800, pageData.width)
        assertEquals(1200, pageData.height)
        assertEquals("/storage/dummy.png", pageData.imageUrl)
        assertEquals(1, pageData.tokens.size)

        val token = pageData.tokens.first()
        assertEquals("中国", token.textZh)
        assertEquals("zhōng guó", token.pinyin)
        assertEquals("China", token.translationEs)
    }

    @Test
    fun testEmptyElementsReturnsEmptyTokens() {
        val tokens = engine.mapRawElementsToTokens(emptyList(), dictionary)
        assertTrue(tokens.isEmpty())
    }
}
