import { computed, type Ref } from 'vue'
import type { BoundingBox } from '@/types/document'

export interface ScaledRect {
  left: number
  top: number
  width: number
  height: number
}

export interface CoordinateScalerOptions {
  originalWidth: Ref<number>
  originalHeight: Ref<number>
  renderedWidth: Ref<number>
  renderedHeight: Ref<number>
}

export function useCoordinateScaler(options: CoordinateScalerOptions) {
  const scaleX = computed(() => {
    if (options.originalWidth.value <= 0) return 0
    return options.renderedWidth.value / options.originalWidth.value
  })

  const scaleY = computed(() => {
    if (options.originalHeight.value <= 0) return 0
    return options.renderedHeight.value / options.originalHeight.value
  })

  function scaleBox(box: BoundingBox): ScaledRect {
    const sx = scaleX.value
    const sy = scaleY.value

    if (sx === 0 || sy === 0) {
      return { left: 0, top: 0, width: 0, height: 0 }
    }

    const left = box.x1 * sx
    const top = box.y1 * sy
    const width = (box.x2 - box.x1) * sx
    const height = (box.y2 - box.y1) * sy

    return {
      left: Number(left.toFixed(2)),
      top: Number(top.toFixed(2)),
      width: Number(width.toFixed(2)),
      height: Number(height.toFixed(2)),
    }
  }

  return {
    scaleX,
    scaleY,
    scaleBox,
  }
}
