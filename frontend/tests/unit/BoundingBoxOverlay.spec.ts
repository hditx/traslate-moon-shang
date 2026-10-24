import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BoundingBoxOverlay from '@/components/BoundingBoxOverlay.vue'
import type { DetectedToken } from '@/types/document'

describe('BoundingBoxOverlay Component', () => {
  const sampleTokens: DetectedToken[] = [
    {
      id: 'tok-1',
      textZh: '你好',
      pinyin: 'nǐ hǎo',
      translationEs: 'Hola',
      box: { x1: 50, y1: 50, x2: 150, y2: 100 },
      confidence: 0.99,
    },
    {
      id: 'tok-2',
      textZh: '世界',
      pinyin: 'shì jiè',
      translationEs: 'Mundo',
      box: { x1: 200, y1: 50, x2: 300, y2: 100 },
      confidence: 0.98,
    },
  ]

  it('renders bounding box items for each token', () => {
    const wrapper = mount(BoundingBoxOverlay, {
      props: {
        tokens: sampleTokens,
        originalWidth: 1000,
        originalHeight: 1000,
        renderedWidth: 500,  // Escala 0.5
        renderedHeight: 500, // Escala 0.5
      },
    })

    const boxes = wrapper.findAll('.bounding-box-item')
    expect(boxes.length).toBe(2)

    // Primera caja: x1: 50 -> 25px, y1: 50 -> 25px, w: 100 -> 50px, h: 50 -> 25px
    const style1 = boxes[0].attributes('style')
    expect(style1).toContain('left: 25px')
    expect(style1).toContain('top: 25px')
    expect(style1).toContain('width: 50px')
    expect(style1).toContain('height: 25px')
  })

  it('emits token-hover when pointer enters a bounding box', async () => {
    const wrapper = mount(BoundingBoxOverlay, {
      props: {
        tokens: sampleTokens,
        originalWidth: 1000,
        originalHeight: 1000,
        renderedWidth: 1000,
        renderedHeight: 1000,
      },
    })

    const box = wrapper.find('.bounding-box-item')
    await box.trigger('mouseenter')

    expect(wrapper.emitted('token-hover')).toBeTruthy()
    const emittedData = wrapper.emitted('token-hover')?.[0]?.[0] as DetectedToken
    expect(emittedData.textZh).toBe('你好')
  })

  it('emits token-leave when pointer exits', async () => {
    const wrapper = mount(BoundingBoxOverlay, {
      props: {
        tokens: sampleTokens,
        originalWidth: 1000,
        originalHeight: 1000,
        renderedWidth: 1000,
        renderedHeight: 1000,
      },
    })

    const box = wrapper.find('.bounding-box-item')
    await box.trigger('mouseleave')

    expect(wrapper.emitted('token-leave')).toBeTruthy()
  })
})
