<script setup lang="ts">
import DocumentViewer from '@/components/DocumentViewer.vue'
</script>

<template>
  <div class="app-layout">
    <DocumentViewer />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: var(--color-bg-primary);
}
</style>
