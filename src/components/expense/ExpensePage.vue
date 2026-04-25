<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useExpenseStore, useBankStore, useCardStore } from '../../stores';
import { useCurrencyStore } from '../../stores/currency';
import type { Currency } from '../../types';
import { formatCurrency, formatDate, getCurrentMonthStr } from '../../utils/formatters';
import { PageHeader, DataTable, Badge, Modal, SearchInput, EmptyState, Tabs, StatCard } from '../ui';
import type { Column } from '../ui/DataTable.vue';
import type { Expense, ExpenseCategory } from '../../types';

const expenseStore = useExpenseStore();
const bankStore = useBankStore();
const cardStore = useCardStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ==================== State ====================
const activeTab = ref('all');
const searchQuery = ref('');
const showExpenseModal = ref(false);
const showCategoryModal = ref(false);
const showDetailModal = ref(false);
const selectedExpense = ref<Expense | null>(null);

// ==================== Form Data ====================
const emptyExpenseForm = {
  amount: 0,
  date: new Date().toISOString().split('T')[0],
  categoryId: '',
  bankAccountId: '',
  cardId: '',
  description: '',
  isRecurring: false,
  recurringCycle: 'monthly' as 'daily' | 'weekly' | 'monthly' | 'yearly' | undefined,
  tags: [] as string[],
  currency: 'BDT' as Currency,
};

const emptyCategoryForm = {
  name: '',
  icon: '📦',
  color: 'slate',
  type: 'needs' as 'needs' | 'wants' | 'savings' | 'investments',
  budgetLimit: 0,
  currency: 'BDT' as Currency,
};

const editingCategoryId = ref<string | null>(null);

const expenseForm = ref({ ...emptyExpenseForm });
const categoryForm = ref({ ...emptyCategoryForm });

const categoryColors = [
  'emerald', 'blue', 'amber', 'violet', 'red', 'indigo',
  'pink', 'purple', 'orange', 'cyan', 'green', 'slate', 'teal', 'rose',
];

const categoryIcons = [
  '🍽️', '🚗', '💡', '🏠', '🏥', '📚', '🛍️', '🎬',
  '🍕', '📱', '📈', '🛡️', '✈️', '💼', '🎮', '🐕',
];

// ==================== Tabs Config ====================
const tabs = [
  { key: 'all', label: 'All Expenses', icon: '💸' },
  { key: 'categories', label: 'Categories', icon: '📂' },
];

// ==================== Computed ====================
const currentMonth = getCurrentMonthStr();

const thisMonthExpense = computed(() => {
  return expenseStore.expenses
    .filter((e) => e.date.startsWith(currentMonth))
    .reduce((sum, e) => sum + e.amount, 0);
});

const thisYearExpense = computed(() => {
  const year = currentMonth.split('-')[0];
  return expenseStore.expenses
    .filter((e) => e.date.startsWith(year))
    .reduce((sum, e) => sum + e.amount, 0);
});

const averageMonthlyExpense = computed(() => {
  const year = currentMonth.split('-')[0];
  const yearExpenses = expenseStore.expenses.filter((e) => e.date.startsWith(year));
  if (yearExpenses.length === 0) return 0;
  const months = new Set(yearExpenses.map((e) => e.date.substring(0, 7)));
  return thisYearExpense.value / months.size;
});

const filteredExpenses = computed(() => {
  let result = [...expenseStore.expenses].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    result = result.filter(
      (e) =>
        e.description.toLowerCase().includes(q) ||
        getCategoryName(e.categoryId).toLowerCase().includes(q) ||
        e.amount.toString().includes(q) ||
        (e.tags && e.tags.some((t) => t.toLowerCase().includes(q)))
    );
  }
  return result;
});

const categoryOptions = computed(() => expenseStore.categories);
const bankAccountOptions = computed(() => bankStore.bankAccounts);
const cardOptions = computed(() => cardStore.cards);

