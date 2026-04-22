<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useIncomeStore, useBankStore } from '../../stores';
import { formatCurrency, formatDate, getCurrentMonthStr } from '../../utils/formatters';
import { useCurrencyStore } from '../../stores/currency';
import type { Currency } from '../../types';
import { PageHeader, DataTable, Badge, Modal, SearchInput, EmptyState, Tabs, StatCard } from '../ui';
import type { Column } from '../ui/DataTable.vue';
import type { Income, IncomeSource } from '../../types';

const incomeStore = useIncomeStore();
const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ==================== State ====================
const activeTab = ref('all');
const searchQuery = ref('');
const showIncomeModal = ref(false);
const showSourceModal = ref(false);
const showDetailModal = ref(false);
const selectedIncome = ref<Income | null>(null);

// ==================== Form Data ====================
const emptyIncomeForm = {
  sourceId: '',
  amount: 0,
  date: new Date().toISOString().split('T')[0],
  bankAccountId: '',
  categoryId: 'inc_cat_001',     // Default: Salary (IncomeCategory)
  description: '',
  isRecurring: false,
  recurringCycle: 'monthly' as 'daily' | 'weekly' | 'monthly' | 'yearly' | undefined,
  currency: 'BDT' as Currency,
};

const emptySourceForm = {
  name: '',
  type: 'salary' as 'salary' | 'freelance' | 'business' | 'investment' | 'rental' | 'other',
  isActive: true,
  monthlyAmount: 0,
};

const incomeForm = ref({ ...emptyIncomeForm });
const sourceForm = ref({ ...emptySourceForm });

// ==================== Tabs Config ====================
const tabs = [
  { key: 'all', label: 'All Income', icon: '💰' },
  { key: 'sources', label: 'Income Sources', icon: '📈' },
];

// ==================== Computed ====================
const currentMonth = getCurrentMonthStr();

const thisMonthIncome = computed(() => {
  return incomeStore.incomes
    .filter((i) => i.date.startsWith(currentMonth))
    .reduce((sum, i) => sum + i.amount, 0);
});

const thisYearIncome = computed(() => {
  const year = currentMonth.split('-')[0];
  return incomeStore.incomes
    .filter((i) => i.date.startsWith(year))
    .reduce((sum, i) => sum + i.amount, 0);
});

const averageMonthlyIncome = computed(() => {
  const year = currentMonth.split('-')[0];
  const yearIncomes = incomeStore.incomes.filter((i) => i.date.startsWith(year));
  if (yearIncomes.length === 0) return 0;
  // Count unique months
  const months = new Set(yearIncomes.map((i) => i.date.substring(0, 7)));
  return thisYearIncome.value / months.size;
});

const filteredIncomes = computed(() => {
  let result = [...incomeStore.incomes].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    result = result.filter(
      (i) =>
        i.description.toLowerCase().includes(q) ||
        getSourceName(i.sourceId).toLowerCase().includes(q) ||
        i.amount.toString().includes(q)
    );
  }
  return result;
});

const incomeSourceOptions = computed(() => incomeStore.incomeSources);
const bankAccountOptions = computed(() => bankStore.bankAccounts);

// ==================== Helpers ====================
function getSourceName(sourceId: string): string {
  return incomeStore.incomeSources.find((s) => s.id === sourceId)?.name ?? 'Unknown';
}

function getSourceType(type: string): string {
  const map: Record<string, string> = {
    salary: '💼 Salary',
    freelance: '🖥️ Freelance',
    business: '🏢 Business',
    investment: '📊 Investment',
    rental: '🏠 Rental',
    other: '📦 Other',
  };
  return map[type] ?? type;
}

function getBankName(accountId: string): string {
  const acc = bankStore.bankAccounts.find((a) => a.id === accountId);
  return acc ? `${acc.bankName} (${acc.accountNumber})` : 'Unknown';
}

// ==================== DataTable Columns ====================
const columns: Column[] = [
  { key: 'date', label: 'Date', sortable: true, width: '100px' },
  { key: 'source', label: 'Source', sortable: true },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount', align: 'right', sortable: true, width: '130px' },
  { key: 'bankAccount', label: 'Bank Account' },
  { key: 'type', label: 'Type', width: '100px' },
  { key: 'actions', label: '', align: 'right', width: '80px' },
];

// ==================== CRUD Handlers ====================
function openAddIncomeModal() {
  incomeForm.value = { ...emptyIncomeForm };
  showIncomeModal.value = true;
}

