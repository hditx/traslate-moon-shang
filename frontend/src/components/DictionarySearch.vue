<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import HanziWriter from 'hanzi-writer'
import { isHanzi, extractHanziList } from '@/utils/hanzi'
import { useSpeech } from '@/composables/useSpeech'
import { getDesktopBridge } from '@/services/bridge.factory'
import { DICTIONARY_ENTRIES, searchDictionary } from '@/data/dictionaryData'
import type { DictionaryEntry } from '@/types/dictionary'
import {
  IconSearch,
  IconSpeaker,
  IconClose,
  IconCopy,
  IconCheck,
  IconDocument,
} from '@/components/icons'

const emit = defineEmits<{
  (e: 'navigate-reader'): void
  (e: 'capture-photo'): void
}>()

const searchQuery = ref('')
const isSearching = ref(false)
const selectedEntry = ref<DictionaryEntry | null>(DICTIONARY_ENTRIES[0]) // Por defecto "学习"
const activeChar = ref<string>('')
const activeMode = ref<'animate' | 'practice'>('animate')
const speed = ref<number>(1.0)
const isLooping = ref<boolean>(false)
const copiedField = ref<'zh' | 'es' | null>(null)

// Estados de práctica caligráfica
const quizProgress = ref<{ currentStroke: number; totalStrokes: number } | null>(null)
const quizMistakes = ref<number>(0)
const isQuizCompleted = ref<boolean>(false)

const writerContainerRef = ref<HTMLElement | null>(null)
let writerInstance: any = null

const { speak, isSpeaking } = useSpeech()
const bridge = getDesktopBridge()

// Sugerencias en tiempo real
const suggestions = computed(() => {
  if (!searchQuery.value.trim()) return []
  return searchDictionary(searchQuery.value).slice(0, 6)
})

// Lista de caracteres individuales para descomponer la palabra
const wordHanziList = computed(() => {
  if (!selectedEntry.value?.hanzi) return []
  return extractHanziList(selectedEntry.value.hanzi)
})

watch(
  () => selectedEntry.value,
  (newEntry) => {
    if (newEntry) {
      const chars = extractHanziList(newEntry.hanzi)
      activeChar.value = chars[0] || ''
      activeMode.value = 'animate'
      nextTick(() => {
        initOrUpdateWriter()
      })
    }
  },
  { immediate: true },
)

watch(
  () => activeChar.value,
  (newChar) => {
    if (newChar && isHanzi(newChar)) {
      nextTick(() => {
        initOrUpdateWriter()
      })
    }
  },
)

function cleanupWriter() {
  if (writerInstance) {
    try {
      writerInstance.cancelQuiz?.()
    } catch {
      // Ignorar errores al cancelar
    }
    writerInstance = null
  }
  if (writerContainerRef.value) {
    writerContainerRef.value.innerHTML = ''
  }
}

function initOrUpdateWriter() {
  if (!writerContainerRef.value || !activeChar.value || !isHanzi(activeChar.value)) return

  cleanupWriter()
  isQuizCompleted.value = false
  quizMistakes.value = 0
  quizProgress.value = null

  try {
    writerInstance = HanziWriter.create(writerContainerRef.value, activeChar.value, {
      width: 190,
      height: 190,
      padding: 10,
      showOutline: true,
      strokeAnimationSpeed: speed.value,
      delayBetweenStrokes: 160,
      strokeColor: '#c5a059', // Oro antiguo erudito
      radicalColor: '#d4af37', // Oro brillante para radicales
      outlineColor: 'rgba(212, 197, 169, 0.22)', // Silueta pergamino
      highlightColor: '#4e8752', // Verde jade erudito
      drawingColor: '#c5a059',
      drawingWidth: 16,
      showHintAfterMisses: 2,
      onLoadCharDataSuccess: (data: any) => {
        if (data?.strokes) {
          quizProgress.value = { currentStroke: 1, totalStrokes: data.strokes.length }
        }
        if (activeMode.value === 'animate') {
          playAnimation()
        } else {
          startPractice()
        }
      },
    })
  } catch (err) {
    console.error('Error al inicializar HanziWriter en diccionario:', err)
  }
}

