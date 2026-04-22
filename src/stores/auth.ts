import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types';
import { mockUser } from '../mock-data';

export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- Computed ---
  const isAuthenticated = computed(() => !!user.value && !!token.value);
  const fullName = computed(() => user.value?.name || '');
  const initials = computed(() => user.value?.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'FL');
  const currency = computed(() => user.value?.currency || 'BDT');
  const isDarkMode = computed(() => user.value?.darkMode || false);
  const userId = computed(() => user.value?.id || '');

  // --- Auth Actions ---
  async function login(email: string, password: string): Promise<boolean> {
    isLoading.value = true;
    error.value = null;
    try {
      // Simulate API call — in production this calls the backend
      await new Promise(r => setTimeout(r, 500));

      // Mock validation: accept any email/password for demo
      if (email && password.length >= 4) {
        user.value = { ...mockUser, email };
        token.value = `mock_jwt_${Date.now()}_${btoa(email)}`;
        // Persist session
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('finlife_token', token.value);
          localStorage.setItem('finlife_user', JSON.stringify(user.value));
        }
        return true;
      }
      error.value = 'Invalid email or password (min 4 chars).';
      return false;
    } catch (e: any) {
      error.value = e.message || 'Login failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function register(name: string, email: string, password: string): Promise<boolean> {
    isLoading.value = true;
    error.value = null;
    try {
      await new Promise(r => setTimeout(r, 500));

      if (!name || !email || password.length < 4) {
        error.value = 'All fields required. Password must be at least 4 characters.';
        return false;
      }

      // In production: call register API
      user.value = { ...mockUser, name, email, id: `user_${Date.now()}` };
      token.value = `mock_jwt_${Date.now()}_${btoa(email)}`;
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('finlife_token', token.value);
        localStorage.setItem('finlife_user', JSON.stringify(user.value));
      }
      return true;
    } catch (e: any) {
      error.value = e.message || 'Registration failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  function logout() {
    user.value = null;
    token.value = null;
    error.value = null;
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('finlife_token');
      localStorage.removeItem('finlife_user');
    }
    // Redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  // --- Session Restore ---
  function restoreSession(): boolean {
    if (typeof localStorage === 'undefined') return false;
    const storedToken = localStorage.getItem('finlife_token');
    const storedUser = localStorage.getItem('finlife_user');
    if (storedToken && storedUser) {
      try {
        token.value = storedToken;
        user.value = JSON.parse(storedUser);
        return true;
      } catch {
        return false;
      }
    }
    return false;
  }

  // --- Profile ---
  function toggleDarkMode() {
    if (user.value) {
      user.value.darkMode = !user.value.darkMode;
      if (typeof document !== 'undefined') {
        document.documentElement.classList.toggle('dark', user.value.darkMode);
      }
    }
  }

  function updateProfile(data: Partial<User>) {
    if (user.value) {
      Object.assign(user.value, data);
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('finlife_user', JSON.stringify(user.value));
      }
    }
  }

  function clearError() {
    error.value = null;
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    fullName,
    initials,
    currency,
    isDarkMode,
    userId,
    login,
    register,
    logout,
    restoreSession,
    toggleDarkMode,
    updateProfile,
    clearError,
  };
});
