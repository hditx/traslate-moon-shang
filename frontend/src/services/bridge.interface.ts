import type { DocumentData, PageData, TranslationResult } from '@/types/document'

export interface IDesktopBridge {
  /**
   * Abre el diálogo nativo del sistema operativo para seleccionar un archivo (.pdf, .png, .jpg).
   */
  openFileDialog(): Promise<{ filePath: string; filename: string } | null>

  /**
   * Obtiene la información básica del documento (número de páginas, tipo de archivo).
   */
  getDocumentInfo(filePath: string): Promise<DocumentData>

  /**
   * Procesa una página específica del documento: ejecuta OCR y retorna imagen + tokens.
   */
  processPage(filePath: string, pageNumber: number): Promise<PageData>

  /**
   * Traduce un término específico o palabra china al español.
   */
  translateToken(textZh: string): Promise<TranslationResult>

  /**
   * Copia texto al portapapeles del sistema a través de la integración nativa del backend.
   */
  copyToClipboard?(text: string): Promise<boolean>

  /**
   * Obtiene la transcripción fonética Pinyin con tonos para un carácter o palabra china.
   */
  getPinyin?(textZh: string): Promise<string>

  /**
   * Reproduce la pronunciación auditiva de un término o carácter mediante el motor nativo del backend.
   */
  playAudio?(textZh: string): Promise<boolean>
}

