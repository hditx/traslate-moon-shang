<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useFloating, offset, flip, shift, autoUpdate } from '@floating-ui/vue'
import type { DetectedToken } from '@/types/document'
import { useSpeech } from '@/composables/useSpeech'
import { getDesktopBridge } from '@/services/bridge.factory'
import { isHanzi, extractHanziList } from '@/utils/hanzi'
import StrokeOrderModal from './StrokeOrderModal.vue'
import {
  IconBrush,
  IconPin,
  IconClose,
  IconSpeaker,
  IconCopy,
  IconCheck,
} from '@/components/icons'

const props = defineProps<{
  token: DetectedToken | null
  targetRect: { top: number; left: number; width: number; height: number } | null
  isPinned?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toggle-pin'): void
}>()

const floatingRef = ref<HTMLElement | null>(null)
const copiedField = ref<'zh' | 'es' | null>(null)
const isStrokeModalOpen = ref(false)
const activeStrokeChar = ref('')
const openedAt = ref(Date.now())

const { speak, isSpeaking, stop } = useSpeech()
const bridge = getDesktopBridge()

const hanziCharacters = computed(() => extractHanziList(props.token?.textZh || ''))

const dynamicTranslation = ref('')
const isTranslating = ref(false)

const displayTranslation = computed(() => {
  return dynamicTranslation.value || props.token?.translationEs || (isTranslating.value ? 'Traduciendo...' : '')
})

watch(
  () => props.token?.id,
  async (newId, oldId) => {
    if (newId !== oldId) {
      openedAt.value = Date.now()
      isStrokeModalOpen.value = false
      activeStrokeChar.value = ''
      dynamicTranslation.value = ''

      if (props.token?.textZh) {
        isTranslating.value = true
        try {
          const res = await bridge.translateToken(props.token.textZh)
          if (res?.translationEs) {
            dynamicTranslation.value = res.translationEs
            if (props.token) {
              props.token.translationEs = res.translationEs
              if (res.pinyin && !props.token.pinyin) {
                props.token.pinyin = res.pinyin
              }
            }
          }
        } catch (err) {
          console.warn('Error fetching token translation:', err)
        } finally {
          isTranslating.value = false
        }
      }
    }
  },
  { immediate: true },
)

function openStrokeOrder(char?: string) {
  // Prevenir que el click sintético táctil (ghost click) de tocar el documento
  // para abrir la traducción active inmediatamente la modal de trazos.
  if (
    typeof window !== 'undefined' &&
    window.matchMedia?.('(pointer: coarse)').matches &&
    Date.now() - openedAt.value < 400
  ) {
    return
  }
  const target = char || hanziCharacters.value[0] || ''
  if (target) {
    activeStrokeChar.value = target
    isStrokeModalOpen.value = true
  }
}

// Virtual reference element para Floating UI basado en las coordenadas pasadas
const virtualReference = computed(() => {
  if (!props.targetRect) return null
  const rect = props.targetRect
  return {
    getBoundingClientRect() {
      return {
        width: rect.width,
        height: rect.height,
        x: rect.left,
        y: rect.top,
        top: rect.top,
        left: rect.left,
        right: rect.left + rect.width,
        bottom: rect.top + rect.height,
      }
    },
  }
})

const { floatingStyles } = useFloating(virtualReference, floatingRef, {
  placement: 'top',
  middleware: [offset(10), flip(), shift({ padding: 12 })],
  whileElementsMounted: autoUpdate,
})

async function playPronunciation() {
  if (props.token?.textZh) {
    await speak(props.token.textZh)
  }
}

async function copyText(text: string, field: 'zh' | 'es') {
  try {
    let copied = false
    // Si estamos en entorno nativo (pywebview o Android WebView), delegar en el bridge
    if (bridge && typeof bridge.copyToClipboard === 'function') {
      copied = await bridge.copyToClipboard(text)
    }
    // En entorno web o si el bridge nativo no está activo, usar navigator.clipboard
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
    console.error('Error al copiar al portapapeles:', err)
  }
}

