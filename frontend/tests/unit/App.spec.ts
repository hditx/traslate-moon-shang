import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import App from '@/App.vue'
import { MockDesktopBridge } from '@/services/mock.bridge'
import { setDesktopBridge } from '@/services/bridge.factory'
import { useDocumentStore } from '@/stores/documentStore'

// Mock de HanziWriter
vi.mock('hanzi-writer', () => ({
  default: {
    create: vi.fn(() => ({
      animateCharacter: vi.fn(),
      loopCharacterAnimation: vi.fn(),
      quiz: vi.fn(),
      cancelQuiz: vi.fn(),
      showOutline: vi.fn(),
      hideOutline: vi.fn(),
    })),
  },
}))

describe('App Navigation and Layout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    setDesktopBridge(new MockDesktopBridge())
  })

  it('renders Dictionary as the default initial view', () => {
    const wrapper = mount(App)
    const dictTab = wrapper.find('[data-testid="nav-dictionary"]')
    expect(dictTab.classes()).toContain('active')
    expect(wrapper.findComponent({ name: 'DictionarySearch' }).exists()).toBe(true)
  })

  it('switches to Reader view when clicking Lector nav tab', async () => {
    const wrapper = mount(App)
    const readerTab = wrapper.find('[data-testid="nav-reader"]')

    await readerTab.trigger('click')

    expect(readerTab.classes()).toContain('active')
    expect(wrapper.findComponent({ name: 'DocumentViewer' }).exists()).toBe(true)
  })

  it('switches back to Dictionary view when clicking Diccionario nav tab', async () => {
    const wrapper = mount(App)
    const readerTab = wrapper.find('[data-testid="nav-reader"]')
    const dictTab = wrapper.find('[data-testid="nav-dictionary"]')

    await readerTab.trigger('click')
    expect(wrapper.findComponent({ name: 'DocumentViewer' }).exists()).toBe(true)

    await dictTab.trigger('click')
    expect(dictTab.classes()).toContain('active')
    expect(wrapper.findComponent({ name: 'DictionarySearch' }).exists()).toBe(true)
  })

  it('calls capturePhoto and navigates to reader when camera action is clicked on Android', async () => {
    const mockBridge = new MockDesktopBridge()
    mockBridge.isAndroid = true
    setDesktopBridge(mockBridge)

    const store = useDocumentStore()
    const captureSpy = vi.spyOn(store, 'capturePhoto').mockResolvedValue(true)

    const wrapper = mount(App)
    const cameraBtn = wrapper.find('[data-testid="nav-camera"]')

    await cameraBtn.trigger('click')
    await flushPromises()

    expect(captureSpy).toHaveBeenCalledOnce()
    expect(wrapper.findComponent({ name: 'DocumentViewer' }).exists()).toBe(true)
  })
})
