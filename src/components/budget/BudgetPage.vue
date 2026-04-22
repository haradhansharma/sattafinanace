<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useBudgetStore } from '../../stores/budget';
import { useExpenseStore } from '../../stores/expense';
import { useCurrencyStore } from '../../stores/currency';
import type { Budget, BudgetCategory, Currency } from '../../types';
import { formatCurrency } from '../../utils/formatters';
import { getMonthName, daysRemainingInMonth, daysElapsedInMonth } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, ProgressBar, Modal } from '../ui';

const budgetStore = useBudgetStore();
const expenseStore = useExpenseStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ============ State ============
const selectedMonth = ref('2026-04');
const showCreateModal = ref(false);
const showAllocateModal = ref(false);
const createForm = ref({ month: '2026-06', totalBudgetAmount: 0, currency: 'BDT' as Currency });
const allocateForm = ref({ categoryId: '', amount: 0 });

// ============ Month Options ============
const monthOptions = computed(() => {
  const months = new Set<string>();
  // Add all months that have budgets
  budgetStore.budgets.forEach(b => months.add(b.month));
  // Ensure current month is included
  const now = new Date();
  const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  months.add(currentMonth);
  // Add next 2 months for planning
  for (let i = 1; i <= 2; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
    const futureMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    months.add(futureMonth);
  }
  // Sort descending (most recent first)
  return Array.from(months).sort().reverse().map(m => ({
    value: m,
    label: (() => {
      const [year, month] = m.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1, 1);
      return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    })(),
  }));
});

// ============ Computed ============
const budget = computed<Budget | undefined>(() => budgetStore.getBudgetByMonth(selectedMonth.value));

const totalBudget = computed(() => budget.value?.totalBudgetAmount ?? 0);
const totalAllocated = computed(() => budget.value?.allocatedAmount ?? 0);
const totalSpent = computed(() => {
  if (!budget.value) return 0;
  return budget.value.categories.reduce((s, c) => s + c.spentAmount, 0);
});
const totalRemaining = computed(() => budget.value?.remainingBalance ?? 0);
const isOverBudget = computed(() => budget.value?.isOverBudget ?? false);

// Budget percentage for the overview bar
const spentPercent = computed(() => {
  if (totalBudget.value === 0) return 0;
  return (totalSpent.value / totalBudget.value) * 100;
});

// Overview bar color
const barColor = computed(() => {
  const p = spentPercent.value;
  if (p > 100) return 'bg-danger-600';
  if (p > 90) return 'bg-danger-500';
  if (p > 70) return 'bg-warning-500';
  return 'bg-accent-500';
});

// Forecast data from budget
const forecastedSpend = computed(() => budget.value?.forecastedSpend ?? 0);
const forecastGap = computed(() => budget.value?.forecastGap ?? 0);
const dailySafeSpend = computed(() => budget.value?.dailySafeSpend ?? 0);
const requiredDailyReduction = computed(() => budget.value?.requiredDailyReduction ?? 0);
const requiredExtraIncome = computed(() => budget.value?.requiredExtraIncome ?? 0);

const daysRemaining = computed(() => daysRemainingInMonth());
const daysElapsed = computed(() => daysElapsedInMonth());

// Budget status
const budgetStatus = computed<'on-track' | 'at-risk' | 'over-budget'>(() => {
  if (isOverBudget.value) return 'over-budget';
  if (forecastGap.value < totalRemaining.value * 0.3) return 'at-risk';
  return 'on-track';
});

// Category breakdown sorted by worst overspend first
const sortedCategories = computed(() => {
  if (!budget.value) return [];
  return [...budget.value.categories].sort((a, b) => {
    // Over budget categories first
    if (a.isOverBudget && !b.isOverBudget) return -1;
    if (!a.isOverBudget && b.isOverBudget) return 1;
    // Then by percentage used (highest first)
    const pctA = a.budgetAmount > 0 ? a.spentAmount / a.budgetAmount : 0;
    const pctB = b.budgetAmount > 0 ? b.spentAmount / b.budgetAmount : 0;
    return pctB - pctA;
  });
});

