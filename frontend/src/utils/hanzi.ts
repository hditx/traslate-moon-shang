/**
 * Utilidades para detección y manipulación de caracteres chinos (Hanzi 汉字).
 */

/**
 * Determina si un carácter es un ideograma Hanzi (CJK Unified Ideographs).
 */
export function isHanzi(char: string): boolean {
  if (!char || char.length === 0) return false
  return /[\u4e00-\u9fa5\u3400-\u4dbf\uf900-\ufaff]/.test(char)
}

/**
 * Extrae todos los caracteres Hanzi de una cadena de texto respetando el orden.
 */
export function extractHanziList(text: string): string[] {
  if (!text) return []
  return Array.from(text).filter(isHanzi)
}
