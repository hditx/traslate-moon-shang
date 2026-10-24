package com.moonshang.translator.net

import com.moonshang.translator.model.TranslationResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.net.URLEncoder
import java.util.concurrent.TimeUnit

/**
 * Cliente HTTP para consultar traducciones enriquecidas y Pinyin al servidor FastAPI.
 */
class RemoteTranslatorClient(
    var serverBaseUrl: String = "http://10.0.2.2:8000",
    private val httpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(3, TimeUnit.SECONDS)
        .readTimeout(5, TimeUnit.SECONDS)
        .build()
) {

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun translate(textZh: String): TranslationResult? = withContext(Dispatchers.IO) {
        val cleanText = textZh.trim().trimStart('|', ' ', '“', '”', '：', ':').trim()
        if (cleanText.isBlank()) return@withContext null

        android.util.Log.d("RemoteTranslator", "translate called for: '$cleanText'")

        // 1. Intentar con el servidor FastAPI local (si está activo en serverBaseUrl)
        val endpoint = "${serverBaseUrl.trimEnd('/')}/api/translate"
        try {
            val payload = JSONObject().apply {
                put("text_zh", cleanText)
            }
            val request = Request.Builder()
                .url(endpoint)
                .post(payload.toString().toRequestBody(jsonMediaType))
                .build()

            val fastClient = httpClient.newBuilder()
                .connectTimeout(800, TimeUnit.MILLISECONDS)
                .readTimeout(1500, TimeUnit.MILLISECONDS)
                .build()

            fastClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string()
                    if (body != null) {
                        val json = JSONObject(body)
                        val res = TranslationResult.fromJSONObject(json)
                        if (res.translationEs.isNotBlank()) {
                            android.util.Log.d("RemoteTranslator", "FastAPI translation: ${res.translationEs}")
                            return@withContext res
                        }
                    }
                }
            }
        } catch (e: Exception) {
            android.util.Log.d("RemoteTranslator", "FastAPI local server unavailable (${e.message}), trying Google GTX")
        }

        // 2. Motor de traducción web directo (Google Translate GTX público)
        try {
            val encoded = URLEncoder.encode(cleanText, "UTF-8")
            val gtxUrl = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=es&dt=t&q=$encoded"
            val gtxRequest = Request.Builder()
                .url(gtxUrl)
                .header("User-Agent", "Mozilla/5.0 (Android; Mobile)")
                .get()
                .build()

            httpClient.newCall(gtxRequest).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string()
                    if (!body.isNullOrBlank()) {
                        val arr = org.json.JSONArray(body)
                        if (arr.length() > 0) {
                            val segs = arr.optJSONArray(0)
                            if (segs != null && segs.length() > 0) {
                                val sb = StringBuilder()
                                for (i in 0 until segs.length()) {
                                    val seg = segs.optJSONArray(i)
                                    if (seg != null && seg.length() > 0) {
                                        val piece = seg.optString(0)
                                        if (piece.isNotBlank()) sb.append(piece)
                                    }
                                }
                                val transEs = sb.toString().trim()
                                if (transEs.isNotEmpty()) {
                                    android.util.Log.d("RemoteTranslator", "GTX translation success: $transEs")
                                    return@withContext TranslationResult(
                                        textZh = cleanText,
                                        pinyin = "",
                                        translationEs = transEs,
                                        fromCache = false
                                    )
                                }
                            }
                        }
                    }
                } else {
                    android.util.Log.w("RemoteTranslator", "GTX response not successful: ${response.code}")
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("RemoteTranslator", "GTX network exception", e)
        }

        null
    }

    suspend fun getPinyin(textZh: String): String? = withContext(Dispatchers.IO) {
        val encodedText = URLEncoder.encode(textZh, "UTF-8")
        val endpoint = "${serverBaseUrl.trimEnd('/')}/api/pinyin?text=$encodedText"

        val request = Request.Builder()
            .url(endpoint)
            .get()
            .build()

        try {
            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string() ?: return@withContext null
                    val json = JSONObject(body)
                    if (json.has("pinyin")) json.getString("pinyin") else null
                } else {
                    null
                }
            }
        } catch (e: Exception) {
            null
        }
    }
}
