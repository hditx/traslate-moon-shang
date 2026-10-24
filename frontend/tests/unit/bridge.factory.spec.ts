import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getDesktopBridge, setDesktopBridge } from '@/services/bridge.factory'
import { AndroidBridge } from '@/services/android.bridge'
import { PyWebViewBridge } from '@/services/pywebview.bridge'
import { MockDesktopBridge } from '@/services/mock.bridge'

describe('bridge.factory Platform Detection', () => {
  beforeEach(() => {
    setDesktopBridge(null)
  })

  it('instantiates AndroidBridge when window.androidApi is present', () => {
    vi.stubGlobal('window', {
      androidApi: {
        openFileDialog: vi.fn(),
      },
    })

    const bridge = getDesktopBridge()
    expect(bridge).toBeInstanceOf(AndroidBridge)
  })

  it('instantiates PyWebViewBridge when window.pywebview.api is present', () => {
    vi.stubGlobal('window', {
      pywebview: {
        api: {},
      },
    })

    const bridge = getDesktopBridge()
    expect(bridge).toBeInstanceOf(PyWebViewBridge)
  })

  it('instantiates MockDesktopBridge when in browser/test environment', () => {
    vi.stubGlobal('window', {})

    const bridge = getDesktopBridge()
    expect(bridge).toBeInstanceOf(MockDesktopBridge)
  })

  it('respects manually injected bridge via setDesktopBridge', () => {
    const customMock: any = { custom: true }
    setDesktopBridge(customMock)

    expect(getDesktopBridge()).toBe(customMock)
  })
})
