<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '../../stores/auth';

const authStore = useAuthStore();
const email = ref('');
const password = ref('');

async function handleSubmit() {
  if (!email.value || !password.value) return;
  const success = await authStore.login(email.value, password.value);
  if (success) {
    window.location.href = '/dashboard';
  }
}

async function fillDemo() {
  email.value = 'rahim@example.com';
  password.value = 'demo1234';
  await handleSubmit();
}
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-1">Welcome back</h2>
    <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">Sign in to your FinLife account</p>

    <!-- Debug info (remove later) -->
    <div v-if="!authStore || typeof authStore.login !== 'function'" class="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20">
      <p class="text-xs text-amber-700 dark:text-amber-400 font-mono">
        Pinia debug: store={{ authStore ? 'exists' : 'null' }}, login={{ typeof authStore?.login }}
      </p>
    </div>

    <!-- Error Alert -->
    <div v-if="authStore.error" class="mb-4 p-3 rounded-lg bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/20 flex items-center gap-2">
      <svg class="w-4 h-4 text-danger-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span class="text-sm text-danger-700 dark:text-danger-400">{{ authStore.error }}</span>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <!-- Email -->
      <div>
        <label for="email" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Email Address</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="you@example.com"
          required
          autocomplete="email"
          class="input-field"
        />
      </div>

      <!-- Password -->
      <div>
        <label for="password" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="Enter your password"
          required
          minlength="4"
          autocomplete="current-password"
          class="input-field"
        />
      </div>

      <!-- Submit -->
      <button
        type="submit"
        :disabled="authStore.isLoading"
        class="w-full btn-primary justify-center py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg v-if="authStore.isLoading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"></circle>
          <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-75"></path>
        </svg>
        <span v-if="authStore.isLoading">Signing in...</span>
        <span v-else>Sign In</span>
      </button>
    </form>

    <!-- Divider -->
    <div class="relative my-6">
      <div class="absolute inset-0 flex items-center">
        <div class="w-full border-t border-surface-200 dark:border-surface-700"></div>
      </div>
      <div class="relative flex justify-center text-xs">
        <span class="px-2 bg-white dark:bg-surface-800 text-surface-400">or</span>
      </div>
    </div>

    <!-- Demo Login — auto-submits -->
    <button
      @click="fillDemo"
      :disabled="authStore.isLoading"
      class="w-full btn-secondary justify-center py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <svg v-if="authStore.isLoading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"></circle>
        <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-75"></path>
      </svg>
      <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
      <span v-if="authStore.isLoading">Logging in...</span>
      <span v-else>Demo Login (Auto Sign In)</span>
    </button>

    <!-- Register Link -->
    <p class="text-center text-sm text-surface-500 dark:text-surface-400 mt-6">
      Don't have an account?
      <a href="/register" class="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
        Register
      </a>
    </p>
  </div>
</template>