function playAnimation() {
  if (!writerInstance) return
  isQuizCompleted.value = false
  try {
    writerInstance.cancelQuiz?.()
    if (isLooping.value) {
      writerInstance.loopCharacterAnimation()
    } else {
      writerInstance.animateCharacter()
    }
  } catch (err) {
    console.error('Error al animar trazos:', err)
  }
}

function toggleLoop() {
  isLooping.value = !isLooping.value
  if (writerInstance && activeMode.value === 'animate') {
    playAnimation()
  }
}

function toggleSpeed() {
  speed.value = speed.value === 1.0 ? 0.5 : 1.0
  if (writerInstance) {
    initOrUpdateWriter()
  }
}

function startPractice() {
  if (!writerInstance) return
  activeMode.value = 'practice'
  isQuizCompleted.value = false
  quizMistakes.value = 0

  try {
    writerInstance.quiz({
      onCorrectStroke: (strokeData: any) => {
        if (quizProgress.value) {
          quizProgress.value.currentStroke = strokeData.strokeNum + 2
        }
      },
      onMistake: () => {
        quizMistakes.value++
      },
      onComplete: () => {
        isQuizCompleted.value = true
      },
    })
  } catch (err) {
    console.error('Error en práctica de escritura:', err)
  }
}

function selectSuggestion(entry: DictionaryEntry) {
  selectedEntry.value = entry
  searchQuery.value = ''
}

async function performCustomSearch() {
  const query = searchQuery.value.trim()
  if (!query) return

  // 1. Buscar en diccionario local
  const results = searchDictionary(query)
  if (results.length > 0) {
    selectedEntry.value = results[0]
    searchQuery.value = ''
    return
  }

  // 2. Si no está en diccionario local, consultar al motor de traducción del bridge
  isSearching.value = true
  try {
    const res = await bridge.translateToken(query)
    let pinyin = res.pinyin
    if (!pinyin && bridge.getPinyin && isHanzi(query)) {
      pinyin = await bridge.getPinyin(query)
    }

    selectedEntry.value = {
      id: `custom-${Date.now()}`,
      hanzi: query,
      pinyin: pinyin || '—',
      pinyinNormalized: query,
      translationEs: res.translationEs || 'Sin traducción encontrada',
      category: 'Traducción directa',
      level: 'General',
    }
    searchQuery.value = ''
  } catch (err) {
    console.error('Error al consultar traducción dinámica:', err)
  } finally {
    isSearching.value = false
  }
}

async function playPronunciation() {
  if (selectedEntry.value?.hanzi) {
    await speak(selectedEntry.value.hanzi)
  }
}

async function copyText(text: string, field: 'zh' | 'es') {
  try {
    let copied = false
    if (bridge && typeof bridge.copyToClipboard === 'function') {
      copied = await bridge.copyToClipboard(text)
    }
    if (!copied && typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      copied = true
    }
    if (copied) {
      copiedField.value = field
      setTimeout(() => {
        if (copiedField.value === field) {
          copiedField.value = null
        }
      }, 1800)
    }
  } catch (err) {
    console.error('Error al copiar:', err)
  }
}

function clearSearch() {
  searchQuery.value = ''
}

onMounted(() => {
  nextTick(() => {
    initOrUpdateWriter()
  })
})

onUnmounted(() => {
  cleanupWriter()
})
</script>

