<script setup lang="ts">
import { ref } from 'vue'
import DocumentViewer from '@/components/DocumentViewer.vue'
import DictionarySearch from '@/components/DictionarySearch.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { IconSearch, IconDocument, IconCamera } from '@/components/icons'

const currentTab = ref<'dictionary' | 'reader'>('dictionary')
const store = useDocumentStore()

async function handleCameraClick() {
  if (store.canCapturePhoto) {
    const success = await store.capturePhoto()
    if (success) {
      currentTab.value = 'reader'
    }
  } else {
    // Si estamos en entorno sin cámara directa, abre selector de archivos
    const success = await store.openDocument()
    if (success) {
      currentTab.value = 'reader'
    }
  }
}

function handleReaderClick() {
  currentTab.value = 'reader'
}

function handleDictionaryClick() {
  currentTab.value = 'dictionary'
}
</script>

<template>
  <div class="app-layout">
    <!-- Vista principal con soporte de caché de estado (KeepAlive) -->
    <main class="main-content">
      <KeepAlive>
        <DictionarySearch
          v-if="currentTab === 'dictionary'"
          @navigate-reader="currentTab = 'reader'"
          @capture-photo="handleCameraClick"
        />
        <DocumentViewer
          v-else-if="currentTab === 'reader'"
        />
      </KeepAlive>
    </main>

    <!-- Barra de navegación inferior ergónomica (Oro Antiguo Erudito) -->
    <nav class="bottom-nav">
      <button
        class="nav-tab"
        :class="{ active: currentTab === 'dictionary' }"
        data-testid="nav-dictionary"
        @click="handleDictionaryClick"
      >
        <IconSearch :size="18" />
        <span class="nav-label">Diccionario</span>
      </button>

      <!-- Botón central destacado para tomar foto / escaneo rápido -->
      <button
        class="nav-action-camera"
        data-testid="nav-camera"
        title="Tomar foto para traducción instantánea"
        @click="handleCameraClick"
      >
        <IconCamera :size="17" />
        <span class="camera-label">{{ store.canCapturePhoto ? 'Sacar Foto' : 'Escanear' }}</span>
      </button>

      <button
        class="nav-tab"
        :class="{ active: currentTab === 'reader' }"
        data-testid="nav-reader"
        @click="handleReaderClick"
      >
        <IconDocument :size="18" />
        <span class="nav-label">Lector</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background-color: var(--color-bg-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: calc(100% - 56px);
  overflow: hidden;
  position: relative;
}

.bottom-nav {
  display: flex;
  align-items: center;
  justify-content: space-around;
  background-color: var(--color-bg-secondary);
  border-top: 1px solid rgba(197, 160, 89, 0.24);
  padding: 6px 16px;
  min-height: 56px;
  height: 56px;
  z-index: 50;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.35);
  flex-shrink: 0;
}

.nav-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 16px;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
  user-select: none;
}

.nav-tab:hover {
  color: var(--color-accent-hover);
}

.nav-tab.active {
  color: var(--color-accent-hover);
  font-weight: 600;
}

.nav-action-camera {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: var(--color-jade-btn);
  color: #f0f7f2;
  border: 1px solid var(--color-jade-border);
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 18px;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 10px rgba(36, 75, 56, 0.35);
  user-select: none;
}

.nav-action-camera:hover {
  background-color: var(--color-jade-btn-hover);
  box-shadow: 0 4px 14px rgba(46, 93, 70, 0.45);
  transform: translateY(-1px);
}

.camera-label {
  white-space: nowrap;
}

@media (max-width: 480px) {
  .bottom-nav {
    padding: 4px 8px;
  }
  .nav-tab {
    padding: 4px 10px;
  }
  .nav-action-camera {
    padding: 6px 14px;
    font-size: 11px;
  }
}
</style>
