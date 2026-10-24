<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import HanziWriter from 'hanzi-writer'
import { isHanzi } from '@/utils/hanzi'
import { useSpeech } from '@/composables/useSpeech'
import { getDesktopBridge } from '@/services/bridge.factory'

const props = defineProps<{
  isOpen: boolean
  initialCharacter: string
  characterList?: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select-character', char: string): void
}>()

const targetRef = ref<HTMLElement | null>(null)
const selectedChar = ref<string>(props.initialCharacter || '')
const currentCharPinyin = ref<string>('')
const activeMode = ref<'animate' | 'practice'>('animate')
const speed = ref<number>(1.0)
const showOutline = ref<boolean>(true)
const isLooping = ref<boolean>(false)
const isLoading = ref<boolean>(false)
const hasError = ref<boolean>(false)

// Estados para el modo práctica
const quizProgress = ref<{ currentStroke: number; totalStrokes: number } | null>(null)
const quizMistakes = ref<number>(0)
const isQuizCompleted = ref<boolean>(false)

const { speak, isSpeaking } = useSpeech()

let writerInstance: any = null

const validCharacters = computed(() => {
  const list = props.characterList || []
  return list.filter(isHanzi)
})

async function updatePinyin(char: string) {
  if (!char || !isHanzi(char)) {
    currentCharPinyin.value = ''
    return
  }
  try {
    const bridge = getDesktopBridge()
    if (typeof bridge.getPinyin === 'function') {
      currentCharPinyin.value = await bridge.getPinyin(char)
    }
  } catch (err) {
    console.error('Error al obtener Pinyin del carácter:', err)
  }
}

watch(
  () => props.initialCharacter,
  (newChar) => {
    if (newChar && isHanzi(newChar)) {
      selectedChar.value = newChar
    }
  },
)

watch(
  () => [props.isOpen, selectedChar.value] as const,
  ([isOpen, char]) => {
    if (isOpen) {
      if (char) {
        updatePinyin(char)
      }
      nextTick(() => {
        initOrUpdateWriter()
      })
    } else {
      cleanupWriter()
    }
  },
  { immediate: true },
)

function cleanupWriter() {
  if (writerInstance) {
    try {
      writerInstance.cancelQuiz?.()
    } catch {
      // Ignorar errores al cancelar quiz
    }
    writerInstance = null
  }
  if (targetRef.value) {
    targetRef.value.innerHTML = ''
  }
}

