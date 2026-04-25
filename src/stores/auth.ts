import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types';
import { api, setTokens, clearTokens, getStoredToken, setStoredUser, getStoredUser } from '../services/api-bridge';

export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- OTP Flow State ---
  type AuthStep = 'login' | 'register' | 'otp-verify' | 'change-password' | 'forgot-password';
  const authStep = ref<AuthStep>('login');
  const pendingEmail = ref<string | null>(null);
  const pendingPurpose = ref<'register' | 'login' | 'change_password' | 'forgot_password' | null>(null);
  const passwordResetDone = ref(false); // tracks if forgot-password confirm succeeded
  const otpResendTimer = ref(0); // seconds until resend is allowed
  let _resendInterval: ReturnType<typeof setInterval> | null = null;

  // --- Computed ---
  const isAuthenticated = computed(() => !!user.value && !!token.value);
  const fullName = computed(() => user.value?.name || '');
  const initials = computed(() => user.value?.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'FL');
  const currency = computed(() => user.value?.currency || 'BDT');
  const isDarkMode = computed(() => user.value?.darkMode || false);
  const userId = computed(() => user.value?.id || '');
  const waitingForOtp = computed(() => authStep.value === 'otp-verify');

  // --- Auth Actions ---

  async function login(email: string, password: string): Promise<boolean> {
    isLoading.value = true;
    error.value = null;
    try {
      await api.post<{ message: string }>('/auth/login/', { email, password }, { noAuth: true });
      // Login credentials valid — OTP sent. Switch to OTP step.
      pendingEmail.value = email;
      pendingPurpose.value = 'login';
      authStep.value = 'otp-verify';
      startResendTimer();
      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'Login failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function register(name: string, email: string, password: string): Promise<boolean> {
    isLoading.value = true;
    error.value = null;
    try {
      await api.post<{ message: string }>('/auth/register/', {
        name,
        email,
        password,
        currency: 'BDT',
        dateFormat: 'dd/MM/yyyy',
        darkMode: false,
      }, { noAuth: true });
      // Registration successful — OTP sent. Switch to OTP step.
      pendingEmail.value = email;
      pendingPurpose.value = 'register';
      authStep.value = 'otp-verify';
      startResendTimer();
      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'Registration failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function verifyOtp(otp: string): Promise<boolean> {
    if (!pendingEmail.value || !pendingPurpose.value) return false;
    isLoading.value = true;
    error.value = null;
    try {
      const data = await api.post<{
        access: string;
        refresh?: string;
        token_type: string;
        user: User;
      }>('/auth/verify-otp/', {
        email: pendingEmail.value,
        otp,
        purpose: pendingPurpose.value,
      }, { noAuth: true });

      token.value = data.access;
      user.value = data.user;
      setTokens(data.access, data.refresh);
      setStoredUser(data.user);

      // Reset OTP state
      resetOtpState();

      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'OTP verification failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function resendOtp(): Promise<boolean> {
    if (!pendingEmail.value || !pendingPurpose.value) return false;
    if (otpResendTimer.value > 0) return false; // cooldown active
    isLoading.value = true;
    error.value = null;
    try {
      await api.post<{ message: string }>('/auth/resend-otp/', {
        email: pendingEmail.value,
        purpose: pendingPurpose.value,
      }, { noAuth: true });
      startResendTimer();
      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'Failed to resend OTP';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  function cancelOtp() {
    resetOtpState();
    error.value = null;
  }

  function resetOtpState() {
    authStep.value = 'login';
    pendingEmail.value = null;
    pendingPurpose.value = null;
    otpResendTimer.value = 0;
    passwordResetDone.value = false;
    if (_resendInterval) {
      clearInterval(_resendInterval);
      _resendInterval = null;
    }
  }

  function startResendTimer(seconds: number = 60) {
    if (_resendInterval) clearInterval(_resendInterval);
    otpResendTimer.value = seconds;
    _resendInterval = setInterval(() => {
      otpResendTimer.value--;
      if (otpResendTimer.value <= 0 && _resendInterval) {
        clearInterval(_resendInterval);
        _resendInterval = null;
      }
    }, 1000);
  }

  // --- Logout ---

  async function logout(): Promise<void> {
    try {
      await api.post('/auth/logout/');
    } catch {
      // Ignore logout errors — clear local state regardless
    }
    user.value = null;
    token.value = null;
    error.value = null;
    clearTokens();
    resetOtpState();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  // --- Session Restore (validate token with backend) ---

  async function restoreSession(): Promise<boolean> {
    // Try loading from localStorage first
    const storedUser = getStoredUser();
    if (storedUser) {
      user.value = storedUser;
    }

    // Then validate with backend
    try {
      const me = await api.get<User>('/auth/me/');
      user.value = me;
      token.value = getStoredToken(); // Token is already in localStorage (set by bridge)
      setStoredUser(me);
      return true;
    } catch {
      // Token invalid or expired — try refresh
      const storedRefresh = localStorage.getItem('finlife_refresh');
      if (storedRefresh) {
        try {
          const data = await api.post<{
            access: string;
            refresh?: string;
          }>('/auth/refresh/', { refresh: storedRefresh }, { noAuth: true });

          token.value = data.access;
          setTokens(data.access, data.refresh);

          // Re-fetch user
          const me = await api.get<User>('/auth/me/');
          user.value = me;
          setStoredUser(me);
          return true;
        } catch {
          // Refresh also failed
        }
      }

      // Session cannot be restored
      user.value = null;
      token.value = null;
      clearTokens();
      return false;
    }
  }

  // --- Profile ---

  async function toggleDarkMode(): Promise<void> {
    if (user.value) {
      user.value.darkMode = !user.value.darkMode;
      if (typeof document !== 'undefined') {
        document.documentElement.classList.toggle('dark', user.value.darkMode);
      }
      await updateProfile({ darkMode: user.value.darkMode });
    }
  }

  async function updateProfile(data: Partial<User>): Promise<void> {
    if (!user.value) return;
    try {
      const updated = await api.put<User>('/auth/me/', data);
      user.value = updated;
      setStoredUser(updated);
    } catch (e: any) {
      console.error('Failed to update profile:', e);
    }
  }

  // --- Password Change (OTP-Verified) ---

  async function requestPasswordChange(currentPassword: string): Promise<boolean> {
    isLoading.value = true;
    error.value = null;
    try {
      await api.post<{ message: string }>('/auth/change-password/', {
        current_password: currentPassword,
      });
      // Current password valid — OTP sent
      pendingEmail.value = user.value?.email || null;
      pendingPurpose.value = 'change_password';
      authStep.value = 'otp-verify';
      startResendTimer();
      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'Password change failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function confirmPasswordChange(otp: string, newPassword: string): Promise<boolean> {
    if (!pendingEmail.value) return false;
    isLoading.value = true;
    error.value = null;
    try {
      await api.post<{ message: string }>('/auth/change-password/confirm/', {
        email: pendingEmail.value,
        otp,
        new_password: newPassword,
      });
      resetOtpState();
      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'OTP verification failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  // --- Forgot Password (OTP-Verified, Unauthenticated) ---

  async function requestForgotPassword(email: string): Promise<boolean> {
    isLoading.value = true;
    error.value = null;
    passwordResetDone.value = false;
    try {
      await api.post<{ message: string }>('/auth/forgot-password/', { email }, { noAuth: true });
      // OTP sent (or email not found — same message to prevent enumeration)
      pendingEmail.value = email;
      pendingPurpose.value = 'forgot_password';
      authStep.value = 'otp-verify';
      startResendTimer();
      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'Failed to send reset code';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function confirmForgotPassword(otp: string, newPassword: string): Promise<boolean> {
    if (!pendingEmail.value) return false;
    isLoading.value = true;
    error.value = null;
    try {
      await api.post<{ message: string }>('/auth/forgot-password/confirm/', {
        email: pendingEmail.value,
        otp,
        new_password: newPassword,
      }, { noAuth: true });
      // Clear OTP flow state but keep passwordResetDone = true so the
      // success screen can render before the user clicks "Sign In".
      pendingEmail.value = null;
      pendingPurpose.value = null;
      authStep.value = 'login';
      otpResendTimer.value = 0;
      if (_resendInterval) {
        clearInterval(_resendInterval);
        _resendInterval = null;
      }
      passwordResetDone.value = true;
      return true;
    } catch (e: any) {
      error.value = e?.data?.message || e?.message || 'Password reset failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  function clearError() {
    error.value = null;
  }

  return {
    // State
    user,
    token,
    isLoading,
    error,
    // OTP Flow
    authStep,
    pendingEmail,
    pendingPurpose,
    otpResendTimer,
    waitingForOtp,
    // Computed
    isAuthenticated,
    fullName,
    initials,
    currency,
    isDarkMode,
    userId,
    // Actions
    login,
    register,
    verifyOtp,
    resendOtp,
    cancelOtp,
    requestPasswordChange,
    confirmPasswordChange,
    requestForgotPassword,
    confirmForgotPassword,
    passwordResetDone,
    logout,
    restoreSession,
    toggleDarkMode,
    updateProfile,
    clearError,
  };
});
