package com.moonshang.translator.data

import android.content.Context
import com.moonshang.translator.model.TranslationResult
import java.io.InputStream
import java.util.concurrent.ConcurrentHashMap

/**
 * Gestor de diccionario local y transcripción Pinyin para el funcionamiento offline.
 * Dispone de una base de datos léxica en memoria de alta frecuencia y soporte para
 * transcripción Pinyin universal de caracteres chinos (tabla completa de más de 40.000 caracteres).
 */
class LocalDictionaryHelper(
    private val context: Context? = null,
    initialEntries: Map<String, Pair<String, String>> = emptyMap()
) {
    // textZh -> Pair(pinyin, translationEs)
    private val dictionary = ConcurrentHashMap<String, Pair<String, String>>()
    // char -> pinyin
    private val pinyinMap = ConcurrentHashMap<String, String>()

    init {
        populateDefaultDictionary()
        initialEntries.forEach { (text, pair) ->
            dictionary[text] = pair
        }
        loadPinyinFromAsset()
    }

    fun loadPinyinFromStream(inputStream: InputStream) {
        try {
            inputStream.bufferedReader(Charsets.UTF_8).useLines { lines ->
                lines.forEach { line ->
                    val tabIdx = line.indexOf('\t')
                    if (tabIdx > 0 && tabIdx < line.length - 1) {
                        val ch = line.substring(0, tabIdx).trim()
                        val py = line.substring(tabIdx + 1).trim()
                        if (ch.isNotEmpty() && py.isNotEmpty()) {
                            pinyinMap[ch] = py
                        }
                    }
                }
            }
        } catch (_: Exception) {}
    }

    private fun loadPinyinFromAsset() {
        if (context == null) return
        try {
            val stream = context.assets.open("data/pinyin_table.txt")
            loadPinyinFromStream(stream)
        } catch (_: Exception) {
            // Silencioso si el asset no está disponible en entorno de tests
        }
    }

    private fun populateDefaultDictionary() {
        val defaults = mapOf(
            "你好" to Pair("nǐ hǎo", "hola"),
            "你" to Pair("nǐ", "tú, usted"),
            "好" to Pair("hǎo", "bueno, bien"),
            "谢谢" to Pair("xiè xie", "gracias"),
            "谢" to Pair("xiè", "agradecer"),
            "再见" to Pair("zài jiàn", "adiós, hasta luego"),
            "不客气" to Pair("bú kè qi", "de nada"),
            "中国" to Pair("zhōng guó", "China"),
            "中文" to Pair("zhōng wén", "idioma chino"),
            "汉字" to Pair("hàn zì", "caracteres chinos"),
            "汉" to Pair("hàn", "chino, etnia Han"),
            "字" to Pair("zì", "carácter, letra"),
            "文" to Pair("wén", "lengua, texto, cultura"),
            "语" to Pair("yǔ", "lenguaje, idioma"),
            "学习" to Pair("xué xí", "estudiar, aprender"),
            "学" to Pair("xué", "estudiar"),
            "习" to Pair("xí", "practicar"),
            "老师" to Pair("lǎo shī", "profesor/a"),
            "学生" to Pair("xué sheng", "estudiante"),
            "朋友" to Pair("péng you", "amigo/a"),
            "月" to Pair("yuè", "luna, mes"),
            "窖" to Pair("jiào", "bodega, fosa, sótano"),
            "商" to Pair("shāng", "comercio, dinastía Shang"),
            "山" to Pair("shān", "montaña"),
            "水" to Pair("shuǐ", "agua"),
            "日" to Pair("rì", "sol, día"),
            "人" to Pair("rén", "persona"),
            "大" to Pair("dà", "grande"),
            "小" to Pair("xiǎo", "pequeño"),
            "中" to Pair("zhōng", "medio, centro"),
            "国" to Pair("guó", "país, nación"),
            "一" to Pair("yī", "uno"),
            "二" to Pair("èr", "dos"),
            "三" to Pair("sān", "tres"),
            "四" to Pair("sì", "cuatro"),
            "五" to Pair("wǔ", "cinco"),
            "六" to Pair("liù", "seis"),
            "七" to Pair("qī", "siete"),
            "八" to Pair("bā", "ocho"),
            "九" to Pair("jiǔ", "nueve"),
            "十" to Pair("shí", "diez"),
            "爱" to Pair("ài", "amar, amor"),
            "家" to Pair("jiā", "familia, hogar"),
            "书" to Pair("shū", "libro"),
            "看" to Pair("kàn", "ver, mirar, leer"),
            "是" to Pair("shì", "ser, sí"),
            "不是" to Pair("bú shì", "no ser, en lugar de"),
            "不" to Pair("bù", "no"),
            "没" to Pair("méi", "no haber, no"),
            "没有" to Pair("méi yǒu", "no haber, no tener"),
            "有" to Pair("yǒu", "haber, tener"),
            "在" to Pair("zài", "estar en, en"),
            "和" to Pair("hé", "y, con"),
            "跟" to Pair("gēn", "con, seguir"),
            "如果" to Pair("rú guǒ", "si, en caso de"),
            "但" to Pair("dàn", "pero"),
            "但是" to Pair("dàn shì", "pero, sin embargo"),
            "而且" to Pair("ér qiě", "además"),
            "而" to Pair("ér", "y, sino que, pero"),
            "或者" to Pair("huò zhě", "o, quizás"),
            "万一" to Pair("wàn yī", "por si acaso, si acaso"),
            "别人" to Pair("bié rén", "otros, los demás"),
            "别" to Pair("bié", "otro, no"),
            "木偶" to Pair("mù ǒu", "muñeco de madera, títere"),
            "木" to Pair("mù", "madera, árbol"),
            "偶" to Pair("ǒu", "muñeco, figura"),
            "说" to Pair("shuō", "decir, hablar"),
            "想" to Pair("xiǎng", "pensar, querer"),
            "要" to Pair("yào", "querer, necesitar, deber"),
            "等" to Pair("děng", "esperar"),
            "上" to Pair("shàng", "subir, arriba, sobre"),
            "下" to Pair("xià", "bajar, abajo"),
            "一天" to Pair("yì tiān", "un día"),
            "天" to Pair("tiān", "día, cielo"),
            "分钟" to Pair("fēn zhōng", "minuto"),
            "分" to Pair("fēn", "minuto, dividir"),
            "钟" to Pair("zhōng", "reloj, campana"),
            "时间" to Pair("shí jiān", "tiempo"),
            "时" to Pair("shí", "tiempo, hora"),
            "间" to Pair("jiān", "entre, espacio"),
            "对于" to Pair("duì yú", "respecto a, en cuanto a"),
            "对" to Pair("duì", "hacia, correcto"),
            "于" to Pair("yú", "en, respecto a"),
            "他" to Pair("tā", "él"),
            "她" to Pair("tā", "ella"),
            "它" to Pair("tā", "ello, animal u objeto"),
            "我" to Pair("wǒ", "yo"),
            "两" to Pair("liǎng", "dos (cantidad)"),
            "千" to Pair("qiān", "mil"),
            "两千" to Pair("liǎng qiān", "dos mil"),
            "五千" to Pair("wǔ qiān", "cinco mil"),
            "万" to Pair("wàn", "diez mil"),
            "个" to Pair("gè", "unidad, clasificador"),
            "呢" to Pair("ne", "partícula interrogativa"),
            "种" to Pair("zhòng", "plantar, cultivar"),
            "出" to Pair("chū", "salir"),
            "出来" to Pair("chū lái", "salir, producir"),
            "的" to Pair("de", "de, que"),
            "地" to Pair("de", "adverbializador"),
            "得" to Pair("de", "partícula estructural"),
            "甚" to Pair("shèn", "muy, qué"),
            "蛋糕" to Pair("dàn gāo", "pastel, tarta"),
            "饼干" to Pair("bǐng gān", "galleta"),
            "图书馆" to Pair("tú shū guǎn", "biblioteca"),
            "水果" to Pair("shuǐ guǒ", "fruta"),
            "蜡烛" to Pair("là zhú", "vela"),
            "柠檬水" to Pair("níng méng shuǐ", "limonada"),
            "冰" to Pair("bīng", "hielo"),
            "宫殿" to Pair("gōng diàn", "palacio"),
            "华美" to Pair("huá měi", "magnífico, hermoso"),
            "心跳" to Pair("xīn tiào", "latido del corazón"),
            "心" to Pair("xīn", "corazón, mente"),
            "激动" to Pair("jī dòng", "emocionado"),
            "耳朵" to Pair("ěr duo", "oreja"),
            "眼睛" to Pair("yǎn jing", "ojo"),
            "鼻子" to Pair("bí zi", "nariz"),
            "方向" to Pair("fāng xiàng", "dirección"),
            "奇迹" to Pair("qí jì", "milagro"),
            "之地" to Pair("zhī dì", "tierra, lugar"),
            "走" to Pair("zǒu", "caminar, ir"),
            "踱步" to Pair("duó bù", "pasear, dar pasos"),
            "心急如焚" to Pair("xīn jí rú fén", "ansioso como fuego, impaciente"),
            "难熬" to Pair("nán áo", "difícil de soportar"),
            "脑袋" to Pair("nǎo dài", "cabeza, cerebro"),
            "不断" to Pair("bú duàn", "continuamente"),
            "玩" to Pair("wán", "jugar, divertirse")
        )
        dictionary.putAll(defaults)
    }

    /**
     * Busca coincidencia exacta directa en el diccionario en memoria.
     */
    fun getExact(textZh: String): TranslationResult? {
        val trimmed = textZh.trim()
        val exact = dictionary[trimmed] ?: return null
        val py = exact.first.ifBlank { getPinyin(trimmed) }
        return TranslationResult(
            textZh = trimmed,
            pinyin = py,
            translationEs = exact.second,
            fromCache = true
        )
    }

    /**
     * Traduce una palabra o carácter chino al español.
     * Si no existe coincidencia exacta, descompone por caracteres individuales.
     */
    fun translate(textZh: String): TranslationResult {
        val trimmed = textZh.trim()
        val exact = dictionary[trimmed]
        if (exact != null) {
            return TranslationResult(
                textZh = trimmed,
                pinyin = exact.first,
                translationEs = exact.second,
                fromCache = true
            )
        }

        // Intento de descomposición por caracteres individuales si tiene longitud > 1
        if (trimmed.length > 1) {
            val pinyinParts = mutableListOf<String>()
            val transParts = mutableListOf<String>()
            var anyFound = false

            for (ch in trimmed) {
                val charStr = ch.toString()
                val charEntry = dictionary[charStr]
                val py = pinyinMap[charStr] ?: charEntry?.first
                if (charEntry != null) {
                    pinyinParts.add(py ?: charEntry.first)
                    transParts.add(charEntry.second)
                    anyFound = true
                } else if (py != null) {
                    pinyinParts.add(py)
                } else if (charStr.isNotBlank()) {
                    pinyinParts.add(charStr)
                }
            }

            if (anyFound) {
                return TranslationResult(
                    textZh = trimmed,
                    pinyin = pinyinParts.joinToString(" "),
                    translationEs = transParts.joinToString("; "),
                    fromCache = true
                )
            }
        }

        return TranslationResult(
            textZh = trimmed,
            pinyin = getPinyin(trimmed),
            translationEs = "Traducción no encontrada (modo offline)",
            fromCache = false
        )
    }

    /**
     * Obtiene la transcripción fonética Pinyin para el texto indicado.
     * Consulta el diccionario léxico y la tabla universal de Pinyin.
     */
    fun getPinyin(textZh: String): String {
        val trimmed = textZh.trim()
        if (trimmed.isEmpty()) return ""
        val exact = dictionary[trimmed]
        if (exact != null) {
            return exact.first
        }

        val parts = mutableListOf<String>()
        for (ch in trimmed) {
            val charStr = ch.toString()
            val py = pinyinMap[charStr] ?: dictionary[charStr]?.first
            if (py != null) {
                parts.add(py)
            } else if (charStr.isNotBlank()) {
                parts.add(charStr)
            }
        }
        return parts.joinToString(" ")
    }

    /**
     * Permite agregar dinámicamente nuevas entradas o sincronizar con una base SQLite.
     */
    fun addEntry(textZh: String, pinyin: String, translationEs: String) {
        dictionary[textZh.trim()] = Pair(pinyin.trim(), translationEs.trim())
    }

    fun contains(textZh: String): Boolean = dictionary.containsKey(textZh.trim())

    fun totalEntries(): Int = dictionary.size
}
