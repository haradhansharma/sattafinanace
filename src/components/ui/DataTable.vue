<script setup lang="ts">
import { computed } from 'vue';

export interface Column {
  key: string;
  label: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

const props = withDefaults(defineProps<{
  columns: Column[];
  data: Record<string, any>[];
  loading?: boolean;
  emptyMessage?: string;
}>(), {
  loading: false,
  emptyMessage: 'No data found',
});

const emit = defineEmits<{
  rowClick: [row: Record<string, any>];
}>();

const alignClass = (align?: string) => {
  switch (align) {
    case 'center': return 'text-center';
    case 'right': return 'text-right tabular-nums';
    default: return 'text-left';
  }
};
</script>

<template>
  <div class="card overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/50">
            <th v-for="col in columns" :key="col.key" class="px-4 py-3 text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider" :class="alignClass(col.align)" :style="col.width ? { width: col.width } : {}">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length" class="px-4 py-12 text-center text-surface-400 dark:text-surface-500">
              <div class="animate-pulse">Loading...</div>
            </td>
          </tr>
          <tr v-else-if="data.length === 0">
            <td :colspan="columns.length" class="px-4 py-12 text-center text-surface-400 dark:text-surface-500">
              {{ emptyMessage }}
            </td>
          </tr>
          <tr v-else v-for="(row, i) in data" :key="i" class="border-b border-surface-100 dark:border-surface-700/50 last:border-0 hover:bg-surface-50 dark:hover:bg-surface-700/30 cursor-pointer transition-colors" @click="emit('rowClick', row)">
            <td v-for="col in columns" :key="col.key" class="px-4 py-3 text-sm text-surface-700 dark:text-surface-300" :class="alignClass(col.align)">
              <slot :name="`cell-${col.key}`" :value="row[col.key]" :row="row">
                {{ row[col.key] }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>