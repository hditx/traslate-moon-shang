import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import DocumentViewer from '@/components/DocumentViewer.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { MockDesktopBridge } from '@/services/mock.bridge'
import { setDesktopBridge } from '@/services/bridge.factory'

describe('DocumentViewer Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    setDesktopBridge(new MockDesktopBridge())
  })

  it('renders empty state when no document is loaded', () => {
    const wrapper = mount(DocumentViewer)
    expect(wrapper.text()).toContain('Carga una imagen o PDF con texto en chino')
    expect(wrapper.find('.empty-card').exists()).toBe(true)
  })

  it('renders document and bounding boxes when document is opened', async () => {
    const store = useDocumentStore()
    const wrapper = mount(DocumentViewer)

    await store.openDocument('/mock/path/documento_chino.pdf')

    expect(wrapper.find('.viewport').exists()).toBe(true)
    expect(wrapper.find('.page-image').exists()).toBe(true)
    expect(wrapper.findAll('.bounding-box-item').length).toBe(4)
  })
})
