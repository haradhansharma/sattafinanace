<script setup lang="ts">
import { ref, computed } from 'vue';
import { useInvestmentStore } from '../../stores/investment';
import { useBankStore } from '../../stores/bank';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, ProgressBar, Modal, DataTable, EmptyState, Tabs } from '../ui';
import type { Investment, InvestmentCategory, InvestmentStatus, InvestmentTransactionType, Currency } from '../../types';

const investmentStore = useInvestmentStore();
const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ============ Tab State ============
type TabKey = 'all' | InvestmentCategory;
const activeTab = ref<TabKey>('all');
const tabItems = [
  { key: 'all', label: 'All', icon: '💼' },
  { key: 'fdr', label: 'FDR', icon: '🏦' },
  { key: 'dps', label: 'DPS', icon: '💰' },
  { key: 'sanchaypatra', label: 'Sanchaypatra', icon: '📜' },
  { key: 'stock', label: 'Stocks', icon: '📈' },
  { key: 'mutual_fund', label: 'Mutual Funds', icon: '📊' },
  { key: 'gold', label: 'Gold', icon: '🥇' },
  { key: 'bond', label: 'Bonds', icon: '📋' },
];

// ============ Modal State ============
const selectedInvestment = ref<Investment | null>(null);
const showDetailModal = ref(false);
const showAddModal = ref(false);
const showTransactionModal = ref(false);
const showEditModal = ref(false);
const showDeleteConfirm = ref(false);

// ============ Category & Status Config ============
const categoryConfig: Record<InvestmentCategory, { label: string; icon: string; color: string }> = {
  fdr: { label: 'FDR', icon: '🏦', color: 'primary' },
  dps: { label: 'DPS', icon: '💰', color: 'success' },
  sanchaypatra: { label: 'Sanchaypatra', icon: '📜', color: 'warning' },
  stock: { label: 'Stocks', icon: '📈', color: 'info' },
  mutual_fund: { label: 'Mutual Funds', icon: '📊', color: 'accent' },
  gold: { label: 'Gold', icon: '🥇', color: 'warning' },
  bond: { label: 'Bonds', icon: '📋', color: 'info' },
  other: { label: 'Other', icon: '💼', color: 'neutral' },
};

const statusConfig: Record<InvestmentStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  active: { variant: 'success', label: 'Active' },
  matured: { variant: 'info', label: 'Matured' },
  sold: { variant: 'warning', label: 'Sold' },
  redeemed: { variant: 'info', label: 'Redeemed' },
  closed: { variant: 'neutral', label: 'Closed' },
};

const compoundingLabels: Record<string, string> = {
  monthly: 'Monthly',
  quarterly: 'Quarterly',
  annually: 'Annually',
  at_maturity: 'At Maturity',
};

const transactionTypeLabels: Record<InvestmentTransactionType, string> = {
  buy: 'Buy',
  sell: 'Sell',
  dividend: 'Dividend',
  interest: 'Interest',
  deposit: 'Deposit',
  withdrawal: 'Withdrawal',
  bonus: 'Bonus',
  maturity: 'Maturity',
};

const txTypeBadgeVariant: Record<InvestmentTransactionType, 'success' | 'danger' | 'warning' | 'info' | 'neutral'> = {
  buy: 'info',
  sell: 'warning',
  dividend: 'success',
  interest: 'success',
  deposit: 'info',
  withdrawal: 'warning',
  bonus: 'success',
  maturity: 'info',
};

// ============ Transaction Type Options by Category ============
const transactionTypesByCategory: Record<string, InvestmentTransactionType[]> = {
  fdr: ['buy', 'interest', 'maturity'],
  dps: ['deposit', 'interest', 'maturity'],
  sanchaypatra: ['buy', 'interest', 'maturity'],
  stock: ['buy', 'sell', 'dividend', 'bonus'],
  mutual_fund: ['buy', 'sell', 'dividend'],
  gold: ['buy', 'sell', 'bonus'],
  bond: ['buy', 'interest', 'maturity'],
  other: ['buy', 'sell', 'dividend', 'interest'],
};

// ============ Helpers ============
function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') {
    return currencyStore.formatWithCurrency(amount, currency as Currency);
  }
  return formatCurrency(amount, 'BDT');
}

function isInterestBased(cat: InvestmentCategory): boolean {
  return ['fdr', 'dps', 'sanchaypatra', 'bond'].includes(cat);
}

