<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { format } from 'date-fns';
import { useBankStore, useIncomeStore, useExpenseStore, useLoanStore, useBudgetStore, useAuthStore, useCurrencyStore } from '../../stores';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { StatCard, PageHeader, ProgressBar, Badge } from '../ui';

const authStore = useAuthStore();
const bankStore = useBankStore();
const incomeStore = useIncomeStore();
const expenseStore = useExpenseStore();
const loanStore = useLoanStore();
const budgetStore = useBudgetStore();
const currencyStore = useCurrencyStore();

const now = new Date();
const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

// ==================== Computed Stats ====================

const totalBalance = computed(() => bankStore.totalBalance);

const upcomingBalance = computed(() => {
  return totalBalance.value + incomeStore.pendingIncomeThisMonth;
});

const monthlyIncome = computed(() => {
  return incomeStore.getIncomeByMonth(currentMonth).reduce((sum: number, i) => sum + currencyStore.convertToBase(i.amount, i.currency || 'BDT'), 0);
});

const monthlyExpense = computed(() => {
  return expenseStore.expenses
    .filter(e => e.date.startsWith(currentMonth))
    .reduce((sum, e) => sum + currencyStore.convertToBase(e.amount, e.currency || 'BDT'), 0);
});

const netWorth = computed(() => totalBalance.value - loanStore.totalDebt);

const currentBudget = computed(() => budgetStore.getCurrentBudget());
const overBudgetCategories = computed(() => budgetStore.overBudgetCategories);
const activeLoans = computed(() => loanStore.getActiveLoans());
const recentTransactions = computed(() => bankStore.getRecentTransactions(8));

// ==================== Income vs Expense Chart Data ====================

interface MonthlyData {
  month: string;
  label: string;
  income: number;
  expense: number;
}

const chartData = computed<MonthlyData[]>(() => {
  const months: MonthlyData[] = [];

  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const monthStr = format(d, 'yyyy-MM');
    const label = format(d, 'MMM');

    const income = incomeStore.getIncomeByMonth(monthStr).reduce((sum: number, inc) => sum + currencyStore.convertToBase(inc.amount, inc.currency || 'BDT'), 0);
    const expense = expenseStore.expenses
      .filter(e => e.date.startsWith(monthStr))
      .reduce((sum, e) => sum + currencyStore.convertToBase(e.amount, e.currency || 'BDT'), 0);

    months.push({ month: monthStr, label, income, expense });
  }
  return months;
});

const maxChartValue = computed(() => {
  return Math.max(...chartData.value.map(d => Math.max(d.income, d.expense)), 1);
});

// ==================== Helpers ====================

function getTransactionIcon(type: string) {
  if (type === 'income') return { icon: '↗', bg: 'bg-accent-100 dark:bg-accent-500/20', text: 'text-accent-600 dark:text-accent-400' };
  if (type === 'expense') return { icon: '↘', bg: 'bg-danger-100 dark:bg-danger-500/20', text: 'text-danger-600 dark:text-danger-400' };
  return { icon: '↔', bg: 'bg-primary-100 dark:bg-primary-500/20', text: 'text-primary-600 dark:text-primary-400' };
}

function getCategoryName(categoryId: string): string {
  const cat = expenseStore.categories.find(c => c.id === categoryId);
  return cat?.name ?? '';
}

function getCategoryIcon(categoryId: string): string {
  const cat = expenseStore.categories.find(c => c.id === categoryId);
  return cat?.icon ?? '📌';
}

