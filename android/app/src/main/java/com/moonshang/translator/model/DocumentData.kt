package com.moonshang.translator.model

import org.json.JSONArray
import org.json.JSONObject

data class DocumentData(
    val id: String,
    val filename: String,
    val fileType: String,
    val totalPages: Int = 1,
    val currentPage: Int = 1,
    val pages: List<PageData> = emptyList()
) {
    fun toJSONObject(): JSONObject = JSONObject().apply {
        put("id", id)
        put("filename", filename)
        put("fileType", fileType)
        put("totalPages", totalPages)
        put("currentPage", currentPage)
        val pagesArray = JSONArray()
        pages.forEach { pagesArray.put(it.toJSONObject()) }
        put("pages", pagesArray)
    }

    companion object {
        fun fromJSONObject(json: JSONObject): DocumentData {
            val pagesList = mutableListOf<PageData>()
            val pagesArray = json.optJSONArray("pages")
            if (pagesArray != null) {
                for (i in 0 until pagesArray.length()) {
                    pagesList.add(PageData.fromJSONObject(pagesArray.getJSONObject(i)))
                }
            }
            return DocumentData(
                id = json.getString("id"),
                filename = json.getString("filename"),
                fileType = json.getString("fileType"),
                totalPages = json.optInt("totalPages", 1),
                currentPage = json.optInt("currentPage", 1),
                pages = pagesList
            )
        }
    }
}
