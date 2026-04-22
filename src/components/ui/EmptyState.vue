<script setup lang="ts">
defineProps<{
  icon?: string;
  title: string;
  description?: string;
}>();
</script>

<template>
  <div class="card p-12 text-center animate-fade-in">
    <div v-if="icon" class="text-4xl mb-3">{{ icon }}</div>
    <h3 class="text-lg font-semibold text-surface-700 dark:text-surface-300">{{ title }}</h3>
    <p v-if="description" class="text-sm text-surface-500 dark:text-surface-400 mt-1">{{ description }}</p>
    <slot name="action" class="mt-4" />
  </div>
</template>