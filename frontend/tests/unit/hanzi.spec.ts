import { describe, it, expect } from 'vitest'
import { isHanzi, extractHanziList } from '@/utils/hanzi'

describe('Hanzi Utilities', () => {
  it('correctly identifies Chinese characters (Hanzi)', () => {
    expect(isHanzi('你')).toBe(true)
    expect(isHanzi('好')).toBe(true)
    expect(isHanzi('窖')).toBe(true)
    expect(isHanzi('蜡')).toBe(true)
    expect(isHanzi('烛')).toBe(true)
  })

  it('rejects punctuation, latin characters and numbers', () => {
    expect(isHanzi('a')).toBe(false)
    expect(isHanzi('Z')).toBe(false)
    expect(isHanzi('1')).toBe(false)
    expect(isHanzi('，')).toBe(false)
    expect(isHanzi('。')).toBe(false)
    expect(isHanzi('！')).toBe(false)
    expect(isHanzi(' ')).toBe(false)
    expect(isHanzi('')).toBe(false)
  })

  it('extracts list of Hanzi characters from mixed text', () => {
    const text = '你好，世界！Hello 123'
    const hanziList = extractHanziList(text)
    expect(hanziList).toEqual(['你', '好', '世', '界'])
  })

  it('returns empty list for text without Hanzi', () => {
    expect(extractHanziList('Hello world! 12345')).toEqual([])
    expect(extractHanziList('')).toEqual([])
  })
})
