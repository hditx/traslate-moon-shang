<script setup lang="ts">
import { useDocumentStore } from '@/stores/documentStore'
import {
  IconFolder,
  IconCamera,
  IconChevronLeft,
  IconChevronRight,
  IconZoomIn,
  IconZoomOut,
  IconReset,
} from '@/components/icons'

defineProps<{
  zoom: number
}>()

const emit = defineEmits<{
  (e: 'zoom-in'): void
  (e: 'zoom-out'): void
  (e: 'zoom-reset'): void
}>()

const store = useDocumentStore()
</script>

<template>
  <nav class="toolbar">
    <!-- Grupo izquierdo: Abrir archivo y título -->
    <div class="toolbar-group file-group">
      <button class="btn btn-primary" title="Abrir archivo" @click="store.openDocument()">
        <IconFolder :size="15" />
        <span class="btn-text-full">Abrir archivo</span>
        <span class="btn-text-short">Abrir</span>
      </button>

      <button
        v-if="store.canCapturePhoto"
        class="btn btn-camera"
        title="Sacar foto para traducir"
        data-testid="camera-button"
        @click="store.capturePhoto()"
      >
        <IconCamera :size="15" />
        <span class="btn-text-full">Sacar foto</span>
        <span class="btn-text-short">Foto</span>
      </button>

      <div v-if="store.currentDocument" class="file-badge" :title="store.currentDocument.filename">
        <span class="file-name">{{ store.currentDocument.filename }}</span>
        <span class="file-type">{{ store.currentDocument.fileType.toUpperCase() }}</span>
      </div>
    </div>

    <!-- Grupo central: Navegación de páginas (si es multipágina) -->
    <div v-if="store.isDocumentLoaded && store.totalPages > 1" class="toolbar-group page-controls">
      <button
        class="btn btn-icon"
        :disabled="store.currentPageNumber <= 1"
        title="Página anterior"
        @click="store.prevPage()"
      >
        <IconChevronLeft :size="13" />
      </button>

      <span class="page-indicator">
        <span class="page-full">Pág. <strong>{{ store.currentPageNumber }}</strong> de {{ store.totalPages }}</span>
        <span class="page-short"><strong>{{ store.currentPageNumber }}</strong>/{{ store.totalPages }}</span>
      </span>

      <button
        class="btn btn-icon"
        :disabled="store.currentPageNumber >= store.totalPages"
        title="Página siguiente"
        @click="store.nextPage()"
      >
        <IconChevronRight :size="13" />
      </button>
    </div>

    <!-- Grupo derecho: Controles de Zoom -->
    <div v-if="store.isDocumentLoaded" class="toolbar-group zoom-controls">
      <button class="btn btn-icon" title="Alejar (Zoom -)" @click="emit('zoom-out')">
        <IconZoomOut :size="13" />
      </button>

      <span class="zoom-indicator" title="Doble clic para restablecer (100%)" @click="emit('zoom-reset')">
        {{ Math.round(zoom * 100) }}%
      </span>

      <button class="btn btn-icon" title="Acercar (Zoom +)" @click="emit('zoom-in')">
        <IconZoomIn :size="13" />
      </button>

      <button class="btn btn-subtle btn-reset" title="Restablecer vista a 100%" @click="emit('zoom-reset')">
        <IconReset :size="13" />
        <span class="reset-text">Restablecer</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid rgba(197, 160, 89, 0.22);
  padding: 6px 14px;
  min-height: 48px;
  gap: 8px;
  z-index: 30;
  box-sizing: border-box;
  width: 100%;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.file-group {
  flex-shrink: 1;
  min-width: 0;
}

.btn-text-short {
  display: none;
}

.page-short {
  display: none;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--color-accent);
  color: #11141a;
  border-color: rgba(212, 175, 55, 0.4);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(197, 160, 89, 0.2);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  box-shadow: 0 2px 14px rgba(197, 160, 89, 0.35);
  transform: translateY(-1px);
}

.btn-camera {
  background-color: var(--color-jade-btn);
  color: #f0f7f2;
  border-color: var(--color-jade-border);
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(36, 75, 56, 0.25);
}

.btn-camera:hover:not(:disabled) {
  background-color: var(--color-jade-btn-hover);
  box-shadow: 0 2px 12px rgba(46, 93, 70, 0.35);
  transform: translateY(-1px);
}

.btn-icon {
  background-color: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border-color: var(--color-border);
  width: 30px;
  height: 30px;
  padding: 0;
  justify-content: center;
}

.btn-icon:hover:not(:disabled) {
  background-color: #2a3344;
  border-color: var(--color-accent);
  color: var(--color-accent-hover);
}

.btn-subtle {
  background: transparent;
  color: var(--color-text-secondary);
  padding: 4px 8px;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
}

.btn-subtle:hover {
  color: var(--color-accent-hover);
  background-color: var(--color-accent-subtle);
}

.file-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: var(--color-bg-tertiary);
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 12px;
  border: 1px solid var(--color-border);
  flex-shrink: 1;
  min-width: 0;
}

.file-name {
  color: var(--color-text-primary);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-type {
  background-color: rgba(197, 160, 89, 0.16);
  color: #d4af37;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
  border: 1px solid rgba(197, 160, 89, 0.25);
}

.page-indicator, .zoom-indicator {
  font-size: 13px;
  color: var(--color-text-secondary);
  min-width: 48px;
  text-align: center;
  user-select: none;
}

.zoom-indicator {
  cursor: pointer;
  padding: 4px 6px;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.zoom-indicator:hover {
  background-color: var(--color-bg-tertiary);
  color: var(--color-accent-hover);
}

/* Adaptación responsive para dispositivos móviles */
@media (max-width: 640px) {
  .toolbar {
    padding: 6px 8px;
    gap: 6px;
  }

  .toolbar-group {
    gap: 4px;
  }

  .btn {
    padding: 5px 8px;
    font-size: 12px;
  }

  .btn-text-full {
    display: none;
  }

  .btn-text-short {
    display: inline;
  }

  .file-badge {
    padding: 2px 6px;
    font-size: 11px;
    max-width: 110px;
  }

  .file-name {
    max-width: 70px;
  }

  .file-type {
    font-size: 9px;
    padding: 1px 4px;
  }

  .btn-icon {
    width: 28px;
    height: 28px;
  }

  .zoom-indicator {
    min-width: 36px;
    font-size: 12px;
    padding: 2px 4px;
  }

  .btn-reset {
    width: 28px;
    height: 28px;
    padding: 0;
    justify-content: center;
    border-radius: var(--radius-sm);
    background-color: var(--color-bg-tertiary);
    border: 1px solid var(--color-border);
    color: var(--color-text-primary);
  }

  .btn-reset:hover {
    background-color: #2a3344;
    border-color: var(--color-accent);
    color: var(--color-accent-hover);
  }

  .reset-text {
    display: none;
  }

  .page-full {
    display: none;
  }

  .page-short {
    display: inline;
    font-size: 12px;
  }
}

@media (max-width: 380px) {
  .file-badge {
    display: none;
  }
}
</style>
