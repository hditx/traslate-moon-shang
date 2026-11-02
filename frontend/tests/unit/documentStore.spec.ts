import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentStore } from '@/stores/documentStore'
import { MockDesktopBridge } from '@/services/mock.bridge'
import { setDesktopBridge } from '@/services/bridge.factory'

describe('documentStore Pinia Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    setDesktopBridge(new MockDesktopBridge())
  })

  it('initializes with idle status and empty document', () => {
    const store = useDocumentStore()
    expect(store.status).toBe('idle')
    expect(store.currentDocument).toBeNull()
    expect(store.currentPageData).toBeNull()
    expect(store.activeToken).toBeNull()
  })

  it('loads a document and its first page correctly', async () => {
    const store = useDocumentStore()
    await store.openDocument('/mock/path/documento_chino.pdf')

    expect(store.status).toBe('ready')
    expect(store.currentDocument).not.toBeNull()
    expect(store.currentDocument?.filename).toBe('documento_chino.pdf')
    expect(store.currentPageData).not.toBeNull()
    expect(store.currentPageData?.tokens.length).toBe(4)
  })

  it('changes page and loads new page data', async () => {
    const store = useDocumentStore()
    await store.openDocument('/mock/path/documento_chino.pdf')
    await store.goToPage(2)

    expect(store.currentPageNumber).toBe(2)
    expect(store.currentPageData?.pageNumber).toBe(2)
  })

  it('sets and clears active token', async () => {
    const store = useDocumentStore()
    await store.openDocument('/mock/path/documento_chino.pdf')

    const firstToken = store.currentPageData?.tokens[0] || null
    expect(firstToken).not.toBeNull()

    store.setActiveToken(firstToken)
    expect(store.activeToken?.textZh).toBe('欢迎使用中文翻译系统')

    store.clearActiveToken()
    expect(store.activeToken).toBeNull()
  })

  it('detects canCapturePhoto when bridge.isAndroid is true or window.androidApi is defined', () => {
    const store = useDocumentStore()
    expect(store.canCapturePhoto).toBe(false)

    const mockAndroidBridge = new MockDesktopBridge()
    mockAndroidBridge.isAndroid = true
    setDesktopBridge(mockAndroidBridge)

    expect(store.canCapturePhoto).toBe(true)
  })

  it('captures photo, loads document and executes OCR successfully', async () => {
    const mockAndroidBridge = new MockDesktopBridge()
    mockAndroidBridge.isAndroid = true
    setDesktopBridge(mockAndroidBridge)

    const store = useDocumentStore()
    const success = await store.capturePhoto()

    expect(success).toBe(true)
    expect(store.status).toBe('ready')
    expect(store.currentDocument?.filename).toBe('camera_photo.jpg')
    expect(store.currentPageData).not.toBeNull()
    expect(store.tokens.length).toBeGreaterThan(0)
  })

  it('handles capturePhoto cancellation without error', async () => {
    const mockBridge = new MockDesktopBridge()
    mockBridge.isAndroid = true
    mockBridge.capturePhoto = async () => null
    setDesktopBridge(mockBridge)

    const store = useDocumentStore()
    const success = await store.capturePhoto()

    expect(success).toBe(false)
    expect(store.status).toBe('idle')
    expect(store.errorMessage).toBeNull()
  })
})
