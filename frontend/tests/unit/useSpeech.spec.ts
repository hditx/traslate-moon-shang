import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useSpeech } from '@/composables/useSpeech'
import { getDesktopBridge, setDesktopBridge } from '@/services/bridge.factory'

describe('useSpeech Composable', () => {
  beforeEach(() => {
    // Mock de SpeechSynthesis de window
    const mockSpeechSynthesis = {
      cancel: vi.fn(),
      speak: vi.fn((utterance: any) => {
        if (utterance.onstart) utterance.onstart()
        if (utterance.onend) utterance.onend()
      }),
      getVoices: vi.fn(() => [
        { name: 'Ting-Ting', lang: 'zh-CN' },
        { name: 'Google Español', lang: 'es-ES' },
      ]),
    }

    vi.stubGlobal('speechSynthesis', mockSpeechSynthesis)
    vi.stubGlobal('SpeechSynthesisUtterance', class {
      text: string
      lang: string = ''
      rate: number = 1
      voice: any = null
      onstart: any = null
      onend: any = null
      onerror: any = null
      constructor(text: string) {
        this.text = text
      }
    })
  })

  it('detects speech synthesis support', () => {
    const { hasSupport } = useSpeech()
    expect(hasSupport).toBe(true)
  })

  it('calls bridge.playAudio when bridge has playAudio implementation', async () => {
    const mockBridge = {
      ...getDesktopBridge(),
      playAudio: vi.fn(async (_text: string) => true),
    }
    setDesktopBridge(mockBridge as any)

    const { speak, isSpeaking } = useSpeech()
    const result = await speak('你好')

    expect(mockBridge.playAudio).toHaveBeenCalledWith('你好')
    expect(result).toBe(true)
    expect(isSpeaking.value).toBe(false)
  })

  it('returns false when text is empty', async () => {
    const { speak } = useSpeech()
    expect(await speak('')).toBe(false)
    expect(await speak('   ')).toBe(false)
  })

  it('falls back to speechSynthesis when bridge.playAudio returns false', async () => {
    const mockBridge = {
      ...getDesktopBridge(),
      playAudio: vi.fn(async () => false),
    }
    setDesktopBridge(mockBridge as any)

    const { speak, isSpeaking } = useSpeech()
    const result = await speak('世界')

    expect(window.speechSynthesis.speak).toHaveBeenCalled()
    expect(result).toBe(true)
    expect(isSpeaking.value).toBe(false)
  })

  it('stops ongoing speech properly', () => {
    const { stop, isSpeaking } = useSpeech()
    isSpeaking.value = true
    stop()
    expect(window.speechSynthesis.cancel).toHaveBeenCalled()
    expect(isSpeaking.value).toBe(false)
  })
})
