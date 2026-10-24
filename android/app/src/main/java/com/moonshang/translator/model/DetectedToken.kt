package com.moonshang.translator.model

import org.json.JSONObject

data class DetectedToken(
    val id: String,
    val textZh: String,
    val pinyin: String = "",
    val translationEs: String = "",
    val box: BoundingBox,
    val confidence: Double = 1.0
) {
    fun toJSONObject(): JSONObject = JSONObject().apply {
        put("id", id)
        put("textZh", textZh)
        put("pinyin", pinyin)
        put("translationEs", translationEs)
        put("box", box.toJSONObject())
        put("confidence", confidence)
    }

    companion object {
        fun fromJSONObject(json: JSONObject): DetectedToken {
            val text = when {
                json.has("textZh") -> json.getString("textZh")
                json.has("text_zh") -> json.getString("text_zh")
                else -> ""
            }
            val translation = when {
                json.has("translationEs") -> json.getString("translationEs")
                json.has("translation_es") -> json.getString("translation_es")
                else -> ""
            }
            return DetectedToken(
                id = json.getString("id"),
                textZh = text,
                pinyin = json.optString("pinyin", ""),
                translationEs = translation,
                box = BoundingBox.fromJSONObject(json.getJSONObject("box")),
                confidence = json.optDouble("confidence", 1.0)
            )
        }
    }
}