function closePopover() {
  stop()
  isStrokeModalOpen.value = false
  emit('close')
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closePopover()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  stop()
})
</script>

<template>
  <Transition name="popover-fade">
    <div
      v-if="token && targetRect"
      ref="floatingRef"
      class="translation-popover"
      :class="{ 'is-pinned': isPinned }"
      :style="floatingStyles"
      @click.stop
    >
      <!-- Cinta superior decorativa de oro antiguo erudito -->
      <div class="popover-accent-bar" />

      <!-- Cabecera de la tarjeta: Estado fijado y botón cerrar -->
      <div class="popover-header">
        <span class="confidence-badge">
          {{ Math.round(token.confidence * 100) }}% precisión
        </span>

        <div class="header-actions">
          <button
            v-if="hanziCharacters.length > 0"
            class="action-btn stroke-btn"
            title="Ver orden de trazos y caligrafía (笔顺)"
            @click.stop="openStrokeOrder()"
          >
            <IconBrush :size="13" />
          </button>
          <button
            class="action-btn pin-btn"
            :class="{ active: isPinned }"
            :title="isPinned ? 'Desfijar ventana' : 'Fijar ventana'"
            @click="emit('toggle-pin')"
          >
            <IconPin :size="13" />
          </button>
          <button class="action-btn close-btn" title="Cerrar (Esc)" @click="closePopover">
            <IconClose :size="12" />
          </button>
        </div>
      </div>

      <!-- Contenido Principal -->
      <div class="popover-body">
        <!-- Caracteres Chinos (Hanzi con selección interactiva) -->
        <div class="hanzi-row">
          <h3 class="hanzi-text zh-text">
            <template v-for="(char, idx) in token.textZh" :key="idx">
              <span
                v-if="isHanzi(char)"
                class="hanzi-char"
                :title="`Ver orden de trazos de '${char}'`"
                @click.stop="openStrokeOrder(char)"
              >
                {{ char }}
              </span>
              <span v-else class="punctuation-char">{{ char }}</span>
            </template>
          </h3>
          <button
            class="speaker-btn"
            :class="{ 'is-speaking': isSpeaking }"
            title="Escuchar pronunciación"
            @click="playPronunciation"
          >
            <IconSpeaker :size="14" />
          </button>
        </div>

        <!-- Pinyin con tonos -->
        <div class="pinyin-row">
          <span class="pinyin-text">{{ token.pinyin || '—' }}</span>
        </div>

        <div class="divider" />

        <!-- Traducción al español -->
        <div class="translation-row">
          <span class="lang-tag">ES</span>
          <p class="translation-text">
            {{ displayTranslation }}
          </p>
        </div>
      </div>

      <!-- Barra de acciones inferiores: Copiar con pastillas elegantes -->
      <div class="popover-footer">
        <button
          class="btn-footer"
          :class="{ copied: copiedField === 'zh' }"
          @click="copyText(token.textZh, 'zh')"
        >
          <IconCheck v-if="copiedField === 'zh'" :size="12" />
          <IconCopy v-else :size="12" />
          <span>{{ copiedField === 'zh' ? '✓ Chino copiado' : 'Copiar Chino' }}</span>
        </button>

        <button
          class="btn-footer"
          :class="{ copied: copiedField === 'es' }"
          @click="copyText(displayTranslation, 'es')"
        >
          <IconCheck v-if="copiedField === 'es'" :size="12" />
          <IconCopy v-else :size="12" />
          <span>{{ copiedField === 'es' ? '✓ Español copiado' : 'Copiar Español' }}</span>
        </button>
      </div>

      <!-- Modal de Orden de Trazos Caligráficos -->
      <StrokeOrderModal
        :is-open="isStrokeModalOpen"
        :initial-character="activeStrokeChar"
        :character-list="hanziCharacters"
        @close="isStrokeModalOpen = false"
      />
    </div>
  </Transition>
</template>

<style scoped>
.translation-popover {
  position: fixed;
  z-index: 1000;
  width: 320px;
  background: var(--color-bg-popover);
  backdrop-filter: blur(20px);
  border: 1px solid var(--color-accent-border);
  border-radius: 14px;
  box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.75), 0 0 20px rgba(197, 160, 89, 0.12);
  color: var(--color-text-primary);
  padding: 0 14px 14px;
  user-select: text;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