const todayFormatted = computed(() => format(new Date(), 'EEEE, MMMM d, yyyy'));
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- ==================== Header Section ==================== -->
    <PageHeader :title="`Welcome back, ${authStore.fullName}`" :subtitle="todayFormatted" />

    <!-- ==================== Stats Grid ==================== -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      <StatCard
        title="Total Balance"
        :value="formatCurrency(totalBalance)"
        icon="💰"
        trend="up"
        :change="12.5"
        color="primary"
      />
      <StatCard
        title="Upcoming Balance"
        :value="formatCurrency(upcomingBalance)"
        icon="🟢"
        color="accent"
      />
      <StatCard
        title="Monthly Income"
        :value="formatCurrency(monthlyIncome)"
        icon="📈"
        trend="up"
        :change="8.3"
        color="accent"
      />
      <StatCard
        title="Monthly Expense"
        :value="formatCurrency(monthlyExpense)"
        icon="📉"
        trend="down"
        :change="-3.2"
        color="danger"
      />
      <StatCard
        title="Net Worth"
        :value="formatCurrency(netWorth)"
        icon="🏦"
        trend="up"
        :change="5.1"
        color="warning"
      />
    </div>

    <!-- ==================== Income vs Expense Chart + Budget Overview ==================== -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Income vs Expense Bar Chart -->
      <div class="lg:col-span-2 card p-5">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-1">Income vs Expense</h2>
        <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">Last 6 months comparison</p>

        <!-- Legend -->
        <div class="flex items-center gap-4 mb-4">
          <div class="flex items-center gap-1.5">
            <div class="w-3 h-3 rounded-sm bg-accent-500" />
            <span class="text-xs text-surface-500 dark:text-surface-400">Income</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-3 h-3 rounded-sm bg-danger-500" />
            <span class="text-xs text-surface-500 dark:text-surface-400">Expense</span>
          </div>
        </div>

        <!-- Bar Chart -->
        <div class="flex items-end gap-3 h-52">
          <div
            v-for="item in chartData"
            :key="item.month"
            class="flex-1 flex flex-col items-center gap-1"
          >
            <!-- Bars -->
            <div class="flex items-end gap-1 w-full h-44">
              <div class="flex-1 flex flex-col justify-end h-full relative group">
                <div
                  class="w-full bg-accent-500 dark:bg-accent-400 rounded-t-sm transition-all duration-500 min-h-[2px]"
                  :style="{ height: `${(item.income / maxChartValue) * 100}%` }"
                  :title="`Income: ${formatCurrency(item.income)}`"
                />
                <!-- Tooltip -->
                <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-900 dark:bg-surface-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                  {{ formatCurrency(item.income) }}
                </div>
              </div>
              <div class="flex-1 flex flex-col justify-end h-full relative group">
                <div
                  class="w-full bg-danger-500 dark:bg-danger-400 rounded-t-sm transition-all duration-500 min-h-[2px]"
                  :style="{ height: `${(item.expense / maxChartValue) * 100}%` }"
                  :title="`Expense: ${formatCurrency(item.expense)}`"
                />
                <!-- Tooltip -->
                <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-900 dark:bg-surface-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                  {{ formatCurrency(item.expense) }}
                </div>
              </div>
            </div>
            <!-- Month Label -->
            <span class="text-xs text-surface-500 dark:text-surface-400 font-medium">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <!-- Budget Overview -->
      <div class="card p-5">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-1">Budget Overview</h2>
        <p class="text-sm text-surface-500 dark:text-surface-400 mb-4">April 2026</p>

        <template v-if="currentBudget">
          <!-- Overall Budget -->
          <div class="mb-5">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Total Spent</span>
              <span class="text-sm tabular-nums text-surface-600 dark:text-surface-400">
                {{ formatCurrency(budgetStore.totalSpent) }} / {{ formatCurrency(budgetStore.totalBudgetAmount) }}
              </span>
            </div>
            <ProgressBar
              :value="budgetStore.totalSpent"
              :max="budgetStore.totalBudgetAmount"
              :color="currentBudget.isOverBudget ? 'danger' : 'primary'"
              size="md"
            />
            <div class="flex items-center justify-between mt-2">
              <span class="text-xs text-surface-500 dark:text-surface-400">
                Remaining: {{ formatCurrency(budgetStore.totalRemaining) }}
              </span>
              <span v-if="currentBudget.isOverBudget" class="text-xs text-danger-500 font-medium">
                Over by {{ formatCurrency(currentBudget.overAmount) }}
              </span>
            </div>
          </div>

          <!-- Budget Categories -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-surface-700 dark:text-surface-300">Categories</h3>
            <div
              v-for="cat in currentBudget.categories"
              :key="cat.id"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <span class="text-xs truncate text-surface-600 dark:text-surface-400">{{ cat.name }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs tabular-nums text-surface-600 dark:text-surface-400">
                  {{ formatCurrency(cat.spentAmount) }}
                </span>
                <Badge v-if="cat.isOverBudget" variant="danger" size="sm">Over</Badge>
              </div>
            </div>
          </div>

          <!-- Over-budget Alert -->
          <div v-if="overBudgetCategories.length > 0" class="mt-4 p-3 rounded-lg bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/20">
            <div class="flex items-center gap-2">
              <span class="text-danger-500">⚠️</span>
              <div>
                <p class="text-sm font-medium text-danger-700 dark:text-danger-400">Over Budget Alert</p>
                <p class="text-xs text-danger-600 dark:text-danger-400/70 mt-0.5">
                  {{ overBudgetCategories.map(c => c.name).join(', ') }}
                </p>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="text-center py-8">
          <p class="text-surface-400 dark:text-surface-500">No budget set for this month</p>
        </div>
      </div>
    </div>

    <!-- ==================== Recent Transactions ==================== -->
    <div class="card p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold text-surface-900 dark:text-white">Recent Transactions</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">Latest 8 transactions</p>
        </div>
        <a href="/bank" class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
          View All →
        </a>
      </div>
      <div class="divide-y divide-surface-100 dark:divide-surface-700">
        <div
          v-for="txn in recentTransactions"
          :key="txn.id"
          class="flex items-center justify-between py-3 first:pt-0 last:pb-0"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center text-base font-bold"
              :class="getTransactionIcon(txn.type).bg + ' ' + getTransactionIcon(txn.type).text"
            >
              {{ getCategoryIcon(txn.categoryId) }}
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-surface-900 dark:text-white truncate">{{ txn.description }}</p>
              <p class="text-xs text-surface-500 dark:text-surface-400 mt-0.5">{{ formatDate(txn.date, 'short') }}</p>
            </div>
          </div>
          <div class="text-right">
            <p
              class="text-sm font-semibold tabular-nums whitespace-nowrap"
              :class="txn.direction === 'credit' ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500 dark:text-danger-400'"
            >
              {{ txn.direction === 'credit' ? '+' : '-' }}{{ currencyStore.formatWithCurrency(txn.amount, txn.currency || 'BDT') }}
            </p>
            <p v-if="txn.currency && txn.currency !== 'BDT'" class="text-[10px] text-surface-400 tabular-nums">
              ≈ {{ formatCurrency(currencyStore.convertToBase(txn.amount, txn.currency)) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Expected Income This Month ==================== -->
    <div class="card p-5" v-if="incomeStore.pendingIncomeThisMonth > 0 || incomeStore.pendingSources.length > 0">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold text-surface-900 dark:text-white">Expected Income</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">Pending receivables this month</p>
        </div>
        <div class="text-right">
          <p class="text-xs text-surface-500 dark:text-surface-400">Received</p>
          <p class="text-sm font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ formatCurrency(incomeStore.receivedThisMonth) }}</p>
          <p class="text-xs text-surface-400">of {{ formatCurrency(incomeStore.expectedMonthlyIncome) }}</p>
        </div>
      </div>
      <ProgressBar
        :value="incomeStore.receivedThisMonth"
        :max="incomeStore.expectedMonthlyIncome || 1"
        color="accent"
        size="md"
        :show-label="true"
      />
      <div v-if="incomeStore.pendingSources.length > 0" class="mt-4 space-y-2">
        <h3 class="text-sm font-medium text-surface-700 dark:text-surface-300">Pending Sources</h3>
        <div
          v-for="source in incomeStore.pendingSources"
          :key="source.id"
          class="flex items-center justify-between py-2 px-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg"
        >
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium text-surface-600 dark:text-surface-400">{{ source.type === 'salary' ? '💼' : source.type === 'rental' ? '🏠' : source.type === 'investment' ? '📊' : '📦' }}</span>
            <span class="text-sm text-surface-700 dark:text-surface-300">{{ source.name }}</span>
          </div>
          <span class="text-sm font-semibold text-amber-600 dark:text-amber-400 tabular-nums">{{ formatCurrency(source.monthlyAmount || 0) }}</span>
        </div>
      </div>
      <div v-else class="mt-3 flex items-center gap-2 text-accent-600 dark:text-accent-400">
        <span>✅</span>
        <span class="text-sm font-medium">All expected income received this month!</span>
      </div>
    </div>

    <!-- ==================== Quick Actions + Upcoming Payments ==================== -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Quick Actions -->
      <div class="card p-5">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Quick Actions</h2>
        <div class="grid grid-cols-2 gap-3">
          <a
            href="/income"
            class="flex items-center gap-3 p-4 rounded-xl bg-accent-50 dark:bg-accent-500/10 hover:bg-accent-100 dark:hover:bg-accent-500/20 border border-accent-200 dark:border-accent-500/20 transition-colors group"
          >
            <div class="w-10 h-10 rounded-lg bg-accent-100 dark:bg-accent-500/20 flex items-center justify-center text-accent-600 dark:text-accent-400 text-lg group-hover:scale-110 transition-transform">
              💰
            </div>
            <div>
              <p class="text-sm font-semibold text-accent-700 dark:text-accent-300">Add Income</p>
              <p class="text-xs text-accent-600/70 dark:text-accent-400/60">Record earnings</p>
            </div>
          </a>
          <a
            href="/expense"
            class="flex items-center gap-3 p-4 rounded-xl bg-danger-50 dark:bg-danger-500/10 hover:bg-danger-100 dark:hover:bg-danger-500/20 border border-danger-200 dark:border-danger-500/20 transition-colors group"
          >
            <div class="w-10 h-10 rounded-lg bg-danger-100 dark:bg-danger-500/20 flex items-center justify-center text-danger-600 dark:text-danger-400 text-lg group-hover:scale-110 transition-transform">
              📝
            </div>
            <div>
              <p class="text-sm font-semibold text-danger-700 dark:text-danger-300">Add Expense</p>
              <p class="text-xs text-danger-600/70 dark:text-danger-400/60">Log spending</p>
            </div>
          </a>
          <a
            href="/bank"
            class="flex items-center gap-3 p-4 rounded-xl bg-primary-50 dark:bg-primary-500/10 hover:bg-primary-100 dark:hover:bg-primary-500/20 border border-primary-200 dark:border-primary-500/20 transition-colors group"
          >
            <div class="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-primary-600 dark:text-primary-400 text-lg group-hover:scale-110 transition-transform">
              ↔️
            </div>
            <div>
              <p class="text-sm font-semibold text-primary-700 dark:text-primary-300">Transfer Money</p>
              <p class="text-xs text-primary-600/70 dark:text-primary-400/60">Move funds</p>
            </div>
          </a>
          <a
            href="/budget"
            class="flex items-center gap-3 p-4 rounded-xl bg-warning-50 dark:bg-warning-500/10 hover:bg-warning-100/80 dark:hover:bg-warning-500/20 border border-warning-400/30 dark:border-warning-500/20 transition-colors group"
          >
            <div class="w-10 h-10 rounded-lg bg-warning-50 dark:bg-warning-500/20 flex items-center justify-center text-amber-600 dark:text-amber-400 text-lg group-hover:scale-110 transition-transform">
              📊
            </div>
            <div>
              <p class="text-sm font-semibold text-amber-700 dark:text-amber-300">Create Budget</p>
              <p class="text-xs text-amber-600/70 dark:text-amber-400/60">Plan spending</p>
            </div>
          </a>
        </div>
      </div>

      <!-- Upcoming Payments -->
      <div class="card p-5">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-1">Upcoming Payments</h2>
        <p class="text-sm text-surface-500 dark:text-surface-400 mb-4">Active loan EMIs</p>

        <div v-if="activeLoans.length > 0" class="space-y-4">
          <div
            v-for="loan in activeLoans"
            :key="loan.id"
            class="p-4 rounded-xl bg-surface-50 dark:bg-surface-700/50 border border-surface-200 dark:border-surface-600"
          >
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-semibold text-surface-900 dark:text-white">{{ loan.name }}</p>
                <p class="text-xs text-surface-500 dark:text-surface-400 mt-0.5">{{ loan.lenderName }}</p>
              </div>
              <Badge variant="info" size="sm">{{ loan.type }}</Badge>
            </div>
            <div class="grid grid-cols-3 gap-3 mt-3">
              <div>
                <p class="text-xs text-surface-500 dark:text-surface-400">EMI Amount</p>
                <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums mt-0.5">
                  {{ formatCurrency(loan.emiAmount) }}
                </p>
              </div>
              <div>
                <p class="text-xs text-surface-500 dark:text-surface-400">Next Payment</p>
                <p class="text-sm font-semibold text-surface-900 dark:text-white mt-0.5">
                  {{ formatDate(loan.nextPaymentDate, 'short') }}
                </p>
              </div>
              <div>
                <p class="text-xs text-surface-500 dark:text-surface-400">Outstanding</p>
                <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums mt-0.5">
                  {{ formatCurrency(loan.currentBalance) }}
                </p>
              </div>
            </div>
            <!-- Progress bar -->
            <div class="mt-3">
              <ProgressBar
                :value="loan.paidInstallments"
                :max="loan.totalInstallments"
                color="primary"
                size="sm"
                :show-label="false"
              />
              <p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
                {{ loan.paidInstallments }} of {{ loan.totalInstallments }} installments paid
              </p>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <p class="text-surface-400 dark:text-surface-500">No active loans</p>
        </div>
      </div>
    </div>
  </div>
</template>
