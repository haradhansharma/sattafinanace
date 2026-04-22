<script setup lang="ts">
const model = defineModel<string>({ default: '' });

defineProps<{
  placeholder?: string;
}>();
</script>

<template>
  <div class="relative">
    <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
    <input v-model="model" type="text" :placeholder="placeholder || 'Search...'" class="input-field pl-10" />
  </div>
</template>
