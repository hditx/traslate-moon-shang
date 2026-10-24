package com.moonshang.translator.ocr

import com.moonshang.translator.model.PageData
import com.moonshang.translator.net.INetworkDetector

/**
 * Motor híbrido inteligente que selecciona dinámicamente entre el motor Online
 * (PaddleOCR de alta precisión) y el motor Offline (Google ML Kit en el chip móvil).
 * Si el servidor remoto no responde o la red falla, conmuta automáticamente a Offline sin errores para el usuario.
 */
class SmartHybridOcrEngine(
    val remoteEngine: IOcrEngine,
    val offlineEngine: IOcrEngine,
    val networkDetector: INetworkDetector
) : IOcrEngine {

    var lastUsedEngine: String = "none"
        private set

    override suspend fun processImage(filePath: String, pageNumber: Int): PageData {
        val isOnlineAvailable = try {
            networkDetector.isOnline()
        } catch (e: Exception) {
            false
        }

        if (isOnlineAvailable) {
            try {
                val result = remoteEngine.processImage(filePath, pageNumber)
                lastUsedEngine = "remote"
                return result
            } catch (e: Exception) {
                // Fallback automático al motor offline si el servidor remoto falla o expira el timeout
                lastUsedEngine = "offline_fallback"
                return offlineEngine.processImage(filePath, pageNumber)
            }
        }

        lastUsedEngine = "offline"
        return offlineEngine.processImage(filePath, pageNumber)
    }
}
