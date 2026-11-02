<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 36 })
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="fluid-icon-book"
  >
    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
    <path d="M6 6h10" opacity="0.4" />
    <path d="M6 10h10" opacity="0.4" />
    <path d="M6 14h6" opacity="0.4" />
    <!-- Sutil sello caligráfico cuadrado oriental -->
    <rect x="13" y="13" width="4" height="4" rx="1" stroke="currentColor" fill="currentColor" fill-opacity="0.15" />
  </svg>
</template>

<style scoped>
.fluid-icon-book {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>
