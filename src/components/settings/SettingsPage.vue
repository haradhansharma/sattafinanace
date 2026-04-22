<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useAuthStore } from '../../stores/auth';
import { useCurrencyStore } from '../../stores/currency';
import type { Currency } from '../../types';
import { PageHeader, Modal, Badge } from '../ui';

const authStore = useAuthStore();
const currencyStore = useCurrencyStore();

// ============ State ============
const showEditProfile = ref(false);
const showResetConfirm = ref(false);
const showExportToast = ref(false);
const toastMessage = ref('Action completed successfully!');

const profileForm = reactive({
  name: authStore.user.name,
  email: authStore.user.email,
});

const preferences = reactive({
  currency: authStore.user.currency,
  dateFormat: authStore.user.dateFormat,
  darkMode: authStore.user.darkMode,
  language: 'en',
});

const notifications = reactive({
  email: authStore.user.notifications.email,
  push: authStore.user.notifications.push,
  budgetAlert: authStore.user.notifications.budgetAlert,
  lowBalance: authStore.user.notifications.lowBalance,
  loanReminder: authStore.user.notifications.loanReminder,
});

// ============ Exchange Rate Editing ============
const editingRate = ref<string | null>(null);
const tempRate = ref('');

function startEditRate(currency: string) {
  editingRate.value = currency;
  tempRate.value = String(currencyStore.getRate(currency as Currency));
}

function cancelEditRate() {
  editingRate.value = null;
  tempRate.value = '';
}

function saveRate(currency: string) {
  const newRate = parseFloat(tempRate.value);
  if (!isNaN(newRate) && newRate > 0) {
    currencyStore.updateRate(currency as Currency, newRate);
    showToast('Exchange rate updated successfully!');
  }
  editingRate.value = null;
  tempRate.value = '';
}

function resetAllRates() {
  currencyStore.resetRates();
  showToast('Exchange rates reset to defaults.');
}

// ============ Quick Conversion Calculator ============
const convertFrom = ref<Currency>('USD');
const convertTo = ref<Currency>('BDT');
const convertAmount = ref('100');
const convertedResult = computed(() => {
  const amount = parseFloat(convertAmount.value);
  if (isNaN(amount) || amount <= 0) return '';
  const inBase = currencyStore.convertToBase(amount, convertFrom.value);
  const result = currencyStore.convertFromBase(inBase, convertTo.value);
  return `${currencyStore.formatWithCurrency(amount, convertFrom.value)} = ${currencyStore.formatWithCurrency(result, convertTo.value)}`;
});

// ============ Actions ============
function saveProfile() {
  authStore.updateProfile({ name: profileForm.name, email: profileForm.email });
  showEditProfile.value = false;
}

function toggleDark() {
  preferences.darkMode = !preferences.darkMode;
  authStore.toggleDarkMode();
}

function savePreferences() {
  authStore.updateProfile({
    currency: preferences.currency,
    dateFormat: preferences.dateFormat,
  });
}

function saveNotifications() {
  authStore.updateProfile({ notifications: { ...notifications } });
}

function showToast(message: string) {
  toastMessage.value = message;
  showExportToast.value = true;
  setTimeout(() => { showExportToast.value = false; }, 3000);
}

function exportData() {
  showToast('Data exported successfully!');
}

function resetData() {
  showResetConfirm.value = false;
  showToast('All data has been reset.');
}