function isUnitBased(cat: InvestmentCategory): boolean {
  return ['stock', 'mutual_fund', 'gold'].includes(cat);
}

function roi(inv: Investment): number {
  const totalCost = inv.investedAmount + (inv.totalDepositedSoFar || 0);
  if (totalCost === 0) return 0;
  return ((inv.currentValue + inv.totalReturns - totalCost) / totalCost) * 100;
}

function isGain(inv: Investment): boolean {
  const totalCost = inv.investedAmount + (inv.totalDepositedSoFar || 0);
  return (inv.currentValue + inv.totalReturns) >= totalCost;
}

// ============ Filtered Investments ============
const filteredInvestments = computed(() => {
  if (activeTab.value === 'all') return investmentStore.investments;
  return investmentStore.investmentsByCategory[activeTab.value as InvestmentCategory] || [];
});

const addButtonText = computed(() => {
  if (activeTab.value === 'all') return 'Add Investment';
  return `Add ${categoryConfig[activeTab.value as InvestmentCategory]?.label || 'Investment'}`;
});

// ============ Transaction Table Columns ============
const transactionColumns = [
  { key: 'date', label: 'Date', width: '110px' },
  { key: 'type', label: 'Type', width: '100px' },
  { key: 'amount', label: 'Amount', align: 'right' as const },
  { key: 'note', label: 'Note' },
];

// ============ Add Investment Form ============
const addForm = ref({
  name: '',
  category: 'fdr' as InvestmentCategory,
  institution: '',
  accountNumber: '',
  purchaseDate: new Date().toISOString().split('T')[0],
  maturityDate: '' as string,
  bankAccountId: '',
  currency: 'BDT' as Currency,
  notes: '',
  // Interest-based
  investedAmount: 0,
  interestRate: 0,
  compounding: 'annually' as 'monthly' | 'quarterly' | 'annually' | 'at_maturity',
  taxOnInterest: false,
  autoRenew: false,
  // DPS specific
  monthlyDepositAmount: 0,
  // Unit-based
  quantity: 0,
  buyPrice: 0,
  currentPrice: 0,
  // Stock specific
  stockSymbol: '',
  stockExchange: 'DSE' as 'DSE' | 'CSE' | 'NASDAQ' | 'NYSE' | 'other',
  dividendYield: 0,
  // Gold specific
  purity: '22k' as '18k' | '21k' | '22k' | '24k',
  weightGrams: 0,
});

// ============ Transaction Form ============
const txForm = ref({
  type: 'interest' as InvestmentTransactionType,
  amount: 0,
  date: new Date().toISOString().split('T')[0],
  note: '',
});

// ============ Edit Form ============
const editForm = ref({
  currentValue: 0,
  interestRate: 0,
  status: 'active' as InvestmentStatus,
  currentPrice: 0,
  currency: 'BDT' as Currency,
  notes: '',
});

// ============ Actions ============
function openDetail(inv: Investment) {
  selectedInvestment.value = inv;
  showDetailModal.value = true;
}

function openAddModal() {
  const cat = activeTab.value !== 'all' ? (activeTab.value as InvestmentCategory) : 'fdr';
  resetAddForm(cat);
  showAddModal.value = true;
}

function resetAddForm(category?: InvestmentCategory) {
  addForm.value = {
    name: '',
    category: category || 'fdr',
    institution: '',
    accountNumber: '',
    purchaseDate: new Date().toISOString().split('T')[0],
    maturityDate: '',
    bankAccountId: '',
    currency: 'BDT',
    notes: '',
    investedAmount: 0,
    interestRate: 0,
    compounding: 'annually',
    taxOnInterest: false,
    autoRenew: false,
    monthlyDepositAmount: 0,
    quantity: 0,
    buyPrice: 0,
    currentPrice: 0,
    stockSymbol: '',
    stockExchange: 'DSE',
    dividendYield: 0,
    purity: '22k',
    weightGrams: 0,
  };
}

