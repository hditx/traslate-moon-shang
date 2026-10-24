package com.moonshang.translator.model

import org.json.JSONObject

data class BoundingBox(
    val x1: Double,
    val y1: Double,
    val x2: Double,
    val y2: Double
) {
    val width: Double get() = x2 - x1
    val height: Double get() = y2 - y1

    fun toJSONObject(): JSONObject = JSONObject().apply {
        put("x1", x1)
        put("y1", y1)
        put("x2", x2)
        put("y2", y2)
    }

    companion object {
        fun fromJSONObject(json: JSONObject): BoundingBox {
            return BoundingBox(
                x1 = json.optDouble("x1", 0.0),
                y1 = json.optDouble("y1", 0.0),
                x2 = json.optDouble("x2", 0.0),
                y2 = json.optDouble("y2", 0.0)
            )
        }
    }
}
