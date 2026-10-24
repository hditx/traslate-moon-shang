import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import StrokeOrderModal from '@/components/StrokeOrderModal.vue'

// Mock de HanziWriter para entorno de pruebas JSDOM
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

describe('StrokeOrderModal Component', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    vi.stubGlobal('speechSynthesis', {
      cancel: vi.fn(),
      speak: vi.fn(),
      getVoices: vi.fn(() => []),
    })
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('renders modal in document.body when isOpen is true', () => {
    mount(StrokeOrderModal, {
      props: {
        isOpen: true,
        initialCharacter: '窖',
        characterList: ['窖', '蜡', '烛'],
      },
      attachTo: document.body,
    })

    expect(document.body.textContent).toContain('Caligrafía y Trazos (笔顺)')
    expect(document.body.textContent).toContain('窖')
    expect(document.body.textContent).toContain('蜡')
    expect(document.body.textContent).toContain('烛')
  })

  it('emits close when clicking the close button', async () => {
    const wrapper = mount(StrokeOrderModal, {
      props: {
        isOpen: true,
        initialCharacter: '窖',
      },
      attachTo: document.body,
    })

    const closeBtn = document.body.querySelector('.btn-close') as HTMLButtonElement
    expect(closeBtn).toBeTruthy()
    closeBtn.click()

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('switches characters when clicking on character strip', async () => {
    const wrapper = mount(StrokeOrderModal, {
      props: {
        isOpen: true,
        initialCharacter: '窖',
        characterList: ['窖', '蜡', '烛'],
      },
      attachTo: document.body,
    })

    const chips = document.body.querySelectorAll('.char-chip')
    expect(chips.length).toBe(3)

    ;(chips[1] as HTMLElement).click() // Clic en '蜡'
    expect(wrapper.emitted('select-character')?.[0]).toEqual(['蜡'])
    expect(document.body.textContent).toContain('蜡')
  })

  it('switches between animation mode and practice mode', async () => {
    mount(StrokeOrderModal, {
      props: {
        isOpen: true,
        initialCharacter: '书',
      },
      attachTo: document.body,
    })

    const tabs = document.body.querySelectorAll('.tab-btn')
    expect(tabs.length).toBe(2)

    ;(tabs[1] as HTMLElement).click() // Activar modo práctica
    await new Promise((r) => setTimeout(r, 20))
    expect(document.body.textContent).toContain('Practicar Escritura')

    ;(tabs[0] as HTMLElement).click() // Volver a animación
    await new Promise((r) => setTimeout(r, 20))
    expect(document.body.textContent).toContain('Animación de Trazos')
  })

  it('emits close on Escape key press', () => {
    const wrapper = mount(StrokeOrderModal, {
      props: {
        isOpen: true,
        initialCharacter: '学',
      },
      attachTo: document.body,
    })

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('fetches and displays pinyin badge and handles pronunciation click', async () => {
    mount(StrokeOrderModal, {
      props: {
        isOpen: true,
        initialCharacter: '窖',
      },
      attachTo: document.body,
    })

    await new Promise((r) => setTimeout(r, 20))

    const pinyinBadge = document.body.querySelector('.pinyin-badge')
    expect(pinyinBadge).toBeTruthy()
    expect(pinyinBadge?.textContent).toContain('jiào')

    const audioBtn = document.body.querySelector('.audio-btn') as HTMLButtonElement
    expect(audioBtn).toBeTruthy()
    audioBtn.click()
  })
})