<template>
  <div class="dictionary-container">
    <!-- Barra superior de búsqueda -->
    <header class="search-header">
      <div class="search-box">
        <IconSearch :size="18" class="search-icon" />
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="Buscar en hanzi (学习), pinyin (xuexi) o español (aprender)..."
          @keydown.enter="performCustomSearch"
        />
        <button v-if="searchQuery" class="btn-clear" title="Limpiar" @click="clearSearch">
          <IconClose :size="14" />
        </button>
        <button
          class="btn-search-submit"
          :disabled="isSearching || !searchQuery.trim()"
          title="Buscar"
          @click="performCustomSearch"
        >
          {{ isSearching ? '...' : 'Buscar' }}
        </button>
      </div>

      <!-- Menú flotante de autocompletado en tiempo real -->
      <div v-if="suggestions.length > 0" class="suggestions-dropdown">
        <div
          v-for="item in suggestions"
          :key="item.id"
          class="suggestion-item"
          @click="selectSuggestion(item)"
        >
          <span class="suggestion-hanzi zh-text">{{ item.hanzi }}</span>
          <span class="suggestion-pinyin">{{ item.pinyin }}</span>
          <span class="suggestion-trans">{{ item.translationEs }}</span>
        </div>
      </div>
    </header>

    <!-- Contenido Principal: Ficha de la Palabra -->
    <main class="dictionary-content">
      <!-- Palabras recomendadas / accesos rápidos -->
      <section class="quick-chips">
        <span class="chips-label">Frecuentes:</span>
        <button
          v-for="entry in DICTIONARY_ENTRIES.slice(0, 8)"
          :key="entry.id"
          class="chip-btn"
          :class="{ active: selectedEntry?.id === entry.id }"
          @click="selectedEntry = entry"
        >
          {{ entry.hanzi }}
        </button>
      </section>

      <!-- Tarjeta Principal de la Palabra (Oro Antiguo Erudito - Obsidiana) -->
      <article v-if="selectedEntry" class="word-card">
        <!-- Cinta superior dorada -->
        <div class="card-accent-bar" />

        <div class="card-body">
          <!-- Cabecera de la palabra: Hanzi, Altavoz y Pinyin -->
          <div class="word-header">
            <div class="hanzi-group">
              <h1 class="hanzi-display zh-text">{{ selectedEntry.hanzi }}</h1>
              <div class="phonetics">
                <span class="pinyin-display">{{ selectedEntry.pinyin }}</span>
                <span v-if="selectedEntry.level" class="level-badge">{{ selectedEntry.level }}</span>
                <span v-if="selectedEntry.category" class="category-tag">{{ selectedEntry.category }}</span>
              </div>
            </div>

            <button
              class="audio-speaker-btn"
              :class="{ 'is-speaking': isSpeaking }"
              title="Escuchar pronunciación"
              @click="playPronunciation"
            >
              <IconSpeaker :size="20" />
            </button>
          </div>

          <!-- Definición / Significado en Español -->
          <div class="meaning-section">
            <span class="section-label">Significado en español</span>
            <p class="meaning-text">{{ selectedEntry.translationEs }}</p>
          </div>

          <!-- Sección: Cómo escribirlo (Trazos & Caligrafía Tianzige) -->
          <div class="calligraphy-section">
            <div class="calligraphy-header">
              <div class="section-title-wrap">
                <span class="section-label">Cómo escribirlo (笔顺)</span>
                <span v-if="selectedEntry.radical" class="meta-pill">Radical: {{ selectedEntry.radical }}</span>
                <span v-if="selectedEntry.totalStrokes" class="meta-pill">{{ selectedEntry.totalStrokes }} trazos</span>
              </div>

              <!-- Selector de carácter si la palabra tiene más de 1 hanzi -->
              <div v-if="wordHanziList.length > 1" class="character-tabs">
                <button
                  v-for="char in wordHanziList"
                  :key="char"
                  class="char-tab-btn zh-text"
                  :class="{ active: char === activeChar }"
                  @click="activeChar = char"
                >
                  {{ char }}
                </button>
              </div>
            </div>

            <!-- Lienzo Tianzige con líneas tradicionales y HanziWriter -->
            <div class="tianzige-container">
              <div class="tianzige-box">
                <!-- Líneas cruzadas y diagonales tradicionales Tianzige -->
                <svg class="grid-svg" viewBox="0 0 190 190" width="190" height="190">
                  <line x1="0" y1="95" x2="190" y2="95" class="guide-cross" />
                  <line x1="95" y1="0" x2="95" y2="190" class="guide-cross" />
                  <line x1="0" y1="0" x2="190" y2="190" class="guide-diag" />
                  <line x1="190" y1="0" x2="0" y2="190" class="guide-diag" />
                </svg>

                <div ref="writerContainerRef" class="writer-target" />
              </div>

              <!-- Controles de la animación de trazos -->
              <div class="calligraphy-controls">
                <button
                  class="btn-calligraphy"
                  :class="{ active: activeMode === 'animate' }"
                  title="Reproducir animación de trazo"
                  @click="activeMode = 'animate'; playAnimation()"
                >
                  ▶ Animar
                </button>
                <button
                  class="btn-calligraphy"
                  :class="{ active: isLooping }"
                  title="Bucle continuo"
                  @click="toggleLoop"
                >
                  🔁 Bucle
                </button>
                <button
                  class="btn-calligraphy"
                  :class="{ active: speed === 0.5 }"
                  title="Velocidad lenta para estudio"
                  @click="toggleSpeed"
                >
                  {{ speed === 0.5 ? '🐢 0.5x' : '⚡ 1.0x' }}
                </button>
                <button
                  class="btn-calligraphy btn-practice"
                  :class="{ active: activeMode === 'practice' }"
                  title="Practicar trazo dibujando en pantalla"
                  @click="startPractice"
                >
                  ✍️ Practicar
                </button>
              </div>

              <!-- Indicador de práctica interactiva -->
              <div v-if="activeMode === 'practice'" class="practice-status">
                <span v-if="isQuizCompleted" class="quiz-done">
                  🎉 ¡Completado con éxito! ({{ quizMistakes }} fallos)
                </span>
                <span v-else-if="quizProgress" class="quiz-info">
                  Dibuja en la cuadrícula: Trazo {{ quizProgress.currentStroke }} de {{ quizProgress.totalStrokes }}
                </span>
              </div>
            </div>
          </div>

          <!-- Ejemplos de uso / Frases en contexto -->
          <div v-if="selectedEntry.examples && selectedEntry.examples.length > 0" class="examples-section">
            <span class="section-label">Frases de ejemplo</span>
            <div
              v-for="(ex, idx) in selectedEntry.examples"
              :key="idx"
              class="example-card"
            >
              <p class="ex-zh zh-text">{{ ex.chinese }}</p>
              <p class="ex-py">{{ ex.pinyin }}</p>
              <p class="ex-es">{{ ex.spanish }}</p>
            </div>
          </div>

          <!-- Acciones inferiores: Copiar y atajos -->
          <div class="card-footer-actions">
            <button
              class="btn-footer-action"
              :class="{ copied: copiedField === 'zh' }"
              @click="copyText(selectedEntry.hanzi, 'zh')"
            >
              <IconCheck v-if="copiedField === 'zh'" :size="13" />
              <IconCopy v-else :size="13" />
              <span>{{ copiedField === 'zh' ? 'Copiado' : 'Copiar Chino' }}</span>
            </button>

            <button
              class="btn-footer-action"
              :class="{ copied: copiedField === 'es' }"
              @click="copyText(selectedEntry.translationEs, 'es')"
            >
              <IconCheck v-if="copiedField === 'es'" :size="13" />
              <IconCopy v-else :size="13" />
              <span>{{ copiedField === 'es' ? 'Copiado' : 'Copiar Español' }}</span>
            </button>

            <button
              class="btn-footer-action btn-reader-jump"
              title="Ir al lector de documentos"
              @click="emit('navigate-reader')"
            >
              <IconDocument :size="13" />
              <span>Ir al Lector</span>
            </button>
          </div>
        </div>
      </article>
    </main>
  </div>
