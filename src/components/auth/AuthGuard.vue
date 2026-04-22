<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue';

const isChecking = ref(true);
const hasError = ref(false);
let fallbackTimer: ReturnType<typeof setTimeout>;

onMounted(async () => {
  // Safety timeout — redirect to login after 4s no matter what
  fallbackTimer = setTimeout(() => {
    if (isChecking.value) {
      console.warn('[AuthGuard] Timed out checking auth — redirecting to login');
      redirectToLogin();
    }
  }, 4000);

  try {
    // Dynamically import the store so pinia must be ready
    const { useAuthStore } = await import('../../stores/auth');
    const authStore = useAuthStore();

    if (!authStore.restoreSession()) {
      redirectToLogin();
    } else {
      isChecking.value = false;
    }
  } catch (err) {
    console.error('[AuthGuard] Error during auth check:', err);
    hasError.value = true;
    // Auto-redirect after showing error briefly
    setTimeout(() => redirectToLogin(), 2000);
  } finally {
    clearTimeout(fallbackTimer);
  }
});

onUnmounted(() => clearTimeout(fallbackTimer));

function redirectToLogin() {
  isChecking.value = false;
  // Avoid redirect loop if already on login
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login';
  }
}
</script>

<template>
  <!-- Full-page overlay while checking auth -->
  <div
    v-if="isChecking"
    class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-surface-50 dark:bg-surface-950"
  >
    <!-- Checking state -->
    <div v-if="!hasError" class="flex flex-col items-center gap-3">
      <div class="w-8 h-8 border-[3px] border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
      <p class="text-sm text-surface-500 dark:text-surface-400">Checking authentication...</p>
      <button
        @click="redirectToLogin"
        class="mt-2 text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 underline transition-colors"
      >
        Skip to Login
      </button>
    </div>

    <!-- Error state -->
    <div v-else class="flex flex-col items-center gap-3">
      <svg class="w-8 h-8 text-danger-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" stroke-width="2"/>
        <path d="M12 8v4M12 16h.01" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <p class="text-sm text-danger-600 dark:text-danger-400">Unable to verify session</p>
      <button
        @click="redirectToLogin"
        class="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 underline transition-colors"
      >
        Go to Login
      </button>
    </div>
  </div>
</template>
