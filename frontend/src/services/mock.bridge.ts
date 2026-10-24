import type { IDesktopBridge } from './bridge.interface'
import type { DocumentData, PageData, TranslationResult, DetectedToken } from '@/types/document'

/**
 * Genera una imagen SVG en Base64 con texto en chino para simular documentos reales.
 */
function createMockPageSvg(width: number, height: number): string {
  const svg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <rect width="100%" height="100%" fill="#1e293b"/>
    <rect x="40" y="40" width="${width - 80}" height="${height - 80}" fill="#0f172a" rx="12" stroke="#334155" stroke-width="2"/>
    <text x="80" y="120" font-family="'Noto Sans SC', sans-serif" font-size="36" font-weight="bold" fill="#38bdf8">月亮翻译 - Moon Shang</text>
    <text x="80" y="180" font-family="'Noto Sans SC', sans-serif" font-size="28" fill="#f8fafc">欢迎使用中文翻译系统</text>
    <text x="80" y="240" font-family="'Noto Sans SC', sans-serif" font-size="24" fill="#94a3b8">学习中文是一件快乐的事</text>
    <text x="80" y="300" font-family="'Noto Sans SC', sans-serif" font-size="24" fill="#cbd5e1">千里之行，始于足下</text>
    <text x="80" y="360" font-family="'Noto Sans SC', sans-serif" font-size="22" fill="#64748b">你好世界，明天会更好</text>
  </svg>
  `.trim()

  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`
}

export class MockDesktopBridge implements IDesktopBridge {
  private mockDictionary: Record<string, { pinyin: string; es: string }> = {
    '欢迎使用中文翻译系统': { pinyin: 'huān yíng shǐ yòng zhōng wén fān yì xì tǒng', es: 'Bienvenido al sistema de traducción de chino' },
    '学习中文是一件快乐的事': { pinyin: 'xué xí zhōng wén shì yī jiàn kuài lè de shì', es: 'Aprender chino es algo feliz y placentero' },
    '千里之行，始于足下': { pinyin: 'qiān lǐ zhī xíng ， shǐ yú zú xià', es: 'Un viaje de mil millas comienza con un solo paso (Proverbio)' },
    '你好世界，明天会更好': { pinyin: 'nǐ hǎo shì jiè ， míng tiān huì gèng hǎo', es: 'Hola mundo, mañana será aún mejor' },
    '你好': { pinyin: 'nǐ hǎo', es: 'Hola' },
    '世界': { pinyin: 'shì jiè', es: 'Mundo' },
    '谢谢': { pinyin: 'xiè xie', es: 'Gracias' },
    '学习': { pinyin: 'xué xí', es: 'Estudiar / Aprender' },
  }

  async openFileDialog(): Promise<{ filePath: string; filename: string } | null> {
    return {
      filePath: '/mock/path/documento_chino.pdf',
      filename: 'documento_chino.pdf',
    }
  }

  async getDocumentInfo(filePath: string): Promise<DocumentData> {
    return {
      id: 'doc-mock-1',
      filename: filePath.split('/').pop() || 'documento_chino.pdf',
      fileType: 'pdf',
      totalPages: 3,
      currentPage: 1,
      pages: [],
    }
  }

  async processPage(_filePath: string, pageNumber: number): Promise<PageData> {
    const width = 800
    const height = 1100

    const tokens: DetectedToken[] = [
      {
        id: 'tok-1',
        textZh: '欢迎使用中文翻译系统',
        pinyin: 'huān yíng shǐ yòng zhōng wén fān yì xì tǒng',
        translationEs: 'Bienvenido al sistema de traducción de chino',
        box: { x1: 75, y1: 150, x2: 440, y2: 190 },
        confidence: 0.99,
      },
      {
        id: 'tok-2',
        textZh: '学习中文是一件快乐的事',
        pinyin: 'xué xí zhōng wén shì yī jiàn kuài lè de shì',
        translationEs: 'Aprender chino es algo feliz y placentero',
        box: { x1: 75, y1: 210, x2: 420, y2: 250 },
        confidence: 0.98,
      },
      {
        id: 'tok-3',
        textZh: '千里之行，始于足下',
        pinyin: 'qiān lǐ zhī xíng ， shǐ yú zú xià',
        translationEs: 'Un viaje de mil millas comienza con un solo paso (Proverbio)',
        box: { x1: 75, y1: 270, x2: 360, y2: 310 },
        confidence: 0.97,
      },
      {
        id: 'tok-4',
        textZh: '你好世界，明天会更好',
        pinyin: 'nǐ hǎo shì jiè ， míng tiān huì gèng hǎo',
        translationEs: 'Hola mundo, mañana será aún mejor',
        box: { x1: 75, y1: 330, x2: 360, y2: 370 },
        confidence: 0.96,
      },
    ]

    return {
      pageNumber,
      width,
      height,
      imageUrl: createMockPageSvg(width, height),
      tokens,
    }
  }

  async translateToken(textZh: string): Promise<TranslationResult> {
    const entry = this.mockDictionary[textZh]
    if (entry) {
      return {
        textZh,
        pinyin: entry.pinyin,
        translationEs: entry.es,
        fromCache: true,
      }
    }

    return {
      textZh,
      pinyin: 'zhōng wén',
      translationEs: `Traducción de: ${textZh}`,
      fromCache: false,
    }
  }

  async copyToClipboard(text: string): Promise<boolean> {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
    return true
  }

  async getPinyin(textZh: string): Promise<string> {
    const singlePinyinMap: Record<string, string> = {
      '窖': 'jiào',
      '欢': 'huān',
      '迎': 'yíng',
      '使': 'shǐ',
      '用': 'yòng',
      '中': 'zhōng',
      '文': 'wén',
      '翻': 'fān',
      '译': 'yì',
      '系': 'xì',
      '统': 'tǒng',
      '你': 'nǐ',
      '好': 'hǎo',
      '世': 'shì',
      '界': 'jiè',
      '谢': 'xiè',
      '学': 'xué',
      '习': 'xí',
    }
    if (singlePinyinMap[textZh]) {
      return singlePinyinMap[textZh]
    }
    const entry = this.mockDictionary[textZh]
    if (entry) {
      return entry.pinyin
    }
    return 'hàn zì'
  }

  async playAudio(_textZh: string): Promise<boolean> {
    return true
  }
}