</template>

<style scoped>
.dictionary-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: var(--color-bg-primary);
  color: var(--color-text-primary);
}

.search-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid rgba(197, 160, 89, 0.22);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--color-bg-tertiary);
  border: 1px solid rgba(197, 160, 89, 0.35);
  border-radius: var(--radius-md);
  padding: 4px 10px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.search-box:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 0 12px rgba(197, 160, 89, 0.28);
}

.search-icon {
  color: var(--color-accent);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 14px;
  padding: 8px 4px;
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.btn-clear {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.btn-clear:hover {
  color: var(--color-text-primary);
}

.btn-search-submit {
  background-color: var(--color-accent);
  color: #11141a;
  border: none;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-search-submit:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  box-shadow: 0 0 10px rgba(197, 160, 89, 0.35);
}

.btn-search-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.suggestions-dropdown {
  background-color: rgba(23, 28, 36, 0.98);
  border: 1px solid var(--color-accent-border);
  border-radius: var(--radius-md);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid rgba(197, 160, 89, 0.1);
  transition: background-color 0.15s ease;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background-color: rgba(197, 160, 89, 0.15);
}

.suggestion-hanzi {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-accent-hover);
  min-width: 50px;
}

.suggestion-pinyin {
  font-size: 13px;
  color: #dfd5c2;
  min-width: 70px;
}

.suggestion-trans {
  font-size: 12px;
  color: var(--color-text-secondary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dictionary-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 16px;
  max-width: 640px;
  margin: 0 auto;
  width: 100%;
}

.quick-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}

.quick-chips::-webkit-scrollbar {
  display: none;
}

.chips-label {
  font-size: 11px;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.chip-btn {
  background-color: var(--color-bg-tertiary);
  border: 1px solid rgba(197, 160, 89, 0.22);
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 9999px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
}

.chip-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-hover);
}

