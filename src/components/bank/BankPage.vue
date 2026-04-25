<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useBankStore } from '../../stores/bank';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { useCurrencyStore } from '../../stores/currency';
import { useExpenseStore } from '../../stores/expense';
import type { Currency } from '../../types';
import { PageHeader, DataTable, Badge, Modal, SearchInput, EmptyState, Tabs, StatCard } from '../ui';
import type { Column } from '../ui/DataTable.vue';
import type { Transaction } from '../../types';

const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;
const expenseStore = useExpenseStore();

// ==================== State ====================
const selectedAccountId = ref<string | null>(null);
const transactionTypeFilter = ref<string>('all');
const searchQuery = ref('');
const showAddTransactionModal = ref(false);
const showAddAccountModal = ref(false);

// ==================== Categories Map ====================
const categoryMap = computed(() => {
  const map: Record<string, { name: string; icon: string }> = {};
  expenseStore.categories.forEach(c => { map[c.id] = { name: c.name, icon: c.icon }; });
  return map;
});

// ==================== Computed: Summary Stats ====================
const currentMonth = new Date().getMonth();
const currentYear = new Date().getFullYear();

const monthlyCredits = computed(() => {
  return bankStore.transactions
    .filter(t => {
      const d = new Date(t.date);
      return d.getMonth() === currentMonth && d.getFullYear() === currentYear && t.direction === 'credit';
    })
    .reduce((sum, t) => sum + currencyStore.convertToBase(t.amount, t.currency || 'BDT'), 0);
});

const monthlyDebits = computed(() => {
  return bankStore.transactions
    .filter(t => {
      const d = new Date(t.date);
      return d.getMonth() === currentMonth && d.getFullYear() === currentYear && t.direction === 'debit';
    })
    .reduce((sum, t) => sum + currencyStore.convertToBase(t.amount, t.currency || 'BDT'), 0);
});

const activeAccountsCount = computed(() => bankStore.bankAccounts.filter(a => a.isActive).length);

// ==================== Computed: Account Balances ====================
function getAccountBalance(accountId: string): number {
  return bankStore.getAccountBalance(accountId);
}

// ==================== Computed: Selected Account ====================
const selectedAccount = computed(() => {
  if (!selectedAccountId.value) return null;
  return bankStore.bankAccounts.find(a => a.id === selectedAccountId.value) || null;
});

const accountBalance = computed(() => {
  if (!selectedAccountId.value) return 0;
  return bankStore.getAccountBalance(selectedAccountId.value);
});

// ==================== Computed: Filtered Transactions ====================
const filteredTransactions = computed(() => {
  // When no account selected ("All Accounts"), show all transactions
  let txns = selectedAccountId.value
    ? bankStore.getAccountTransactions(selectedAccountId.value)
    : [...bankStore.transactions].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  if (transactionTypeFilter.value !== 'all') {
    txns = txns.filter(t => t.type === transactionTypeFilter.value);
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    txns = txns.filter(t =>
      t.description.toLowerCase().includes(q) ||
      t.referenceId?.toLowerCase().includes(q) ||
      t.tags?.some(tag => tag.toLowerCase().includes(q))
    );
  }

  return txns;
});

// ==================== Transaction Table Columns ====================
const txnColumns: Column[] = [
  { key: 'date', label: 'Date', width: '110px' },
  { key: 'description', label: 'Description' },
  { key: 'type', label: 'Type', width: '90px', align: 'center' },
  { key: 'direction', label: 'Direction', width: '90px', align: 'center' },
  { key: 'amount', label: 'Amount', width: '120px', align: 'right' },
  { key: 'category', label: 'Category', width: '140px' },
];

// ==================== Account Type Badge ====================
function accountTypeBadge(type: string): { label: string; variant: 'success' | 'info' | 'warning' | 'neutral' } {
  const map: Record<string, { label: string; variant: 'success' | 'info' | 'warning' | 'neutral' }> = {
    savings: { label: 'Savings', variant: 'success' },
    checking: { label: 'Checking', variant: 'info' },
    current: { label: 'Current', variant: 'info' },
    fixed_deposit: { label: 'Fixed Deposit', variant: 'warning' },
    salary: { label: 'Salary', variant: 'neutral' },
  };
  return map[type] || { label: type, variant: 'neutral' };
}

function transactionTypeBadge(type: string): { label: string; variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral' } {
  const map: Record<string, { label: string; variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral' }> = {
    income: { label: 'Income', variant: 'success' },
    expense: { label: 'Expense', variant: 'danger' },
    transfer: { label: 'Transfer', variant: 'warning' },
  };
  return map[type] || { label: type, variant: 'neutral' };
}

