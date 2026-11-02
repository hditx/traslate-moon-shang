import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import Toolbar from '@/components/Toolbar.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { MockDesktopBridge } from '@/services/mock.bridge'
import { setDesktopBridge } from '@/services/bridge.factory'

describe('Toolbar Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('hides camera button when on desktop (bridge.isAndroid is false)', () => {
    const mockBridge = new MockDesktopBridge()
    mockBridge.isAndroid = false
    setDesktopBridge(mockBridge)

    const wrapper = mount(Toolbar, {
      props: { zoom: 1.0 },
    })

    expect(wrapper.find('[data-testid="camera-button"]').exists()).toBe(false)
  })

  it('renders camera button when on Android (bridge.isAndroid is true)', () => {
    const mockBridge = new MockDesktopBridge()
    mockBridge.isAndroid = true
    setDesktopBridge(mockBridge)

    const wrapper = mount(Toolbar, {
      props: { zoom: 1.0 },
    })

    const cameraBtn = wrapper.find('[data-testid="camera-button"]')
    expect(cameraBtn.exists()).toBe(true)
    expect(cameraBtn.text()).toContain('Sacar foto')
  })

  it('calls store.capturePhoto when camera button is clicked', async () => {
    const mockBridge = new MockDesktopBridge()
    mockBridge.isAndroid = true
    setDesktopBridge(mockBridge)

    const store = useDocumentStore()
    const captureSpy = vi.spyOn(store, 'capturePhoto').mockResolvedValue(true)

    const wrapper = mount(Toolbar, {
      props: { zoom: 1.0 },
    })

    const cameraBtn = wrapper.find('[data-testid="camera-button"]')
    await cameraBtn.trigger('click')

    expect(captureSpy).toHaveBeenCalledOnce()
  })
})
