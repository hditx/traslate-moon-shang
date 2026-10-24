package com.moonshang.translator

import com.moonshang.translator.data.LocalDictionaryHelper
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class LocalDictionaryHelperTest {

    private lateinit var dictionary: LocalDictionaryHelper

    @BeforeEach
    fun setUp() {
        dictionary = LocalDictionaryHelper()
    }

    @Test
    fun testExactWordTranslation() {
        val niHao = dictionary.translate("你好")
        assertEquals("你好", niHao.textZh)
        assertEquals("nǐ hǎo", niHao.pinyin)
        assertEquals("hola", niHao.translationEs)
        assertTrue(niHao.fromCache)

        val jiao = dictionary.translate("窖")
        assertEquals("jiào", jiao.pinyin)
        assertEquals("bodega, fosa, sótano", jiao.translationEs)
    }

    @Test
    fun testCharacterDecomposition() {
        // "大山" no está en el diccionario completo, pero sí "大" (grande) y "山" (montaña)
        val daShan = dictionary.translate("大山")
        assertEquals("大山", daShan.textZh)
        assertEquals("dà shān", daShan.pinyin)
        assertEquals("grande; montaña", daShan.translationEs)
        assertTrue(daShan.fromCache)
    }

    @Test
    fun testPinyinLookup() {
        assertEquals("xué xí", dictionary.getPinyin("学习"))
        assertEquals("zhōng guó", dictionary.getPinyin("中国"))
        assertEquals("yuè", dictionary.getPinyin("月"))
    }

    @Test
    fun testAddCustomEntry() {
        assertFalse(dictionary.contains("计算机"))

        dictionary.addEntry("计算机", "jì suàn jī", "computadora")
        assertTrue(dictionary.contains("计算机"))

        val result = dictionary.translate("计算机")
        assertEquals("jì suàn jī", result.pinyin)
        assertEquals("computadora", result.translationEs)
    }

    @Test
    fun testUnknownWordFallback() {
        val unknown = dictionary.translate("未知xyz")
        assertEquals("未知xyz", unknown.textZh)
        assertFalse(unknown.fromCache)
        assertTrue(unknown.translationEs.contains("modo offline"))
    }
}
