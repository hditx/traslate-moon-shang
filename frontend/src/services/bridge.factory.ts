import type { IDesktopBridge } from './bridge.interface'
import { MockDesktopBridge } from './mock.bridge'
import { PyWebViewBridge } from './pywebview.bridge'
import { AndroidBridge } from './android.bridge'

let bridgeInstance: IDesktopBridge | null = null

export function getDesktopBridge(): IDesktopBridge {
  if (!bridgeInstance) {
    if (typeof window !== 'undefined' && window.androidApi) {
      bridgeInstance = new AndroidBridge()
    } else if (typeof window !== 'undefined' && window.pywebview?.api) {
      bridgeInstance = new PyWebViewBridge()
    } else {
      bridgeInstance = new MockDesktopBridge()
    }
  }
  return bridgeInstance
}

export function setDesktopBridge(bridge: IDesktopBridge | null): void {
  bridgeInstance = bridge
}
