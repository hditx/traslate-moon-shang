<script setup lang="ts">
import { ref } from 'vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useZoomPan } from '@/composables/useZoomPan'
import type { DetectedToken } from '@/types/document'
import Toolbar from './Toolbar.vue'
import BoundingBoxOverlay from './BoundingBoxOverlay.vue'
import TranslationPopover from './TranslationPopover.vue'

const store = useDocumentStore()
const {
  zoom,
  panX,
  panY,
  isPanning,
  zoomIn,
  zoomOut,
  resetZoom,
  startPan,
  onPan,
  endPan,
  handleWheel,
} = useZoomPan({ minZoom: 0.25, maxZoom: 4.0, step: 0.15 })

const viewportRef = ref<HTMLElement | null>(null)
const isPopoverPinned = ref(false)
let leaveTimeout: ReturnType<typeof setTimeout> | null = null

function onMouseDown(event: MouseEvent) {
  // Solo iniciar paneo con el botón izquierdo y si no se está haciendo clic en un elemento interactivo
  if (event.button !== 0) return
  startPan(event.clientX, event.clientY)
}

function onMouseMove(event: MouseEvent) {
  onPan(event.clientX, event.clientY)
}

function onMouseUp() {
  endPan()
}

function onTouchStart(event: TouchEvent) {
  if (event.touches.length === 1) {
    const touch = event.touches[0]
    startPan(touch.clientX, touch.clientY)
  }
}

function onTouchMove(event: TouchEvent) {
  if (event.touches.length === 1) {
    const touch = event.touches[0]
    onPan(touch.clientX, touch.clientY)
  }
}

function onTouchEnd() {
  endPan()
}

function handleTokenHover(token: DetectedToken, rect: DOMRect) {
  if (leaveTimeout) {
    clearTimeout(leaveTimeout)
    leaveTimeout = null
  }

  // Si no está fijado, actualiza el token al pasar el puntero
  if (!isPopoverPinned.value) {
    store.setActiveToken(token, {
      top: rect.top,
      left: rect.left,
      width: rect.width,
      height: rect.height,
    })
  }
}

function handleTokenLeave() {
  if (isPopoverPinned.value) return

  // Dar 250ms de margen por si el usuario mueve el cursor hacia el popover
  leaveTimeout = setTimeout(() => {
    if (!isPopoverPinned.value) {
      store.clearActiveToken()
    }
  }, 250)
}

function handleTokenClick(token: DetectedToken, rect: DOMRect) {
  if (leaveTimeout) {
    clearTimeout(leaveTimeout)
    leaveTimeout = null
  }

  // Si se hace clic en el mismo token ya fijado, se cierra el popover
  if (isPopoverPinned.value && store.activeToken?.id === token.id) {
    closePopover()
    return
  }

  isPopoverPinned.value = true
  store.setActiveToken(token, {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  })
}

function closePopover() {
  isPopoverPinned.value = false
  store.clearActiveToken()
}

function togglePin() {
  isPopoverPinned.value = !isPopoverPinned.value
}

function onViewportClick() {
  if (!isPanning.value && store.activeToken) {
    closePopover()
  }
}
</script>

<template>
  <div class="document-viewer-container">
    <Toolbar
      :zoom="zoom"
      @zoom-in="zoomIn()"
      @zoom-out="zoomOut()"
      @zoom-reset="resetZoom()"
    />

    <!-- Estado vacío: cuando aún no se ha cargado documento -->
    <div v-if="!store.isDocumentLoaded" class="empty-state">
      <div class="empty-card" @click="store.openDocument()">
        <span class="empty-icon">📄</span>
        <h2 class="empty-title">Carga una imagen o PDF con texto en chino</h2>
        <p class="empty-subtitle">Haz clic para buscar en tus archivos (.png, .jpg, .pdf)</p>
        <button class="btn-open">Seleccionar archivo</button>
      </div>
    </div>

    <!-- Viewport interactivo con Zoom y Paneo -->
    <div
      v-else
      ref="viewportRef"
      class="viewport"
      :class="{ 'is-dragging': isPanning }"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="endPan"
      @wheel="handleWheel"
      @touchstart.passive="onTouchStart"
      @touchmove.passive="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchEnd"
      @click="onViewportClick"
    >
      <div
        class="canvas-layer"
        :style="{
          transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
        }"
      >
        <div
          v-if="store.currentPageData"
          class="document-surface"
          :style="{
            width: `${store.currentPageData.width}px`,
            height: `${store.currentPageData.height}px`,
          }"
        >
          <!-- Imagen de la página renderizada -->
          <img
            :src="store.currentPageData.imageUrl"
            alt="Página del documento"
            class="page-image"
            draggable="false"
          />

          <!-- Capa interactiva de cajas delimitadoras -->
          <BoundingBoxOverlay
            :tokens="store.tokens"
            :original-width="store.currentPageData.width"
            :original-height="store.currentPageData.height"
            :rendered-width="store.currentPageData.width"
            :rendered-height="store.currentPageData.height"
            :active-token-id="store.activeToken?.id"
            @token-hover="handleTokenHover"
            @token-leave="handleTokenLeave"
            @token-click="handleTokenClick"
          />
        </div>
      </div>

      <!-- Ventana emergente interactiva de traducción (Popover) -->
      <TranslationPopover
        :token="store.activeToken"
        :target-rect="store.activeTokenRect"
        :is-pinned="isPopoverPinned"
        @close="closePopover"
        @toggle-pin="togglePin"
      />

      <!-- Indicador de procesamiento de OCR -->
      <div v-if="store.status === 'processing_ocr'" class="loading-overlay">
        <div class="spinner"></div>
        <span>Detectando caracteres chinos con PaddleOCR...</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.document-viewer-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: var(--color-bg-primary);
}

.viewport {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  background-image: radial-gradient(rgba(51, 65, 85, 0.4) 1px, transparent 1px);
  background-size: 24px 24px;
}

.viewport.is-dragging {
  cursor: grabbing;
}

.canvas-layer {
  transform-origin: center center;
  transition: transform 0.05s linear;
  will-change: transform;
}

.document-surface {
  position: relative;
  background-color: #ffffff;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  overflow: hidden;
}

.page-image {
  width: 100%;
  height: 100%;
  display: block;
  user-select: none;
  pointer-events: none;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  background-color: var(--color-bg-secondary);
  border: 2px dashed var(--color-border);
  padding: 48px;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease;
  max-width: 480px;
  text-align: center;
}

.empty-card:hover {
  border-color: var(--color-accent);
  background-color: rgba(30, 41, 59, 0.8);
  box-shadow: 0 0 24px rgba(56, 189, 248, 0.15);
}

.empty-icon {
  font-size: 48px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.empty-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.btn-open {
  margin-top: 8px;
  background-color: var(--color-accent);
  color: #0f172a;
  border: none;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-open:hover {
  background-color: var(--color-accent-hover);
}

.loading-overlay {
  position: absolute;
  bottom: 24px;
  background-color: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  padding: 10px 20px;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  z-index: 50;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(56, 189, 248, 0.3);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .empty-card {
    padding: 28px 16px;
    width: 90%;
    max-width: 340px;
    gap: 8px;
  }
  .empty-icon {
    font-size: 36px;
  }
  .empty-title {
    font-size: 16px;
  }
  .empty-subtitle {
    font-size: 13px;
  }
  .btn-open {
    padding: 6px 16px;
    font-size: 13px;
  }
  .loading-overlay {
    bottom: 12px;
    padding: 8px 14px;
    font-size: 12px;
    gap: 8px;
  }
}
</style>
