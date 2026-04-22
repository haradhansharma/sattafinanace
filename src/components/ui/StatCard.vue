<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  title: string;
  value: string;
  change?: number;
  icon?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'primary' | 'accent' | 'danger' | 'warning';
}>();

const trendClass = computed(() => {
  if (!props.trend || props.trend === 'neutral') return 'text-surface-500';
  return props.trend === 'up' ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500 dark:text-danger-400';
});

const iconBg = computed(() => {
  const colors: Record<string, string> = {
    primary: 'bg-primary-100 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400',
    accent: 'bg-accent-100 dark:bg-accent-500/20 text-accent-600 dark:text-accent-400',
    danger: 'bg-danger-100 dark:bg-danger-500/20 text-danger-600 dark:text-danger-400',
    warning: 'bg-warning-50 dark:bg-warning-500/20 text-amber-600 dark:text-amber-400',
  };
  return colors[props.color || 'primary'];
});
</script>

<template>
  <div class="card p-5 animate-fade-in">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-sm text-surface-500 dark:text-surface-400">{{ title }}</p>
        <p class="text-2xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ value }}</p>
        <p v-if="change !== undefined" class="text-sm mt-1" :class="trendClass">
          {{ change >= 0 ? '↑' : '↓' }} {{ Math.abs(change).toFixed(1) }}% from last month
        </p>
      </div>
      <div v-if="icon" class="w-10 h-10 rounded-lg flex items-center justify-center text-lg" :class="iconBg">
        {{ icon }}
      </div>
    </div>
  </div>
</template>