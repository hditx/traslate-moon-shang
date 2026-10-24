package com.moonshang.translator.model

import org.json.JSONArray
import org.json.JSONObject

data class PageData(
    val pageNumber: Int,
    val width: Int,
    val height: Int,
    val imageUrl: String = "",
    val tokens: List<DetectedToken> = emptyList()
) {
    fun toJSONObject(): JSONObject = JSONObject().apply {
        put("pageNumber", pageNumber)
        put("width", width)
        put("height", height)
        put("imageUrl", imageUrl)
        val tokensArray = JSONArray()
        tokens.forEach { tokensArray.put(it.toJSONObject()) }
        put("tokens", tokensArray)
    }

    companion object {
        fun fromJSONObject(json: JSONObject): PageData {
            val tokensList = mutableListOf<DetectedToken>()
            val tokensArray = json.optJSONArray("tokens")
            if (tokensArray != null) {
                for (i in 0 until tokensArray.length()) {
                    tokensList.add(DetectedToken.fromJSONObject(tokensArray.getJSONObject(i)))
                }
            }
            return PageData(
                pageNumber = json.getInt("pageNumber"),
                width = json.getInt("width"),
                height = json.getInt("height"),
                imageUrl = json.optString("imageUrl", ""),
                tokens = tokensList
            )
        }
    }
}
