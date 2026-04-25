<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '../../stores/auth';

const authStore = useAuthStore();
const email = ref('');
const otpDigits = ref<string[]>(['', '', '', '', '', '']);
const newPassword = ref('');
const confirmPassword = ref('');

const passwordMismatch = computed(() => {
  return confirmPassword.value.length > 0 && newPassword.value !== confirmPassword.value;
});

// Determine which step we're on:
//   1. Email entry (not waiting for OTP, password not reset)
//   2. OTP + New Password entry (waiting for OTP)
//   3. Success screen (password reset done)
const showEmailStep = computed(() => !authStore.waitingForOtp && !authStore.passwordResetDone);
const showOtpStep = computed(() => authStore.waitingForOtp && !authStore.passwordResetDone);
const showSuccessStep = computed(() => authStore.passwordResetDone);

async function handleSubmitEmail() {
  if (!email.value) return;
  const success = await authStore.requestForgotPassword(email.value);
  if (success) {
    // OTP sent — OTP step is now shown
  }
}

async function handleSubmitReset() {
  const code = otpDigits.value.join('');
  if (code.length !== 6 || !newPassword.value || passwordMismatch.value) return;
  const success = await authStore.confirmForgotPassword(code, newPassword.value);
  if (success) {
    // Password reset done — success step shown
  }
}

async function handleResend() {
  await authStore.resendOtp();
}

function handleBack() {
  authStore.cancelOtp();
  authStore.clearError();
}

function goToLogin() {
  window.location.href = '/login';
}

function handleOtpInput(index: number, event: Event) {
  const input = event.target as HTMLInputElement;
  const value = input.value.replace(/\D/g, '');
  if (value.length > 1) return;
  // Use splice — guaranteed to trigger Vue reactivity (unlike index assignment)
  otpDigits.value.splice(index, 1, value);

  // Auto-focus next input
  if (value && index < 5) {
    const nextInput = input.parentElement?.querySelector(`input[data-otp-index="${index + 1}"]`);
    if (nextInput) (nextInput as HTMLInputElement).focus();
  }
}

function handleOtpKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    // Clear previous digit and focus it
    otpDigits.value.splice(index - 1, 1, '');
    const prevInput = (event.target as HTMLInputElement).parentElement?.querySelector(
      `input[data-otp-index="${index - 1}"]`
    );
    if (prevInput) (prevInput as HTMLInputElement).focus();
  }
}

