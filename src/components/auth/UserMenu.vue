<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '../../stores/auth';

const authStore = useAuthStore();
const showDropdown = ref(false);
const initials = ref('FL');
const fullName = ref('');

onMounted(() => {
  // Restore session to get user info for the header
  authStore.restoreSession();
  initials.value = authStore.initials;
  fullName.value = authStore.fullName;
});

function toggleDropdown() {
  showDropdown.value = !showDropdown.value;
}

function closeDropdown() {
  showDropdown.value = false;
}

function handleLogout() {
  closeDropdown();
  authStore.logout();
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    closeDropdown();
  }
}
</script>

<template>
  <div class="relative" @keydown="handleKeyDown">
    <!-- Avatar Button -->
    <button
      @click="toggleDropdown"
      class="flex items-center gap-2 p-0.5 rounded-full hover:ring-2 hover:ring-primary-300 dark:hover:ring-primary-700 transition-all"
      aria-label="User menu"
      aria-expanded="showDropdown"
    >
      <div class="w-9 h-9 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-semibold shrink-0">
        {{ initials }}
      </div>
      <!-- Chevron (desktop) -->
      <svg class="w-3.5 h-3.5 text-surface-400 hidden lg:block transition-transform duration-200" :class="{ 'rotate-180': showDropdown }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <!-- Dropdown -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="showDropdown"
        class="absolute right-0 mt-2 w-56 bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 shadow-lg py-1.5 z-50 origin-top-right"
      >
        <!-- User Info -->
        <div class="px-4 py-2.5 border-b border-surface-100 dark:border-surface-700">
          <p class="text-sm font-semibold text-surface-900 dark:text-white truncate">{{ fullName }}</p>
          <p v-if="authStore.user?.email" class="text-xs text-surface-500 dark:text-surface-400 truncate mt-0.5">{{ authStore.user.email }}</p>
        </div>

        <!-- Dropdown Items -->
        <div class="py-1">
          <a
            href="/settings"
            @click="closeDropdown"
            class="flex items-center gap-2.5 px-4 py-2 text-sm text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700/50 transition-colors"
          >
            <svg class="w-4 h-4 text-surface-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>
            Settings
          </a>
        </div>

        <!-- Logout -->
        <div class="border-t border-surface-100 dark:border-surface-700 pt-1">
          <button
            @click="handleLogout"
            class="flex items-center gap-2.5 w-full px-4 py-2 text-sm text-danger-600 dark:text-danger-400 hover:bg-danger-50 dark:hover:bg-danger-500/10 transition-colors"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Sign Out
          </button>
        </div>
      </div>
    </Transition>

    <!-- Click Outside Overlay -->
    <div v-if="showDropdown" class="fixed inset-0 z-40" @click="closeDropdown"></div>
  </div>
</template>