function initOrUpdateWriter() {
  if (!targetRef.value || !selectedChar.value || !isHanzi(selectedChar.value)) return

  cleanupWriter()
  isLoading.value = true
  hasError.value = false
  isQuizCompleted.value = false
  quizMistakes.value = 0
  quizProgress.value = null

  try {
    writerInstance = HanziWriter.create(targetRef.value, selectedChar.value, {
      width: 220,
      height: 220,
      padding: 15,
      showOutline: showOutline.value,
      strokeAnimationSpeed: speed.value,
      delayBetweenStrokes: 160,
      strokeColor: '#38bdf8', // Azul cian brillante para trazos
      radicalColor: '#f59e0b', // Ámbar dorado para radicales
      outlineColor: 'rgba(148, 163, 184, 0.25)', // Silueta suave
      highlightColor: '#10b981', // Verde esmeralda para aciertos
      drawingColor: '#38bdf8',
      drawingWidth: 16,
      showHintAfterMisses: 2,
      onLoadCharDataSuccess: (data: any) => {
        isLoading.value = false
        if (data?.strokes) {
          quizProgress.value = { currentStroke: 1, totalStrokes: data.strokes.length }
        }
        if (activeMode.value === 'animate') {
          playAnimation()
        } else {
          startPractice()
        }
      },
      onLoadCharDataError: () => {
        isLoading.value = false
        hasError.value = true
      },
    })
  } catch (err) {
    console.error('Error al inicializar HanziWriter:', err)
    isLoading.value = false
    hasError.value = true
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
    console.error('Error al reproducir animación:', err)
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

function toggleOutline() {
  showOutline.value = !showOutline.value
  if (writerInstance) {
    if (showOutline.value) {
      writerInstance.showOutline()
    } else {
      writerInstance.hideOutline()
    }
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
    console.error('Error al iniciar quiz caligráfico:', err)
  }
}

function switchMode(mode: 'animate' | 'practice') {
  activeMode.value = mode
  if (mode === 'animate') {
    playAnimation()
  } else {
    startPractice()
  }
}

function selectCharacter(char: string) {
  if (char === selectedChar.value) return
  selectedChar.value = char
  emit('select-character', char)
}

async function playCharSpeech() {
  if (selectedChar.value) {
    await speak(selectedChar.value)
  }
}

function handleKeyDown(event: KeyboardEvent) {
  if (!props.isOpen) return
  if (event.key === 'Escape') {
    emit('close')
  } else if (event.key === ' ' && activeMode.value === 'animate') {
    event.preventDefault()
    playAnimation()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  cleanupWriter()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="stroke-modal-fade">
      <div v-if="isOpen" class="stroke-modal-backdrop" @click="emit('close')">
        <div class="stroke-modal-card" @click.stop>
          <!-- Cabecera del modal -->
          <div class="modal-header">
            <div class="header-info">
              <span class="modal-badge">Caligrafía y Trazos (笔顺)</span>
              <h2 class="modal-title">
                Carácter:
                <span class="highlight-char">{{ selectedChar }}</span>
                <span v-if="currentCharPinyin" class="pinyin-badge" title="Transcripción fonética Pinyin">
                  {{ currentCharPinyin }}
                </span>
                <button
                  class="audio-btn"
                  :class="{ 'is-speaking': isSpeaking }"
                  title="Escuchar pronunciación"
                  @click="playCharSpeech"
                >
                  🔊
                </button>
              </h2>
            </div>
            <button class="btn-close" title="Cerrar (Esc)" @click="emit('close')">✕</button>
          </div>

          <!-- Selector de caracteres en contexto (si hay más de uno) -->
          <div v-if="validCharacters.length > 1" class="characters-strip">
            <span class="strip-label">Caracteres detectados:</span>
            <div class="strip-tokens">
              <button
                v-for="char in validCharacters"
                :key="char"
                class="char-chip"
                :class="{ active: char === selectedChar }"
                @click="selectCharacter(char)"
              >
                {{ char }}
              </button>
            </div>
          </div>

          <!-- Pestañas de modo: Animación / Práctica -->
          <div class="mode-tabs">
            <button
              class="tab-btn"
              :class="{ active: activeMode === 'animate' }"
              @click="switchMode('animate')"
            >
              🎬 Animación de Trazos
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeMode === 'practice' }"
              @click="switchMode('practice')"
            >
              ✍️ Practicar Escritura
            </button>
          </div>

          <!-- Cuadrícula Caligráfica Tianzige (田字格) y Lienzo HanziWriter -->
          <div class="canvas-wrapper">
            <div class="tianzige-grid">
              <!-- Líneas guía cruzadas y diagonales tradicionales -->
              <svg class="grid-lines" viewBox="0 0 220 220" width="220" height="220">
                <line x1="0" y1="110" x2="220" y2="110" class="guide-line cross" />
                <line x1="110" y1="0" x2="110" y2="220" class="guide-line cross" />
                <line x1="0" y1="0" x2="220" y2="220" class="guide-line diag" />
                <line x1="220" y1="0" x2="0" y2="220" class="guide-line diag" />
              </svg>

              <!-- Contenedor montado por HanziWriter -->
              <div id="hanzi-writer-canvas" ref="targetRef" class="hanzi-target" />

              <!-- Overlay de Carga -->
              <div v-if="isLoading" class="loading-state">
                <span class="spinner" />
                <p>Cargando trazos...</p>
              </div>

              <!-- Overlay de Error / Carácter no disponible -->
              <div v-if="hasError" class="error-state">
                <span>⚠️</span>
                <p>Trazos no disponibles para este carácter</p>
              </div>
            </div>
          </div>

          <!-- Feedback de progreso en modo Práctica -->
          <div v-if="activeMode === 'practice'" class="practice-feedback">
            <div v-if="isQuizCompleted" class="quiz-complete-card">
              <span class="complete-icon">🎉</span>
              <div>
                <h4>¡Excelente trabajo!</h4>
                <p>Completaste el carácter con {{ quizMistakes }} error(es).</p>
              </div>
              <button class="btn-retry" @click="startPractice">Repetir práctica</button>
            </div>
            <div v-else class="quiz-progress-bar">
              <span class="quiz-label">
                Dibuja el carácter en la cuadrícula con el cursor o pantalla táctil
              </span>
              <span v-if="quizProgress" class="quiz-step">
                Trazo {{ Math.min(quizProgress.currentStroke, quizProgress.totalStrokes) }} de
                {{ quizProgress.totalStrokes }}
              </span>
            </div>
          </div>

          <!-- Barra de controles y herramientas -->
          <div class="modal-footer">
            <template v-if="activeMode === 'animate'">
              <button class="btn-tool" title="Reproducir animación de trazos" @click="playAnimation">
                ▶ Animar
              </button>
              <button
                class="btn-tool"
                :class="{ active: isLooping }"
                title="Bucle continuo"
                @click="toggleLoop"
              >
                🔁 Bucle
              </button>
              <button
                class="btn-tool"
                :class="{ active: speed === 0.5 }"
                title="Alternar velocidad de trazo"
                @click="toggleSpeed"
              >
                {{ speed === 0.5 ? '🐢 Lento (0.5x)' : '⚡ Normal (1x)' }}
              </button>
              <button
                class="btn-tool"
                :class="{ active: showOutline }"
                title="Alternar silueta guía"
                @click="toggleOutline"
              >
                👁️ Silueta
              </button>
            </template>
            <template v-else>
              <button class="btn-tool" @click="startPractice">
                🔄 Reiniciar lienzo
              </button>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.stroke-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(8px);
}

.stroke-modal-card {
  display: flex;
  flex-direction: column;
  width: 90%;
  max-width: 460px;
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 16px;
  box-shadow:
    0 20px 40px -15px rgba(0, 0, 0, 0.7),
    0 0 30px rgba(56, 189, 248, 0.15);
  overflow: hidden;
  color: #f8fafc;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.6);
}

.modal-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #38bdf8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.highlight-char {
  font-size: 26px;
  font-weight: bold;
  color: #f59e0b;
  font-family: 'Noto Sans SC', sans-serif;
}

.pinyin-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 6px;
  color: #38bdf8;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.15);
}

