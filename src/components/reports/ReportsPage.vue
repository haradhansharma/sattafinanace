<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { format, subMonths } from 'date-fns';
import { useBankStore, useIncomeStore, useExpenseStore, useLoanStore, useBudgetStore, useAuthStore } from '../../stores';
import { formatCurrency, formatDate, getMonthName } from '../../utils/formatters';
import { StatCard, PageHeader, ProgressBar, Badge, Tabs } from '../ui';

const incomeStore = useIncomeStore();
const expenseStore = useExpenseStore();
const bankStore = useBankStore();

// ==================== Date Range Filter ====================

type PeriodKey = 'current_month' | 'last_3_months' | 'last_6_months' | 'this_year';

const periodOptions: { key: PeriodKey; label: string }[] = [
  { key: 'current_month', label: 'This Month' },
  { key: 'last_3_months', label: 'Last 3 Months' },
  { key: 'last_6_months', label: 'Last 6 Months' },
  { key: 'this_year', label: 'This Year' },
];

const activePeriod = ref<PeriodKey>('last_6_months');

function getMonthsForPeriod(period: PeriodKey): string[] {
  const months: string[] = [];
  const baseDate = new Date();
  let count: number;

  switch (period) {
    case 'current_month':
      count = 1;
      break;
    case 'last_3_months':
      count = 3;
      break;
    case 'last_6_months':
      count = 6;
      break;
    case 'this_year':
      count = 4; // Jan-Apr 2026
      break;
    default:
      count = 1;
  }

  for (let i = count - 1; i >= 0; i--) {
    const d = new Date(baseDate.getFullYear(), baseDate.getMonth() - i, 1);
    months.push(format(d, 'yyyy-MM'));
  }
  return months;
}

// ==================== Computed Report Data ====================

const selectedMonths = computed(() => getMonthsForPeriod(activePeriod.value));

const filteredIncomes = computed(() => {
  return incomeStore.incomes.filter(i => selectedMonths.value.some(m => i.date.startsWith(m)));
});

const filteredExpenses = computed(() => {
  return expenseStore.expenses.filter(e => selectedMonths.value.some(m => e.date.startsWith(m)));
});

const totalIncome = computed(() => filteredIncomes.value.reduce((sum, i) => sum + i.amount, 0));
const totalExpense = computed(() => filteredExpenses.value.reduce((sum, e) => sum + e.amount, 0));
const totalSavings = computed(() => totalIncome.value - totalExpense.value);
const savingsRate = computed(() => {
  if (totalIncome.value === 0) return 0;
  return (totalSavings.value / totalIncome.value) * 100;
});

// ==================== Monthly Trend Data ====================

interface MonthlyTrend {
  month: string;
  label: string;
  income: number;
  expense: number;
  savings: number;
  savingsRate: number;
}

const monthlyTrend = computed<MonthlyTrend[]>(() => {
  return selectedMonths.value.map(monthStr => {
    const income = incomeStore.incomes
      .filter(i => i.date.startsWith(monthStr))
      .reduce((sum, i) => sum + i.amount, 0);
    const expense = expenseStore.expenses
      .filter(e => e.date.startsWith(monthStr))
      .reduce((sum, e) => sum + e.amount, 0);
    const savings = income - expense;
    const rate = income > 0 ? (savings / income) * 100 : 0;
    const d = new Date(monthStr + '-01');
    return {
      month: monthStr,
      label: format(d, 'MMM yyyy'),
      income,
      expense,
      savings,
      savingsRate: rate,
    };
  });
});

// ==================== Category Breakdown ====================

interface CategoryData {
  categoryId: string;
  name: string;
  icon: string;
  color: string;
  amount: number;
  percentage: number;
}

const categoryBreakdown = computed<CategoryData[]>(() => {
  if (filteredExpenses.value.length === 0) return [];
  const total = totalExpense.value;

  const categoryMap = new Map<string, { name: string; icon: string; color: string; amount: number }>();

  for (const exp of filteredExpenses.value) {
    const existing = categoryMap.get(exp.categoryId);
    const cat = expenseStore.categories.find(c => c.id === exp.categoryId);
    if (existing) {
      existing.amount += exp.amount;
    } else {
      categoryMap.set(exp.categoryId, {
        name: cat?.name ?? 'Unknown',
        icon: cat?.icon ?? '📌',
        color: cat?.color ?? 'slate',
        amount: exp.amount,
      });
    }
  }

  return Array.from(categoryMap.entries())
    .map(([categoryId, data]) => ({
      categoryId,
      ...data,
      percentage: total > 0 ? (data.amount / total) * 100 : 0,
    }))
    .sort((a, b) => b.amount - a.amount);
});

