<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '../../stores/auth';

const authStore = useAuthStore();
const email = ref('');
const password = ref('');
const otp = ref('');
const otpDigits = ref<string[]>(['', '', '', '', '', '']);

async function handleSubmit() {
  if (!email.value || !password.value) return;
  const success = await authStore.login(email.value, password.value);
  if (success) {
    // OTP sent — OTP step is now shown
  }
}

async function handleOtpSubmit() {
  const code = otpDigits.value.join('');
  if (code.length !== 6) return;
  otp.value = code;
  const success = await authStore.verifyOtp(code);
  if (success) {
    window.location.href = '/dashboard';
  }
}

async function handleResend() {
  await authStore.resendOtp();
}

function handleOtpInput(index: number, event: Event) {
  const input = event.target as HTMLInputElement;
  const value = input.value.replace(/\D/g, '');
  if (value.length > 1) return;
  otpDigits.value[index] = value;

  // Auto-focus next input
  if (value && index < 5) {
    const nextInput = input.parentElement?.querySelector(`input[data-otp-index="${index + 1}"]`);
    if (nextInput) (nextInput as HTMLInputElement).focus();
  }

  // Auto-submit when all 6 digits entered
  if (otpDigits.value.every(d => d.length === 1)) {
    handleOtpSubmit();
  }
}

function handleOtpKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    const prevInput = (event.target as HTMLInputElement).parentElement?.querySelector(
      `input[data-otp-index="${index - 1}"]`
    );
    if (prevInput) (prevInput as HTMLInputElement).focus();
  }
}

async function fillDemo() {
  email.value = 'rahim@example.com';
  password.value = 'demo1234';
  await handleSubmit();
}

function formatTimer(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
</script>

<template>
  <div>
    <!-- ==================== LOGIN FORM ==================== -->
    <template v-if="!authStore.waitingForOtp">
      <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-1">Welcome back</h2>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">Sign in to your FinLife account</p>

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

        <!-- Forgot Password -->
        <p class="text-center text-sm text-surface-500 dark:text-surface-400 mt-4">
          <a href="/forgot-password" class="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
            Forgot Password?
          </a>
        </p>
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

      <!-- Demo Login -->
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
    </template>

    <!-- ==================== OTP VERIFICATION ==================== -->
    <template v-else>
      <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-1">Verify Login</h2>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">
        Enter the 6-digit code sent to <span class="font-medium text-surface-700 dark:text-surface-200">{{ authStore.pendingEmail }}</span>
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

      <!-- OTP Input — 6 digit boxes -->
      <form @submit.prevent="handleOtpSubmit" class="space-y-4">
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

        <!-- Submit OTP -->
        <button
          type="submit"
          :disabled="authStore.isLoading || otpDigits.some(d => !d)"
          class="w-full btn-primary justify-center py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="authStore.isLoading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"></circle>
            <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-75"></path>
          </svg>
          <span v-if="authStore.isLoading">Verifying...</span>
          <span v-else>Verify Code</span>
        </button>
      </form>

      <!-- Resend / Cancel -->
      <div class="flex items-center justify-between mt-4">
        <button
          @click="authStore.cancelOtp()"
          :disabled="authStore.isLoading"
          class="text-sm text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 transition-colors disabled:opacity-50"
        >
          Back to Sign In
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
  </div>
</template>
