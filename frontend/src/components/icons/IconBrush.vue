<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 16 })
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="fluid-icon"
  >
    <!-- Mango de pincel tradicional -->
    <path d="m18 2 4 4-8.5 8.5-4-4L18 2z" />
    <!-- Cerdas del pincel con punta de tinta -->
    <path d="m9.5 10.5-4 4C4 16 2 20 2 22c2 0 6-2 7.5-3.5l4-4" />
  </svg>
</template>

<style scoped>
.fluid-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>