.popover-accent-bar {
  margin: 0 -14px 2px;
  height: 3px;
  background: var(--color-accent-gradient);
  flex-shrink: 0;
}

.translation-popover.is-pinned {
  border-color: var(--color-accent-hover);
  box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.8), 0 0 24px rgba(212, 175, 55, 0.25);
}

.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.confidence-badge {
  font-size: 11px;
  background: var(--color-accent-subtle);
  color: var(--color-accent-hover);
  border: 1px solid var(--color-accent-border);
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: rgba(197, 160, 89, 0.15);
  color: var(--color-accent-hover);
}

.action-btn.pin-btn.active {
  color: var(--color-accent-hover);
  background: rgba(197, 160, 89, 0.22);
}

.action-btn.stroke-btn:hover {
  background: rgba(197, 160, 89, 0.2);
  color: var(--color-accent-hover);
  transform: scale(1.08);
}

.popover-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hanzi-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.hanzi-text {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-accent-hover);
  line-height: 1.2;
  letter-spacing: 0.02em;
}

.hanzi-char {
  display: inline-block;
  padding: 0 2px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.hanzi-char:hover {
  background-color: rgba(197, 160, 89, 0.2);
  color: #ffffff;
  transform: translateY(-2px);
  text-shadow: 0 0 10px rgba(212, 175, 55, 0.4);
}

.punctuation-char {
  color: var(--color-text-muted);
}

.speaker-btn {
  background: var(--color-accent-subtle);
  border: 1px solid var(--color-accent-border);
  color: var(--color-accent-hover);
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.speaker-btn:hover {
  background: var(--color-accent);
  color: #11141a;
  transform: scale(1.05);
  box-shadow: 0 0 10px rgba(197, 160, 89, 0.35);
}

.speaker-btn.is-speaking {
  animation: pulse-speaker 1s infinite alternate;
}

@keyframes pulse-speaker {
  from {
    box-shadow: 0 0 4px #c5a059;
  }
  to {
    box-shadow: 0 0 14px #d4af37;
    transform: scale(1.08);
  }
}

.pinyin-row {
  display: flex;
  align-items: center;
}

.pinyin-text {
  color: #dfd5c2;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.03em;
}

.divider {
  height: 1px;
  background: rgba(197, 160, 89, 0.16);
  margin: 4px 0;
}

.translation-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.lang-tag {
  background: rgba(197, 160, 89, 0.14);
  color: var(--color-accent);
  border: 1px solid rgba(197, 160, 89, 0.25);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 4px;
  margin-top: 2px;
}

.translation-text {
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.48;
  font-weight: 500;
  flex: 1;
}

.popover-footer {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.btn-footer {
  flex: 1;
  background: var(--color-bronze-btn);
  border: 1px solid var(--color-bronze-border);
  color: #e2dacb;
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  padding: 6px 10px;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.btn-footer:hover {
  background: var(--color-bronze-btn-hover);
  border-color: var(--color-accent);
  color: #ffffff;
}

.btn-footer.copied {
  background: rgba(46, 93, 70, 0.28);
  border-color: rgba(69, 133, 100, 0.6);
  color: #8fd4af;
}

/* Transiciones suaves */
.popover-fade-enter-active,
.popover-fade-leave-active {
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

.popover-fade-enter-from,
.popover-fade-leave-to {
  opacity: 0;
  transform: scale(0.94) translateY(6px);
}

@media (max-width: 480px) {
  .translation-popover {
    width: calc(100vw - 20px);
    max-width: 340px;
    padding: 0 10px 10px;
    gap: 8px;
    border-radius: 12px;
  }
  .popover-accent-bar {
    margin: 0 -10px 2px;
  }
  .hanzi-text {
    font-size: 22px;
  }
  .pinyin-text {
    font-size: 13px;
  }
  .translation-text {
    font-size: 13px;
  }
}
</style>
