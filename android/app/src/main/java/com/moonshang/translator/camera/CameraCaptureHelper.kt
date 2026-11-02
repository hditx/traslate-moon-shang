package com.moonshang.translator.camera

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.exifinterface.media.ExifInterface
import java.io.File
import java.io.FileOutputStream
import kotlin.math.max

/**
 * Utilidad para la gestión de archivos temporales de cámara,
 * generación segura de URIs vía FileProvider y post-procesamiento de imágenes
 * (rotación automática según metadatos EXIF y compresión a resolución óptima).
 */
object CameraCaptureHelper {

    fun createTempImageFile(context: Context): File {
        val storageDir = File(context.cacheDir, "camera_captures").apply {
            if (!exists()) mkdirs()
        }
        return File.createTempFile("photo_", ".jpg", storageDir)
    }

    fun getUriForFile(context: Context, file: File): Uri {
        val authority = "${context.packageName}.fileprovider"
        return FileProvider.getUriForFile(context, authority, file)
    }

    /**
     * Corrige la orientación del sensor de la cámara según los metadatos EXIF,
     * reescala la imagen si supera [maxDimension] para optimizar la inferencia OCR
     * y comprime a JPEG.
     */
    fun correctOrientationAndCompress(
        imageFile: File,
        maxDimension: Int = 2048,
        quality: Int = 85
    ): File {
        if (!imageFile.exists() || imageFile.length() == 0L) {
            return imageFile
        }

        try {
            val exif = ExifInterface(imageFile.absolutePath)
            val orientation = exif.getAttributeInt(
                ExifInterface.TAG_ORIENTATION,
                ExifInterface.ORIENTATION_NORMAL
            )

            val rotationDegrees = when (orientation) {
                ExifInterface.ORIENTATION_ROTATE_90 -> 90f
                ExifInterface.ORIENTATION_ROTATE_180 -> 180f
                ExifInterface.ORIENTATION_ROTATE_270 -> 270f
                else -> 0f
            }

            // Obtener dimensiones sin cargar bitmap completo en memoria
            val boundsOptions = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            BitmapFactory.decodeFile(imageFile.absolutePath, boundsOptions)
            val rawW = boundsOptions.outWidth
            val rawH = boundsOptions.outHeight

            if (rawW <= 0 || rawH <= 0) {
                return imageFile
            }

            // Calcular inSampleSize si la imagen es gigantesca
            var inSampleSize = 1
            val maxRawDim = max(rawW, rawH)
            if (maxRawDim > maxDimension * 2) {
                inSampleSize = 2
            }

            val decodeOptions = BitmapFactory.Options().apply {
                this.inSampleSize = inSampleSize
            }
            val loadedBitmap = BitmapFactory.decodeFile(imageFile.absolutePath, decodeOptions) ?: return imageFile

            // Aplicar rotación y/o reescalado final
            val matrix = Matrix()
            if (rotationDegrees != 0f) {
                matrix.postRotate(rotationDegrees)
            }

            val currentW = loadedBitmap.width
            val currentH = loadedBitmap.height
            val currentMax = max(currentW, currentH)

            if (currentMax > maxDimension) {
                val scale = maxDimension.toFloat() / currentMax.toFloat()
                matrix.postScale(scale, scale)
            }

            val finalBitmap = if (!matrix.isIdentity) {
                val transformed = Bitmap.createBitmap(
                    loadedBitmap,
                    0,
                    0,
                    currentW,
                    currentH,
                    matrix,
                    true
                )
                if (transformed != loadedBitmap) {
                    loadedBitmap.recycle()
                }
                transformed
            } else {
                loadedBitmap
            }

            FileOutputStream(imageFile).use { fos ->
                finalBitmap.compress(Bitmap.CompressFormat.JPEG, quality, fos)
                fos.flush()
            }
            finalBitmap.recycle()

            return imageFile
        } catch (e: Exception) {
            // En caso de cualquier error durante la transformación, preservar el archivo original
            return imageFile
        }
    }
}