.audio-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 2px 6px;
  border-radius: 6px;
  transition: transform 0.15s ease;
}

.audio-btn:hover {
  transform: scale(1.15);
}

.audio-btn.is-speaking {
  animation: pulse-audio 0.9s infinite alternate ease-in-out;
}

@keyframes pulse-audio {
  from {
    transform: scale(1);
    filter: drop-shadow(0 0 2px #38bdf8);
  }
  to {
    transform: scale(1.25);
    filter: drop-shadow(0 0 8px #38bdf8);
  }
}

.btn-close {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.btn-close:hover {
  color: #f8fafc;
  background-color: rgba(239, 68, 68, 0.2);
}

.characters-strip {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 20px;
  background-color: rgba(15, 23, 42, 0.5);
  border-bottom: 1px solid rgba(51, 65, 85, 0.4);
}

.strip-label {
  font-size: 11px;
  color: #94a3b8;
}

.strip-tokens {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.char-chip {
  min-width: 32px;
  height: 32px;
  padding: 0 6px;
  background-color: rgba(51, 65, 85, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 6px;
  color: #cbd5e1;
  font-size: 16px;
  font-family: 'Noto Sans SC', sans-serif;
  cursor: pointer;
  transition: all 0.15s ease;
}

.char-chip:hover {
  border-color: #38bdf8;
  color: #38bdf8;
  transform: translateY(-1px);
}

.char-chip.active {
  background-color: #38bdf8;
  border-color: #38bdf8;
  color: #0f172a;
  font-weight: bold;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
}

.mode-tabs {
  display: flex;
  padding: 12px 20px 0;
  gap: 8px;
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 8px;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: #f8fafc;
  border-color: #475569;
}

.tab-btn.active {
  background-color: rgba(56, 189, 248, 0.15);
  border-color: #38bdf8;
  color: #38bdf8;
  font-weight: 600;
}

.canvas-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.tianzige-grid {
  position: relative;
  width: 220px;
  height: 220px;
  background-color: #0f172a;
  border: 2px solid #475569;
  border-radius: 8px;
  box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.guide-line.cross {
  stroke: rgba(148, 163, 184, 0.25);
  stroke-width: 1.5;
  stroke-dasharray: 4, 4;
}

.guide-line.diag {
  stroke: rgba(71, 85, 105, 0.2);
  stroke-width: 1;
  stroke-dasharray: 2, 4;
}

.hanzi-target {
  width: 220px;
  height: 220px;
  cursor: crosshair;
}

.loading-state,
.error-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(15, 23, 42, 0.85);
  gap: 8px;
  font-size: 13px;
  color: #94a3b8;
  text-align: center;
  padding: 16px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(56, 189, 248, 0.2);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.practice-feedback {
  padding: 0 20px 10px;
}

.quiz-progress-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #94a3b8;
  background-color: rgba(15, 23, 42, 0.4);
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(51, 65, 85, 0.4);
}

.quiz-step {
  color: #38bdf8;
  font-weight: 600;
}

.quiz-complete-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.4);
  padding: 8px 12px;
  border-radius: 8px;
}

.complete-icon {
  font-size: 24px;
}

.quiz-complete-card h4 {
  margin: 0;
  font-size: 13px;
  color: #10b981;
}

.quiz-complete-card p {
  margin: 2px 0 0;
  font-size: 11px;
  color: #94a3b8;
}

.btn-retry {
  margin-left: auto;
  padding: 4px 10px;
  background-color: #10b981;
  color: #0f172a;
  border: none;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-retry:hover {
  opacity: 0.9;
}

.modal-footer {
  display: flex;
  gap: 8px;
  padding: 12px 20px 16px;
  border-top: 1px solid rgba(51, 65, 85, 0.6);
  background-color: rgba(15, 23, 42, 0.4);
}

.btn-tool {
  flex: 1;
  padding: 8px 10px;
  background-color: rgba(51, 65, 85, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  color: #f8fafc;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.15s ease;
}

.btn-tool:hover {
  background-color: rgba(56, 189, 248, 0.2);
  border-color: #38bdf8;
  color: #38bdf8;
}

.btn-tool.active {
  background-color: rgba(56, 189, 248, 0.25);
  border-color: #38bdf8;
  color: #38bdf8;
}

/* Transición animada del Modal */
.stroke-modal-fade-enter-active,
.stroke-modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.stroke-modal-fade-enter-from,
.stroke-modal-fade-leave-to {
  opacity: 0;
}

.stroke-modal-fade-enter-active .stroke-modal-card {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.stroke-modal-fade-enter-from .stroke-modal-card {
  transform: scale(0.92) translateY(10px);
}
</style>