function submitAddInvestment() {
  const form = addForm.value;
  const interest = isInterestBased(form.category);
  const unit = isUnitBased(form.category);

  const data: any = {
    name: form.name,
    category: form.category,
    institution: form.institution,
    accountNumber: form.accountNumber || undefined,
    purchaseDate: new Date(form.purchaseDate).toISOString(),
    maturityDate: form.maturityDate ? new Date(form.maturityDate).toISOString() : undefined,
    bankAccountId: form.bankAccountId || undefined,
    currency: form.currency,
    notes: form.notes || undefined,
    status: 'active' as InvestmentStatus,
    totalReturns: 0,
  };

  if (form.category === 'dps') {
    data.investedAmount = 0;
    data.currentValue = 0;
    data.monthlyDepositAmount = form.monthlyDepositAmount || undefined;
    data.totalDepositedSoFar = 0;
    data.depositCount = 0;
  } else if (unit) {
    data.investedAmount = form.quantity * form.buyPrice;
    data.currentValue = form.quantity * form.currentPrice;
    data.quantity = form.quantity || undefined;
    data.avgBuyPrice = form.buyPrice || undefined;
    data.currentUnitPrice = form.currentPrice || undefined;
  } else {
    data.investedAmount = form.investedAmount;
    data.currentValue = form.investedAmount;
  }

  if (interest) {
    data.interestRate = form.interestRate || undefined;
    data.compounding = form.compounding || undefined;
    data.taxOnInterest = form.taxOnInterest || undefined;
    data.autoRenew = form.autoRenew || undefined;
  }

  if (form.category === 'stock') {
    data.stockSymbol = form.stockSymbol || undefined;
    data.stockExchange = form.stockExchange || undefined;
    data.dividendYield = form.dividendYield || undefined;
  }

  if (form.category === 'gold') {
    data.purity = form.purity || undefined;
    data.weightGrams = form.weightGrams || undefined;
  }

  investmentStore.addInvestment(data);
  showAddModal.value = false;
}

function openTransactionModal(inv: Investment) {
  selectedInvestment.value = inv;
  const availableTypes = transactionTypesByCategory[inv.category] || ['buy', 'sell'];
  txForm.value = {
    type: availableTypes[0],
    amount: 0,
    date: new Date().toISOString().split('T')[0],
    note: '',
  };
  showTransactionModal.value = true;
}

function submitTransaction() {
  if (!selectedInvestment.value) return;
  investmentStore.addTransaction(selectedInvestment.value.id, {
    type: txForm.value.type,
    amount: txForm.value.amount,
    date: new Date(txForm.value.date).toISOString(),
    note: txForm.value.note || undefined,
  });
  showTransactionModal.value = false;
  selectedInvestment.value = investmentStore.getInvestmentById(selectedInvestment.value.id) || null;
}

function openEditModal(inv: Investment) {
  selectedInvestment.value = inv;
  editForm.value = {
    currentValue: inv.currentValue,
    interestRate: inv.interestRate || 0,
    status: inv.status,
    currentPrice: inv.currentUnitPrice || 0,
    currency: inv.currency || 'BDT',
    notes: inv.notes || '',
  };
  showDetailModal.value = false;
  showEditModal.value = true;
}

function submitEdit() {
  if (!selectedInvestment.value) return;
  const data: Partial<Investment> = {
    currentValue: editForm.value.currentValue,
    interestRate: editForm.value.interestRate || undefined,
    status: editForm.value.status,
    currency: editForm.value.currency,
    notes: editForm.value.notes || undefined,
  };
  if (isUnitBased(selectedInvestment.value.category)) {
    data.currentUnitPrice = editForm.value.currentPrice || undefined;
  }
  investmentStore.updateInvestment(selectedInvestment.value.id, data);
  showEditModal.value = false;
  selectedInvestment.value = investmentStore.getInvestmentById(selectedInvestment.value.id) || null;
}

