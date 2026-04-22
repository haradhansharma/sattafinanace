<script setup lang="ts">
defineProps<{
  tabs: { key: string; label: string; icon?: string }[];
  activeTab: string;
}>();

const emit = defineEmits<{
  'update:activeTab': [key: string];
}>();
</script>

<template>
  <div class="flex gap-1 border-b border-surface-200 dark:border-surface-700 overflow-x-auto">
    <button v-for="tab in tabs" :key="tab.key" @click="emit('update:activeTab', tab.key)" class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap" :class="activeTab === tab.key ? 'border-primary-500 text-primary-600 dark:text-primary-400' : 'border-transparent text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-300'">
      <span v-if="tab.icon" class="mr-1.5">{{ tab.icon }}</span>
      {{ tab.label }}
    </button>
  </div>
</template>
