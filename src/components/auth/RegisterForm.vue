<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '../../stores/auth';

const authStore = useAuthStore();
const name = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const otpDigits = ref<string[]>(['', '', '', '', '', '']);

const passwordMismatch = computed(() => {
  return confirmPassword.value.length > 0 && password.value !== confirmPassword.value;
});

async function handleSubmit() {
  if (!name.value || !email.value || !password.value || !confirmPassword.value) return;
  if (passwordMismatch.value) return;
  const success = await authStore.register(name.value, email.value, password.value);
  if (success) {
    // OTP sent — OTP step is now shown
  }
}

async function handleOtpSubmit() {
  const code = otpDigits.value.join('');
  if (code.length !== 6) return;
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

function formatTimer(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
</script>

<template>
  <div>
    <!-- ==================== REGISTER FORM ==================== -->
    <template v-if="!authStore.waitingForOtp">
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
    </template>

    <!-- ==================== OTP VERIFICATION ==================== -->
    <template v-else>
      <h2 class="text-xl font-bold text-surface-900 dark:text-white mb-1">Verify Your Email</h2>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">
        Enter the 6-digit code sent to <span class="font-medium text-surface-700 dark:text-surface-200">{{ authStore.pendingEmail }}</span>
      </p>

      <!-- Info Alert -->
      <div class="mb-4 p-3 rounded-lg bg-primary-50 dark:bg-primary-500/10 border border-primary-200 dark:border-primary-500/20 flex items-start gap-2">
        <svg class="w-4 h-4 text-primary-500 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-8.97 5.7a1.94 1.94 0 01-2.06 0L2 7"/>
        </svg>
        <span class="text-sm text-primary-700 dark:text-primary-400">We sent a verification code to your email. It expires in 5 minutes.</span>
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
          Back to Register
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
