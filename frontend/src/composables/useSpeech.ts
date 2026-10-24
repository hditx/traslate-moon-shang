import { ref } from 'vue'
import { getDesktopBridge } from '@/services/bridge.factory'

export function useSpeech() {
  const isSpeaking = ref(false)
  const hasSupport = typeof window !== 'undefined'

  async function speak(text: string, lang = 'zh-CN'): Promise<boolean> {
    if (!text || !text.trim()) {
      return false
    }

    const cleanedText = text.trim()
    isSpeaking.value = true

    // 1. Prioridad: Bridge nativo de escritorio (audio directo en el SO sin depender del navegador)
    try {
      const bridge = getDesktopBridge()
      if (typeof bridge.playAudio === 'function') {
        const played = await bridge.playAudio(cleanedText)
        if (played) {
          isSpeaking.value = false
          return true
        }
      }
    } catch (err) {
      console.warn('Fallo en reproducción vía bridge nativo, intentando fallback web:', err)
    }

    // 2. Respaldo Web: HTML5 Audio con Google TTS
    if (typeof Audio !== 'undefined') {
      try {
        const encoded = encodeURIComponent(cleanedText)
        const ttsUrl = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encoded}&tl=zh-CN&client=tw-ob`
        const audio = new Audio(ttsUrl)

        const played = await new Promise<boolean>((resolve) => {
          audio.onended = () => resolve(true)
          audio.onerror = () => resolve(false)
          audio.play().catch(() => resolve(false))
        })

        if (played) {
          isSpeaking.value = false
          return true
        }
      } catch {
        // Continuar al siguiente fallback
      }
    }

    // 3. Respaldo Web Estándar: window.speechSynthesis
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      return new Promise((resolve) => {
        window.speechSynthesis.cancel()

        const utterance = new SpeechSynthesisUtterance(cleanedText)
        utterance.lang = lang
        utterance.rate = 0.85

        const voices = window.speechSynthesis.getVoices()
        const chineseVoice = voices.find(
          (v) => v.lang.startsWith('zh') || v.name.toLowerCase().includes('chinese')
        )
        if (chineseVoice) {
          utterance.voice = chineseVoice
        }

        utterance.onend = () => {
          isSpeaking.value = false
          resolve(true)
        }

        utterance.onerror = () => {
          isSpeaking.value = false
          resolve(false)
        }

        window.speechSynthesis.speak(utterance)
      })
    }

    isSpeaking.value = false
    return false
  }

  function stop(): void {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    isSpeaking.value = false
  }

  return {
    isSpeaking,
    hasSupport,
    speak,
    stop,
  }
}

