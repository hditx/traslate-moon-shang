package com.moonshang.translator.model

import org.json.JSONObject

data class TranslationResult(
    val textZh: String,
    val pinyin: String,
    val translationEs: String,
    val fromCache: Boolean = false
) {
    fun toJSONObject(): JSONObject = JSONObject().apply {
        put("textZh", textZh)
        put("pinyin", pinyin)
        put("translationEs", translationEs)
        put("fromCache", fromCache)
    }

    companion object {
        fun fromJSONObject(json: JSONObject): TranslationResult {
            return TranslationResult(
                textZh = json.optString("textZh", json.optString("text_zh", "")),
                pinyin = json.optString("pinyin", ""),
                translationEs = json.optString("translationEs", json.optString("translation_es", "")),
                fromCache = json.optBoolean("fromCache", json.optBoolean("from_cache", false))
            )
        }
    }
}