// Category icons
const categoryIcons: Record<string, string> = {
  'Rent/Housing': '🏠',
  'Food & Groceries': '🛒',
  'Transport': '🚗',
  'Shopping': '🛍️',
  'Utilities & Subscriptions': '💡',
  'Dining Out & Entertainment': '🍽️',
};

// Category bar color
function categoryBarColor(cat: BudgetCategory): string {
  if (cat.isOverBudget) return 'bg-danger-500';
  const pct = cat.budgetAmount > 0 ? (cat.spentAmount / cat.budgetAmount) * 100 : 0;
  if (pct > 90) return 'bg-warning-500';
  if (pct > 70) return 'bg-warning-400';
  return 'bg-accent-500';
}

function categoryBarClass(cat: BudgetCategory): string {
  if (cat.isOverBudget) return 'bg-danger-500';
  const pct = cat.budgetAmount > 0 ? (cat.spentAmount / cat.budgetAmount) * 100 : 0;
  if (pct > 90) return 'bg-danger-500';
  if (pct > 70) return 'bg-warning-500';
  return 'bg-accent-500';
}

// ============ Actions ============
function openAllocate() {
  allocateForm.value = { categoryId: '', amount: 0 };
  showAllocateModal.value = true;
}

function submitCreate() {
  budgetStore.addBudget({
    name: getMonthName(createForm.value.month) + ' Budget',
    month: createForm.value.month,
    totalBudgetAmount: createForm.value.totalBudgetAmount,
    currency: createForm.value.currency,
    allocatedAmount: 0,
    availableBalance: createForm.value.totalBudgetAmount,
    remainingBalance: createForm.value.totalBudgetAmount,
    isOverBudget: false,
    overAmount: 0,
    forecastedSpend: 0,
    forecastGap: createForm.value.totalBudgetAmount,
    dailySafeSpend: Math.round(createForm.value.totalBudgetAmount / 30),
    requiredDailyReduction: 0,
    requiredExtraIncome: 0,
    categories: [],
  });
  showCreateModal.value = false;
}

// ============ Helpers ============
function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') {
    return currencyStore.formatWithCurrency(amount, currency as Currency);
  }
  return formatCurrency(amount, 'BDT');
}

// Helper: Get expense transactions for a budget category (from expenseStore, not embedded data)
function getExpenseCategoryTransactions(categoryId: string) {
  return expenseStore.expenses
    .filter(e => e.categoryId === categoryId)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5);
}

