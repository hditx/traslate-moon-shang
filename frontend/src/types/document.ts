/**
 * Coordenadas de una caja delimitadora (Bounding Box) en el sistema de coordenadas
 * de la imagen o página original (píxeles absolutos).
 */
export interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

/**
 * Representa un token, palabra o bloque de texto chino detectado por el OCR.
 */
export interface DetectedToken {
  id: string
  textZh: string           // Texto original en caracteres chinos (Hanzi 汉字)
  pinyin: string           // Transcripción fonética con tonos (ej. "nǐ hǎo")
  translationEs: string    // Traducción al español
  box: BoundingBox         // Coordenadas absolutas en la resolución original
  confidence: number       // Nivel de confianza del OCR (0.0 a 1.0)
}

/**
 * Datos correspondientes a una página de documento o imagen analizada.
 */
export interface PageData {
  pageNumber: number
  width: number            // Ancho en píxeles de la resolución original
  height: number           // Alto en píxeles de la resolución original
  imageUrl: string         // URL o data-uri de la imagen de la página renderizada
  tokens: DetectedToken[]  // Lista de caracteres/palabras chinas detectadas
}

/**
 * Representa el documento completo cargado (PDF o Imagen).
 */
export interface DocumentData {
  id: string
  filename: string
  fileType: 'image' | 'pdf'
  totalPages: number
  currentPage: number
  pages: PageData[]
}

/**
 * Estado de procesamiento de un archivo.
 */
export type ProcessingStatus = 'idle' | 'loading' | 'processing_ocr' | 'ready' | 'error'

/**
 * Resultado de traducción individual.
 */
export interface TranslationResult {
  textZh: string
  pinyin: string
  translationEs: string
  fromCache: boolean
}