.chip-btn.active {
  background-color: var(--color-accent);
  color: #11141a;
  border-color: var(--color-accent-hover);
  font-weight: 600;
}

.word-card {
  background-color: rgba(23, 28, 36, 0.95);
  border: 1px solid rgba(197, 160, 89, 0.35);
  border-radius: var(--radius-lg);
  box-shadow: 0 16px 36px -10px rgba(0, 0, 0, 0.65), 0 0 20px rgba(197, 160, 89, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card-accent-bar {
  height: 3px;
  background: var(--color-accent-gradient);
  width: 100%;
}

.card-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.word-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  border-bottom: 1px solid rgba(197, 160, 89, 0.16);
  padding-bottom: 14px;
}

.hanzi-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hanzi-display {
  font-size: 40px;
  font-weight: 700;
  color: var(--color-accent-hover);
  line-height: 1.1;
  letter-spacing: 0.04em;
}

.phonetics {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pinyin-display {
  font-size: 18px;
  font-weight: 600;
  color: #dfd5c2;
  letter-spacing: 0.02em;
}

.level-badge {
  background: rgba(197, 160, 89, 0.18);
  color: var(--color-accent);
  border: 1px solid rgba(197, 160, 89, 0.3);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
}

.category-tag {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-style: italic;
}

.audio-speaker-btn {
  background: var(--color-accent-subtle);
  border: 1px solid var(--color-accent-border);
  color: var(--color-accent-hover);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.audio-speaker-btn:hover {
  background: var(--color-accent);
  color: #11141a;
  transform: scale(1.08);
  box-shadow: 0 0 14px rgba(197, 160, 89, 0.4);
}

.audio-speaker-btn.is-speaking {
  animation: pulse-speaker 1s infinite alternate;
}

@keyframes pulse-speaker {
  from { box-shadow: 0 0 4px #c5a059; }
  to { box-shadow: 0 0 16px #d4af37; transform: scale(1.1); }
}

.section-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-accent);
  font-weight: 600;
  display: block;
  margin-bottom: 6px;
}

.meaning-section {
  display: flex;
  flex-direction: column;
}

.meaning-text {
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-text-primary);
  font-weight: 500;
}

.calligraphy-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background-color: rgba(18, 22, 30, 0.6);
  border: 1px solid rgba(197, 160, 89, 0.2);
  border-radius: var(--radius-md);
  padding: 14px;
}

.calligraphy-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-pill {
  font-size: 11px;
  background-color: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}

.character-tabs {
  display: flex;
  gap: 4px;
}

.char-tab-btn {
  background-color: var(--color-bg-tertiary);
  border: 1px solid rgba(197, 160, 89, 0.25);
  color: var(--color-text-secondary);
  font-size: 15px;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.char-tab-btn:hover {
  color: var(--color-accent-hover);
  border-color: var(--color-accent);
}

.char-tab-btn.active {
  background-color: var(--color-accent);
  color: #11141a;
  font-weight: 700;
  border-color: var(--color-accent-hover);
}

.tianzige-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.tianzige-box {
  position: relative;
  width: 190px;
  height: 190px;
  background-color: #12161f;
  border: 2px solid rgba(197, 160, 89, 0.35);
  border-radius: 8px;
  box-shadow: inset 0 0 16px rgba(0, 0, 0, 0.65);
  overflow: hidden;
}

.grid-svg {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.guide-cross {
  stroke: rgba(197, 160, 89, 0.22);
  stroke-width: 1.5;
  stroke-dasharray: 4, 4;
}

.guide-diag {
  stroke: rgba(197, 160, 89, 0.14);
  stroke-width: 1;
  stroke-dasharray: 2, 4;
}

.writer-target {
  width: 190px;
  height: 190px;
  cursor: crosshair;
}

.calligraphy-controls {
  display: flex;
  gap: 6px;
  width: 100%;
  max-width: 320px;
}

.btn-calligraphy {
  flex: 1;
  background-color: var(--color-bronze-btn);
  border: 1px solid var(--color-bronze-border);
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  padding: 6px 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
}

.btn-calligraphy:hover {
  background-color: var(--color-bronze-btn-hover);
  border-color: var(--color-accent);
  color: var(--color-accent-hover);
}

.btn-calligraphy.active {
  background-color: rgba(197, 160, 89, 0.22);
  border-color: var(--color-accent);
  color: var(--color-accent-hover);
}

.btn-practice {
  background-color: rgba(36, 75, 56, 0.3);
  border-color: rgba(69, 133, 100, 0.45);
}

.btn-practice:hover {
  background-color: rgba(46, 93, 70, 0.5);
  color: #8fd4af;
}

.practice-status {
  font-size: 12px;
  text-align: center;
  color: var(--color-accent-hover);
}

.quiz-done {
  color: #8fd4af;
  font-weight: 600;
}

.examples-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-card {
  background-color: rgba(18, 22, 30, 0.5);
  border: 1px solid rgba(197, 160, 89, 0.15);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ex-zh {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-accent-hover);
}

.ex-py {
  font-size: 12px;
  color: #dfd5c2;
}

.ex-es {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.card-footer-actions {
  display: flex;
  gap: 8px;
  border-top: 1px solid rgba(197, 160, 89, 0.16);
  padding-top: 14px;
}

.btn-footer-action {
  flex: 1;
  background-color: var(--color-bronze-btn);
  border: 1px solid var(--color-bronze-border);
  color: #e2dacb;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 9999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.15s ease;
}

.btn-footer-action:hover {
  background-color: var(--color-bronze-btn-hover);
  border-color: var(--color-accent);
  color: #ffffff;
}

.btn-footer-action.copied {
  background-color: rgba(46, 93, 70, 0.28);
  border-color: rgba(69, 133, 100, 0.6);
  color: #8fd4af;
}

.btn-reader-jump {
  background-color: rgba(197, 160, 89, 0.15);
  border-color: var(--color-accent);
  color: var(--color-accent-hover);
}

.btn-reader-jump:hover {
  background-color: var(--color-accent);
  color: #11141a;
}
</style>