// ==================== Add Transaction Form ====================
const txnForm = ref({
  type: 'expense' as 'income' | 'expense' | 'transfer',
  amount: '',
  date: new Date().toISOString().split('T')[0],
  bankAccountId: '',
  categoryId: '',
  description: '',
  referenceId: '',
  tags: '',
  toBankAccountId: '',
  currency: 'BDT' as Currency,
});

function resetTxnForm() {
  txnForm.value = {
    type: 'expense',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    bankAccountId: selectedAccountId.value || bankStore.bankAccounts[0]?.id || '',
    categoryId: '',
    description: '',
    referenceId: '',
    tags: '',
    toBankAccountId: '',
    currency: 'BDT' as Currency,
  };
}

async function handleSaveTransaction() {
  const amount = parseFloat(txnForm.value.amount);

  // ── Validation with user feedback ──
  const missing: string[] = [];
  if (!amount || amount <= 0) missing.push('Amount');
  if (!txnForm.value.bankAccountId) missing.push('Bank Account');
  if (!txnForm.value.categoryId) missing.push('Category');
  if (!txnForm.value.description.trim()) missing.push('Description');
  if (txnForm.value.type === 'transfer' && !txnForm.value.toBankAccountId) missing.push('Transfer To Account');

  if (missing.length > 0) {
    alert(`Please fill in the required field(s): ${missing.join(', ')}`);
    return;
  }

  const tags = txnForm.value.tags
    .split(',')
    .map(t => t.trim())
    .filter(Boolean);

  const baseData = {
    amount,
    date: txnForm.value.date, // Already YYYY-MM-DD from date input
    bankAccountId: txnForm.value.bankAccountId,
    categoryId: txnForm.value.categoryId,
    description: txnForm.value.description,
    referenceId: txnForm.value.referenceId || undefined,
    tags: tags.length ? tags : undefined,
    currency: txnForm.value.currency,
  };

  try {
    if (txnForm.value.type === 'transfer' && txnForm.value.toBankAccountId) {
      // Create debit from source
      await bankStore.addTransaction({
        ...baseData,
        type: 'transfer',
        direction: 'debit',
        toBankAccountId: txnForm.value.toBankAccountId,
      });
      // Create credit to destination
      await bankStore.addTransaction({
        ...baseData,
        bankAccountId: txnForm.value.toBankAccountId,
        toBankAccountId: txnForm.value.bankAccountId,
        type: 'transfer',
        direction: 'credit',
        description: `Transfer from ${bankStore.bankAccounts.find(a => a.id === txnForm.value.bankAccountId)?.bankName || 'Account'}`,
      });
    } else {
      await bankStore.addTransaction({
        ...baseData,
        type: txnForm.value.type,
        direction: txnForm.value.type === 'income' ? 'credit' : 'debit',
      });
    }

    showAddTransactionModal.value = false;
    resetTxnForm();
  } catch (err: any) {
    alert(err?.message || 'Failed to save transaction');
  }
}

// ==================== Add Account Form ====================
const accountForm = ref({
  bankName: '',
  accountNumber: '',
  accountName: '',
  type: 'savings' as 'savings' | 'checking' | 'current' | 'fixed_deposit' | 'salary',
  openingBalance: '',
  currency: 'BDT' as Currency,
  color: '#3B82F6',
});

function resetAccountForm() {
  accountForm.value = {
    bankName: '',
    accountNumber: '',
    accountName: '',
    type: 'savings',
    openingBalance: '',
    currency: 'BDT' as Currency,
    color: '#3B82F6',
  };
}

async function handleSaveAccount() {
  const missing: string[] = [];
  if (!accountForm.value.bankName.trim()) missing.push('Bank Name');
  if (!accountForm.value.accountNumber.trim()) missing.push('Account Number');
  if (!accountForm.value.accountName.trim()) missing.push('Account Name');

  if (missing.length > 0) {
    alert(`Please fill in the required field(s): ${missing.join(', ')}`);
    return;
  }

  try {
    await bankStore.addAccount({
      bankName: accountForm.value.bankName,
      accountNumber: accountForm.value.accountNumber,
      accountName: accountForm.value.accountName,
      type: accountForm.value.type,
      openingBalance: parseFloat(accountForm.value.openingBalance) || 0,
      isActive: true,
      currency: accountForm.value.currency,
      color: accountForm.value.color,
    });

    showAddAccountModal.value = false;
    resetAccountForm();
  } catch (err: any) {
    alert(err?.message || 'Failed to create bank account');
  }
}

