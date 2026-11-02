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
    stroke-width="2.2"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="fluid-icon text-success"
  >
    <polyline points="20 6 9 17 4 12" />
  </svg>
</template>

<style scoped>
.fluid-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  animation: checkmark-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes checkmark-pop {
  0% { transform: scale(0.5); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
</style>