function saveIncome() {
  if (!incomeForm.value.sourceId || !incomeForm.value.amount || !incomeForm.value.bankAccountId) return;
  incomeStore.addIncome({
    sourceId: incomeForm.value.sourceId,
    amount: Number(incomeForm.value.amount),
    date: new Date(incomeForm.value.date).toISOString(),
    bankAccountId: incomeForm.value.bankAccountId,
    categoryId: incomeForm.value.categoryId,
    description: incomeForm.value.description,
    isRecurring: incomeForm.value.isRecurring,
    recurringCycle: incomeForm.value.isRecurring ? incomeForm.value.recurringCycle : undefined,
    currency: incomeForm.value.currency,
  });
  showIncomeModal.value = false;
}

function handleDeleteIncome(income: Income) {
  if (confirm(`Delete this income entry of ${formatCurrency(income.amount)}?`)) {
    incomeStore.deleteIncome(income.id);
  }
}

function handleRowClick(row: Record<string, any>) {
  selectedIncome.value = row as Income;
  showDetailModal.value = true;
}

function openAddSourceModal() {
  sourceForm.value = { ...emptySourceForm };
  showSourceModal.value = true;
}

function saveSource() {
  if (!sourceForm.value.name) return;
  incomeStore.addIncomeSource({
    name: sourceForm.value.name,
    type: sourceForm.value.type,
    isActive: sourceForm.value.isActive,
    monthlyAmount: sourceForm.value.monthlyAmount || undefined,
  });
  showSourceModal.value = false;
}

function handleDeleteSource(source: IncomeSource) {
  if (confirm(`Delete income source "${source.name}"?`)) {
    incomeStore.deleteIncomeSource(source.id);
  }
}

function toggleSourceStatus(source: IncomeSource) {
  incomeStore.updateIncomeSource(source.id, { isActive: !source.isActive });
}

// ==================== Init ====================
onMounted(() => {
  incomeStore.incomes;
  incomeStore.incomeSources;
});
</script>