function getExpenseCategoryTransactionCount(categoryId: string): number {
  return expenseStore.expenses.filter(e => e.categoryId === categoryId).length;
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Budget" subtitle="Set budgets and track your spending limits">
      <template #actions>
        <button class="btn-primary" @click="showCreateModal = true">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Create Budget
        </button>
      </template>
    </PageHeader>

    <!-- No Budget State -->
    <div v-if="!budget" class="card p-12 text-center">
      <div class="text-5xl mb-4">🎯</div>
      <h3 class="text-lg font-semibold text-surface-700 dark:text-surface-300 mb-2">No Budget Found</h3>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-4">Create a budget for this month to start tracking your spending.</p>
      <button class="btn-primary" @click="showCreateModal = true">Create Budget</button>
    </div>

    <template v-else>
      <!-- Month Selector -->
      <div class="flex items-center gap-3">
        <label class="text-sm font-medium text-surface-600 dark:text-surface-400">Month:</label>
        <div class="flex gap-1 bg-surface-100 dark:bg-surface-800 rounded-lg p-1">
          <button
            v-for="m in monthOptions"
            :key="m.value"
            @click="selectedMonth = m.value"
            class="px-4 py-1.5 text-sm font-medium rounded-md transition-all"
            :class="selectedMonth === m.value
              ? 'bg-white dark:bg-surface-700 text-primary-600 dark:text-primary-400 shadow-sm'
              : 'text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-300'"
          >
            {{ m.label }}
          </button>
        </div>
        <span v-if="budget?.currency && budget.currency !== 'BDT'" class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">
          {{ budget.currency }}
        </span>
        <button class="btn-secondary text-sm" @click="openAllocate">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"/></svg>
          Allocate
        </button>
      </div>

      <!-- Summary Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Budget"
          :value="fmtCur(totalBudget, budget?.currency)"
          icon="🎯"
          color="primary"
        />
        <StatCard
          title="Total Allocated"
          :value="fmtCur(totalAllocated, budget?.currency)"
          icon="📊"
          color="primary"
        />
        <StatCard
          title="Total Spent"
          :value="fmtCur(totalSpent, budget?.currency)"
          icon="💳"
          :color="isOverBudget ? 'danger' : 'warning'"
          :trend="isOverBudget ? 'up' : 'down'"
          :change="isOverBudget ? 5 : -12"
        />
        <StatCard
          title="Remaining Balance"
          :value="fmtCur(totalRemaining, budget?.currency)"
          icon="💰"
          :color="totalRemaining >= 0 ? 'accent' : 'danger'"
        />
      </div>

      <!-- Budget Overview Bar -->
      <div class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-surface-700 dark:text-surface-300">Budget Overview</h3>
          <span class="text-sm font-bold tabular-nums" :class="spentPercent > 100 ? 'text-danger-500' : spentPercent > 90 ? 'text-warning-500' : 'text-accent-600'">
            {{ spentPercent.toFixed(1) }}% used
          </span>
        </div>
        <div class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-4 overflow-hidden">
          <div
            class="h-4 rounded-full transition-all duration-700"
            :class="barColor"
            :style="{ width: `${Math.min(spentPercent, 100)}%` }"
          />
        </div>
        <div class="flex justify-between mt-2 text-xs text-surface-500 dark:text-surface-400">
          <span>{{ fmtCur(totalSpent, budget?.currency) }} spent</span>
          <span>{{ fmtCur(totalBudget, budget?.currency) }} budget</span>
        </div>
        <!-- Over budget alert -->
        <div v-if="isOverBudget" class="mt-3 bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/30 rounded-lg px-4 py-3 flex items-center gap-2">
          <span class="text-danger-500 text-lg">🚨</span>
          <span class="text-sm font-medium text-danger-700 dark:text-danger-400">
            Over budget by {{ fmtCur(budget!.overAmount, budget?.currency) }}! Take action now.
          </span>
        </div>
      </div>

      <!-- Forecast Section -->
      <div class="card p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-surface-700 dark:text-surface-300">Budget Forecast & Insights</h3>
          <div class="flex items-center gap-2">
            <span
              class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
              :class="{
                'bg-accent-100 dark:bg-accent-500/20 text-accent-700 dark:text-accent-400': budgetStatus === 'on-track',
                'bg-warning-50 dark:bg-warning-500/20 text-amber-700 dark:text-amber-400': budgetStatus === 'at-risk',
                'bg-danger-100 dark:bg-danger-500/20 text-danger-700 dark:text-danger-400': budgetStatus === 'over-budget',
              }"
            >
              {{ budgetStatus === 'on-track' ? '✅ On Track' : budgetStatus === 'at-risk' ? '⚠️ At Risk' : '🚨 Over Budget' }}
            </span>
            <span class="text-xs text-surface-400">{{ daysRemaining }} days remaining in month</span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-4">
            <p class="text-xs text-surface-400 mb-1">Forecasted Spend</p>
            <p class="text-lg font-bold tabular-nums" :class="forecastedSpend > totalBudget ? 'text-danger-500' : 'text-surface-900 dark:text-white'">
              {{ fmtCur(forecastedSpend, budget?.currency) }}
            </p>
            <p class="text-xs text-surface-400 mt-1">Based on daily avg × {{ daysRemaining }} days</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-4">
            <p class="text-xs text-surface-400 mb-1">Forecast Gap</p>
            <p class="text-lg font-bold tabular-nums" :class="forecastGap >= 0 ? 'text-accent-600' : 'text-danger-500'">
              {{ forecastGap >= 0 ? '+' : '' }}{{ fmtCur(forecastGap, budget?.currency) }}
            </p>
            <p class="text-xs text-surface-400 mt-1">{{ forecastGap >= 0 ? 'Under budget' : 'Will exceed budget' }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-4">
            <p class="text-xs text-surface-400 mb-1">Days Elapsed / Remaining</p>
            <p class="text-lg font-bold text-surface-900 dark:text-white tabular-nums">
              {{ daysElapsed }} <span class="text-sm font-normal text-surface-400">/</span> {{ daysRemaining }}
            </p>
            <p class="text-xs text-surface-400 mt-1">{{ ((daysElapsed / (daysElapsed + daysRemaining)) * 100).toFixed(0) }}% of month passed</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-4">
            <p class="text-xs text-surface-400 mb-1">Total Spent So Far</p>
            <p class="text-lg font-bold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(totalSpent, budget?.currency) }}</p>
            <p class="text-xs text-surface-400 mt-1">Daily avg: {{ fmtCur(daysElapsed > 0 ? totalSpent / daysElapsed : 0, budget?.currency) }}</p>
          </div>
        </div>

        <!-- Actionable Insights -->
        <div class="border-t border-surface-200 dark:border-surface-700 pt-4 space-y-3">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300">Actionable Insights</h4>

          <!-- On Track -->
          <div v-if="budgetStatus === 'on-track' && dailySafeSpend > 0" class="flex items-start gap-3 bg-accent-50 dark:bg-accent-500/10 border border-accent-200 dark:border-accent-500/30 rounded-lg px-4 py-3">
            <span class="text-accent-600 dark:text-accent-400 text-lg mt-0.5">✅</span>
            <div>
              <p class="text-sm font-medium text-accent-700 dark:text-accent-400">You're on track!</p>
              <p class="text-sm text-accent-600 dark:text-accent-500">
                Your daily safe spend is <strong class="tabular-nums">{{ fmtCur(dailySafeSpend, budget?.currency) }}</strong> per day for the remaining {{ daysRemaining }} days.
              </p>
            </div>
          </div>

          <!-- At Risk -->
          <div v-if="budgetStatus === 'at-risk' || requiredDailyReduction > 0" class="flex items-start gap-3 bg-warning-50 dark:bg-warning-500/10 border border-warning-400/30 rounded-lg px-4 py-3">
            <span class="text-amber-600 dark:text-amber-400 text-lg mt-0.5">⚠️</span>
            <div>
              <p class="text-sm font-medium text-amber-700 dark:text-amber-400">Spending is above pace</p>
              <p class="text-sm text-amber-600 dark:text-amber-500">
                Reduce daily spending by <strong class="tabular-nums">{{ fmtCur(requiredDailyReduction, budget?.currency) }}</strong> to stay within budget.
              </p>
              <p v-if="dailySafeSpend > 0" class="text-sm text-amber-600 dark:text-amber-500 mt-1">
                Daily safe spend: <strong class="tabular-nums">{{ fmtCur(dailySafeSpend, budget?.currency) }}</strong> per day.
              </p>
            </div>
          </div>

          <!-- Over Budget / Need Extra Income -->
          <div v-if="requiredExtraIncome > 0" class="flex items-start gap-3 bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/30 rounded-lg px-4 py-3">
            <span class="text-danger-500 text-lg mt-0.5">🚨</span>
            <div>
              <p class="text-sm font-medium text-danger-700 dark:text-danger-400">Extra income needed</p>
              <p class="text-sm text-danger-600 dark:text-danger-500">
                You need <strong class="tabular-nums">{{ fmtCur(requiredExtraIncome, budget?.currency) }}</strong> extra income this month to meet your budget target.
              </p>
            </div>
          </div>

          <!-- Forecast warning -->
          <div v-if="forecastedSpend > totalBudget" class="flex items-start gap-3 bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/30 rounded-lg px-4 py-3">
            <span class="text-danger-500 text-lg mt-0.5">📈</span>
            <div>
              <p class="text-sm font-medium text-danger-700 dark:text-danger-400">Projected to exceed budget</p>
              <p class="text-sm text-danger-600 dark:text-danger-500">
                At current pace, you'll spend <strong class="tabular-nums">{{ fmtCur(forecastedSpend - totalBudget, budget?.currency) }}</strong> over your budget by month end.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Category Breakdown -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-surface-900 dark:text-white">Category Breakdown</h3>
          <span class="text-sm text-surface-400">{{ sortedCategories.length }} categories</span>
        </div>

        <div class="space-y-4">
          <div
            v-for="cat in sortedCategories"
            :key="cat.id"
            class="card p-5 animate-fade-in"
            :class="cat.isOverBudget ? 'border-danger-300 dark:border-danger-500/50 bg-danger-50/50 dark:bg-danger-500/5' : ''"
          >
            <!-- Category Header -->
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                  :class="cat.isOverBudget ? 'bg-danger-100 dark:bg-danger-500/20' : 'bg-primary-100 dark:bg-primary-500/20'"
                >
                  {{ categoryIcons[cat.name] || '📂' }}
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <h4 class="font-semibold text-surface-900 dark:text-white">{{ cat.name }}</h4>
                    <Badge v-if="cat.isOverBudget" variant="danger">Over Budget</Badge>
                  </div>
                  <p class="text-xs text-surface-400">{{ getExpenseCategoryTransactionCount(cat.categoryId) }} transactions</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-sm font-semibold tabular-nums" :class="cat.remainingBalance < 0 ? 'text-danger-500' : 'text-accent-600 dark:text-accent-400'">
                  {{ cat.remainingBalance < 0 ? '-' : '' }}{{ fmtCur(Math.abs(cat.remainingBalance), budget?.currency) }} remaining
                </p>
              </div>
            </div>

            <!-- Category Progress -->
            <div class="mb-3">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-surface-500 dark:text-surface-400 tabular-nums">{{ fmtCur(cat.spentAmount, budget?.currency) }} / {{ fmtCur(cat.budgetAmount, budget?.currency) }}</span>
                <span class="text-xs font-semibold tabular-nums" :class="cat.isOverBudget ? 'text-danger-500' : cat.budgetAmount > 0 && (cat.spentAmount / cat.budgetAmount) > 70 ? 'text-warning-500' : 'text-accent-600'">
                  {{ cat.budgetAmount > 0 ? ((cat.spentAmount / cat.budgetAmount) * 100).toFixed(0) : 0 }}%
                </span>
              </div>
              <div class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-2 overflow-hidden">
                <div
                  class="h-2 rounded-full transition-all duration-500"
                  :class="categoryBarClass(cat)"
                  :style="{ width: `${Math.min(cat.budgetAmount > 0 ? (cat.spentAmount / cat.budgetAmount) * 100 : 0, 100)}%` }"
                />
              </div>
            </div>

            <!-- Category Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
              <div>
                <p class="text-xs text-surface-400">Budget</p>
                <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ fmtCur(cat.budgetAmount, budget?.currency) }}</p>
              </div>
              <div>
                <p class="text-xs text-surface-400">Allocated</p>
                <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ fmtCur(cat.allocatedAmount, budget?.currency) }}</p>
              </div>
              <div>
                <p class="text-xs text-surface-400">Spent</p>
                <p class="text-sm font-medium tabular-nums" :class="cat.isOverBudget ? 'text-danger-500' : 'text-surface-700 dark:text-surface-300'">{{ fmtCur(cat.spentAmount, budget?.currency) }}</p>
              </div>
              <div>
                <p class="text-xs text-surface-400">Remaining</p>
                <p class="text-sm font-medium tabular-nums" :class="cat.remainingBalance < 0 ? 'text-danger-500' : 'text-accent-600 dark:text-accent-400'">
                  {{ cat.remainingBalance < 0 ? '-' : '' }}{{ fmtCur(Math.abs(cat.remainingBalance), budget?.currency) }}
                </p>
              </div>
            </div>

            <!-- Category Forecast & Insight -->
            <div class="mt-3 pt-3 border-t border-surface-100 dark:border-surface-700">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div class="flex items-center gap-2">
                  <span class="text-xs text-surface-400 w-20 shrink-0">Forecast:</span>
                  <span class="text-xs font-medium tabular-nums" :class="cat.forecastedSpend > cat.budgetAmount ? 'text-danger-500' : 'text-surface-600 dark:text-surface-400'">
                    {{ fmtCur(cat.forecastedSpend, budget?.currency) }}
                    <span v-if="cat.forecastedSpend > cat.budgetAmount" class="text-danger-500">(over by {{ fmtCur(cat.forecastedSpend - cat.budgetAmount, budget?.currency) }})</span>
                  </span>
                </div>
                <div v-if="cat.dailySafeSpend > 0 && !cat.isOverBudget" class="flex items-center gap-2">
                  <span class="text-xs text-surface-400 w-20 shrink-0">Safe Spend:</span>
                  <span class="text-xs font-medium text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(cat.dailySafeSpend, budget?.currency) }}/day</span>
                </div>
                <div v-if="cat.requiredDailyReduction > 0" class="flex items-center gap-2">
                  <span class="text-xs text-surface-400 w-20 shrink-0">Reduce by:</span>
                  <span class="text-xs font-medium text-warning-500 tabular-nums">{{ fmtCur(cat.requiredDailyReduction, budget?.currency) }}/day</span>
                </div>
                <div v-if="cat.requiredExtraIncome > 0" class="flex items-center gap-2">
                  <span class="text-xs text-surface-400 w-20 shrink-0">Extra Income:</span>
                  <span class="text-xs font-medium text-danger-500 tabular-nums">{{ fmtCur(cat.requiredExtraIncome, budget?.currency) }} needed</span>
                </div>
              </div>
            </div>

            <!-- Category Transactions (derived from Expense store, not embedded) -->
            <div v-if="getExpenseCategoryTransactions(cat.categoryId).length > 0" class="mt-3 pt-3 border-t border-surface-100 dark:border-surface-700">
              <p class="text-xs font-semibold text-surface-500 dark:text-surface-400 mb-2 uppercase tracking-wider">Recent Transactions</p>
              <div class="space-y-2">
                <div
                  v-for="tx in getExpenseCategoryTransactions(cat.categoryId)"
                  :key="tx.id"
                  class="flex items-center justify-between py-1.5"
                >
                  <div class="flex items-center gap-2 min-w-0">
                    <div class="w-7 h-7 rounded-full bg-surface-100 dark:bg-surface-700 flex items-center justify-center text-xs">
                      💸
                    </div>
                    <div class="min-w-0">
                      <p class="text-sm text-surface-700 dark:text-surface-300 truncate">{{ tx.description }}</p>
                      <p class="text-xs text-surface-400">{{ new Date(tx.date).toLocaleDateString('en-US', { day: 'numeric', month: 'short' }) }}</p>
                    </div>
                  </div>
                  <span class="text-sm font-medium text-danger-500 tabular-nums shrink-0">-{{ fmtCur(tx.amount, budget?.currency) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ============ CREATE BUDGET MODAL ============ -->
    <Modal :is-open="showCreateModal" title="Create New Budget" size="md" @close="showCreateModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Month</label>
          <select v-model="createForm.month" class="input-field">
            <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Budget Currency</label>
          <select v-model="createForm.currency" class="input-field">
            <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Total Budget Amount</label>
          <input v-model.number="createForm.totalBudgetAmount" type="number" class="input-field tabular-nums" placeholder="e.g. 120000" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showCreateModal = false">Cancel</button>
          <button class="btn-primary" @click="submitCreate">Create Budget</button>
        </div>
      </div>
    </Modal>

    <!-- ============ ALLOCATE MODAL ============ -->
    <Modal :is-open="showAllocateModal" title="Allocate to Category" size="md" @close="showAllocateModal = false">
      <div class="space-y-4">
        <div v-if="budget">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3 mb-4 flex items-center justify-between">
            <span class="text-sm text-surface-600 dark:text-surface-400">Available to Allocate</span>
            <span class="text-sm font-bold text-primary-600 dark:text-primary-400 tabular-nums">{{ fmtCur(budget.availableBalance, budget?.currency) }}</span>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Category</label>
          <select v-model="allocateForm.categoryId" class="input-field">
            <option value="">Select Category</option>
            <option v-for="cat in budget?.categories" :key="cat.id" :value="cat.id">
              {{ cat.name }} ({{ fmtCur(cat.budgetAmount, budget?.currency) }})
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Amount</label>
          <input v-model.number="allocateForm.amount" type="number" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showAllocateModal = false">Cancel</button>
          <button class="btn-primary" @click="showAllocateModal = false">Allocate</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
