<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  value: number;
  max: number;
  color?: 'primary' | 'accent' | 'danger' | 'warning';
  showLabel?: boolean;
  size?: 'sm' | 'md';
}>(), {
  color: 'primary',
  showLabel: true,
  size: 'md',
});

const percentage = computed(() => Math.min((props.value / props.max) * 100, 100));
const isOver = computed(() => props.value > props.max);

const barColor = computed(() => {
  if (isOver.value) return 'bg-danger-500';
  const colors: Record<string, string> = {
    primary: 'bg-primary-500',
    accent: 'bg-accent-500',
    danger: 'bg-danger-500',
    warning: 'bg-warning-500',
  };
  return colors[props.color];
});

const sizeClass = props.size === 'sm' ? 'h-1.5' : 'h-2.5';
</script>

<template>
  <div>
    <div v-if="showLabel" class="flex items-center justify-between mb-1">
      <span class="text-sm text-surface-600 dark:text-surface-400 tabular-nums">{{ value.toLocaleString() }} / {{ max.toLocaleString() }}</span>
      <span class="text-sm font-medium tabular-nums" :class="isOver ? 'text-danger-500' : 'text-surface-600 dark:text-surface-400'">{{ percentage.toFixed(0) }}%</span>
    </div>
    <div class="w-full bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden" :class="sizeClass">
      <div class="rounded-full transition-all duration-500" :class="[barColor, sizeClass]" :style="{ width: `${percentage}%` }" />
    </div>
  </div>
</template>