function formatTimer(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
</script>

<template>
  <div>
    <!-- ==================== STEP 1: EMAIL ENTRY ==================== -->
    <template v-if="showEmailStep">
      <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-1">Forgot Password</h2>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">
        Enter your email and we'll send you a verification code to reset your password.
      </p>

      <!-- Error Alert -->
      <div v-if="authStore.error" class="mb-4 p-3 rounded-lg bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/20 flex items-center gap-2">
        <svg class="w-4 h-4 text-danger-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span class="text-sm text-danger-700 dark:text-danger-400">{{ authStore.error }}</span>
      </div>

      <form @submit.prevent="handleSubmitEmail" class="space-y-4">
        <!-- Email -->
        <div>
          <label for="forgot-email" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Email Address</label>
          <input
            id="forgot-email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            autocomplete="email"
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
          <span v-if="authStore.isLoading">Sending code...</span>
          <span v-else>Send Reset Code</span>
        </button>
      </form>

      <!-- Back to Login -->
      <p class="text-center text-sm text-surface-500 dark:text-surface-400 mt-6">
        Remember your password?
        <a href="/login" class="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
          Sign In
        </a>
      </p>
    </template>

    <!-- ==================== STEP 2: OTP + NEW PASSWORD ==================== -->
    <template v-else-if="showOtpStep">
      <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-1">Reset Password</h2>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">
        Enter the code sent to <span class="font-medium text-surface-700 dark:text-surface-200">{{ authStore.pendingEmail }}</span>
      </p>

      <!-- Info Alert -->
      <div class="mb-4 p-3 rounded-lg bg-primary-50 dark:bg-primary-500/10 border border-primary-200 dark:border-primary-500/20 flex items-start gap-2">
        <svg class="w-4 h-4 text-primary-500 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
        </svg>
        <span class="text-sm text-primary-700 dark:text-primary-400">Check your email for the verification code. It expires in 5 minutes.</span>
      </div>

      <!-- Error Alert -->
      <div v-if="authStore.error" class="mb-4 p-3 rounded-lg bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/20 flex items-center gap-2">
        <svg class="w-4 h-4 text-danger-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span class="text-sm text-danger-700 dark:text-danger-400">{{ authStore.error }}</span>
      </div>

      <form @submit.prevent="handleSubmitReset" class="space-y-4">
        <!-- OTP Input — 6 digit boxes -->
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">Verification Code</label>
          <div class="flex justify-center gap-2">
            <input
              v-for="i in 6"
              :key="i"
              :data-otp-index="i - 1"
              :value="otpDigits[i - 1]"
              @input="handleOtpInput(i - 1, $event)"
              @keydown="handleOtpKeydown(i - 1, $event)"
              type="text"
              inputmode="numeric"
              maxlength="1"
              autocomplete="one-time-code"
              class="w-11 h-12 text-center text-lg font-bold rounded-lg border border-surface-300 dark:border-surface-600 bg-white dark:bg-surface-800 text-surface-900 dark:text-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all"
              required
            />
          </div>
        </div>

        <!-- New Password -->
        <div>
          <label for="new-password" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">New Password</label>
          <input
            id="new-password"
            v-model="newPassword"
            type="password"
            placeholder="At least 4 characters"
            required
            minlength="4"
            autocomplete="new-password"
            class="input-field"
          />
        </div>

        <!-- Confirm New Password -->
        <div>
          <label for="confirm-new-password" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">Confirm New Password</label>
          <input
            id="confirm-new-password"
            v-model="confirmPassword"
            type="password"
            placeholder="Confirm your new password"
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
          :disabled="authStore.isLoading || otpDigits.some(d => !d) || !newPassword || passwordMismatch"
          class="w-full btn-primary justify-center py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="authStore.isLoading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"></circle>
            <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-75"></path>
          </svg>
          <span v-if="authStore.isLoading">Resetting password...</span>
          <span v-else>Reset Password</span>
        </button>
      </form>

      <!-- Resend / Back -->
      <div class="flex items-center justify-between mt-4">
        <button
          @click="handleBack"
          :disabled="authStore.isLoading"
          class="text-sm text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 transition-colors disabled:opacity-50"
        >
          Back
        </button>
        <button
          v-if="authStore.otpResendTimer > 0"
          disabled
          class="text-sm text-surface-400 dark:text-surface-500 cursor-not-allowed"
        >
          Resend in {{ formatTimer(authStore.otpResendTimer) }}
        </button>
        <button
          v-else
          @click="handleResend"
          :disabled="authStore.isLoading"
          class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors disabled:opacity-50"
        >
          Resend Code
        </button>
      </div>
    </template>

    <!-- ==================== STEP 3: SUCCESS ==================== -->
    <template v-else-if="showSuccessStep">
      <div class="text-center py-4">
        <!-- Success Icon -->
        <div class="mx-auto w-16 h-16 rounded-full bg-green-100 dark:bg-green-500/10 flex items-center justify-center mb-4">
          <svg class="w-8 h-8 text-green-600 dark:text-green-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>

        <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-2">Password Reset Successful</h2>
        <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">
          Your password has been changed. You can now sign in with your new password.
        </p>

        <button
          @click="goToLogin"
          class="w-full btn-primary justify-center py-2.5"
        >
          Sign In
        </button>
      </div>
    </template>
  </div>
</template>
