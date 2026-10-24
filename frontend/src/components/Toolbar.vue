<script setup lang="ts">
import { useDocumentStore } from '@/stores/documentStore'

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
        <span class="icon">📂</span>
        <span class="btn-text-full">Abrir archivo</span>
        <span class="btn-text-short">Abrir</span>
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
        ◀
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
        ▶
      </button>
    </div>

    <!-- Grupo derecho: Controles de Zoom -->
    <div v-if="store.isDocumentLoaded" class="toolbar-group zoom-controls">
      <button class="btn btn-icon" title="Alejar (Zoom -)" @click="emit('zoom-out')">
        −
      </button>

      <span class="zoom-indicator" title="Doble clic para restablecer (100%)" @click="emit('zoom-reset')">
        {{ Math.round(zoom * 100) }}%
      </span>

      <button class="btn btn-icon" title="Acercar (Zoom +)" @click="emit('zoom-in')">
        +
      </button>

      <button class="btn btn-subtle btn-reset" title="Restablecer vista a 100%" @click="emit('zoom-reset')">
        <span class="reset-icon">↺</span>
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
  border-bottom: 1px solid var(--color-border);
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

.reset-icon {
  display: none;
  font-size: 15px;
  line-height: 1;
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
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--color-accent);
  color: #0f172a;
  border-color: transparent;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
}

.btn-icon {
  background-color: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border-color: var(--color-border);
  width: 32px;
  height: 32px;
  padding: 0;
  justify-content: center;
  font-size: 14px;
}

.btn-icon:hover:not(:disabled) {
  background-color: #475569;
  border-color: var(--color-accent);
}

.btn-subtle {
  background: transparent;
  color: var(--color-text-secondary);
  padding: 4px 8px;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.btn-subtle:hover {
  color: var(--color-text-primary);
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
  background-color: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
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
}

.zoom-indicator:hover {
  background-color: var(--color-bg-tertiary);
  color: var(--color-text-primary);
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
    font-size: 13px;
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
    background-color: #475569;
    border-color: var(--color-accent);
  }

  .reset-text {
    display: none;
  }

  .reset-icon {
    display: inline-block;
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
