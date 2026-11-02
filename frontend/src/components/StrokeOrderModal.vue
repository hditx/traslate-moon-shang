<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import HanziWriter from 'hanzi-writer'
import { isHanzi } from '@/utils/hanzi'
import { useSpeech } from '@/composables/useSpeech'
import { getDesktopBridge } from '@/services/bridge.factory'
import { IconSpeaker, IconClose } from '@/components/icons'

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
      strokeColor: '#c5a059', // Oro antiguo erudito para trazos
      radicalColor: '#d4af37', // Oro radiante para radicales
      outlineColor: 'rgba(212, 197, 169, 0.22)', // Silueta suave pergamino
      highlightColor: '#4e8752', // Verde jade erudito para aciertos
      drawingColor: '#c5a059',
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
          <!-- Cinta superior decorativa -->
          <div class="modal-accent-bar" />

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
                  <IconSpeaker :size="16" />
                </button>
              </h2>
            </div>
            <button class="btn-close" title="Cerrar (Esc)" @click="emit('close')">
              <IconClose :size="15" />
            </button>
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
  background-color: rgba(14, 17, 23, 0.82);
  backdrop-filter: blur(8px);
}

.stroke-modal-card {
  display: flex;
  flex-direction: column;
  width: 90%;
  max-width: 460px;
  background: rgba(22, 27, 36, 0.97);
  border: 1px solid rgba(197, 160, 89, 0.35);
  border-radius: 16px;
  box-shadow:
    0 24px 48px -15px rgba(0, 0, 0, 0.8),
    0 0 28px rgba(197, 160, 89, 0.12);
  overflow: hidden;
  color: var(--color-text-primary);
}

.modal-accent-bar {
  height: 3px;
  background: var(--color-accent-gradient);
  width: 100%;
  flex-shrink: 0;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 14px 20px 12px;
  border-bottom: 1px solid rgba(197, 160, 89, 0.18);
}

.modal-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #d4af37;
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
  color: #d4af37;
  font-family: 'Noto Sans SC', sans-serif;
}

.pinyin-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: rgba(197, 160, 89, 0.15);
  border: 1px solid rgba(197, 160, 89, 0.35);
  border-radius: 6px;
  color: #d4af37;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 0 10px rgba(197, 160, 89, 0.15);
}

.audio-btn {
  background: rgba(197, 160, 89, 0.12);
  border: 1px solid rgba(197, 160, 89, 0.28);
  color: #d4af37;
  cursor: pointer;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.15s ease;
}

.audio-btn:hover {
  transform: scale(1.1);
  background: var(--color-accent);
  color: #11141a;
}

.audio-btn.is-speaking {
  animation: pulse-audio 0.9s infinite alternate ease-in-out;
}

@keyframes pulse-audio {
  from {
    transform: scale(1);
    box-shadow: 0 0 2px #c5a059;
  }
  to {
    transform: scale(1.15);
    box-shadow: 0 0 10px #d4af37;
  }
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.btn-close:hover {
  color: var(--color-text-primary);
  background-color: rgba(239, 68, 68, 0.2);
}

.characters-strip {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 20px;
  background-color: rgba(17, 20, 26, 0.6);
  border-bottom: 1px solid rgba(197, 160, 89, 0.16);
}

.strip-label {
  font-size: 11px;
  color: var(--color-text-muted);
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
  background-color: rgba(32, 39, 51, 0.7);
  border: 1px solid rgba(197, 160, 89, 0.22);
  border-radius: 6px;
  color: #e2dacb;
  font-size: 16px;
  font-family: 'Noto Sans SC', sans-serif;
  cursor: pointer;
  transition: all 0.15s ease;
}

.char-chip:hover {
  border-color: #d4af37;
  color: #d4af37;
  transform: translateY(-1px);
}

.char-chip.active {
  background-color: #c5a059;
  border-color: #d4af37;
  color: #11141a;
  font-weight: bold;
  box-shadow: 0 0 10px rgba(197, 160, 89, 0.4);
}

.mode-tabs {
  display: flex;
  padding: 12px 20px 0;
  gap: 8px;
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  background: rgba(17, 20, 26, 0.5);
  border: 1px solid rgba(197, 160, 89, 0.22);
  border-radius: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--color-text-primary);
  border-color: var(--color-accent);
}

.tab-btn.active {
  background-color: rgba(197, 160, 89, 0.16);
  border-color: var(--color-accent);
  color: #d4af37;
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
  background-color: #12161f;
  border: 2px solid rgba(197, 160, 89, 0.32);
  border-radius: 8px;
  box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.guide-line.cross {
  stroke: rgba(197, 160, 89, 0.22);
  stroke-width: 1.5;
  stroke-dasharray: 4, 4;
}

.guide-line.diag {
  stroke: rgba(197, 160, 89, 0.14);
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
  background-color: rgba(17, 20, 26, 0.88);
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  text-align: center;
  padding: 16px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(197, 160, 89, 0.2);
  border-top-color: #d4af37;
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
  color: var(--color-text-secondary);
  background-color: rgba(17, 20, 26, 0.5);
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(197, 160, 89, 0.2);
}

.quiz-step {
  color: #d4af37;
  font-weight: 600;
}

.quiz-complete-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: rgba(46, 93, 70, 0.25);
  border: 1px solid rgba(69, 133, 100, 0.5);
  padding: 8px 12px;
  border-radius: 8px;
}

.complete-icon {
  font-size: 24px;
}

.quiz-complete-card h4 {
  margin: 0;
  font-size: 13px;
  color: #6ee7b7;
}

.quiz-complete-card p {
  margin: 2px 0 0;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.btn-retry {
  margin-left: auto;
  padding: 4px 10px;
  background-color: var(--color-jade-btn);
  color: #f0f7f2;
  border: 1px solid var(--color-jade-border);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-retry:hover {
  background-color: var(--color-jade-btn-hover);
}

.modal-footer {
  display: flex;
  gap: 8px;
  padding: 12px 20px 16px;
  border-top: 1px solid rgba(197, 160, 89, 0.18);
  background-color: rgba(17, 20, 26, 0.5);
}

.btn-tool {
  flex: 1;
  padding: 8px 10px;
  background-color: var(--color-bronze-btn);
  border: 1px solid var(--color-bronze-border);
  border-radius: 8px;
  color: var(--color-text-primary);
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
  background-color: var(--color-bronze-btn-hover);
  border-color: var(--color-accent);
  color: #d4af37;
}

.btn-tool.active {
  background-color: rgba(197, 160, 89, 0.22);
  border-color: #d4af37;
  color: #d4af37;
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