<template>
  <div class="animate-fade-in">
    <PageHeader title="Income" subtitle="Track and manage your income sources">
      <template #actions>
        <button
          v-if="activeTab === 'all'"
          class="btn-primary"
          @click="openAddIncomeModal"
        >
          <span>+ Add Income</span>
        </button>
        <button
          v-else
          class="btn-primary"
          @click="openAddSourceModal"
        >
          <span>+ Add Source</span>
        </button>
      </template>
    </PageHeader>

    <Tabs :tabs="tabs" :active-tab="activeTab" @update:active-tab="activeTab = $event" />

    <!-- ==================== All Income Tab ==================== -->
    <div v-if="activeTab === 'all'" class="mt-6 space-y-6">
      <!-- Stat Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="This Month"
          :value="formatCurrency(thisMonthIncome)"
          icon="📅"
          color="primary"
        />
        <StatCard
          title="Expected"
          :value="formatCurrency(incomeStore.expectedMonthlyIncome)"
          icon="📈"
          color="accent"
        />
        <StatCard
          title="Pending"
          :value="formatCurrency(incomeStore.pendingIncomeThisMonth)"
          icon="⏳"
          :color="incomeStore.pendingIncomeThisMonth > 0 ? 'warning' : 'accent'"
        />
        <StatCard
          title="Avg. Monthly"
          :value="formatCurrency(averageMonthlyIncome)"
          icon="📊"
          color="primary"
        />
      </div>

      <!-- Upcoming Income Sources -->
      <div v-if="incomeStore.pendingSources.length > 0" class="card p-5">
        <h3 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Pending Income Sources</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <div
            v-for="source in incomeStore.pendingSources"
            :key="source.id"
            class="flex items-center justify-between p-3 bg-warning-50 dark:bg-warning-500/10 border border-warning-400/30 rounded-lg"
          >
            <div class="flex items-center gap-2">
              <span class="text-sm">{{ source.type === 'salary' ? '💼' : source.type === 'rental' ? '🏠' : source.type === 'investment' ? '📊' : '📦' }}</span>
              <div>
                <p class="text-sm font-medium text-surface-700 dark:text-surface-300">{{ source.name }}</p>
                <p class="text-xs text-surface-400 capitalize">{{ source.type }}</p>
              </div>
            </div>
            <span class="text-sm font-semibold text-amber-600 dark:text-amber-400 tabular-nums">{{ formatCurrency(source.monthlyAmount || 0) }}</span>
          </div>
        </div>
      </div>

      <!-- Search -->
      <div class="flex items-center gap-3">
        <SearchInput v-model="searchQuery" placeholder="Search income entries..." class="max-w-sm" />
      </div>

      <!-- Data Table -->
      <DataTable
        v-if="filteredIncomes.length > 0"
        :columns="columns"
        :data="filteredIncomes"
        @row-click="handleRowClick"
      >
        <template #cell-date="{ value }">
          <span class="text-surface-600 dark:text-surface-400 whitespace-nowrap">{{ formatDate(value, 'short') }}</span>
        </template>
        <template #cell-source="{ row }">
          <span class="font-medium text-surface-900 dark:text-white">{{ getSourceName(row.sourceId) }}</span>
        </template>
        <template #cell-description="{ value }">
          <span class="text-surface-600 dark:text-surface-400">{{ value }}</span>
        </template>
        <template #cell-amount="{ value, row }">
          <span class="font-semibold text-accent-600 dark:text-accent-400">{{ currencyStore.formatWithCurrency(value, row.currency || 'BDT') }}</span>
          <span v-if="row.currency && row.currency !== 'BDT'" class="text-[10px] text-surface-400 block">
            ≈ {{ formatCurrency(currencyStore.convertToBase(value, row.currency)) }}
          </span>
        </template>
        <template #cell-bankAccount="{ row }">
          <span class="text-surface-600 dark:text-surface-400 text-xs">{{ getBankName(row.bankAccountId) }}</span>
        </template>
        <template #cell-type="{ row }">
          <Badge v-if="row.isRecurring" variant="info" size="sm">Recurring</Badge>
          <Badge v-else variant="neutral" size="sm">One-time</Badge>
        </template>
        <template #cell-actions="{ row }">
          <button
            class="text-surface-400 hover:text-danger-500 dark:hover:text-danger-400 transition-colors p-1"
            title="Delete"
            @click.stop="handleDeleteIncome(row)"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </template>
      </DataTable>

      <EmptyState
        v-else
        icon="💰"
        title="No income entries found"
        :description="searchQuery ? 'Try a different search term' : 'Add your first income entry to get started'"
      >
        <template #action>
          <button v-if="!searchQuery" class="btn-primary btn-sm" @click="openAddIncomeModal">+ Add Income</button>
        </template>
      </EmptyState>
    </div>

    <!-- ==================== Income Sources Tab ==================== -->
    <div v-else class="mt-6">
      <div v-if="incomeSourceOptions.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="source in incomeSourceOptions"
          :key="source.id"
          class="card p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between mb-3">
            <div>
              <h3 class="text-base font-semibold text-surface-900 dark:text-white">{{ source.name }}</h3>
              <p class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">{{ getSourceType(source.type) }}</p>
            </div>
            <Badge :variant="source.isActive ? 'success' : 'neutral'" size="sm">
              {{ source.isActive ? 'Active' : 'Inactive' }}
            </Badge>
          </div>
          <div class="mb-4">
            <p class="text-sm text-surface-500 dark:text-surface-400">
              {{ source.monthlyAmount ? 'Expected Monthly' : 'Variable Amount' }}
            </p>
            <p v-if="source.monthlyAmount" class="text-xl font-bold text-accent-600 dark:text-accent-400">{{ formatCurrency(source.monthlyAmount) }}</p>
            <p v-else class="text-sm text-surface-400 italic">Amount varies per payment</p>
            <p class="text-xs text-surface-400 mt-1">
              {{ source.type === 'salary' ? 'Fixed monthly income from employer' : source.type === 'freelance' ? 'Project-based income, varies by contract' : source.type === 'rental' ? 'Fixed monthly rental income' : source.type === 'investment' ? 'Dividend & capital gains income' : 'Miscellaneous income' }}
            </p>
          </div>
          <div class="flex items-center gap-2 pt-3 border-t border-surface-200 dark:border-surface-700">
            <button
              class="text-xs px-3 py-1.5 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors"
              @click="toggleSourceStatus(source)"
            >
              {{ source.isActive ? 'Deactivate' : 'Activate' }}
            </button>
            <button
              class="text-xs px-3 py-1.5 rounded-lg bg-danger-50 dark:bg-danger-500/10 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/20 transition-colors"
              @click="handleDeleteSource(source)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="📈" title="No income sources" description="Add your first income source">
        <template #action>
          <button class="btn-primary btn-sm" @click="openAddSourceModal">+ Add Source</button>
        </template>
      </EmptyState>
    </div>

    <!-- ==================== Add Income Modal ==================== -->
    <Modal :is-open="showIncomeModal" title="Add Income" size="lg" @close="showIncomeModal = false">
      <form @submit.prevent="saveIncome" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Source *</label>
            <select v-model="incomeForm.sourceId" required class="input-field">
              <option value="" disabled>Select source</option>
              <option v-for="s in incomeSourceOptions" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Amount *</label>
            <input v-model.number="incomeForm.amount" type="number" min="0" required class="input-field" placeholder="0" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Date *</label>
            <input v-model="incomeForm.date" type="date" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Bank Account *</label>
            <select v-model="incomeForm.bankAccountId" required class="input-field">
              <option value="" disabled>Select account</option>
              <option v-for="acc in bankAccountOptions" :key="acc.id" :value="acc.id">{{ acc.bankName }} ({{ acc.accountNumber }})</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Currency</label>
          <select v-model="incomeForm.currency" class="input-field">
            <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Description</label>
          <input v-model="incomeForm.description" type="text" class="input-field" placeholder="e.g., Monthly Salary - ABC Corporation" />
        </div>
        <div class="flex items-center gap-3">
          <label class="relative inline-flex items-center cursor-pointer">
            <input v-model="incomeForm.isRecurring" type="checkbox" class="sr-only peer" />
            <div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-surface-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:after:border-surface-600 peer-checked:bg-primary-500"></div>
          </label>
          <span class="text-sm text-surface-700 dark:text-surface-300">Is Recurring</span>
        </div>
        <div v-if="incomeForm.isRecurring">
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Recurring Cycle</label>
          <select v-model="incomeForm.recurringCycle" class="input-field">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showIncomeModal = false">Cancel</button>
          <button type="submit" class="btn-primary">Save Income</button>
        </div>
      </form>
    </Modal>

    <!-- ==================== Add Income Source Modal ==================== -->
    <Modal :is-open="showSourceModal" title="Add Income Source" size="md" @close="showSourceModal = false">
      <form @submit.prevent="saveSource" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Source Name *</label>
          <input v-model="sourceForm.name" type="text" required class="input-field" placeholder="e.g., ABC Corporation" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Type</label>
          <select v-model="sourceForm.type" class="input-field">
            <option value="salary">Salary</option>
            <option value="freelance">Freelance</option>
            <option value="business">Business</option>
            <option value="investment">Investment</option>
            <option value="rental">Rental</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Monthly Amount (BDT)</label>
          <input v-model.number="sourceForm.monthlyAmount" type="number" min="0" class="input-field" placeholder="0" />
        </div>
        <div class="flex items-center gap-3">
          <label class="relative inline-flex items-center cursor-pointer">
            <input v-model="sourceForm.isActive" type="checkbox" class="sr-only peer" />
            <div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-surface-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:after:border-surface-600 peer-checked:bg-primary-500"></div>
          </label>
          <span class="text-sm text-surface-700 dark:text-surface-300">Active</span>
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showSourceModal = false">Cancel</button>
          <button type="submit" class="btn-primary">Save Source</button>
        </div>
      </form>
    </Modal>

    <!-- ==================== Income Detail Modal ==================== -->
    <Modal :is-open="showDetailModal" :title="'Income Details'" size="md" @close="showDetailModal = false">
      <div v-if="selectedIncome" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Source</p>
            <p class="text-sm font-medium text-surface-900 dark:text-white mt-1">{{ getSourceName(selectedIncome.sourceId) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Amount</p>
            <p class="text-sm font-bold text-accent-600 dark:text-accent-400 mt-1">{{ currencyStore.formatWithCurrency(selectedIncome.amount, selectedIncome.currency || 'BDT') }}</p>
            <p v-if="selectedIncome.currency && selectedIncome.currency !== 'BDT'" class="text-xs text-surface-400 mt-0.5">
              ≈ {{ formatCurrency(currencyStore.convertToBase(selectedIncome.amount, selectedIncome.currency)) }} BDT
            </p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Date</p>
            <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">{{ formatDate(selectedIncome.date, 'long') }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Bank Account</p>
            <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">{{ getBankName(selectedIncome.bankAccountId) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Type</p>
            <p class="mt-1">
              <Badge v-if="selectedIncome.isRecurring" variant="info" size="sm">Recurring ({{ selectedIncome.recurringCycle }})</Badge>
              <Badge v-else variant="neutral" size="sm">One-time</Badge>
            </p>
          </div>
        </div>
        <div>
          <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Description</p>
          <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">{{ selectedIncome.description || 'No description' }}</p>
        </div>
        <div class="flex justify-end pt-4 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showDetailModal = false">Close</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
