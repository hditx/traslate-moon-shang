package com.moonshang.translator.ocr

import android.content.Context
import android.graphics.BitmapFactory
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.chinese.ChineseTextRecognizerOptions
import com.moonshang.translator.data.LocalDictionaryHelper
import com.moonshang.translator.model.BoundingBox
import com.moonshang.translator.model.DetectedToken
import com.moonshang.translator.model.PageData
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import java.io.File

data class RawOcrElement(
    val text: String,
    val x1: Double,
    val y1: Double,
    val x2: Double,
    val y2: Double,
    val confidence: Double = 1.0
)

/**
 * Motor de OCR Offline para caracteres chinos simplificados y tradicionales,
 * basado en el SDK de Google ML Kit (com.google.mlkit:text-recognition-chinese).
 */
class MlKitOcrEngine(
    private val context: Context? = null,
    private val dictionaryHelper: LocalDictionaryHelper = LocalDictionaryHelper(),
    private val customExtractor: (suspend (String, Int) -> List<RawOcrElement>)? = null
) : IOcrEngine {

    private val recognizer by lazy {
        TextRecognition.getClient(ChineseTextRecognizerOptions.Builder().build())
    }

    /**
     * Procesa una imagen local utilizando Google ML Kit y enriquece los tokens
     * detectados con Pinyin y traducción del diccionario offline.
     */
    override suspend fun processImage(filePath: String, pageNumber: Int): PageData = withContext(Dispatchers.IO) {
        if (customExtractor != null) {
            val rawElements = customExtractor.invoke(filePath, pageNumber)
            val tokens = mapRawElementsToTokens(rawElements, dictionaryHelper)
            return@withContext PageData(
                pageNumber = pageNumber,
                width = 800,
                height = 1200,
                imageUrl = filePath,
                tokens = tokens
            )
        }

        val file = File(filePath)
        if (!file.exists()) {
            return@withContext PageData(
                pageNumber = pageNumber,
                width = 800,
                height = 1200,
                imageUrl = filePath,
                tokens = emptyList()
            )
        }

        val isPdf = filePath.endsWith(".pdf", ignoreCase = true)
        val bitmap: android.graphics.Bitmap? = if (isPdf) {
            renderPdfToBitmap(file, pageNumber)
        } else {
            BitmapFactory.decodeFile(filePath)
        }

        if (bitmap == null) {
            return@withContext PageData(pageNumber, 800, 1200, filePath, emptyList())
        }

        val imageWidth = bitmap.width
        val imageHeight = bitmap.height

        val outStream = java.io.ByteArrayOutputStream()
        bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 85, outStream)
        val base64Image = "data:image/jpeg;base64," + android.util.Base64.encodeToString(outStream.toByteArray(), android.util.Base64.NO_WRAP)

        val inputImage = try {
            InputImage.fromBitmap(bitmap, 0)
        } catch (e: Exception) {
            return@withContext PageData(pageNumber, imageWidth, imageHeight, base64Image, emptyList())
        }

        val visionText = try {
            recognizer.process(inputImage).await()
        } catch (e: Exception) {
            return@withContext PageData(pageNumber, imageWidth, imageHeight, base64Image, emptyList())
        }

        val rawElements = mutableListOf<RawOcrElement>()
        for (block in visionText.textBlocks) {
            for (line in block.lines) {
                val rect = line.boundingBox
                if (rect != null) {
                    rawElements.add(
                        RawOcrElement(
                            text = line.text,
                            x1 = rect.left.toDouble(),
                            y1 = rect.top.toDouble(),
                            x2 = rect.right.toDouble(),
                            y2 = rect.bottom.toDouble(),
                            confidence = 1.0
                        )
                    )
                }
            }
        }

        val tokens = mapRawElementsToTokens(rawElements, dictionaryHelper)

        PageData(
            pageNumber = pageNumber,
            width = imageWidth,
            height = imageHeight,
            imageUrl = base64Image,
            tokens = tokens
        )
    }

    private fun renderPdfToBitmap(file: File, pageNumber: Int): android.graphics.Bitmap? {
        return try {
            val pfd = android.os.ParcelFileDescriptor.open(file, android.os.ParcelFileDescriptor.MODE_READ_ONLY) ?: return null
            val renderer = android.graphics.pdf.PdfRenderer(pfd)
            if (pageNumber < 1 || pageNumber > renderer.pageCount) {
                renderer.close()
                pfd.close()
                return null
            }
            val page = renderer.openPage(pageNumber - 1)
            val bmp = android.graphics.Bitmap.createBitmap(page.width * 2, page.height * 2, android.graphics.Bitmap.Config.ARGB_8888)
            val canvas = android.graphics.Canvas(bmp)
            canvas.drawColor(android.graphics.Color.WHITE)
            page.render(bmp, null, null, android.graphics.pdf.PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            page.close()
            renderer.close()
            pfd.close()
            bmp
        } catch (_: Exception) {
            null
        }
    }

    /**
     * Mapea elementos OCR brutos a la lista de DetectedToken consumida por Vue 3.
     */
    fun mapRawElementsToTokens(
        elements: List<RawOcrElement>,
        dictionary: LocalDictionaryHelper
    ): List<DetectedToken> {
        val result = mutableListOf<DetectedToken>()
        var counter = 0

        for (el in elements) {
            val trimmed = el.text.trim()
            if (trimmed.isEmpty()) continue

            counter++
            val id = "tok_${counter}"
            val pinyin = dictionary.getPinyin(trimmed)
            val translation = dictionary.translate(trimmed).translationEs

            result.add(
                DetectedToken(
                    id = id,
                    textZh = trimmed,
                    pinyin = pinyin,
                    translationEs = translation,
                    box = BoundingBox(
                        x1 = el.x1,
                        y1 = el.y1,
                        x2 = el.x2,
                        y2 = el.y2
                    ),
                    confidence = el.confidence
                )
            )
        }

        return result
    }
}