// Category breakdown with spending this month
const categoriesWithSpending = computed(() => {
  return expenseStore.categories.map((cat) => {
    const spent = expenseStore.expenses
      .filter((e) => e.categoryId === cat.id && e.date.startsWith(currentMonth))
      .reduce((sum, e) => sum + e.amount, 0);
    const budget = cat.budgetLimit ?? 0;
    const percentage = budget > 0 ? (spent / budget) * 100 : 0;
    return { ...cat, spent, budget, percentage };
  }).sort((a, b) => b.spent - a.spent);
});

// ==================== Helpers ====================
function getCategoryName(categoryId: string): string {
  return expenseStore.categories.find((c) => c.id === categoryId)?.name ?? 'Unknown';
}

function getCategoryIcon(categoryId: string): string {
  return expenseStore.categories.find((c) => c.id === categoryId)?.icon ?? '📦';
}

function getCategoryColor(categoryId: string): string {
  return expenseStore.categories.find((c) => c.id === categoryId)?.color ?? 'slate';
}

function getBankName(accountId?: string): string {
  if (!accountId) return 'Cash / Other';
  const acc = bankStore.bankAccounts.find((a) => a.id === accountId);
  return acc ? `${acc.bankName} (${acc.accountNumber})` : 'Unknown';
}

function getCardName(cardId: string): string {
  const card = cardStore.cards.find((c) => c.id === cardId);
  return card ? `${card.name} (${card.brand})` : '';
}

function getTypeBadgeVariant(type: string): 'success' | 'danger' | 'warning' | 'info' | 'neutral' {
  const map: Record<string, 'success' | 'danger' | 'warning' | 'info' | 'neutral'> = {
    needs: 'info',
    wants: 'warning',
    savings: 'success',
    investments: 'neutral',
  };
  return map[type] ?? 'neutral';
}

function getProgressColor(percentage: number): string {
  if (percentage >= 100) return 'bg-danger-500';
  if (percentage >= 80) return 'bg-warning-500';
  return 'bg-accent-500';
}

function getProgressTrackColor(color: string): string {
  const map: Record<string, string> = {
    emerald: 'bg-emerald-500',
    blue: 'bg-blue-500',
    amber: 'bg-amber-500',
    violet: 'bg-violet-500',
    red: 'bg-red-500',
    indigo: 'bg-indigo-500',
    pink: 'bg-pink-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    cyan: 'bg-cyan-500',
    green: 'bg-green-500',
    slate: 'bg-slate-500',
    teal: 'bg-teal-500',
    rose: 'bg-rose-500',
  };
  return map[color] ?? 'bg-slate-500';
}

function getCategoryBreakdownTotal(): number {
  return categoriesWithSpending.value.reduce((sum, c) => sum + c.spent, 0);
}

// ==================== DataTable Columns ====================
const columns: Column[] = [
  { key: 'date', label: 'Date', sortable: true, width: '100px' },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount', align: 'right', sortable: true, width: '130px' },
  { key: 'bankAccount', label: 'Bank Account' },
  { key: 'type', label: 'Type', width: '100px' },
  { key: 'actions', label: '', align: 'right', width: '80px' },
];

// ==================== CRUD Handlers ====================
function openAddExpenseModal() {
  expenseForm.value = { ...emptyExpenseForm };
  showExpenseModal.value = true;
}

async function saveExpense() {
  if (!expenseForm.value.categoryId || !expenseForm.value.amount) return;
  try {
    await expenseStore.addExpense({
      amount: Number(expenseForm.value.amount),
      date: expenseForm.value.date,
      categoryId: expenseForm.value.categoryId,
      bankAccountId: expenseForm.value.bankAccountId || undefined,
      cardId: expenseForm.value.cardId || undefined,
      description: expenseForm.value.description,
      isRecurring: expenseForm.value.isRecurring,
      recurringCycle: expenseForm.value.isRecurring ? expenseForm.value.recurringCycle : undefined,
      tags: expenseForm.value.tags,
      currency: expenseForm.value.currency,
    });
    showExpenseModal.value = false;
  } catch (err: any) {
    alert(err?.message || 'Failed to save expense');
  }
}

