package com.moonshang.translator.ocr

import com.moonshang.translator.model.PageData
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

class RemoteOcrException(message: String, cause: Throwable? = null) : IOException(message, cause)

/**
 * Motor OCR Online que delega el procesamiento de documentos al servidor FastAPI
 * equipado con PaddleOCR (alta precisión para caracteres chinos complejos).
 */
class RemoteOcrEngine(
    var serverBaseUrl: String = "http://10.0.2.2:8000",
    private val httpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
) : IOcrEngine {

    override suspend fun processImage(filePath: String, pageNumber: Int): PageData = withContext(Dispatchers.IO) {
        val file = File(filePath)
        if (!file.exists()) {
            throw RemoteOcrException("El archivo local no existe: $filePath")
        }

        val endpoint = "${serverBaseUrl.trimEnd('/')}/api/process-page"
        val mediaType = when {
            filePath.endsWith(".pdf", ignoreCase = true) -> "application/pdf".toMediaTypeOrNull()
            filePath.endsWith(".png", ignoreCase = true) -> "image/png".toMediaTypeOrNull()
            else -> "image/jpeg".toMediaTypeOrNull()
        }

        val fileBody = file.asRequestBody(mediaType)
        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", file.name, fileBody)
            .addFormDataPart("page_number", pageNumber.toString())
            .build()

        val request = Request.Builder()
            .url(endpoint)
            .post(requestBody)
            .build()

        try {
            httpClient.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    val errorBody = response.body?.string() ?: ""
                    throw RemoteOcrException("Error del servidor FastAPI [HTTP ${response.code}]: $errorBody")
                }

                val bodyStr = response.body?.string()
                    ?: throw RemoteOcrException("Respuesta vacía del servidor FastAPI")

                val json = JSONObject(bodyStr)
                PageData.fromJSONObject(json)
            }
        } catch (e: Exception) {
            if (e is RemoteOcrException) throw e
            throw RemoteOcrException("Fallo en la comunicación con el servidor FastAPI: ${e.message}", e)
        }
    }
}