function confirmDelete() {
  if (!selectedInvestment.value) return;
  investmentStore.deleteInvestment(selectedInvestment.value.id);
  showDeleteConfirm.value = false;
  showDetailModal.value = false;
  selectedInvestment.value = null;
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Investments &amp; Portfolio" subtitle="Track FDR, DPS, Sanchaypatra, stocks, gold, and more">
      <template #actions>
        <button class="btn-primary" @click="openAddModal">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          {{ addButtonText }}
        </button>
      </template>
    </PageHeader>

    <!-- Tabs -->
    <Tabs :tabs="tabItems" :active-tab="activeTab" @update:active-tab="(k: string) => activeTab = k as TabKey" />

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Total Invested" :value="fmtCur(investmentStore.totalInvested)" icon="💰" color="primary" />
      <StatCard title="Current Value" :value="fmtCur(investmentStore.totalCurrentValue)" icon="📊" color="primary" />
      <StatCard title="Total Returns" :value="fmtCur(investmentStore.totalReturns)" icon="📈" :color="investmentStore.totalReturns >= 0 ? 'accent' : 'danger'" />
      <StatCard title="Monthly Income" :value="fmtCur(investmentStore.totalMonthlyIncome)" icon="💵" color="accent" />
    </div>

    <!-- Empty State -->
    <div v-if="filteredInvestments.length === 0">
      <EmptyState
        :icon="activeTab === 'all' ? '💼' : (categoryConfig[activeTab as InvestmentCategory]?.icon || '💼')"
        :title="activeTab === 'all' ? 'No investments yet' : `No ${categoryConfig[activeTab as InvestmentCategory]?.label || ''} investments`"
        description="Add your first investment to start tracking your portfolio."
      >
        <template #action>
          <button class="btn-primary" @click="openAddModal">{{ addButtonText }}</button>
        </template>
      </EmptyState>
    </div>

    <!-- Investment Cards Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="inv in filteredInvestments"
        :key="inv.id"
        class="card-hover p-5 cursor-pointer animate-fade-in"
        @click="openDetail(inv)"
      >
        <!-- Header -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-lg flex items-center justify-center text-xl" :class="{
              'bg-primary-100 dark:bg-primary-500/20': categoryConfig[inv.category].color === 'primary',
              'bg-accent-100 dark:bg-accent-500/20': categoryConfig[inv.category].color === 'success',
              'bg-warning-50 dark:bg-warning-500/20': categoryConfig[inv.category].color === 'warning',
              'bg-info-100 dark:bg-info-500/20': categoryConfig[inv.category].color === 'info',
              'bg-surface-100 dark:bg-surface-700': categoryConfig[inv.category].color === 'neutral',
            }">
              {{ categoryConfig[inv.category].icon }}
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">{{ inv.name }}</h3>
              <p class="text-sm text-surface-500 dark:text-surface-400">{{ inv.institution }}</p>
            </div>
          </div>
          <Badge :variant="statusConfig[inv.status].variant">{{ statusConfig[inv.status].label }}</Badge>
        </div>

        <!-- Key Metrics: Interest-based -->
        <div v-if="isInterestBased(inv.category)" class="grid grid-cols-3 gap-3 mb-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Invested</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(inv.investedAmount, inv.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Current Value</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(inv.currentValue, inv.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Returns</p>
            <p class="text-sm font-semibold tabular-nums" :class="inv.totalReturns >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ fmtCur(inv.totalReturns, inv.currency) }}
            </p>
          </div>
        </div>

        <!-- Key Metrics: Unit-based -->
        <div v-else-if="isUnitBased(inv.category)" class="grid grid-cols-3 gap-3 mb-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Quantity</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ inv.quantity?.toLocaleString() }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Avg Buy</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(inv.avgBuyPrice || 0, inv.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Current Price</p>
            <p class="text-sm font-semibold tabular-nums" :class="(inv.currentUnitPrice || 0) >= (inv.avgBuyPrice || 0) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ fmtCur(inv.currentUnitPrice || 0, inv.currency) }}
            </p>
          </div>
        </div>

        <!-- Key Metrics: Other / fallback -->
        <div v-else class="grid grid-cols-3 gap-3 mb-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Invested</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(inv.investedAmount, inv.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Current Value</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(inv.currentValue, inv.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Returns</p>
            <p class="text-sm font-semibold tabular-nums" :class="inv.totalReturns >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ fmtCur(inv.totalReturns, inv.currency) }}
            </p>
          </div>
        </div>

        <!-- ROI Progress -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-surface-500 dark:text-surface-400">Return on Investment</span>
            <span class="text-xs font-medium tabular-nums" :class="roi(inv) >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ roi(inv) >= 0 ? '+' : '' }}{{ roi(inv).toFixed(1) }}%
            </span>
          </div>
          <ProgressBar
            :value="Math.max(0, inv.currentValue + inv.totalReturns)"
            :max="Math.max(1, inv.investedAmount + (inv.totalDepositedSoFar || 0))"
            :color="isGain(inv) ? 'accent' : 'danger'"
            size="sm"
          />
        </div>

        <!-- Bottom Info Bar -->
        <div class="flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2">
          <span v-if="inv.maturityDate" class="text-xs text-surface-500 dark:text-surface-400">
            Maturity: {{ formatDate(inv.maturityDate, 'short') }}
          </span>
          <span v-else-if="inv.category === 'dps' && inv.monthlyDepositAmount" class="text-xs text-surface-500 dark:text-surface-400">
            Monthly: {{ fmtCur(inv.monthlyDepositAmount, inv.currency) }}
          </span>
          <span v-else-if="inv.category === 'stock' && inv.dividendYield" class="text-xs text-surface-500 dark:text-surface-400">
            Div Yield: {{ inv.dividendYield }}%
          </span>
          <span v-else-if="inv.category === 'gold' && inv.weightGrams" class="text-xs text-surface-500 dark:text-surface-400">
            {{ inv.weightGrams }}g {{ inv.purity }}
          </span>
          <span v-else-if="inv.interestRate" class="text-xs text-surface-500 dark:text-surface-400">
            {{ inv.interestRate }}% p.a.
          </span>
          <span v-else class="text-xs text-surface-500 dark:text-surface-400">
            {{ categoryConfig[inv.category].label }}
          </span>
          <span class="text-sm font-medium tabular-nums" :class="isGain(inv) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
            {{ isGain(inv) ? '▲' : '▼' }}
            {{ fmtCur(Math.abs((inv.currentValue + inv.totalReturns) - (inv.investedAmount + (inv.totalDepositedSoFar || 0))), inv.currency) }}
          </span>
        </div>
      </div>
    </div>

    <!-- ======================== DETAIL MODAL ======================== -->
    <Modal v-if="selectedInvestment" :is-open="showDetailModal" title="Investment Details" size="xl" @close="showDetailModal = false">
      <div class="space-y-6" v-if="selectedInvestment">
        <!-- Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl" :class="{
            'bg-primary-100 dark:bg-primary-500/20': categoryConfig[selectedInvestment.category].color === 'primary',
            'bg-accent-100 dark:bg-accent-500/20': categoryConfig[selectedInvestment.category].color === 'success',
            'bg-warning-50 dark:bg-warning-500/20': categoryConfig[selectedInvestment.category].color === 'warning',
            'bg-info-100 dark:bg-info-500/20': categoryConfig[selectedInvestment.category].color === 'info',
            'bg-surface-100 dark:bg-surface-700': categoryConfig[selectedInvestment.category].color === 'neutral',
          }">
            {{ categoryConfig[selectedInvestment.category].icon }}
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedInvestment.name }}</h3>
            <p class="text-surface-500 dark:text-surface-400">
              {{ selectedInvestment.institution }}
              <span v-if="selectedInvestment.accountNumber" class="ml-1">&middot; {{ selectedInvestment.accountNumber }}</span>
            </p>
          </div>
          <Badge :variant="statusConfig[selectedInvestment.status].variant" class="ml-auto">
            {{ statusConfig[selectedInvestment.status].label }}
          </Badge>
        </div>

        <!-- Key Metrics Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Invested</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInvestment.investedAmount, selectedInvestment.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Current Value</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInvestment.currentValue, selectedInvestment.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Returns</p>
            <p class="font-semibold tabular-nums" :class="selectedInvestment.totalReturns >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ fmtCur(selectedInvestment.totalReturns, selectedInvestment.currency) }}
            </p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">ROI</p>
            <p class="font-semibold tabular-nums" :class="roi(selectedInvestment) >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ roi(selectedInvestment) >= 0 ? '+' : '' }}{{ roi(selectedInvestment).toFixed(1) }}%
            </p>
          </div>
        </div>

        <!-- FDR Details -->
        <div v-if="selectedInvestment.category === 'fdr'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">FDR Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Interest Rate</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.interestRate }}% p.a.</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Compounding</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ compoundingLabels[selectedInvestment.compounding || 'annually'] }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Maturity Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.maturityDate ? formatDate(selectedInvestment.maturityDate, 'long') : '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Tax on Interest</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.taxOnInterest ? 'Yes' : 'No' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Auto-Renew</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.autoRenew ? 'Yes' : 'No' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Purchase Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInvestment.purchaseDate, 'long') }}</p>
            </div>
          </div>
        </div>

        <!-- DPS Details -->
        <div v-if="selectedInvestment.category === 'dps'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">DPS Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Monthly Deposit</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInvestment.monthlyDepositAmount || 0, selectedInvestment.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Total Deposited</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInvestment.totalDepositedSoFar || 0, selectedInvestment.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Deposit Count</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.depositCount || 0 }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Interest Rate</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.interestRate || 0 }}% p.a.</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Compounding</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ compoundingLabels[selectedInvestment.compounding || 'annually'] }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Maturity Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.maturityDate ? formatDate(selectedInvestment.maturityDate, 'long') : '—' }}</p>
            </div>
          </div>
        </div>

        <!-- Sanchaypatra Details -->
        <div v-if="selectedInvestment.category === 'sanchaypatra'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Sanchaypatra Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Interest Rate</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.interestRate }}% p.a.</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Compounding</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ compoundingLabels[selectedInvestment.compounding || 'annually'] }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Tax on Interest</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.taxOnInterest ? 'Yes' : 'No' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Maturity Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.maturityDate ? formatDate(selectedInvestment.maturityDate, 'long') : '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Purchase Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInvestment.purchaseDate, 'long') }}</p>
            </div>
          </div>
        </div>

        <!-- Stock Details -->
        <div v-if="selectedInvestment.category === 'stock'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Stock Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Symbol</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.stockSymbol || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Exchange</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.stockExchange || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Quantity</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.quantity?.toLocaleString() || 0 }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Avg Buy Price</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInvestment.avgBuyPrice || 0, selectedInvestment.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Current Price</span>
              <p class="font-medium tabular-nums" :class="(selectedInvestment.currentUnitPrice || 0) >= (selectedInvestment.avgBuyPrice || 0) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
                {{ fmtCur(selectedInvestment.currentUnitPrice || 0, selectedInvestment.currency) }}
              </p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Dividend Yield</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.dividendYield || 0 }}%</p>
            </div>
          </div>
        </div>

        <!-- Gold Details -->
        <div v-if="selectedInvestment.category === 'gold'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Gold Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Purity</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.purity || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Weight</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.weightGrams || 0 }} grams</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Per Gram Price</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.weightGrams ? fmtCur(Math.round(selectedInvestment.currentValue / selectedInvestment.weightGrams), selectedInvestment.currency) : '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Quantity</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.quantity?.toLocaleString() || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Avg Buy / Unit</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInvestment.avgBuyPrice || 0, selectedInvestment.currency) }}</p>
            </div>
          </div>
        </div>

        <!-- Mutual Fund Details -->
        <div v-if="selectedInvestment.category === 'mutual_fund'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Mutual Fund Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Quantity (Units)</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.quantity?.toLocaleString() || 0 }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Avg Buy Price (NAV)</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInvestment.avgBuyPrice || 0, selectedInvestment.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Current NAV</span>
              <p class="font-medium tabular-nums" :class="(selectedInvestment.currentUnitPrice || 0) >= (selectedInvestment.avgBuyPrice || 0) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
                {{ fmtCur(selectedInvestment.currentUnitPrice || 0, selectedInvestment.currency) }}
              </p>
            </div>
          </div>
        </div>

        <!-- Bond Details -->
        <div v-if="selectedInvestment.category === 'bond'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Bond Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Interest Rate</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInvestment.interestRate }}% p.a.</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Compounding</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ compoundingLabels[selectedInvestment.compounding || 'annually'] }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Tax on Interest</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.taxOnInterest ? 'Yes' : 'No' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Maturity Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvestment.maturityDate ? formatDate(selectedInvestment.maturityDate, 'long') : '—' }}</p>
            </div>
          </div>
        </div>

        <!-- Progress -->
        <div>
          <ProgressBar
            :value="Math.max(0, selectedInvestment.currentValue + selectedInvestment.totalReturns)"
            :max="Math.max(1, selectedInvestment.investedAmount + (selectedInvestment.totalDepositedSoFar || 0))"
            :color="isGain(selectedInvestment) ? 'accent' : 'danger'"
            size="md"
          />
          <div class="flex justify-between mt-2 text-xs text-surface-500 dark:text-surface-400">
            <span>{{ fmtCur(selectedInvestment.currentValue + selectedInvestment.totalReturns, selectedInvestment.currency) }} total value</span>
            <span>{{ fmtCur(selectedInvestment.investedAmount + (selectedInvestment.totalDepositedSoFar || 0), selectedInvestment.currency) }} invested</span>
          </div>
        </div>

        <!-- Transaction History -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Transaction History</h4>
          <div class="max-h-64 overflow-y-auto">
            <DataTable
              :columns="transactionColumns"
              :data="[...selectedInvestment.transactions].reverse()"
              empty-message="No transactions yet"
            >
              <template #cell-date="{ value }">
                {{ formatDate(value, 'short') }}
              </template>
              <template #cell-type="{ value }">
                <Badge :variant="txTypeBadgeVariant[value as InvestmentTransactionType] || 'neutral'">
                  {{ transactionTypeLabels[value as InvestmentTransactionType] || value }}
                </Badge>
              </template>
              <template #cell-amount="{ value }">
                <span class="tabular-nums" :class="value >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
                  {{ fmtCur(value, selectedInvestment?.currency) }}
                </span>
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedInvestment.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedInvestment.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button v-if="selectedInvestment.status === 'active'" class="btn-primary" @click="openTransactionModal(selectedInvestment!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Record Transaction
          </button>
          <button class="btn-secondary" @click="openEditModal(selectedInvestment!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button class="btn-danger" @click="showDeleteConfirm = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            Delete
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== ADD INVESTMENT MODAL ======================== -->
    <Modal :is-open="showAddModal" title="Add Investment" size="xl" @close="showAddModal = false">
      <div class="space-y-5">
        <!-- Basic Details Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>{{ categoryConfig[addForm.category].icon }}</span> Basic Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Category</label>
              <select v-model="addForm.category" class="input-field">
                <option value="fdr">🏦 FDR</option>
                <option value="dps">💰 DPS</option>
                <option value="sanchaypatra">📜 Sanchaypatra</option>
                <option value="stock">📈 Stocks</option>
                <option value="mutual_fund">📊 Mutual Funds</option>
                <option value="gold">🥇 Gold</option>
                <option value="bond">📋 Bonds</option>
                <option value="other">💼 Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Investment Name</label>
              <input v-model="addForm.name" type="text" class="input-field" placeholder="e.g. Sonali Bank FDR" />
            </div>
            <div>
              <label class="field-label">Institution</label>
              <input v-model="addForm.institution" type="text" class="input-field" placeholder="e.g. Sonali Bank" />
            </div>
            <div>
              <label class="field-label">Account Number</label>
              <input v-model="addForm.accountNumber" type="text" class="input-field" placeholder="Optional" />
            </div>
            <div>
              <label class="field-label">Purchase Date</label>
              <input v-model="addForm.purchaseDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Maturity Date (optional)</label>
              <input v-model="addForm.maturityDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Currency</label>
              <select v-model="addForm.currency" class="input-field">
                <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
              </select>
            </div>
            <div>
              <label class="field-label">Bank Account</label>
              <select v-model="addForm.bankAccountId" class="input-field">
                <option value="">Select Bank Account</option>
                <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Interest-based Fields -->
        <div v-if="isInterestBased(addForm.category)">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>💵</span> Interest Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-if="addForm.category !== 'dps'">
              <label class="field-label">Invested Amount</label>
              <input v-model.number="addForm.investedAmount" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Interest Rate (%)</label>
              <input v-model.number="addForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Compounding</label>
              <select v-model="addForm.compounding" class="input-field">
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="annually">Annually</option>
                <option value="at_maturity">At Maturity</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <input v-model="addForm.taxOnInterest" type="checkbox" id="taxOnInterest" class="w-4 h-4 rounded border-surface-300 text-primary-500 focus:ring-primary-500" />
              <label for="taxOnInterest" class="text-sm font-medium text-surface-700 dark:text-surface-300">Tax on Interest</label>
            </div>
            <div v-if="addForm.category !== 'dps'" class="flex items-center gap-2">
              <input v-model="addForm.autoRenew" type="checkbox" id="autoRenew" class="w-4 h-4 rounded border-surface-300 text-primary-500 focus:ring-primary-500" />
              <label for="autoRenew" class="text-sm font-medium text-surface-700 dark:text-surface-300">Auto-Renew</label>
            </div>
          </div>
        </div>

        <!-- DPS Specific Fields -->
        <div v-if="addForm.category === 'dps'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>💰</span> DPS Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Monthly Deposit Amount</label>
              <input v-model.number="addForm.monthlyDepositAmount" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
          </div>
        </div>

        <!-- Unit-based Fields -->
        <div v-if="isUnitBased(addForm.category)">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>{{ categoryConfig[addForm.category].icon }}</span> Unit Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Quantity</label>
              <input v-model.number="addForm.quantity" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Buy Price (per unit)</label>
              <input v-model.number="addForm.buyPrice" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Current Price (per unit)</label>
              <input v-model.number="addForm.currentPrice" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
          </div>
        </div>

        <!-- Stock Specific Fields -->
        <div v-if="addForm.category === 'stock'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>📈</span> Stock Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Stock Symbol</label>
              <input v-model="addForm.stockSymbol" type="text" class="input-field" placeholder="e.g. Grameenphone" />
            </div>
            <div>
              <label class="field-label">Stock Exchange</label>
              <select v-model="addForm.stockExchange" class="input-field">
                <option value="DSE">DSE</option>
                <option value="CSE">CSE</option>
                <option value="NASDAQ">NASDAQ</option>
                <option value="NYSE">NYSE</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Dividend Yield (%)</label>
              <input v-model.number="addForm.dividendYield" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
            </div>
          </div>
        </div>

        <!-- Gold Specific Fields -->
        <div v-if="addForm.category === 'gold'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>🥇</span> Gold Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Purity</label>
              <select v-model="addForm.purity" class="input-field">
                <option value="18k">18 Karat</option>
                <option value="21k">21 Karat</option>
                <option value="22k">22 Karat</option>
                <option value="24k">24 Karat</option>
              </select>
            </div>
            <div>
              <label class="field-label">Weight (grams)</label>
              <input v-model.number="addForm.weightGrams" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="addForm.notes" rows="2" placeholder="Additional notes..." class="input-field resize-none"></textarea>
        </div>

        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showAddModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddInvestment">Add Investment</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== RECORD TRANSACTION MODAL ======================== -->
    <Modal v-if="selectedInvestment" :is-open="showTransactionModal" title="Record Transaction" size="sm" @close="showTransactionModal = false">
      <div class="space-y-4">
        <div>
          <label class="field-label">Transaction Type</label>
          <select v-model="txForm.type" class="input-field">
            <option
              v-for="t in (transactionTypesByCategory[selectedInvestment.category] || ['buy', 'sell'])"
              :key="t"
              :value="t"
            >
              {{ transactionTypeLabels[t] }}
            </option>
          </select>
        </div>
        <div>
          <label class="field-label">Amount ({{ selectedInvestment.currency || 'BDT' }})</label>
          <input v-model.number="txForm.amount" type="number" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div>
          <label class="field-label">Date</label>
          <input v-model="txForm.date" type="date" class="input-field" />
        </div>
        <div>
          <label class="field-label">Note</label>
          <input v-model="txForm.note" type="text" class="input-field" placeholder="Optional note" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showTransactionModal = false">Cancel</button>
          <button class="btn-primary" @click="submitTransaction">Record Transaction</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== EDIT INVESTMENT MODAL ======================== -->
    <Modal v-if="selectedInvestment" :is-open="showEditModal" title="Edit Investment" size="md" @close="showEditModal = false">
      <div class="space-y-4">
        <div>
          <label class="field-label">Current Value ({{ editForm.currency }})</label>
          <input v-model.number="editForm.currentValue" type="number" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div v-if="isInterestBased(selectedInvestment.category)">
          <label class="field-label">Interest Rate (%)</label>
          <input v-model.number="editForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div v-if="isUnitBased(selectedInvestment.category)">
          <label class="field-label">Current Unit Price ({{ editForm.currency }})</label>
          <input v-model.number="editForm.currentPrice" type="number" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div>
          <label class="field-label">Currency</label>
          <select v-model="editForm.currency" class="input-field">
            <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
          </select>
        </div>
        <div>
          <label class="field-label">Status</label>
          <select v-model="editForm.status" class="input-field">
            <option value="active">Active</option>
            <option value="matured">Matured</option>
            <option value="sold">Sold</option>
            <option value="redeemed">Redeemed</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="editForm.notes" rows="2" placeholder="Additional notes..." class="input-field resize-none"></textarea>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showEditModal = false">Cancel</button>
          <button class="btn-primary" @click="submitEdit">Save Changes</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== DELETE CONFIRM MODAL ======================== -->
    <Modal :is-open="showDeleteConfirm" title="Delete Investment" size="sm" @close="showDeleteConfirm = false">
      <div class="space-y-4">
        <div class="bg-danger-50 dark:bg-danger-500/10 rounded-lg p-4">
          <p class="text-sm text-danger-700 dark:text-danger-400">
            Are you sure you want to delete <strong>{{ selectedInvestment?.name }}</strong>? This action cannot be undone. All transaction history will be permanently removed.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
          <button class="btn-danger" @click="confirmDelete">Delete Investment</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