const initials = authStore.initials;
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Settings" subtitle="Manage your account and application preferences" />

    <!-- Toast Notification -->
    <Transition name="modal">
      <div
        v-if="showExportToast"
        class="fixed top-6 right-6 z-50 bg-accent-600 text-white px-5 py-3 rounded-lg shadow-lg flex items-center gap-2 text-sm font-medium"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        {{ toastMessage }}
      </div>
    </Transition>

    <!-- ==================== Currency Conversion Rates ==================== -->
    <div class="card p-6 animate-fade-in">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-lg font-semibold text-surface-900 dark:text-white">Currency Conversion Rates</h3>
        <button class="text-xs px-3 py-1.5 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors" @click="resetAllRates">
          Reset to Defaults
        </button>
      </div>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-5">
        Base currency: <strong>{{ currencyStore.baseCurrency }}</strong> — 1 unit of foreign currency = X {{ currencyStore.baseCurrency }}
      </p>

      <!-- Exchange Rate Table -->
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-surface-200 dark:border-surface-700">
              <th class="text-left py-2.5 px-3 text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">Currency</th>
              <th class="text-left py-2.5 px-3 text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">Rate to {{ currencyStore.baseCurrency }}</th>
              <th class="text-right py-2.5 px-3 text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">Symbol</th>
              <th class="text-center py-2.5 px-3 text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider w-24">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="rate in currencyStore.allRates"
              :key="rate.currency"
              class="border-b border-surface-100 dark:border-surface-700/50 last:border-0"
            >
              <td class="py-3 px-3">
                <div class="flex items-center gap-2">
                  <span class="text-base">{{ rate.flag }}</span>
                  <div>
                    <span class="font-medium text-surface-900 dark:text-white">{{ rate.currency }}</span>
                    <span v-if="rate.currency === currencyStore.baseCurrency" class="ml-1.5">
                      <Badge variant="info" size="sm">Base</Badge>
                    </span>
                    <p class="text-xs text-surface-400">{{ rate.name }}</p>
                  </div>
                </div>
              </td>
              <td class="py-3 px-3">
                <!-- Editing mode -->
                <div v-if="editingRate === rate.currency" class="flex items-center gap-2">
                  <input
                    v-model.number="tempRate"
                    type="number"
                    step="0.01"
                    min="0.01"
                    class="input-field w-32 py-1.5 text-sm tabular-nums"
                    autofocus
                    @keyup.enter="saveRate(rate.currency)"
                    @keyup.escape="cancelEditRate"
                  />
                  <button @click="saveRate(rate.currency)" class="text-xs px-2 py-1 rounded bg-accent-100 dark:bg-accent-500/20 text-accent-600 dark:text-accent-400 hover:bg-accent-200 dark:hover:bg-accent-500/30 transition-colors font-medium">
                    Save
                  </button>
                  <button @click="cancelEditRate" class="text-xs px-2 py-1 rounded bg-surface-100 dark:bg-surface-700 text-surface-500 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors">
                    Cancel
                  </button>
                </div>
                <!-- Display mode -->
                <div v-else>
                  <span class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ rate.rate }}</span>
                  <span class="text-xs text-surface-400 ml-1">{{ currencyStore.baseCurrency }}/{{ rate.currency }}</span>
                </div>
              </td>
              <td class="py-3 px-3 text-right">
                <span class="text-surface-600 dark:text-surface-400">{{ rate.symbol }}</span>
              </td>
              <td class="py-3 px-3 text-center">
                <button
                  v-if="rate.currency !== currencyStore.baseCurrency"
                  @click="startEditRate(rate.currency)"
                  class="text-xs px-2.5 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-500/20 transition-colors font-medium"
                >
                  Edit
                </button>
                <span v-else class="text-xs text-surface-400">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Quick Conversion Calculator -->
      <div class="mt-5 pt-5 border-t border-surface-200 dark:border-surface-700">
        <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Quick Conversion Calculator</h4>
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div class="flex-1">
            <label class="text-[10px] text-surface-400 uppercase tracking-wider mb-1 block">Amount</label>
            <input
              v-model="convertAmount"
              type="number"
              min="0"
              class="input-field py-2 text-sm tabular-nums"
              placeholder="100"
            />
          </div>
          <div class="flex-1">
            <label class="text-[10px] text-surface-400 uppercase tracking-wider mb-1 block">From</label>
            <select v-model="convertFrom" class="input-field py-2 text-sm">
              <option v-for="r in currencyStore.allRates" :key="r.currency" :value="r.currency">{{ r.flag }} {{ r.currency }}</option>
            </select>
          </div>
          <div class="flex items-center justify-center pt-4 sm:pt-4">
            <svg class="w-5 h-5 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/></svg>
          </div>
          <div class="flex-1">
            <label class="text-[10px] text-surface-400 uppercase tracking-wider mb-1 block">To</label>
            <select v-model="convertTo" class="input-field py-2 text-sm">
              <option v-for="r in currencyStore.allRates" :key="r.currency" :value="r.currency">{{ r.flag }} {{ r.currency }}</option>
            </select>
          </div>
          <div class="flex-1 flex items-end">
            <div class="w-full bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2.5 text-center">
              <p class="text-[10px] text-surface-400 uppercase tracking-wider mb-0.5">Result</p>
              <p class="text-sm font-bold text-surface-900 dark:text-white tabular-nums" v-if="convertedResult">
                {{ convertedResult }}
              </p>
              <p v-else class="text-sm text-surface-400">Enter amount</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile Section -->
    <div class="card p-6 animate-fade-in">
      <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-5">Profile</h3>
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-6">
        <!-- Avatar -->
        <div class="w-20 h-20 rounded-full bg-primary-500 flex items-center justify-center text-white text-2xl font-bold shrink-0">
          {{ initials }}
        </div>
        <div class="flex-1 min-w-0">
          <h4 class="text-xl font-bold text-surface-900 dark:text-white">{{ authStore.fullName }}</h4>
          <p class="text-surface-500 dark:text-surface-400">{{ authStore.user.email }}</p>
          <div class="flex flex-wrap gap-2 mt-2">
            <span class="badge-info">{{ currencyStore.baseCurrency }} Currency</span>
            <span class="badge-success">Active</span>
          </div>
        </div>
        <button class="btn-secondary" @click="showEditProfile = true">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
          Edit Profile
        </button>
      </div>
    </div>

    <!-- Preferences Section -->
    <div class="card p-6 animate-fade-in">
      <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-5">Preferences</h3>
      <div class="space-y-5">
        <!-- Base Currency -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-surface-100 dark:border-surface-700">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Base Currency</p>
            <p class="text-xs text-surface-400">All amounts are converted to this currency for totals and summaries</p>
          </div>
          <select
            :value="currencyStore.baseCurrency"
            class="input-field sm:w-48"
            @change="currencyStore.setBaseCurrency(($event.target as HTMLSelectElement).value as Currency)"
          >
            <option v-for="r in currencyStore.allRates" :key="r.currency" :value="r.currency">{{ r.flag }} {{ r.currency }} ({{ r.symbol }}) — {{ r.name }}</option>
          </select>
        </div>

        <!-- Date Format -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-surface-100 dark:border-surface-700">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Date Format</p>
            <p class="text-xs text-surface-400">Choose how dates are displayed</p>
          </div>
          <select v-model="preferences.dateFormat" class="input-field sm:w-48" @change="savePreferences">
            <option value="dd/MM/yyyy">DD/MM/YYYY</option>
            <option value="MM/dd/yyyy">MM/DD/YYYY</option>
            <option value="yyyy-MM-dd">YYYY-MM-DD</option>
            <option value="dd MMM yyyy">DD MMM YYYY</option>
          </select>
        </div>

        <!-- Dark Mode -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-surface-100 dark:border-surface-700">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Dark Mode</p>
            <p class="text-xs text-surface-400">Toggle dark theme appearance</p>
          </div>
          <button
            @click="toggleDark"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0"
            :class="preferences.darkMode ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm"
              :class="preferences.darkMode ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Language -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Language</p>
            <p class="text-xs text-surface-400">Select your preferred language</p>
          </div>
          <select v-model="preferences.language" class="input-field sm:w-48" disabled>
            <option value="en">English (Coming Soon)</option>
            <option value="bn">বাংলা (Coming Soon)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Notification Settings -->
    <div class="card p-6 animate-fade-in">
      <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-1">Notification Settings</h3>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-5">Choose what notifications you want to receive</p>

      <div class="space-y-4">
        <!-- Email -->
        <div class="flex items-center justify-between pb-4 border-b border-surface-100 dark:border-surface-700">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Email Notifications</p>
            <p class="text-xs text-surface-400">Receive important updates via email</p>
          </div>
          <button
            @click="notifications.email = !notifications.email; saveNotifications()"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0"
            :class="notifications.email ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm"
              :class="notifications.email ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Push -->
        <div class="flex items-center justify-between pb-4 border-b border-surface-100 dark:border-surface-700">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Push Notifications</p>
            <p class="text-xs text-surface-400">Get real-time push notifications</p>
          </div>
          <button
            @click="notifications.push = !notifications.push; saveNotifications()"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0"
            :class="notifications.push ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm"
              :class="notifications.push ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Budget Alert -->
        <div class="flex items-center justify-between pb-4 border-b border-surface-100 dark:border-surface-700">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Budget Alerts</p>
            <p class="text-xs text-surface-400">Get warned when nearing or exceeding budget limits</p>
          </div>
          <button
            @click="notifications.budgetAlert = !notifications.budgetAlert; saveNotifications()"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0"
            :class="notifications.budgetAlert ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm"
              :class="notifications.budgetAlert ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Low Balance -->
        <div class="flex items-center justify-between pb-4 border-b border-surface-100 dark:border-surface-700">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Low Balance Alert</p>
            <p class="text-xs text-surface-400">Get notified when account balance is low</p>
          </div>
          <button
            @click="notifications.lowBalance = !notifications.lowBalance; saveNotifications()"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0"
            :class="notifications.lowBalance ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm"
              :class="notifications.lowBalance ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Loan Reminder -->
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">Loan Payment Reminders</p>
            <p class="text-xs text-surface-400">Get reminders before loan EMI due dates</p>
          </div>
          <button
            @click="notifications.loanReminder = !notifications.loanReminder; saveNotifications()"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0"
            :class="notifications.loanReminder ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm"
              :class="notifications.loanReminder ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>
      </div>
    </div>

    <!-- Data Management -->
    <div class="card p-6 animate-fade-in">
      <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-1">Data Management</h3>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-5">Export or reset your financial data</p>

      <div class="flex flex-col sm:flex-row gap-3">
        <button class="btn-primary" @click="exportData">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          Export Data
        </button>
        <button class="btn-danger" @click="showResetConfirm = true">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          Reset All Data
        </button>
      </div>
    </div>

    <!-- ============ EDIT PROFILE MODAL ============ -->
    <Modal :is-open="showEditProfile" title="Edit Profile" size="md" @close="showEditProfile = false">
      <div class="space-y-4">
        <!-- Avatar Preview -->
        <div class="flex justify-center mb-4">
          <div class="w-24 h-24 rounded-full bg-primary-500 flex items-center justify-center text-white text-3xl font-bold">
            {{ profileForm.name.split(' ').map(n => n[0]).join('').toUpperCase() }}
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Full Name</label>
          <input v-model="profileForm.name" type="text" class="input-field" placeholder="Your name" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Email Address</label>
          <input v-model="profileForm.email" type="email" class="input-field" placeholder="you@example.com" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showEditProfile = false">Cancel</button>
          <button class="btn-primary" @click="saveProfile">Save Changes</button>
        </div>
      </div>
    </Modal>

    <!-- ============ RESET CONFIRM MODAL ============ -->
    <Modal :is-open="showResetConfirm" title="Reset All Data" size="sm" @close="showResetConfirm = false">
      <div class="space-y-4">
        <div class="bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/30 rounded-lg p-4">
          <p class="text-sm text-danger-700 dark:text-danger-400">
            This will permanently delete <strong>all your financial data</strong> including transactions, budgets, loans, and settings. This action cannot be undone.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showResetConfirm = false">Cancel</button>
          <button class="btn-danger" @click="resetData">Yes, Reset Everything</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
