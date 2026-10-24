<script setup lang="ts">
import { toRef } from 'vue'
import type { DetectedToken } from '@/types/document'
import { useCoordinateScaler } from '@/composables/useCoordinateScaler'

const props = defineProps<{
  tokens: DetectedToken[]
  originalWidth: number
  originalHeight: number
  renderedWidth: number
  renderedHeight: number
  activeTokenId?: string
}>()

const emit = defineEmits<{
  (e: 'token-hover', token: DetectedToken, rect: DOMRect): void
  (e: 'token-leave'): void
  (e: 'token-click', token: DetectedToken, rect: DOMRect): void
}>()

const { scaleBox } = useCoordinateScaler({
  originalWidth: toRef(props, 'originalWidth'),
  originalHeight: toRef(props, 'originalHeight'),
  renderedWidth: toRef(props, 'renderedWidth'),
  renderedHeight: toRef(props, 'renderedHeight'),
})

function handleMouseEnter(token: DetectedToken, event: MouseEvent) {
  // En dispositivos móviles / pantallas táctiles no disparamos hover para no adelantar
  // la aparición del popover antes de que termine el tap del usuario (evita ghost clicks).
  if (
    typeof window !== 'undefined' &&
    (window.matchMedia?.('(pointer: coarse)').matches ||
      (event as PointerEvent).pointerType === 'touch')
  ) {
    return
  }
  const target = event.currentTarget as HTMLElement
  emit('token-hover', token, target.getBoundingClientRect())
}

function handleClick(token: DetectedToken, event: MouseEvent) {
  event.stopPropagation()
  const target = event.currentTarget as HTMLElement
  emit('token-click', token, target.getBoundingClientRect())
}
</script>

<template>
  <div
    class="bounding-box-overlay"
    :style="{
      width: `${renderedWidth}px`,
      height: `${renderedHeight}px`,
    }"
  >
    <div
      v-for="token in tokens"
      :key="token.id"
      class="bounding-box-item"
      :class="{
        'is-active': activeTokenId === token.id,
      }"
      :style="{
        left: `${scaleBox(token.box).left}px`,
        top: `${scaleBox(token.box).top}px`,
        width: `${scaleBox(token.box).width}px`,
        height: `${scaleBox(token.box).height}px`,
      }"
      @mouseenter="handleMouseEnter(token, $event)"
      @mouseleave="emit('token-leave')"
      @click="handleClick(token, $event)"
    />
  </div>
</template>

<style scoped>
.bounding-box-overlay {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  user-select: none;
}

.bounding-box-item {
  position: absolute;
  pointer-events: auto;
  border: 1.5px solid rgba(56, 189, 248, 0.4);
  background-color: rgba(56, 189, 248, 0.08);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.bounding-box-item:hover {
  border-color: #38bdf8;
  background-color: rgba(56, 189, 248, 0.25);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.45);
  transform: scale(1.02);
  z-index: 10;
}

.bounding-box-item.is-active {
  border-color: #f59e0b;
  background-color: rgba(245, 158, 11, 0.3);
  box-shadow: 0 0 14px rgba(245, 158, 11, 0.6);
  z-index: 20;
}
</style>
