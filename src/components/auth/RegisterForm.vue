<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '../../stores/auth';

const authStore = useAuthStore();
const name = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');

const passwordMismatch = computed(() => {
  return confirmPassword.value.length > 0 && password.value !== confirmPassword.value;
});

async function handleSubmit() {
  if (!name.value || !email.value || !password.value || !confirmPassword.value) return;
  if (passwordMismatch.value) return;
  const success = await authStore.register(name.value, email.value, password.value);
  if (success) {
    window.location.href = '/dashboard';
  }
}
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-1">Create your account</h2>
    <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">Start managing your finances with FinLife</p>

    <!-- Error Alert -->
    <div v-if="authStore.error" class="mb-4 p-3 rounded-lg bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/20 flex items-center gap-2">
      <svg class="w-4 h-4 text-danger-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span class="text-sm text-danger-700 dark:text-danger-400">{{ authStore.error }}</span>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <!-- Full Name -->
      <div>
        <label for="name" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Full Name</label>
        <input
          id="name"
          v-model="name"
          type="text"
          placeholder="Rahim Uddin"
          required
          autocomplete="name"
          class="input-field"
        />
      </div>

      <!-- Email -->
      <div>
        <label for="reg-email" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Email Address</label>
        <input
          id="reg-email"
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
        <label for="reg-password" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Password</label>
        <input
          id="reg-password"
          v-model="password"
          type="password"
          placeholder="At least 4 characters"
          required
          minlength="4"
          autocomplete="new-password"
          class="input-field"
        />
      </div>

      <!-- Confirm Password -->
      <div>
        <label for="reg-confirm" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Confirm Password</label>
        <input
          id="reg-confirm"
          v-model="confirmPassword"
          type="password"
          placeholder="Confirm your password"
          required
          minlength="4"
          autocomplete="new-password"
          class="input-field"
        />
        <p v-if="passwordMismatch" class="text-xs text-danger-500 mt-1">Passwords do not match.</p>
      </div>

      <!-- Submit -->
      <button
        type="submit"
        :disabled="authStore.isLoading || passwordMismatch"
        class="w-full btn-primary justify-center py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg v-if="authStore.isLoading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"></circle>
          <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-75"></path>
        </svg>
        <span v-if="authStore.isLoading">Creating account...</span>
        <span v-else>Create Account</span>
      </button>
    </form>

    <!-- Login Link -->
    <p class="text-center text-sm text-surface-500 dark:text-surface-400 mt-6">
      Already have an account?
      <a href="/login" class="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
        Sign In
      </a>
    </p>
  </div>
</template>