async function handleDeleteExpense(expense: Expense) {
  if (confirm(`Delete this expense of ${formatCurrency(expense.amount)}?`)) {
    try {
      await expenseStore.deleteExpense(expense.id);
    } catch (err: any) {
      alert(err?.message || 'Failed to delete expense');
    }
  }
}

function handleRowClick(row: Record<string, any>) {
  selectedExpense.value = row as Expense;
  showDetailModal.value = true;
}

function openAddCategoryModal() {
  categoryForm.value = { ...emptyCategoryForm };
  editingCategoryId.value = null;
  showCategoryModal.value = true;
}

function openEditCategoryModal(category: ExpenseCategory) {
  categoryForm.value = {
    name: category.name,
    icon: category.icon,
    color: category.color,
    type: category.type,
    budgetLimit: category.budgetLimit ?? 0,
    currency: (category.currency as Currency) || 'BDT',
  };
  editingCategoryId.value = category.id;
  showCategoryModal.value = true;
}

async function saveCategory() {
  if (!categoryForm.value.name) return;
  const data = {
    name: categoryForm.value.name,
    icon: categoryForm.value.icon,
    color: categoryForm.value.color,
    type: categoryForm.value.type,
    budgetLimit: categoryForm.value.budgetLimit || undefined,
    currency: categoryForm.value.currency,
  };
  if (editingCategoryId.value) {
    await expenseStore.updateCategory(editingCategoryId.value, data);
  } else {
    await expenseStore.addCategory(data);
  }
  showCategoryModal.value = false;
}

function getCategoryModalTitle(): string {
  return editingCategoryId.value ? 'Edit Category' : 'Add Category';
}

async function handleDeleteCategory(category: ExpenseCategory) {
  if (!confirm(`Delete category "${category.name}"? This cannot be undone.`)) return;
  try {
    await expenseStore.deleteCategory(category.id);
  } catch (err: any) {
    alert(err?.message || 'Cannot delete this category. It may have linked expense records.');
  }
}

// ==================== Init ====================
onMounted(async () => {
  try {
    await Promise.all([
      expenseStore.fetchExpenses(),
      expenseStore.fetchCategories(),
    ]);
  } catch (err) {
    console.error('Failed to load expense data:', err);
  }
});
</script>

