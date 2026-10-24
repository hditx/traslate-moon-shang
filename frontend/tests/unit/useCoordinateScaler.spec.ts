import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useCoordinateScaler } from '@/composables/useCoordinateScaler'
import type { BoundingBox } from '@/types/document'

describe('useCoordinateScaler Composable', () => {
  it('correctly scales a bounding box proportionally', () => {
    const originalWidth = ref(1000)
    const originalHeight = ref(2000)
    const renderedWidth = ref(500)   // Escala 0.5
    const renderedHeight = ref(1000) // Escala 0.5

    const { scaleBox } = useCoordinateScaler({
      originalWidth,
      originalHeight,
      renderedWidth,
      renderedHeight,
    })

    const box: BoundingBox = { x1: 100, y1: 200, x2: 300, y2: 400 }
    const scaled = scaleBox(box)

    expect(scaled.left).toBe(50)
    expect(scaled.top).toBe(100)
    expect(scaled.width).toBe(100)
    expect(scaled.height).toBe(100)
  })

  it('handles zoom scaling factor on rendered dimensions', () => {
    const originalWidth = ref(800)
    const originalHeight = ref(1200)
    const renderedWidth = ref(1200)  // Escala 1.5
    const renderedHeight = ref(1800) // Escala 1.5

    const { scaleBox } = useCoordinateScaler({
      originalWidth,
      originalHeight,
      renderedWidth,
      renderedHeight,
    })

    const box: BoundingBox = { x1: 10, y1: 20, x2: 110, y2: 60 }
    const scaled = scaleBox(box)

    expect(scaled.left).toBe(15)
    expect(scaled.top).toBe(30)
    expect(scaled.width).toBe(150)
    expect(scaled.height).toBe(60)
  })

  it('avoids division by zero when dimensions are 0', () => {
    const originalWidth = ref(0)
    const originalHeight = ref(0)
    const renderedWidth = ref(100)
    const renderedHeight = ref(100)

    const { scaleBox } = useCoordinateScaler({
      originalWidth,
      originalHeight,
      renderedWidth,
      renderedHeight,
    })

    const box: BoundingBox = { x1: 10, y1: 20, x2: 30, y2: 40 }
    const scaled = scaleBox(box)

    expect(scaled.left).toBe(0)
    expect(scaled.top).toBe(0)
    expect(scaled.width).toBe(0)
    expect(scaled.height).toBe(0)
  })
})
