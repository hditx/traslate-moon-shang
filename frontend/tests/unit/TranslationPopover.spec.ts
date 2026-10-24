import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import TranslationPopover from '@/components/TranslationPopover.vue'
import type { DetectedToken } from '@/types/document'

describe('TranslationPopover Component', () => {
  const sampleToken: DetectedToken = {
    id: 'tok-1',
    textZh: '谢谢',
    pinyin: 'xiè xie',
    translationEs: 'Gracias',
    box: { x1: 50, y1: 50, x2: 150, y2: 100 },
    confidence: 0.98,
  }

  const sampleRect = {
    top: 100,
    left: 200,
    width: 100,
    height: 50,
  }

  beforeEach(() => {
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

  it('renders token information correctly', () => {
    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
        isPinned: false,
      },
    })

    expect(wrapper.text()).toContain('谢谢')
    expect(wrapper.text()).toContain('xiè xie')
    expect(wrapper.text()).toContain('Gracias')
    expect(wrapper.text()).toContain('98% precisión')
  })

  it('emits close when close button is clicked', async () => {
    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
      },
    })

    const closeBtn = wrapper.find('.close-btn')
    await closeBtn.trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits toggle-pin when pin button is clicked', async () => {
    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
        isPinned: false,
      },
    })

    const pinBtn = wrapper.find('.pin-btn')
    await pinBtn.trigger('click')

    expect(wrapper.emitted('toggle-pin')).toBeTruthy()
  })

  it('copies text to clipboard when copy button is clicked', async () => {
    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
      },
    })

    const copyButtons = wrapper.findAll('.btn-footer')
    await copyButtons[0].trigger('click') // Copiar chino

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('谢谢')
  })

  it('closes on Escape key press', () => {
    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
      },
    })

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders interactive hanzi character elements', () => {
    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
      },
    })

    const hanziChars = wrapper.findAll('.hanzi-char')
    expect(hanziChars.length).toBe(2) // '谢', '谢'
    expect(hanziChars[0].text()).toBe('谢')
  })

  it('opens StrokeOrderModal when clicking a character or stroke button', async () => {
    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
      },
    })

    const strokeBtn = wrapper.find('.stroke-btn')
    expect(strokeBtn.exists()).toBe(true)

    // Clic en el botón de trazos
    await strokeBtn.trigger('click')
    const modal = wrapper.findComponent({ name: 'StrokeOrderModal' })
    expect(modal.exists()).toBe(true)
    expect(modal.props('isOpen')).toBe(true)
    expect(modal.props('initialCharacter')).toBe('谢')
  })

  it('prevents ghost click on touch devices immediately after opening', async () => {
    vi.stubGlobal('matchMedia', vi.fn().mockImplementation((query: string) => ({
      matches: query === '(pointer: coarse)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })))

    const wrapper = mount(TranslationPopover, {
      props: {
        token: sampleToken,
        targetRect: sampleRect,
      },
    })

    const strokeBtn = wrapper.find('.stroke-btn')
    // Click inmediato tras montaje en dispositivo táctil (simulando ghost click < 400ms)
    await strokeBtn.trigger('click')

    const modal = wrapper.findComponent({ name: 'StrokeOrderModal' })
    expect(modal.props('isOpen')).toBe(false)
  })
})

