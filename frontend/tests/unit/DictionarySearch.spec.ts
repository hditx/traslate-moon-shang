import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import DictionarySearch from '@/components/DictionarySearch.vue'
import { MockDesktopBridge } from '@/services/mock.bridge'
import { setDesktopBridge } from '@/services/bridge.factory'

// Mock de HanziWriter para entorno JSDOM
vi.mock('hanzi-writer', () => {
  return {
    default: {
      create: vi.fn((_element: any, _char: string, options?: any) => {
        setTimeout(() => {
          options?.onLoadCharDataSuccess?.({
            strokes: ['stroke1', 'stroke2', 'stroke3'],
          })
        }, 10)

        return {
          animateCharacter: vi.fn(),
          loopCharacterAnimation: vi.fn(),
          quiz: vi.fn((quizOptions?: any) => {
            quizOptions?.onCorrectStroke?.({ strokeNum: 0 })
          }),
          cancelQuiz: vi.fn(),
          showOutline: vi.fn(),
          hideOutline: vi.fn(),
        }
      }),
    },
  }
})

describe('DictionarySearch Component', () => {
  beforeEach(() => {
    setDesktopBridge(new MockDesktopBridge())
    vi.stubGlobal('speechSynthesis', {
      cancel: vi.fn(),
      speak: vi.fn(),
      getVoices: vi.fn(() => []),
    })
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText: vi.fn(() => Promise.resolve()),
      },
    })
  })

  it('renders initial default dictionary entry', () => {
    const wrapper = mount(DictionarySearch)
    expect(wrapper.text()).toContain('学习')
    expect(wrapper.text()).toContain('xué xí')
    expect(wrapper.text()).toContain('Estudiar, aprender')
  })

  it('filters and displays suggestions when typing in search input', async () => {
    const wrapper = mount(DictionarySearch)
    const input = wrapper.find('.search-input')

    await input.setValue('nihao')
    expect(wrapper.find('.suggestions-dropdown').exists()).toBe(true)
    expect(wrapper.text()).toContain('你好')

    // Clic en la sugerencia
    const suggestion = wrapper.find('.suggestion-item')
    await suggestion.trigger('click')

    expect(wrapper.find('.hanzi-display').text()).toBe('你好')
    expect(wrapper.text()).toContain('Hola, saludos')
  })

  it('switches word when clicking on quick chip', async () => {
    const wrapper = mount(DictionarySearch)
    const chips = wrapper.findAll('.chip-btn')
    expect(chips.length).toBeGreaterThan(1)

    // Buscar el chip de "中国" o el segundo chip
    const secondChip = chips[1]
    const chipText = secondChip.text()
    await secondChip.trigger('click')

    expect(wrapper.find('.hanzi-display').text()).toBe(chipText)
  })

  it('triggers speech audio when clicking speaker button', async () => {
    const bridge = new MockDesktopBridge()
    const playAudioSpy = vi.spyOn(bridge, 'playAudio').mockResolvedValue(true)
    setDesktopBridge(bridge)

    const wrapper = mount(DictionarySearch)
    const speakerBtn = wrapper.find('.audio-speaker-btn')
    await speakerBtn.trigger('click')

    expect(playAudioSpy).toHaveBeenCalledWith('学习')
  })

  it('switches between characters in multicharacter words', async () => {
    const wrapper = mount(DictionarySearch)
    const charTabs = wrapper.findAll('.char-tab-btn')
    expect(charTabs.length).toBe(2) // '学' y '习'

    await charTabs[1].trigger('click')
    expect(charTabs[1].classes()).toContain('active')
  })

  it('emits navigate-reader when clicking "Ir al Lector"', async () => {
    const wrapper = mount(DictionarySearch)
    const jumpBtn = wrapper.find('.btn-reader-jump')
    await jumpBtn.trigger('click')

    expect(wrapper.emitted('navigate-reader')).toBeTruthy()
  })
})
