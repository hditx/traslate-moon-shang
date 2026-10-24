import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import App from '@/App.vue'
import type { DetectedToken, BoundingBox } from '@/types/document'

describe('Frontend Environment & Sanity Check', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders App component properly with DocumentViewer', () => {
    const wrapper = mount(App)
    expect(wrapper.text()).toContain('Carga una imagen o PDF con texto en chino')
    expect(wrapper.find('.empty-card').exists()).toBe(true)
  })

  it('correctly types BoundingBox and DetectedToken interfaces', () => {
    const box: BoundingBox = { x1: 0, y1: 0, x2: 100, y2: 50 }
    const token: DetectedToken = {
      id: 'token-1',
      textZh: '谢谢',
      pinyin: 'xiè xie',
      translationEs: 'Gracias',
      box,
      confidence: 0.98,
    }

    expect(token.textZh).toBe('谢谢')
    expect(token.pinyin).toBe('xiè xie')
    expect(token.box.x2 - token.box.x1).toBe(100)
  })
})
