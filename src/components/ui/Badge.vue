<script setup lang="ts">
const props = defineProps<{
  variant?: 'success' | 'danger' | 'warning' | 'info' | 'neutral';
  size?: 'sm' | 'md';
}>();

const variantClass = {
  success: 'bg-accent-100 dark:bg-accent-500/20 text-accent-700 dark:text-accent-400',
  danger: 'bg-danger-100 dark:bg-danger-500/20 text-danger-700 dark:text-danger-400',
  warning: 'bg-warning-50 dark:bg-warning-500/20 text-amber-700 dark:text-amber-400',
  info: 'bg-primary-100 dark:bg-primary-500/20 text-primary-700 dark:text-primary-400',
  neutral: 'bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400',
};
</script>

<template>
  <span class="inline-flex items-center rounded-full font-medium" :class="[variantClass?.[variant || 'neutral'] || variantClass.neutral, size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-0.5 text-xs']">
    <slot />
  </span>
</template>