// ==================== Bar Chart Data ====================

const maxChartValue = computed(() => {
  return Math.max(...monthlyTrend.value.map(m => Math.max(m.income, m.expense)), 1);
});

// ==================== Bank Account Summary ====================

interface AccountSummary {
  id: string;
  name: string;
  bankName: string;
  balance: number;
  totalCredits: number;
  totalDebits: number;
}

const accountSummaries = computed<AccountSummary[]>(() => {
  return bankStore.bankAccounts.map(account => {
    const txns = bankStore.getAccountTransactions(account.id);
    const credits = txns.filter(t => t.direction === 'credit').reduce((s, t) => s + t.amount, 0);
    const debits = txns.filter(t => t.direction === 'debit').reduce((s, t) => s + t.amount, 0);
    return {
      id: account.id,
      name: account.accountName,
      bankName: account.bankName,
      balance: bankStore.getAccountBalance(account.id),
      totalCredits: credits,
      totalDebits: debits,
    };
  });
});

// ==================== Top Expenses ====================

const topExpenses = computed(() => {
  return [...filteredExpenses.value]
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 10)
    .map(exp => {
      const cat = expenseStore.categories.find(c => c.id === exp.categoryId);
      return {
        ...exp,
        categoryName: cat?.name ?? 'Unknown',
        categoryIcon: cat?.icon ?? '📌',
        categoryColor: cat?.color ?? 'slate',
      };
    });
});

// ==================== Helpers ====================

const colorMap: Record<string, { bg: string; lightBg: string; text: string }> = {
  emerald: { bg: 'bg-emerald-500', lightBg: 'bg-emerald-50 dark:bg-emerald-500/20', text: 'text-emerald-600 dark:text-emerald-400' },
  blue: { bg: 'bg-blue-500', lightBg: 'bg-blue-50 dark:bg-blue-500/20', text: 'text-blue-600 dark:text-blue-400' },
  amber: { bg: 'bg-amber-500', lightBg: 'bg-amber-50 dark:bg-amber-500/20', text: 'text-amber-600 dark:text-amber-400' },
  violet: { bg: 'bg-violet-500', lightBg: 'bg-violet-50 dark:bg-violet-500/20', text: 'text-violet-600 dark:text-violet-400' },
  red: { bg: 'bg-red-500', lightBg: 'bg-red-50 dark:bg-red-500/20', text: 'text-red-600 dark:text-red-400' },
  indigo: { bg: 'bg-indigo-500', lightBg: 'bg-indigo-50 dark:bg-indigo-500/20', text: 'text-indigo-600 dark:text-indigo-400' },
  pink: { bg: 'bg-pink-500', lightBg: 'bg-pink-50 dark:bg-pink-500/20', text: 'text-pink-600 dark:text-pink-400' },
  purple: { bg: 'bg-purple-500', lightBg: 'bg-purple-50 dark:bg-purple-500/20', text: 'text-purple-600 dark:text-purple-400' },
  orange: { bg: 'bg-orange-500', lightBg: 'bg-orange-50 dark:bg-orange-500/20', text: 'text-orange-600 dark:text-orange-400' },
  cyan: { bg: 'bg-cyan-500', lightBg: 'bg-cyan-50 dark:bg-cyan-500/20', text: 'text-cyan-600 dark:text-cyan-400' },
  green: { bg: 'bg-green-500', lightBg: 'bg-green-50 dark:bg-green-500/20', text: 'text-green-600 dark:text-green-400' },
  slate: { bg: 'bg-slate-500', lightBg: 'bg-slate-50 dark:bg-slate-500/20', text: 'text-slate-600 dark:text-slate-400' },
};

function getColorClasses(color: string) {
  return colorMap[color] ?? colorMap.slate;
}

// ==================== Tab Management ====================

const reportTabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'categories', label: 'Categories' },
  { key: 'accounts', label: 'Accounts' },
];

const activeTab = ref('overview');

