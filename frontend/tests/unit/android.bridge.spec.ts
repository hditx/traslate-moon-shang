import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AndroidBridge } from '@/services/android.bridge'

describe('AndroidBridge Service', () => {
  beforeEach(() => {
    vi.stubGlobal('window', {
      androidApi: {
        openFileDialog: vi.fn(async () =>
          JSON.stringify({ filePath: '/storage/emulated/0/doc.pdf', filename: 'doc.pdf' }),
        ),
        getDocumentInfo: vi.fn(async (path: string) =>
          JSON.stringify({
            id: 'doc.pdf',
            filename: path,
            fileType: 'pdf',
            totalPages: 10,
            currentPage: 1,
            pages: [],
          }),
        ),
        processPage: vi.fn(async (_path: string, page: number) =>
          JSON.stringify({
            pageNumber: page,
            width: 720,
            height: 1280,
            imageUrl: 'data:image/png;base64,mock',
            tokens: [
              {
                id: 'tok-1',
                textZh: '你好',
                pinyin: 'nǐ hǎo',
                translationEs: 'Hola',
                box: { x1: 10, y1: 10, x2: 50, y2: 30 },
                confidence: 0.98,
              },
            ],
          }),
        ),
        translateToken: vi.fn(async (text: string) =>
          JSON.stringify({
            textZh: text,
            pinyin: 'xiè xie',
            translationEs: 'Gracias',
            fromCache: true,
          }),
        ),
        copyToClipboard: vi.fn(async (_text: string) => true),
        getPinyin: vi.fn(async (_text: string) => 'jiào'),
        playAudio: vi.fn(async (_text: string) => true),
      },
    })
  })

  it('throws error when window.androidApi is not defined', () => {
    vi.stubGlobal('window', {})
    const bridge = new AndroidBridge()
    expect(() => bridge.openFileDialog()).rejects.toThrow(
      'La interfaz nativa Android (window.androidApi) no está disponible en este entorno.',
    )
  })

  it('delegates openFileDialog and parses JSON string response', async () => {
    const bridge = new AndroidBridge()
    const result = await bridge.openFileDialog()

    expect(window.androidApi?.openFileDialog).toHaveBeenCalled()
    expect(result).toEqual({ filePath: '/storage/emulated/0/doc.pdf', filename: 'doc.pdf' })
  })

  it('handles openFileDialog when Android returns direct object or null', async () => {
    window.androidApi!.openFileDialog = vi.fn(async () => null)
    const bridge = new AndroidBridge()
    const result = await bridge.openFileDialog()
    expect(result).toBeNull()

    window.androidApi!.openFileDialog = vi.fn(async () => ({
      filePath: '/storage/photo.jpg',
      filename: 'photo.jpg',
    }))
    const resObject = await bridge.openFileDialog()
    expect(resObject?.filename).toBe('photo.jpg')
  })

  it('delegates getDocumentInfo and parses response', async () => {
    const bridge = new AndroidBridge()
    const docInfo = await bridge.getDocumentInfo('/storage/emulated/0/doc.pdf')

    expect(window.androidApi?.getDocumentInfo).toHaveBeenCalledWith('/storage/emulated/0/doc.pdf')
    expect(docInfo.totalPages).toBe(10)
  })

  it('delegates processPage and parses page tokens', async () => {
    const bridge = new AndroidBridge()
    const page = await bridge.processPage('/doc.pdf', 3)

    expect(window.androidApi?.processPage).toHaveBeenCalledWith('/doc.pdf', 3)
    expect(page.pageNumber).toBe(3)
    expect(page.tokens.length).toBe(1)
    expect(page.tokens[0].textZh).toBe('你好')
  })

  it('delegates translateToken correctly', async () => {
    const bridge = new AndroidBridge()
    const trans = await bridge.translateToken('谢谢')

    expect(window.androidApi?.translateToken).toHaveBeenCalledWith('谢谢')
    expect(trans.translationEs).toBe('Gracias')
    expect(trans.pinyin).toBe('xiè xie')
  })

  it('delegates copyToClipboard and returns boolean', async () => {
    const bridge = new AndroidBridge()
    const copied = await bridge.copyToClipboard('你好')
    expect(window.androidApi?.copyToClipboard).toHaveBeenCalledWith('你好')
    expect(copied).toBe(true)

    window.androidApi!.copyToClipboard = vi.fn(async () => {
      throw new Error('Clipboard denied')
    })
    expect(await bridge.copyToClipboard('你好')).toBe(false)
  })

  it('delegates getPinyin and playAudio', async () => {
    const bridge = new AndroidBridge()
    const pinyin = await bridge.getPinyin('窖')
    expect(window.androidApi?.getPinyin).toHaveBeenCalledWith('窖')
    expect(pinyin).toBe('jiào')

    const played = await bridge.playAudio('窖')
    expect(window.androidApi?.playAudio).toHaveBeenCalledWith('窖')
    expect(played).toBe(true)
  })

  it('supports snake_case Android native methods', async () => {
    vi.stubGlobal('window', {
      androidApi: {
        open_file_dialog: vi.fn(async () =>
          JSON.stringify({ filePath: '/doc.png', filename: 'doc.png' }),
        ),
        get_pinyin: vi.fn(async (_text: string) => 'nǐ hǎo'),
        play_pronunciation: vi.fn(async (_text: string) => true),
      },
    })

    const bridge = new AndroidBridge()
    const file = await bridge.openFileDialog()
    expect(file?.filename).toBe('doc.png')

    const pinyin = await bridge.getPinyin('你好')
    expect(pinyin).toBe('nǐ hǎo')

    const played = await bridge.playAudio('你好')
    expect(played).toBe(true)
  })
})
