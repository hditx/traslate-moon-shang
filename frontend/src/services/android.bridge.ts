import type { IDesktopBridge } from './bridge.interface'
import type { DocumentData, PageData, TranslationResult } from '@/types/document'
import { logger } from './logger.service'

/**
 * Parsea respuestas devueltas por la interfaz nativa @JavascriptInterface de Android,
 * manejando tanto strings en formato JSON como objetos directos.
 */
function parseAndroidResponse<T>(response: any): T {
  if (response === null || response === undefined) {
    return response as T
  }
  if (typeof response === 'string') {
    const trimmed = response.trim()
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        return JSON.parse(trimmed) as T
      } catch (err) {
        logger.error('AndroidBridge', 'Fallo al parsear JSON devuelto por Android:', err)
        throw new Error(`Respuesta JSON corrupta de Android: ${err instanceof Error ? err.message : String(err)}`)
      }
    }
  }
  return response as T
}

export class AndroidBridge implements IDesktopBridge {
  private get api() {
    if (typeof window === 'undefined' || !window.androidApi) {
      const err = new Error('La interfaz nativa Android (window.androidApi) no está disponible en este entorno.')
      logger.error('AndroidBridge', 'API no disponible', err)
      throw err
    }
    return window.androidApi
  }

  /**
   * Invoca un método nativo de Android soportando convenciones snake_case y camelCase.
   */
  private async invokeNative(methodName: string, ...args: any[]): Promise<any> {
    const api = this.api
    const snakeCaseName = methodName.replace(/([A-Z])/g, '_$1').toLowerCase()

    let fn = api[methodName]
    if (typeof fn !== 'function') {
      fn = api[snakeCaseName]
    }

    if (typeof fn !== 'function') {
      throw new Error(`Método nativo '${methodName}' (o '${snakeCaseName}') no encontrado en window.androidApi`)
    }

    return Promise.resolve(fn.apply(api, args))
  }

  async openFileDialog(): Promise<{ filePath: string; filename: string } | null> {
    logger.debug('AndroidBridge', 'Invocando selector de archivos nativo Android...')
    try {
      const raw = await this.invokeNative('openFileDialog')
      const parsed = parseAndroidResponse<{ filePath: string; filename: string } | null>(raw)
      logger.info('AndroidBridge', 'Archivo seleccionado en Android:', parsed)
      return parsed ?? null
    } catch (err) {
      logger.error('AndroidBridge', 'Error en openFileDialog Android', err)
      throw err
    }
  }

  async getDocumentInfo(filePath: string): Promise<DocumentData> {
    logger.debug('AndroidBridge', `Obteniendo información del documento: ${filePath}`)
    try {
      const raw = await this.invokeNative('getDocumentInfo', filePath)
      const parsed = parseAndroidResponse<DocumentData>(raw)
      logger.info('AndroidBridge', 'Información del documento obtenida:', parsed)
      return parsed
    } catch (err) {
      logger.error('AndroidBridge', `Error al obtener información de ${filePath}`, err)
      throw err
    }
  }

  async processPage(filePath: string, pageNumber: number): Promise<PageData> {
    logger.debug('AndroidBridge', `Procesando página ${pageNumber} de ${filePath} en Android`)
    try {
      const raw = await this.invokeNative('processPage', filePath, pageNumber)
      const parsed = parseAndroidResponse<PageData>(raw)
      logger.info('AndroidBridge', `Página ${pageNumber} procesada con éxito`, {
        tokensCount: parsed.tokens?.length,
      })
      return parsed
    } catch (err) {
      logger.error('AndroidBridge', `Error procesando página ${pageNumber} de ${filePath}`, err)
      throw err
    }
  }

  async translateToken(textZh: string): Promise<TranslationResult> {
    logger.debug('AndroidBridge', `Solicitando traducción para '${textZh}'`)
    try {
      const raw = await this.invokeNative('translateToken', textZh)
      return parseAndroidResponse<TranslationResult>(raw)
    } catch (err) {
      logger.error('AndroidBridge', `Error al traducir '${textZh}'`, err)
      throw err
    }
  }

  async copyToClipboard(text: string): Promise<boolean> {
    logger.debug('AndroidBridge', `Copiando al portapapeles nativo Android (${text.length} caracteres)`)
    try {
      const raw = await this.invokeNative('copyToClipboard', text)
      return Boolean(raw)
    } catch (err) {
      logger.error('AndroidBridge', 'Error al copiar al portapapeles de Android', err)
      return false
    }
  }

  async getPinyin(textZh: string): Promise<string> {
    logger.debug('AndroidBridge', `Solicitando Pinyin para '${textZh}'`)
    try {
      const raw = await this.invokeNative('getPinyin', textZh)
      return String(raw ?? '')
    } catch (err) {
      logger.error('AndroidBridge', `Error al obtener Pinyin para '${textZh}'`, err)
      return ''
    }
  }

  async playAudio(textZh: string): Promise<boolean> {
    logger.debug('AndroidBridge', `Solicitando reproducción de audio en Android para '${textZh}'`)
    try {
      let raw = false
      try {
        raw = await this.invokeNative('playAudio', textZh)
      } catch {
        // Fallback si en Kotlin se llamó play_pronunciation
        raw = await this.invokeNative('playPronunciation', textZh)
      }
      return Boolean(raw)
    } catch (err) {
      logger.error('AndroidBridge', `Error al reproducir audio para '${textZh}'`, err)
      return false
    }
  }
}
