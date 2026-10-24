import { ref } from 'vue'

export interface ZoomPanOptions {
  minZoom?: number
  maxZoom?: number
  step?: number
  initialZoom?: number
}

export function useZoomPan(options: ZoomPanOptions = {}) {
  const minZoom = options.minZoom ?? 0.2
  const maxZoom = options.maxZoom ?? 4.0
  const step = options.step ?? 0.2
  const initialZoom = options.initialZoom ?? 1.0

  const zoom = ref(initialZoom)
  const panX = ref(0)
  const panY = ref(0)
  const isPanning = ref(false)

  let startClientX = 0
  let startClientY = 0
  let startPanX = 0
  let startPanY = 0

  function clampZoom(value: number): number {
    return Math.min(Math.max(value, minZoom), maxZoom)
  }

  function setZoom(value: number): void {
    zoom.value = Number(clampZoom(value).toFixed(2))
  }

  function zoomIn(customStep?: number): void {
    setZoom(zoom.value + (customStep ?? step))
  }

  function zoomOut(customStep?: number): void {
    setZoom(zoom.value - (customStep ?? step))
  }

  function resetZoom(): void {
    zoom.value = initialZoom
    panX.value = 0
    panY.value = 0
  }

  function startPan(clientX: number, clientY: number): void {
    isPanning.value = true
    startClientX = clientX
    startClientY = clientY
    startPanX = panX.value
    startPanY = panY.value
  }

  function onPan(clientX: number, clientY: number): void {
    if (!isPanning.value) return
    const deltaX = clientX - startClientX
    const deltaY = clientY - startClientY
    panX.value = startPanX + deltaX
    panY.value = startPanY + deltaY
  }

  function endPan(): void {
    isPanning.value = false
  }

  function handleWheel(event: WheelEvent): void {
    if (event.ctrlKey || event.metaKey) {
      // Zoom con Ctrl + Rueda
      event.preventDefault()
      const direction = event.deltaY < 0 ? 1 : -1
      if (direction > 0) {
        zoomIn(0.1)
      } else {
        zoomOut(0.1)
      }
    }
  }

  return {
    zoom,
    panX,
    panY,
    isPanning,
    zoomIn,
    zoomOut,
    setZoom,
    resetZoom,
    startPan,
    onPan,
    endPan,
    handleWheel,
  }
}
