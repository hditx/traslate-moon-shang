<script setup lang="ts">
withDefaults(defineProps<{ size?: number; active?: boolean }>(), { size: 16, active: false })
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
    :class="{ 'is-active': active }"
  >
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07" class="wave wave-1" />
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14" class="wave wave-2" />
  </svg>
</template>

<style scoped>
.fluid-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.is-active .wave-1 {
  animation: pulse-wave 1s infinite alternate ease-in-out;
}

.is-active .wave-2 {
  animation: pulse-wave 1s infinite alternate ease-in-out 0.2s;
}

@keyframes pulse-wave {
  from { opacity: 0.3; }
  to { opacity: 1; stroke-width: 2.2; }
}
</style>