// ==================== Tabs ====================
const mainTabs = [
  { key: 'accounts', label: 'Accounts', icon: '🏦' },
  { key: 'transactions', label: 'Transactions', icon: '📋' },
];
const activeMainTab = ref('accounts');

// ==================== Transaction Type Filter Tabs ====================
const txnTypeTabs = [
  { key: 'all', label: 'All' },
  { key: 'income', label: 'Income' },
  { key: 'expense', label: 'Expense' },
  { key: 'transfer', label: 'Transfer' },
];

// ==================== Init ====================
onMounted(async () => {
  try {
    await Promise.all([
      bankStore.fetchAccounts(),
      bankStore.fetchTransactions(),
      expenseStore.fetchCategories(),
    ]);
    // Auto-select first account
    if (bankStore.bankAccounts.length > 0 && !selectedAccountId.value) {
      selectedAccountId.value = bankStore.bankAccounts[0].id;
    }
  } catch (err) {
    console.error('Failed to load bank data:', err);
  }
});
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Bank Accounts" subtitle="Manage your linked bank accounts and transactions">
      <template #actions>
        <div class="flex gap-3">
          <button @click="resetTxnForm(); showAddTransactionModal = true" class="btn-secondary">
            <span>+ Add Transaction</span>
          </button>
          <button @click="resetAccountForm(); showAddAccountModal = true" class="btn-primary">
            <span>+ Link Account</span>
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Balance"
        :value="formatCurrency(bankStore.totalBalance)"
        icon="💰"
        color="primary"
      />
      <StatCard
        title="Credits This Month"
        :value="formatCurrency(monthlyCredits)"
        icon="📥"
        color="accent"
        trend="up"
        :change="8.2"
      />
      <StatCard
        title="Debits This Month"
        :value="formatCurrency(monthlyDebits)"
        icon="📤"
        color="danger"
        trend="down"
        :change="3.1"
      />
      <StatCard
        title="Active Accounts"
        :value="String(activeAccountsCount)"
        icon="🏦"
        color="warning"
      />
    </div>

    <!-- Main Tabs -->
    <Tabs :tabs="mainTabs" v-model:activeTab="activeMainTab" />

    <!-- Accounts Grid -->
    <div v-show="activeMainTab === 'accounts'">
      <div v-if="bankStore.bankAccounts.length === 0">
        <EmptyState
          icon="🏦"
          title="No bank accounts linked"
          description="Add your first bank account to start tracking your finances"
        >
          <template #action>
            <button @click="resetAccountForm(); showAddAccountModal = true" class="btn-primary mt-4">
              <span>+ Link Account</span>
            </button>
          </template>
        </EmptyState>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        <div
          v-for="account in bankStore.bankAccounts.filter(a => a.isActive)"
          :key="account.id"
          @click="selectedAccountId = account.id; activeMainTab = 'transactions'"
          class="card p-5 cursor-pointer hover:shadow-lg transition-all duration-200 group relative overflow-hidden"
          :class="{ 'ring-2 ring-primary-500': selectedAccountId === account.id }"
        >
          <!-- Color indicator strip -->
          <div class="absolute top-0 left-0 w-1.5 h-full rounded-l-xl" :style="{ backgroundColor: account.color || '#3B82F6' }" />

          <div class="pl-3">
            <!-- Header -->
            <div class="flex items-start justify-between mb-3">
              <div>
                <h3 class="font-semibold text-surface-900 dark:text-white text-sm">{{ account.bankName }}</h3>
                <p class="text-xs text-surface-500 dark:text-surface-400 mt-0.5">{{ account.accountName }}</p>
              </div>
              <Badge :variant="accountTypeBadge(account.type).variant" size="sm">
                {{ accountTypeBadge(account.type).label }}
              </Badge>
            </div>

            <!-- Account Number -->
            <p class="text-xs text-surface-400 dark:text-surface-500 font-mono mb-3">{{ account.accountNumber }}</p>

            <!-- Balance -->
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400">Current Balance</p>
              <p class="text-xl font-bold text-surface-900 dark:text-white tabular-nums mt-0.5">
                {{ formatCurrency(getAccountBalance(account.id)) }}
              </p>
              <div v-if="account.currency && account.currency !== 'BDT'" class="flex items-center gap-1 mt-1">
                <span class="text-[10px] px-1.5 py-0.5 bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 rounded font-medium">{{ account.currency }}</span>
              </div>
            </div>

            <!-- Opening Balance -->
            <p class="text-xs text-surface-400 dark:text-surface-500 mt-2">
              Opening: {{ formatCurrency(account.openingBalance) }}
            </p>
          </div>

          <!-- Hover arrow -->
          <div class="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
            <svg class="w-5 h-5 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Transactions View -->
    <div v-show="activeMainTab === 'transactions'">
      <!-- Account Selector -->
      <div class="card p-4 mb-4">
        <div class="flex flex-col sm:flex-row sm:items-center gap-4">
          <div class="flex-1">
            <label class="text-xs text-surface-500 dark:text-surface-400 mb-1 block">Select Account</label>
            <select
              v-model="selectedAccountId"
              class="input-field"
            >
              <option :value="null">All Accounts</option>
              <option v-for="account in bankStore.bankAccounts" :key="account.id" :value="account.id">
                {{ account.bankName }} - {{ account.accountNumber }}
              </option>
            </select>
          </div>
          <div class="flex-1">
            <SearchInput v-model="searchQuery" placeholder="Search transactions..." />
          </div>
        </div>
      </div>

      <!-- Selected Account Balance -->
      <div v-if="selectedAccount" class="card p-4 mb-4" :style="{ borderLeft: `4px solid ${selectedAccount.color || '#3B82F6'}` }">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <p class="text-sm font-medium text-surface-900 dark:text-white">{{ selectedAccount.bankName }} - {{ selectedAccount.accountName }}</p>
            <p class="text-xs text-surface-500 dark:text-surface-400">{{ selectedAccount.accountNumber }}</p>
          </div>
          <div class="text-right">
            <p class="text-sm text-surface-500 dark:text-surface-400">Balance</p>
            <p class="text-lg font-bold text-surface-900 dark:text-white tabular-nums">{{ formatCurrency(accountBalance) }}</p>
          </div>
        </div>
      </div>

      <!-- Transaction Type Filter -->
      <div class="mb-4">
        <Tabs :tabs="txnTypeTabs" v-model:activeTab="transactionTypeFilter" />
      </div>

      <!-- Transactions Table -->
      <DataTable
        :columns="txnColumns"
        :data="filteredTransactions as unknown as Record<string, any>[]"
        :empty-message="selectedAccountId ? 'No transactions found' : 'Select an account to view transactions'"
      >
        <template #cell-date="{ value }">
          <span class="text-xs whitespace-nowrap">{{ formatDate(value, 'short') }}</span>
        </template>
        <template #cell-description="{ value, row }">
          <div class="max-w-xs">
            <p class="font-medium text-surface-900 dark:text-white truncate">{{ value }}</p>
            <div v-if="row.tags && row.tags.length" class="flex gap-1 mt-0.5">
              <span v-for="tag in row.tags.slice(0, 2)" :key="tag" class="text-[10px] px-1.5 py-0.5 bg-surface-100 dark:bg-surface-700 text-surface-500 dark:text-surface-400 rounded">
                {{ tag }}
              </span>
            </div>
          </div>
        </template>
        <template #cell-type="{ value }">
          <Badge :variant="transactionTypeBadge(value).variant" size="sm">
            {{ transactionTypeBadge(value).label }}
          </Badge>
        </template>
        <template #cell-direction="{ value }">
          <Badge :variant="value === 'credit' ? 'success' : 'danger'" size="sm">
            {{ value === 'credit' ? '↓ Credit' : '↑ Debit' }}
          </Badge>
        </template>
        <template #cell-amount="{ value, row }">
          <div class="text-right">
            <span class="font-semibold tabular-nums whitespace-nowrap" :class="row.direction === 'credit' ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500 dark:text-danger-400'">
              {{ currencyStore.formatWithCurrency(Math.abs(value), row.currency || 'BDT') }}
            </span>
            <span v-if="row.currency && row.currency !== 'BDT'" class="text-[10px] text-surface-400 block tabular-nums">
              ≈ {{ formatCurrency(currencyStore.convertToBase(Math.abs(value), row.currency)) }}
            </span>
          </div>
        </template>
        <template #cell-category="{ value }">
          <span class="flex items-center gap-1.5 text-xs text-surface-600 dark:text-surface-400">
            <span>{{ categoryMap[value]?.icon || '📌' }}</span>
            <span>{{ categoryMap[value]?.name || value }}</span>
          </span>
        </template>
      </DataTable>
    </div>

    <!-- ==================== Add Transaction Modal ==================== -->
    <Modal
      :is-open="showAddTransactionModal"
      title="Add Transaction"
      size="lg"
      @close="showAddTransactionModal = false"
    >
      <form @submit.prevent="handleSaveTransaction" class="space-y-4">
        <!-- Type -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="field-label">Type <span class="text-danger-500">*</span></label>
            <select v-model="txnForm.type" class="input-field">
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
          <div>
            <label class="field-label">Amount <span class="text-danger-500">*</span></label>
            <input v-model="txnForm.amount" type="number" min="0" step="0.01" placeholder="0.00" class="input-field" />
          </div>
          <div>
            <label class="field-label">Currency</label>
            <select v-model="txnForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
        </div>

        <!-- Date & Account -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Date <span class="text-danger-500">*</span></label>
            <input v-model="txnForm.date" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Bank Account <span class="text-danger-500">*</span></label>
            <select v-model="txnForm.bankAccountId" class="input-field">
              <option value="">Select Account</option>
              <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">
                {{ acc.bankName }} - {{ acc.accountNumber }}
              </option>
            </select>
          </div>
        </div>

        <!-- To Account (for transfers) -->
        <div v-if="txnForm.type === 'transfer'" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Transfer To Account <span class="text-danger-500">*</span></label>
            <select v-model="txnForm.toBankAccountId" class="input-field">
              <option value="">Select Destination Account</option>
              <option v-for="acc in bankStore.bankAccounts.filter(a => a.id !== txnForm.bankAccountId)" :key="acc.id" :value="acc.id">
                {{ acc.bankName }} - {{ acc.accountNumber }}
              </option>
            </select>
          </div>
        </div>

        <!-- Category & Description -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Category <span class="text-danger-500">*</span></label>
            <select v-model="txnForm.categoryId" class="input-field">
              <option value="">Select Category</option>
              <option v-for="cat in expenseStore.categories" :key="cat.id" :value="cat.id">
                {{ cat.icon }} {{ cat.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label">Reference ID</label>
            <input v-model="txnForm.referenceId" type="text" placeholder="Optional reference" class="input-field" />
          </div>
        </div>

        <!-- Description -->
        <div>
          <label class="field-label">Description <span class="text-danger-500">*</span></label>
          <input v-model="txnForm.description" type="text" placeholder="Transaction description" class="input-field" />
        </div>

        <!-- Tags -->
        <div>
          <label class="field-label">Tags</label>
          <input v-model="txnForm.tags" type="text" placeholder="Comma-separated tags (e.g., rent, housing)" class="input-field" />
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" @click="showAddTransactionModal = false" class="btn-secondary">Cancel</button>
          <button type="submit" class="btn-primary">
            <span>{{ txnForm.type === 'transfer' ? 'Create Transfer' : 'Save Transaction' }}</span>
          </button>
        </div>
      </form>
    </Modal>

    <!-- ==================== Add Bank Account Modal ==================== -->
    <Modal
      :is-open="showAddAccountModal"
      title="Link Bank Account"
      size="md"
      @close="showAddAccountModal = false"
    >
      <form @submit.prevent="handleSaveAccount" class="space-y-4">
        <!-- Bank Name & Account Name -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Bank Name <span class="text-danger-500">*</span></label>
            <input v-model="accountForm.bankName" type="text" placeholder="e.g., Sonali Bank" class="input-field" />
          </div>
          <div>
            <label class="field-label">Account Name <span class="text-danger-500">*</span></label>
            <input v-model="accountForm.accountName" type="text" placeholder="e.g., Primary Savings" class="input-field" />
          </div>
        </div>

        <!-- Account Number & Type -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Account Number <span class="text-danger-500">*</span></label>
            <input v-model="accountForm.accountNumber" type="text" placeholder="e.g., ****1234" class="input-field" />
          </div>
          <div>
            <label class="field-label">Account Type</label>
            <select v-model="accountForm.type" class="input-field">
              <option value="savings">Savings</option>
              <option value="checking">Checking</option>
              <option value="current">Current</option>
              <option value="fixed_deposit">Fixed Deposit</option>
              <option value="salary">Salary</option>
            </select>
          </div>
        </div>

        <!-- Opening Balance & Color -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Opening Balance (৳)</label>
            <input v-model="accountForm.openingBalance" type="number" min="0" step="0.01" placeholder="0.00" class="input-field" />
          </div>
          <div>
            <label class="field-label">Account Currency</label>
            <select v-model="accountForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
        </div>

        <!-- Color -->
        <div>
          <label class="field-label">Color</label>
          <div class="flex items-center gap-3">
            <input v-model="accountForm.color" type="color" class="w-10 h-10 rounded-lg border border-surface-300 dark:border-surface-600 cursor-pointer" />
            <span class="text-sm text-surface-500 dark:text-surface-400 font-mono">{{ accountForm.color }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" @click="showAddAccountModal = false" class="btn-secondary">Cancel</button>
          <button type="submit" class="btn-primary">
            <span>Link Account</span>
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>