const tabItems = computed(() => periodOptions.map(p => ({
  key: p.key,
  label: p.label,
})));
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- ==================== Header ==================== -->
    <PageHeader title="Financial Reports" subtitle="Analyze your income, expenses, and savings trends" />

    <!-- ==================== Period Selector ==================== -->
    <div class="card p-4">
      <Tabs
        :tabs="tabItems"
        :active-tab="activePeriod"
        @update:active-tab="activePeriod = ($event as PeriodKey)"
      />
    </div>

    <!-- ==================== Summary Stats ==================== -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Income"
        :value="formatCurrency(totalIncome)"
        icon="📈"
        color="accent"
      />
      <StatCard
        title="Total Expense"
        :value="formatCurrency(totalExpense)"
        icon="📉"
        color="danger"
      />
      <StatCard
        title="Total Savings"
        :value="formatCurrency(totalSavings)"
        :icon="totalSavings >= 0 ? '💵' : '⚠️'"
        :trend="totalSavings >= 0 ? 'up' : 'down'"
        :color="totalSavings >= 0 ? 'primary' : 'warning'"
      />
      <StatCard
        title="Savings Rate"
        :value="`${savingsRate.toFixed(1)}%`"
        :icon="savingsRate >= 20 ? '🎯' : '⚠️'"
        :trend="savingsRate >= 20 ? 'up' : 'neutral'"
        color="primary"
      />
    </div>

    <!-- ==================== Income vs Expense Chart ==================== -->
    <div class="card p-5">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-1">Income vs Expense</h2>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-6">Month-by-month comparison</p>

      <!-- Legend -->
      <div class="flex items-center gap-6 mb-4">
        <div class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded-sm bg-accent-500" />
          <span class="text-xs text-surface-500 dark:text-surface-400">Income</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded-sm bg-danger-500" />
          <span class="text-xs text-surface-500 dark:text-surface-400">Expense</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded-sm bg-primary-400" />
          <span class="text-xs text-surface-500 dark:text-surface-400">Savings</span>
        </div>
      </div>

      <!-- Bar Chart -->
      <div class="flex items-end gap-3 h-56">
        <div
          v-for="item in monthlyTrend"
          :key="item.month"
          class="flex-1 flex flex-col items-center gap-1"
        >
          <div class="flex items-end gap-0.5 w-full h-48">
            <div class="flex-1 flex flex-col justify-end h-full relative group">
              <div
                class="w-full bg-accent-500 dark:bg-accent-400 rounded-t-sm transition-all duration-500 min-h-[2px]"
                :style="{ height: `${(item.income / maxChartValue) * 100}%` }"
              />
              <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-900 dark:bg-surface-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                {{ formatCurrency(item.income) }}
              </div>
            </div>
            <div class="flex-1 flex flex-col justify-end h-full relative group">
              <div
                class="w-full bg-danger-500 dark:bg-danger-400 rounded-t-sm transition-all duration-500 min-h-[2px]"
                :style="{ height: `${(item.expense / maxChartValue) * 100}%` }"
              />
              <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-900 dark:bg-surface-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                {{ formatCurrency(item.expense) }}
              </div>
            </div>
            <div class="flex-1 flex flex-col justify-end h-full relative group">
              <div
                class="w-full bg-primary-400 dark:bg-primary-500 rounded-t-sm transition-all duration-500 min-h-[2px]"
                :style="{ height: `${(Math.max(item.savings, 0) / maxChartValue) * 100}%` }"
              />
              <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-900 dark:bg-surface-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                {{ formatCurrency(item.savings) }}
              </div>
            </div>
          </div>
          <span class="text-xs text-surface-500 dark:text-surface-400 font-medium whitespace-nowrap">{{ item.label.split(' ')[0] }}</span>
        </div>
      </div>
    </div>

    <!-- ==================== Section Tabs ==================== -->
    <div class="card">
      <div class="p-5 pb-0">
        <Tabs
          :tabs="reportTabs"
          :active-tab="activeTab"
          @update:active-tab="activeTab = $event"
        />
      </div>

      <!-- ==================== Monthly Trend Table ==================== -->
      <div v-show="activeTab === 'overview'" class="p-5">
        <h3 class="text-base font-semibold text-surface-900 dark:text-white mb-4">Monthly Trend</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-surface-200 dark:border-surface-700">
                <th class="text-left py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Month</th>
                <th class="text-right py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Income</th>
                <th class="text-right py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Expense</th>
                <th class="text-right py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Savings</th>
                <th class="text-right py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Savings Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in monthlyTrend.slice(-6)"
                :key="row.month"
                class="border-b border-surface-100 dark:border-surface-700/50 last:border-0"
              >
                <td class="py-3 px-2 font-medium text-surface-900 dark:text-white">{{ row.label }}</td>
                <td class="py-3 px-2 text-right tabular-nums text-accent-600 dark:text-accent-400">{{ formatCurrency(row.income) }}</td>
                <td class="py-3 px-2 text-right tabular-nums text-danger-500 dark:text-danger-400">{{ formatCurrency(row.expense) }}</td>
                <td class="py-3 px-2 text-right tabular-nums" :class="row.savings >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500 dark:text-danger-400'">
                  {{ row.savings >= 0 ? '+' : '' }}{{ formatCurrency(row.savings) }}
                </td>
                <td class="py-3 px-2 text-right">
                  <Badge
                    :variant="row.savingsRate >= 20 ? 'success' : row.savingsRate >= 0 ? 'warning' : 'danger'"
                    size="sm"
                  >
                    {{ row.savingsRate.toFixed(1) }}%
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ==================== Category Breakdown ==================== -->
      <div v-show="activeTab === 'categories'" class="p-5">
        <h3 class="text-base font-semibold text-surface-900 dark:text-white mb-4">Category Breakdown</h3>

        <div v-if="categoryBreakdown.length > 0" class="space-y-4">
          <div
            v-for="cat in categoryBreakdown"
            :key="cat.categoryId"
          >
            <div class="flex items-center justify-between mb-1.5">
              <div class="flex items-center gap-2">
                <span class="text-base">{{ cat.icon }}</span>
                <span class="text-sm font-medium text-surface-900 dark:text-white">{{ cat.name }}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-sm tabular-nums font-semibold text-surface-900 dark:text-white">{{ formatCurrency(cat.amount) }}</span>
                <span class="text-xs tabular-nums text-surface-500 dark:text-surface-400 w-12 text-right">{{ cat.percentage.toFixed(1) }}%</span>
              </div>
            </div>
            <div class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-2 overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="getColorClasses(cat.color).bg"
                :style="{ width: `${cat.percentage}%` }"
              />
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <p class="text-surface-400 dark:text-surface-500">No expenses found for this period</p>
        </div>
      </div>

      <!-- ==================== Bank Account Summary ==================== -->
      <div v-show="activeTab === 'accounts'" class="p-5">
        <h3 class="text-base font-semibold text-surface-900 dark:text-white mb-4">Bank Account Summary</h3>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-surface-200 dark:border-surface-700">
                <th class="text-left py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Account</th>
                <th class="text-right py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Balance</th>
                <th class="text-right py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Total Credits</th>
                <th class="text-right py-3 px-2 text-surface-500 dark:text-surface-400 font-medium">Total Debits</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="acct in accountSummaries"
                :key="acct.id"
                class="border-b border-surface-100 dark:border-surface-700/50 last:border-0"
              >
                <td class="py-3 px-2">
                  <div>
                    <p class="font-medium text-surface-900 dark:text-white">{{ acct.name }}</p>
                    <p class="text-xs text-surface-500 dark:text-surface-400">{{ acct.bankName }}</p>
                  </div>
                </td>
                <td class="py-3 px-2 text-right tabular-nums font-semibold text-surface-900 dark:text-white">
                  {{ formatCurrency(acct.balance) }}
                </td>
                <td class="py-3 px-2 text-right tabular-nums text-accent-600 dark:text-accent-400">
                  +{{ formatCurrency(acct.totalCredits) }}
                </td>
                <td class="py-3 px-2 text-right tabular-nums text-danger-500 dark:text-danger-400">
                  -{{ formatCurrency(acct.totalDebits) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ==================== Top Expenses ==================== -->
    <div class="card p-5">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-1">Top Expenses</h2>
      <p class="text-sm text-surface-500 dark:text-surface-400 mb-4">Highest individual expenses in selected period</p>

      <div v-if="topExpenses.length > 0" class="space-y-2">
        <div
          v-for="(exp, index) in topExpenses"
          :key="exp.id"
          class="flex items-center justify-between py-3 border-b border-surface-100 dark:border-surface-700/50 last:border-0"
        >
          <div class="flex items-center gap-3">
            <span class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold" :class="index < 3 ? 'bg-warning-50 dark:bg-warning-500/20 text-amber-700 dark:text-amber-400' : 'bg-surface-100 dark:bg-surface-700 text-surface-500 dark:text-surface-400'">
              {{ index + 1 }}
            </span>
            <div class="w-9 h-9 rounded-lg flex items-center justify-center text-base" :class="getColorClasses(exp.categoryColor).lightBg">
              {{ exp.categoryIcon }}
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-surface-900 dark:text-white truncate">{{ exp.description }}</p>
              <p class="text-xs text-surface-500 dark:text-surface-400 mt-0.5">{{ exp.categoryName }} · {{ formatDate(exp.date, 'short') }}</p>
            </div>
          </div>
          <p class="text-sm font-semibold tabular-nums text-danger-500 dark:text-danger-400 whitespace-nowrap ml-4">
            -{{ formatCurrency(exp.amount) }}
          </p>
        </div>
      </div>
      <div v-else class="text-center py-8">
        <p class="text-surface-400 dark:text-surface-500">No expenses found for this period</p>
      </div>
    </div>
  </div>
</template>
