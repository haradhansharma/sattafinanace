<script setup lang="ts">
import { toRef, ref, watch, nextTick } from 'vue';
import { useModalStack } from '../../composables/useModalStack';

const props = defineProps<{
  isOpen: boolean;
  title: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}>();

const emit = defineEmits<{
  close: [];
}>();

const sizeClass = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

// Z-index stacking from shared composable
const zIndex = useModalStack(toRef(props, 'isOpen'));

// DOM reordering: move to end of body when opening so it's visually on top
const rootRef = ref<HTMLElement | null>(null);

watch(() => props.isOpen, async (open) => {
  if (open && rootRef.value) {
    await nextTick();
    await nextTick();
    const parent = rootRef.value.parentElement;
    if (parent && parent.lastElementChild !== rootRef.value) {
      parent.appendChild(rootRef.value);
    }
  }
});
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        ref="rootRef"
        class="fixed inset-0 flex items-center justify-center p-4"
        :style="{ zIndex }"
        @click.self="emit('close')"
      >
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" :style="{ zIndex: zIndex }" @click="emit('close')" />
        <div
          class="relative bg-white dark:bg-surface-800 rounded-xl shadow-xl w-full max-h-[90vh] overflow-auto animate-fade-in"
          :style="{ zIndex: zIndex + 1 }"
          :class="sizeClass?.[size || 'md'] || 'max-w-lg'"
        >
          <div class="flex items-center justify-between p-5 border-b border-surface-200 dark:border-surface-700">
            <h3 class="text-lg font-semibold text-surface-900 dark:text-white">{{ title }}</h3>
            <button @click="emit('close')" class="text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="p-5">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active { transition: opacity 0.2s ease; }
.modal-leave-active { transition: opacity 0.15s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
