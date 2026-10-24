import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { useDocumentStore } from '@/stores/documentStore'
import { AndroidBridge } from '@/services/android.bridge'
import { setDesktopBridge } from '@/services/bridge.factory'
import DocumentViewer from '@/components/DocumentViewer.vue'
import BoundingBoxOverlay from '@/components/BoundingBoxOverlay.vue'

describe('Android & Frontend End-to-End Integration with Security Checks', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    document.body.innerHTML = ''
    delete (window as any).androidApi
  })

  it('integrates AndroidBridge with useDocumentStore and mounts DocumentViewer safely', async () => {
    // Simular API nativa de Android inyectada en WebView
    const mockAndroidApi = {
      openFileDialog: vi.fn().mockReturnValue(JSON.stringify({
        filePath: '/storage/emulated/0/Download/documento.pdf',
        filename: 'documento.pdf'
      })),
      getDocumentInfo: vi.fn().mockReturnValue(JSON.stringify({
        id: 'documento.pdf',
        filename: 'documento.pdf',
        fileType: 'pdf',
        totalPages: 2,
        currentPage: 1,
        pages: []
      })),
      processPage: vi.fn().mockReturnValue(JSON.stringify({
        pageNumber: 1,
        width: 1000,
        height: 1500,
        imageUrl: '/mock/page1.png',
        tokens: [
          {
            id: 'tok_1',
            textZh: '中国',
            pinyin: 'zhōng guó',
            translationEs: 'China',
            box: { x1: 50, y1: 100, x2: 250, y2: 200 },
            confidence: 0.99
          }
        ]
      })),
      translateToken: vi.fn().mockReturnValue(JSON.stringify({
        textZh: '中国',
        pinyin: 'zhōng guó',
        translationEs: 'China',
        fromCache: true
      })),
      getPinyin: vi.fn().mockReturnValue('zhōng guó'),
      playAudio: vi.fn().mockReturnValue(true)
    }

    ;(window as any).androidApi = mockAndroidApi
    const bridge = new AndroidBridge()
    setDesktopBridge(bridge)
    const store = useDocumentStore()

    // 1. Abrir documento mediante el puente Android
    const opened = await store.openDocument()
    expect(opened).toBe(true)
    expect(store.currentDocument?.filename).toBe('documento.pdf')
    expect(store.currentPageData?.tokens.length).toBe(1)
    expect(store.currentPageData?.tokens[0].textZh).toBe('中国')

    // 2. Montar visor con el estado resultante
    const wrapper = mount(DocumentViewer, {
      global: {
        provide: {
          bridge
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    const overlay = wrapper.findComponent(BoundingBoxOverlay)
    expect(overlay.exists()).toBe(true)
  })

  it('neutralizes malicious XSS payload returned from Android native layer', async () => {
    const maliciousPayload = "<script>alert('xss_attack')</script><img src=x onerror=alert(1)>"
    
    ;(window as any).androidApi = {
      processPage: vi.fn().mockReturnValue(JSON.stringify({
        pageNumber: 1,
        width: 800,
        height: 1200,
        imageUrl: '/mock/page.png',
        tokens: [
          {
            id: 'tok_malicious',
            textZh: '你好',
            pinyin: 'nǐ hǎo',
            translationEs: maliciousPayload,
            box: { x1: 10, y1: 10, x2: 100, y2: 50 },
            confidence: 1.0
          }
        ]
      })),
      translateToken: vi.fn().mockReturnValue(JSON.stringify({
        textZh: '你好',
        pinyin: 'nǐ hǎo',
        translationEs: maliciousPayload,
        fromCache: false
      }))
    }

    const bridge = new AndroidBridge()
    const result = await bridge.translateToken('你好')

    // El contenido malicioso debe ser devuelto como texto literal, sin haber ejecutado scripts
    expect(result.translationEs).toBe(maliciousPayload)
    // El DOM no debe contener etiquetas script inyectadas
    expect(document.querySelectorAll('script').length).toBe(0)
  })

  it('handles malformed or corrupted JSON from Android bridge without crashing', async () => {
    ;(window as any).androidApi = {
      processPage: vi.fn().mockReturnValue('{ invalid json format'),
      translateToken: vi.fn().mockReturnValue('null')
    }

    const bridge = new AndroidBridge()
    await expect(bridge.processPage('/some/doc.pdf', 1)).rejects.toThrow()
  })
})
