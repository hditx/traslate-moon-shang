export interface DictionaryEntry {
  id: string
  hanzi: string
  pinyin: string
  pinyinNormalized: string
  translationEs: string
  category?: string
  level?: string
  radical?: string
  totalStrokes?: number
  examples?: Array<{
    chinese: string
    pinyin: string
    spanish: string
  }>
}
