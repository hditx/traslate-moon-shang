import type { IDesktopBridge } from './bridge.interface'
import type { DocumentData, PageData, TranslationResult } from '@/types/document'
import { logger } from './logger.service'

export class PyWebViewBridge implements IDesktopBridge {
  private get api() {
    if (typeof window === 'undefined' || !window.pywebview?.api) {
      const err = new Error('PyWebView API no está disponible en este entorno.')
      logger.error('PyWebViewBridge', 'API no disponible', err)
      throw err
    }
    return window.pywebview.api
  }

  async openFileDialog(): Promise<{ filePath: string; filename: string } | null> {
    logger.debug('PyWebViewBridge', 'Invocando openFileDialog...')
    try {
      const res = await this.api.open_file_dialog()
      logger.info('PyWebViewBridge', 'openFileDialog resuelto', res)
      return res ?? null
    } catch (err) {
      logger.error('PyWebViewBridge', 'Error en openFileDialog', err)
      throw err
    }
  }

  async getDocumentInfo(filePath: string): Promise<DocumentData> {
    logger.debug('PyWebViewBridge', `Obteniendo info del documento: ${filePath}`)
    try {
      const res = await this.api.get_document_info(filePath)
      logger.info('PyWebViewBridge', 'Document info obtenido', res)
      return res as DocumentData
    } catch (err) {
      logger.error('PyWebViewBridge', `Error al obtener info de ${filePath}`, err)
      throw err
    }
  }

  async processPage(filePath: string, pageNumber: number): Promise<PageData> {
    logger.debug('PyWebViewBridge', `Procesando página ${pageNumber} de ${filePath}`)
    try {
      const res = await this.api.process_page(filePath, pageNumber)
      logger.info('PyWebViewBridge', `Página ${pageNumber} procesada con éxito`, {
        tokensCount: res.tokens?.length,
      })
      return res as PageData
    } catch (err) {
      logger.error('PyWebViewBridge', `Error procesando página ${pageNumber} de ${filePath}`, err)
      throw err
    }
  }

  async translateToken(textZh: string): Promise<TranslationResult> {
    logger.debug('PyWebViewBridge', `Solicitando traducción para '${textZh}'`)
    try {
      const res = await this.api.translate_token(textZh)
      return res as TranslationResult
    } catch (err) {
      logger.error('PyWebViewBridge', `Error al traducir '${textZh}'`, err)
      throw err
    }
  }

  async copyToClipboard(text: string): Promise<boolean> {
    logger.debug('PyWebViewBridge', `Copiando texto al portapapeles nativo (${text.length} caracteres)`)
    try {
      if (typeof this.api.copy_to_clipboard === 'function') {
        const res = await this.api.copy_to_clipboard(text)
        return Boolean(res)
      }
      return false
    } catch (err) {
      logger.error('PyWebViewBridge', 'Error al invocar copy_to_clipboard nativo', err)
      return false
    }
  }

  async getPinyin(textZh: string): Promise<string> {
    logger.debug('PyWebViewBridge', `Solicitando Pinyin para '${textZh}'`)
    try {
      if (typeof this.api.get_pinyin === 'function') {
        const res = await this.api.get_pinyin(textZh)
        return String(res ?? '')
      }
      return ''
    } catch (err) {
      logger.error('PyWebViewBridge', `Error al obtener Pinyin para '${textZh}'`, err)
      return ''
    }
  }

  async playAudio(textZh: string): Promise<boolean> {
    logger.debug('PyWebViewBridge', `Solicitando reproducción de audio nativo para '${textZh}'`)
    try {
      if (typeof this.api.play_pronunciation === 'function') {
        const res = await this.api.play_pronunciation(textZh)
        return Boolean(res)
      }
      return false
    } catch (err) {
      logger.error('PyWebViewBridge', `Error al reproducir audio para '${textZh}'`, err)
      return false
    }
  }
}

