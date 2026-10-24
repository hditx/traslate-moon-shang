import { describe, it, expect, vi, beforeEach } from 'vitest'
import { PyWebViewBridge } from '@/services/pywebview.bridge'

describe('PyWebViewBridge Service', () => {
  beforeEach(() => {
    vi.stubGlobal('window', {
      pywebview: {
        api: {
          open_file_dialog: vi.fn(async () => ({
            filePath: '/home/user/doc.pdf',
            filename: 'doc.pdf',
          })),
          get_document_info: vi.fn(async (path: string) => ({
            id: 'doc.pdf',
            filename: path,
            fileType: 'pdf',
            totalPages: 5,
            currentPage: 1,
            pages: [],
          })),
          process_page: vi.fn(async (_path: string, page: number) => ({
            pageNumber: page,
            width: 800,
            height: 1200,
            imageUrl: 'data:image/png;base64,abc',
            tokens: [],
          })),
          translate_token: vi.fn(async (text: string) => ({
            textZh: text,
            pinyin: 'nǐ hǎo',
            translationEs: 'Hola',
            fromCache: true,
          })),
          copy_to_clipboard: vi.fn(async (_text: string) => true),
        },
      },
    })
  })

  it('delegates openFileDialog to window.pywebview.api.open_file_dialog', async () => {
    const bridge = new PyWebViewBridge()
    const result = await bridge.openFileDialog()

    expect(window.pywebview?.api.open_file_dialog).toHaveBeenCalled()
    expect(result?.filename).toBe('doc.pdf')
  })

  it('delegates getDocumentInfo to window.pywebview.api.get_document_info', async () => {
    const bridge = new PyWebViewBridge()
    const docInfo = await bridge.getDocumentInfo('/home/user/doc.pdf')

    expect(window.pywebview?.api.get_document_info).toHaveBeenCalledWith('/home/user/doc.pdf')
    expect(docInfo.totalPages).toBe(5)
  })

  it('delegates processPage and translateToken', async () => {
    const bridge = new PyWebViewBridge()
    const page = await bridge.processPage('/doc.pdf', 2)
    expect(page.pageNumber).toBe(2)

    const trans = await bridge.translateToken('你好')
    expect(trans.translationEs).toBe('Hola')
  })

  it('delegates copyToClipboard to window.pywebview.api.copy_to_clipboard', async () => {
    const bridge = new PyWebViewBridge()
    const copied = await bridge.copyToClipboard('谢谢')
    expect(window.pywebview?.api.copy_to_clipboard).toHaveBeenCalledWith('谢谢')
    expect(copied).toBe(true)
  })

  it('delegates getPinyin and playAudio to native pywebview api', async () => {
    window.pywebview!.api.get_pinyin = vi.fn(async (_text: string) => 'jiào')
    window.pywebview!.api.play_pronunciation = vi.fn(async (_text: string) => true)

    const bridge = new PyWebViewBridge()
    const pinyin = await bridge.getPinyin('窖')
    expect(window.pywebview?.api.get_pinyin).toHaveBeenCalledWith('窖')
    expect(pinyin).toBe('jiào')

    const played = await bridge.playAudio('窖')
    expect(window.pywebview?.api.play_pronunciation).toHaveBeenCalledWith('窖')
    expect(played).toBe(true)
  })
})

