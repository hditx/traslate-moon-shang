import { shallowRef } from 'vue'
import type { IDesktopBridge } from './bridge.interface'
import { MockDesktopBridge } from './mock.bridge'
import { PyWebViewBridge } from './pywebview.bridge'
import { AndroidBridge } from './android.bridge'

const bridgeRef = shallowRef<IDesktopBridge | null>(null)

export function getDesktopBridge(): IDesktopBridge {
  if (!bridgeRef.value) {
    if (typeof window !== 'undefined' && (window.androidApi || window.AndroidBridge)) {
      bridgeRef.value = new AndroidBridge()
    } else if (typeof window !== 'undefined' && window.pywebview?.api) {
      bridgeRef.value = new PyWebViewBridge()
    } else {
      bridgeRef.value = new MockDesktopBridge()
    }
  }
  return bridgeRef.value
}

export function setDesktopBridge(bridge: IDesktopBridge | null): void {
  bridgeRef.value = bridge
}
