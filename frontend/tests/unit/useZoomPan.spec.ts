import { describe, it, expect } from 'vitest'
import { useZoomPan } from '@/composables/useZoomPan'

describe('useZoomPan Composable', () => {
  it('initializes with default values', () => {
    const { zoom, panX, panY, isPanning } = useZoomPan()
    expect(zoom.value).toBe(1.0)
    expect(panX.value).toBe(0)
    expect(panY.value).toBe(0)
    expect(isPanning.value).toBe(false)
  })

  it('increments zoom on zoomIn within limits', () => {
    const { zoom, zoomIn } = useZoomPan({ minZoom: 0.5, maxZoom: 2.0, step: 0.25 })
    zoomIn()
    expect(zoom.value).toBe(1.25)

    // Aumentar hasta superar el límite
    zoomIn()
    zoomIn()
    zoomIn()
    zoomIn()
    zoomIn()
    expect(zoom.value).toBe(2.0)
  })

  it('decrements zoom on zoomOut within limits', () => {
    const { zoom, zoomOut } = useZoomPan({ minZoom: 0.5, maxZoom: 2.0, step: 0.25 })
    zoomOut()
    expect(zoom.value).toBe(0.75)
    zoomOut()
    expect(zoom.value).toBe(0.5)
    zoomOut()
    expect(zoom.value).toBe(0.5) // Clamped al mínimo
  })

  it('resets zoom and pan correctly', () => {
    const { zoom, panX, panY, zoomIn, resetZoom } = useZoomPan()
    zoomIn()
    panX.value = 150
    panY.value = -80

    resetZoom()
    expect(zoom.value).toBe(1.0)
    expect(panX.value).toBe(0)
    expect(panY.value).toBe(0)
  })

  it('handles panning movements', () => {
    const { panX, panY, isPanning, startPan, onPan, endPan } = useZoomPan()
    startPan(100, 100)
    expect(isPanning.value).toBe(true)

    onPan(120, 150)
    expect(panX.value).toBe(20)
    expect(panY.value).toBe(50)

    endPan()
    expect(isPanning.value).toBe(false)
  })
})
