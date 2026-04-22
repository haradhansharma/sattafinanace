<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold text-surface-900 dark:text-white">{{ title }}</h1>
      <p v-if="subtitle" class="text-surface-500 dark:text-surface-400 mt-1">{{ subtitle }}</p>
    </div>
    <slot name="actions" />
  </div>
</template>
