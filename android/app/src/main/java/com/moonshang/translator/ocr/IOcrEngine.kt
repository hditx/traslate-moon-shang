package com.moonshang.translator.ocr

import com.moonshang.translator.model.PageData

/**
 * Interfaz común para motores de OCR (tanto el motor Offline con ML Kit
 * como el motor Online remoto con FastAPI/PaddleOCR).
 */
interface IOcrEngine {
    /**
     * Procesa una página de imagen o documento y retorna los tokens detectados con cajas delimitadoras.
     */
    suspend fun processImage(filePath: String, pageNumber: Int): PageData
}