<template>
  <div class="animate-fade-in">
    <PageHeader title="Expenditure" subtitle="Track and categorize your expenses">
      <template #actions>
        <button
          v-if="activeTab === 'all'"
          class="btn-primary"
          @click="openAddExpenseModal"
        >
          <span>+ Add Expense</span>
        </button>
        <button
          v-else
          class="btn-primary"
          @click="openAddCategoryModal"
        >
          <span>+ Add Category</span>
        </button>
      </template>
    </PageHeader>

    <Tabs :tabs="tabs" :active-tab="activeTab" @update:active-tab="activeTab = $event" />

    <!-- ==================== All Expenses Tab ==================== -->
    <div v-if="activeTab === 'all'" class="mt-6 space-y-6">
      <!-- Stat Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="This Month"
          :value="formatCurrency(thisMonthExpense)"
          icon="📅"
          color="danger"
        />
        <StatCard
          title="This Year"
          :value="formatCurrency(thisYearExpense)"
          icon="📊"
          color="warning"
        />
        <StatCard
          title="Avg. Monthly"
          :value="formatCurrency(averageMonthlyExpense)"
          icon="📉"
          color="primary"
        />
      </div>

      <!-- Search -->
      <div class="flex items-center gap-3">
        <SearchInput v-model="searchQuery" placeholder="Search expenses..." class="max-w-sm" />
      </div>

      <!-- Data Table -->
      <DataTable
        v-if="filteredExpenses.length > 0"
        :columns="columns"
        :data="filteredExpenses"
        @row-click="handleRowClick"
      >
        <template #cell-date="{ value }">
          <span class="text-surface-600 dark:text-surface-400 whitespace-nowrap">{{ formatDate(value, 'short') }}</span>
        </template>
        <template #cell-category="{ row }">
          <div class="flex items-center gap-2">
            <span>{{ getCategoryIcon(row.categoryId) }}</span>
            <span class="font-medium text-surface-900 dark:text-white">{{ getCategoryName(row.categoryId) }}</span>
          </div>
        </template>
        <template #cell-description="{ value }">
          <span class="text-surface-600 dark:text-surface-400">{{ value }}</span>
        </template>
        <template #cell-amount="{ value, row }">
          <div class="text-right">
            <span class="font-semibold text-danger-600 dark:text-danger-400">-{{ currencyStore.formatWithCurrency(value, row.currency || 'BDT') }}</span>
            <span v-if="row.currency && row.currency !== 'BDT'" class="text-[10px] text-surface-400 block tabular-nums">
              ≈ {{ formatCurrency(currencyStore.convertToBase(value, row.currency)) }}
            </span>
          </div>
        </template>
        <template #cell-bankAccount="{ row }">
          <div>
            <span class="text-surface-600 dark:text-surface-400 text-xs">{{ row.bankAccountId ? getBankName(row.bankAccountId) : 'Cash' }}</span>
            <span v-if="row.cardId" class="text-surface-400 dark:text-surface-500 text-xs block">{{ getCardName(row.cardId) }}</span>
          </div>
        </template>
        <template #cell-type="{ row }">
          <Badge v-if="row.isRecurring" variant="warning" size="sm">Recurring</Badge>
          <Badge v-else variant="neutral" size="sm">One-time</Badge>
        </template>
        <template #cell-actions="{ row }">
          <button
            class="text-surface-400 hover:text-danger-500 dark:hover:text-danger-400 transition-colors p-1"
            title="Delete"
            @click.stop="handleDeleteExpense(row)"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </template>
      </DataTable>

      <EmptyState
        v-else
        icon="💸"
        title="No expenses found"
        :description="searchQuery ? 'Try a different search term' : 'Add your first expense entry to get started'"
      >
        <template #action>
          <button v-if="!searchQuery" class="btn-primary btn-sm" @click="openAddExpenseModal">+ Add Expense</button>
        </template>
      </EmptyState>
    </div>

    <!-- ==================== Categories Tab ==================== -->
    <div v-else class="mt-6">
      <!-- Budget Overview -->
      <div v-if="categoriesWithSpending.length > 0" class="mb-6 p-4 card">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-surface-700 dark:text-surface-300 uppercase tracking-wider">Total Budget Usage</h3>
          <span class="text-sm font-medium text-surface-600 dark:text-surface-400">
            {{ formatCurrency(getCategoryBreakdownTotal()) }} spent this month
          </span>
        </div>
        <div class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-2.5">
          <div
            class="h-2.5 rounded-full transition-all duration-500"
            :class="getCategoryBreakdownTotal() > expenseStore.categories.reduce((s, c) => s + (c.budgetLimit || 0), 0) ? 'bg-danger-500' : 'bg-primary-500'"
            :style="{ width: Math.min(100, (getCategoryBreakdownTotal() / Math.max(1, expenseStore.categories.reduce((s, c) => s + (c.budgetLimit || 0), 0))) * 100) + '%' }"
          ></div>
        </div>
      </div>

      <!-- Category Cards Grid -->
      <div v-if="categoriesWithSpending.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="cat in categoriesWithSpending"
          :key="cat.id"
          class="card p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-surface-100 dark:bg-surface-700 flex items-center justify-center text-lg">
                {{ cat.icon }}
              </div>
              <div>
                <h3 class="text-base font-semibold text-surface-900 dark:text-white">{{ cat.name }}</h3>
                <Badge :variant="getTypeBadgeVariant(cat.type)" size="sm">{{ cat.type }}</Badge>
              </div>
            </div>
          </div>

          <!-- Budget Progress -->
          <div class="mt-3">
            <div class="flex items-center justify-between text-sm mb-1.5">
              <span class="text-surface-500 dark:text-surface-400">
                {{ formatCurrency(cat.spent) }} / {{ cat.budget ? formatCurrency(cat.budget) : 'No limit' }}
              </span>
              <span
                class="font-medium"
                :class="cat.percentage >= 100 ? 'text-danger-600 dark:text-danger-400' : cat.percentage >= 80 ? 'text-warning-600 dark:text-warning-400' : 'text-surface-600 dark:text-surface-400'"
              >
                {{ cat.percentage.toFixed(0) }}%
              </span>
            </div>
            <div v-if="cat.budget" class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-500"
                :class="[getProgressColor(cat.percentage)]"
                :style="{ width: Math.min(100, cat.percentage) + '%' }"
              ></div>
            </div>
            <div v-else class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-500"
                :class="getProgressTrackColor(cat.color)"
                :style="{ width: '100%', opacity: 0.3 }"
              ></div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 pt-3 mt-3 border-t border-surface-200 dark:border-surface-700">
            <span v-if="cat.currency" class="text-xs text-surface-400 mr-auto">{{ cat.currency }}</span>
            <button
              class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-500/20 transition-colors"
              @click="openEditCategoryModal(cat)"
            >
              Edit
            </button>
            <button
              class="text-xs px-3 py-1.5 rounded-lg bg-danger-50 dark:bg-danger-500/10 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/20 transition-colors"
              @click="handleDeleteCategory(cat)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      <EmptyState v-else icon="📂" title="No categories" description="Add expense categories to organize your spending">
        <template #action>
          <button class="btn-primary btn-sm" @click="openAddCategoryModal">+ Add Category</button>
        </template>
      </EmptyState>
    </div>

    <!-- ==================== Add Expense Modal ==================== -->
    <Modal :is-open="showExpenseModal" title="Add Expense" size="lg" @close="showExpenseModal = false">
      <form @submit.prevent="saveExpense" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Amount *</label>
            <input v-model.number="expenseForm.amount" type="number" min="0" required class="input-field" placeholder="0" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Currency</label>
            <select v-model="expenseForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Date *</label>
            <input v-model="expenseForm.date" type="date" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Category *</label>
            <select v-model="expenseForm.categoryId" required class="input-field">
              <option value="" disabled>Select category</option>
              <option v-for="cat in categoryOptions" :key="cat.id" :value="cat.id">{{ cat.icon }} {{ cat.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Bank Account (optional)</label>
            <select v-model="expenseForm.bankAccountId" class="input-field">
              <option value="">Cash / No Account</option>
              <option v-for="acc in bankAccountOptions" :key="acc.id" :value="acc.id">{{ acc.bankName }} ({{ acc.accountNumber }})</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Card (optional)</label>
            <select v-model="expenseForm.cardId" class="input-field">
              <option value="">None</option>
              <option v-for="card in cardOptions" :key="card.id" :value="card.id">{{ card.name }} ({{ card.brand }})</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Description</label>
          <input v-model="expenseForm.description" type="text" class="input-field" placeholder="e.g., Groceries from Agora" />
        </div>
        <div class="flex items-center gap-3">
          <label class="relative inline-flex items-center cursor-pointer">
            <input v-model="expenseForm.isRecurring" type="checkbox" class="sr-only peer" />
            <div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-surface-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:after:border-surface-600 peer-checked:bg-primary-500"></div>
          </label>
          <span class="text-sm text-surface-700 dark:text-surface-300">Is Recurring</span>
        </div>
        <div v-if="expenseForm.isRecurring">
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Recurring Cycle</label>
          <select v-model="expenseForm.recurringCycle" class="input-field">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showExpenseModal = false">Cancel</button>
          <button type="submit" class="btn-primary">Save Expense</button>
        </div>
      </form>
    </Modal>

    <!-- ==================== Add/Edit Category Modal ==================== -->
    <Modal :is-open="showCategoryModal" :title="getCategoryModalTitle()" size="md" @close="showCategoryModal = false">
      <form @submit.prevent="saveCategory" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Category Name *</label>
          <input v-model="categoryForm.name" type="text" required class="input-field" placeholder="e.g., Food & Groceries" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Icon</label>
          <div class="grid grid-cols-8 gap-2">
            <button
              v-for="icon in categoryIcons"
              :key="icon"
              type="button"
              class="w-10 h-10 rounded-lg text-xl flex items-center justify-center transition-colors"
              :class="categoryForm.icon === icon ? 'bg-primary-100 dark:bg-primary-500/20 ring-2 ring-primary-500' : 'bg-surface-100 dark:bg-surface-700 hover:bg-surface-200 dark:hover:bg-surface-600'"
              @click="categoryForm.icon = icon"
            >
              {{ icon }}
            </button>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Color</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="color in categoryColors"
              :key="color"
              type="button"
              class="w-8 h-8 rounded-full border-2 transition-all"
              :class="[
                `bg-${color}-500`,
                categoryForm.color === color ? 'ring-2 ring-offset-2 ring-offset-white dark:ring-offset-surface-800 ring-surface-900 dark:ring-white scale-110' : 'border-transparent hover:scale-105'
              ]"
              @click="categoryForm.color = color"
            ></button>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Type</label>
          <select v-model="categoryForm.type" class="input-field">
            <option value="needs">Needs</option>
            <option value="wants">Wants</option>
            <option value="savings">Savings</option>
            <option value="investments">Investments</option>
          </select>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Budget Limit</label>
            <input v-model.number="categoryForm.budgetLimit" type="number" min="0" class="input-field" placeholder="0" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Currency</label>
            <select v-model="categoryForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }}</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showCategoryModal = false">Cancel</button>
          <button type="submit" class="btn-primary">Save Category</button>
        </div>
      </form>
    </Modal>

    <!-- ==================== Expense Detail Modal ==================== -->
    <Modal :is-open="showDetailModal" title="Expense Details" size="md" @close="showDetailModal = false">
      <div v-if="selectedExpense" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Category</p>
            <p class="text-sm font-medium text-surface-900 dark:text-white mt-1 flex items-center gap-2">
              <span>{{ getCategoryIcon(selectedExpense.categoryId) }}</span>
              {{ getCategoryName(selectedExpense.categoryId) }}
            </p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Amount</p>
            <p class="text-sm font-bold text-danger-600 dark:text-danger-400 mt-1">-{{ currencyStore.formatWithCurrency(selectedExpense.amount, selectedExpense.currency || 'BDT') }}</p>
            <p v-if="selectedExpense.currency && selectedExpense.currency !== 'BDT'" class="text-xs text-surface-400 mt-0.5">
              ≈ {{ formatCurrency(currencyStore.convertToBase(selectedExpense.amount, selectedExpense.currency)) }} BDT
            </p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Date</p>
            <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">{{ formatDate(selectedExpense.date, 'long') }}</p>
          </div>
          <div v-if="selectedExpense.bankAccountId">
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Bank Account</p>
            <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">{{ getBankName(selectedExpense.bankAccountId) }}</p>
          </div>
          <div v-else>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Payment Method</p>
            <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">Cash</p>
          </div>
          <div v-if="selectedExpense.cardId">
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Card</p>
            <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">{{ getCardName(selectedExpense.cardId) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Type</p>
            <p class="mt-1">
              <Badge v-if="selectedExpense.isRecurring" variant="warning" size="sm">Recurring ({{ selectedExpense.recurringCycle }})</Badge>
              <Badge v-else variant="neutral" size="sm">One-time</Badge>
            </p>
          </div>
        </div>
        <div>
          <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider">Description</p>
          <p class="text-sm text-surface-700 dark:text-surface-300 mt-1">{{ selectedExpense.description || 'No description' }}</p>
        </div>
        <div v-if="selectedExpense.tags && selectedExpense.tags.length > 0">
          <p class="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wider mb-2">Tags</p>
          <div class="flex flex-wrap gap-1.5">
            <Badge v-for="tag in selectedExpense.tags" :key="tag" variant="neutral" size="sm">{{ tag }}</Badge>
          </div>
        </div>
        <div class="flex justify-end pt-4 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showDetailModal = false">Close</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
