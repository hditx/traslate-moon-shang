import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DocumentData, PageData, DetectedToken, ProcessingStatus } from '@/types/document'
import { getDesktopBridge } from '@/services/bridge.factory'
import { logger } from '@/services/logger.service'

export const useDocumentStore = defineStore('document', () => {
  const currentDocument = ref<DocumentData | null>(null)
  const currentFilePath = ref<string>('')
  const currentPageData = ref<PageData | null>(null)
  const currentPageNumber = ref<number>(1)
  const status = ref<ProcessingStatus>('idle')
  const errorMessage = ref<string | null>(null)
  const activeToken = ref<DetectedToken | null>(null)
  const activeTokenRect = ref<{ top: number; left: number; width: number; height: number } | null>(null)

  const isDocumentLoaded = computed(() => currentDocument.value !== null)
  const totalPages = computed(() => currentDocument.value?.totalPages ?? 1)
  const tokens = computed(() => currentPageData.value?.tokens ?? [])

  async function openDocument(explicitPath?: string): Promise<boolean> {
    const bridge = getDesktopBridge()
    errorMessage.value = null
    status.value = 'loading'

    try {
      let targetPath = explicitPath

      if (!targetPath) {
        logger.debug('documentStore', 'Abriendo diálogo de selección...')
        const dialogRes = await bridge.openFileDialog()
        if (!dialogRes) {
          logger.info('documentStore', 'Selección de archivo cancelada')
          status.value = currentDocument.value ? 'ready' : 'idle'
          return false
        }
        targetPath = dialogRes.filePath
      }

      currentFilePath.value = targetPath
      logger.info('documentStore', `Cargando información del documento: ${targetPath}`)
      const docInfo = await bridge.getDocumentInfo(targetPath)
      currentDocument.value = docInfo
      currentPageNumber.value = 1

      await loadPage(1)
      status.value = 'ready'
      return true
    } catch (err: any) {
      logger.error('documentStore', 'Fallo al abrir el documento', err)
      status.value = 'error'
      errorMessage.value = err?.message || 'Error al abrir el documento'
      return false
    }
  }

  async function loadPage(pageNumber: number): Promise<void> {
    if (!currentDocument.value) return
    const bridge = getDesktopBridge()

    status.value = 'processing_ocr'
    errorMessage.value = null

    try {
      const fileToLoad = currentFilePath.value || currentDocument.value.filename
      logger.info('documentStore', `Iniciando OCR para página ${pageNumber} de ${fileToLoad}`)
      const pageData = await bridge.processPage(fileToLoad, pageNumber)
      currentPageData.value = pageData
      currentPageNumber.value = pageNumber
      status.value = 'ready'
      logger.info('documentStore', `Página ${pageNumber} cargada con ${pageData.tokens.length} tokens`)
    } catch (err: any) {
      logger.error('documentStore', `Fallo al procesar página ${pageNumber}`, err)
      status.value = 'error'
      errorMessage.value = err?.message || `Error al procesar la página ${pageNumber}`
    }
  }

  async function goToPage(pageNumber: number): Promise<void> {
    if (pageNumber < 1 || pageNumber > totalPages.value) return
    await loadPage(pageNumber)
  }

  async function nextPage(): Promise<void> {
    if (currentPageNumber.value < totalPages.value) {
      await goToPage(currentPageNumber.value + 1)
    }
  }

  async function prevPage(): Promise<void> {
    if (currentPageNumber.value > 1) {
      await goToPage(currentPageNumber.value - 1)
    }
  }

  function setActiveToken(
    token: DetectedToken | null,
    rect?: { top: number; left: number; width: number; height: number }
  ): void {
    activeToken.value = token
    activeTokenRect.value = rect ?? null
  }

  function clearActiveToken(): void {
    activeToken.value = null
    activeTokenRect.value = null
  }

  return {
    currentDocument,
    currentPageData,
    currentPageNumber,
    status,
    errorMessage,
    activeToken,
    activeTokenRect,
    isDocumentLoaded,
    totalPages,
    tokens,
    openDocument,
    loadPage,
    goToPage,
    nextPage,
    prevPage,
    setActiveToken,
    clearActiveToken,
  }
})
