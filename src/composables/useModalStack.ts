import { ref, watch, type Ref } from 'vue';

/**
 * Module-level counter shared across ALL Modal instances.
 * Ensures each new modal that opens gets a higher z-index than the previous one.
 */
let stackDepth = 0;

export function useModalStack(isOpen: Ref<boolean> | (() => boolean)) {
  const zIndex = ref(50);

  const getter = typeof isOpen === 'function' ? isOpen : () => isOpen.value;

  watch(getter, (open) => {
    if (open) {
      stackDepth++;
      zIndex.value = 50 + stackDepth * 10;
    } else {
      stackDepth = Math.max(0, stackDepth - 1);
    }
  }, { immediate: true });

  return zIndex;
}
