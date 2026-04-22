<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLoanStore } from '../../stores/loan';
import type { Loan } from '../../types';
import { useBankStore } from '../../stores/bank';
import { useCurrencyStore } from '../../stores/currency';
import type { Currency } from '../../types';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, ProgressBar, Modal, DataTable, EmptyState } from '../ui';

const loanStore = useLoanStore();
const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ============ State ============
const selectedLoan = ref<Loan | null>(null);
const showDetailModal = ref(false);
const showRecordPaymentModal = ref(false);
const showAddLoanModal = ref(false);
const showConfirmCloseModal = ref(false);
const showEditLoanModal = ref(false);

const editLoanForm = ref({
  name: '',
  type: 'personal' as Loan['type'],
  lenderName: '',
  interestRate: 0,
  emiAmount: 0,
  currentBalance: 0,
  nextPaymentDate: '',
  status: 'active' as Loan['status'],
  currency: 'BDT' as Currency,
});

// ============ Form State ============
const paymentForm = ref({
  date: new Date().toISOString().split('T')[0],
  amount: 0,
  bankAccountId: '',
  paymentNumber: 1,
});

const addLoanForm = ref({
  name: '',
  type: 'personal' as Loan['type'],
  lenderName: '',
  principalAmount: 0,
  interestRate: 0,
  termMonths: 0,
  startDate: new Date().toISOString().split('T')[0],
  bankAccountId: '',
  emiAmount: 0,
  currency: 'BDT' as Currency,
});

// ============ Computed ============
const activeLoans = computed(() => loanStore.getActiveLoans());
const nextPayment = computed(() => {
  const loans = activeLoans.value;
  if (loans.length === 0) return null;
  return loans.reduce((nearest, loan) => {
    if (!nearest || new Date(loan.nextPaymentDate) < new Date(nearest.nextPaymentDate)) return loan;
    return nearest;
  }, loans[0] as Loan | null);
});

const paymentSchedule = computed(() => {
  if (!selectedLoan.value) return [];
  const loan = selectedLoan.value;
  const remaining = loan.totalInstallments - loan.paidInstallments;
  const schedule = [];
  for (let i = 1; i <= Math.min(remaining, 12); i++) {
    const d = new Date(loan.nextPaymentDate);
    d.setMonth(d.getMonth() + i - 1);
    schedule.push({
      installment: loan.paidInstallments + i,
      date: d.toISOString(),
      emi: loan.emiAmount,
      status: i === 1 ? 'upcoming' : 'scheduled',
    });
  }
  return schedule;
});

// ============ Helpers ============
const loanTypeLabel: Record<string, string> = {
  personal: 'Personal',
  home: 'Home',
  auto: 'Auto',
  education: 'Education',
  business: 'Business',
  other: 'Other',
};

const loanTypeIcon: Record<string, string> = {
  personal: '👤',
  home: '🏠',
  auto: '🚗',
  education: '🎓',
  business: '💼',
  other: '📋',
};

function statusBadge(status: Loan['status']): { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string } {
  switch (status) {
    case 'active': return { variant: 'success', label: 'Active' };
    case 'completed': return { variant: 'info', label: 'Completed' };
    case 'defaulted': return { variant: 'danger', label: 'Defaulted' };
    case 'paused': return { variant: 'warning', label: 'Paused' };
    default: return { variant: 'neutral', label: status };
  }
}

function remainingMonths(loan: Loan): number {
  return loan.totalInstallments - loan.paidInstallments;
}

// ============ Actions ============
function openDetail(loan: Loan) {
  selectedLoan.value = loan;
  showDetailModal.value = true;
}

function openRecordPayment(loan: Loan) {
  selectedLoan.value = loan;
  paymentForm.value = {
    date: new Date().toISOString().split('T')[0],
    amount: loan.emiAmount,
    bankAccountId: loan.bankAccountId || '',
    paymentNumber: loan.paidInstallments + 1,
  };
  showRecordPaymentModal.value = true;
}

function submitPayment() {
  if (!selectedLoan.value) return;
  const loan = selectedLoan.value;
  const newPaidAmount = loan.paidAmount + paymentForm.value.amount;
  const interestPortion = Math.round(loan.currentBalance * (loan.interestRate / 100 / 12));
  const principalPortion = paymentForm.value.amount - interestPortion;

  loanStore.updateLoan(loan.id, {
    paidAmount: newPaidAmount,
    paidInstallments: loan.paidInstallments + 1,
    currentBalance: Math.max(0, loan.currentBalance - principalPortion),
    nextPaymentDate: (() => {
      const d = new Date(loan.nextPaymentDate);
      d.setMonth(d.getMonth() + 1);
      return d.toISOString();
    })(),
  });
  showRecordPaymentModal.value = false;
  selectedLoan.value = loanStore.getLoanById(loan.id) || null;
}

function submitAddLoan() {
  const form = addLoanForm.value;
  loanStore.addLoan({
    name: form.name,
    type: form.type,
    lenderName: form.lenderName,
    principalAmount: form.principalAmount,
    currentBalance: form.principalAmount,
    interestRate: form.interestRate,
    termMonths: form.termMonths,
    emiAmount: form.emiAmount,
    startDate: new Date(form.startDate).toISOString(),
    nextPaymentDate: (() => {
      const d = new Date(form.startDate);
      d.setMonth(d.getMonth() + 1);
      return d.toISOString();
    })(),
    nextPaymentAmount: form.emiAmount,
    paidAmount: 0,
    paidInstallments: 0,
    totalInstallments: form.termMonths,
    status: 'active',
    bankAccountId: form.bankAccountId || undefined,
    currency: form.currency,
  });
  showAddLoanModal.value = false;
  addLoanForm.value = {
    name: '', type: 'personal', lenderName: '', principalAmount: 0,
    interestRate: 0, termMonths: 0, startDate: new Date().toISOString().split('T')[0],
    bankAccountId: '', emiAmount: 0, currency: 'BDT' as Currency,
  };
}

function closeLoan() {
  if (!selectedLoan.value) return;
  loanStore.updateLoan(selectedLoan.value.id, { status: 'completed' });
  showConfirmCloseModal.value = false;
  showDetailModal.value = false;
  selectedLoan.value = null;
}

function openEditLoan(loan: Loan) {
  selectedLoan.value = loan;
  editLoanForm.value = {
    name: loan.name,
    type: loan.type,
    lenderName: loan.lenderName,
    interestRate: loan.interestRate,
    emiAmount: loan.emiAmount,
    currentBalance: loan.currentBalance,
    nextPaymentDate: loan.nextPaymentDate.split('T')[0],
    status: loan.status,
    currency: loan.currency || 'BDT' as Currency,
  };
  showDetailModal.value = false;
  showEditLoanModal.value = true;
}

function submitEditLoan() {
  if (!selectedLoan.value) return;
  loanStore.updateLoan(selectedLoan.value.id, {
    name: editLoanForm.value.name,
    lenderName: editLoanForm.value.lenderName,
    interestRate: editLoanForm.value.interestRate,
    emiAmount: editLoanForm.value.emiAmount,
    currentBalance: editLoanForm.value.currentBalance,
    nextPaymentDate: new Date(editLoanForm.value.nextPaymentDate).toISOString(),
    nextPaymentAmount: editLoanForm.value.emiAmount,
    status: editLoanForm.value.status,
    currency: editLoanForm.value.currency,
  });
  showEditLoanModal.value = false;
  selectedLoan.value = loanStore.getLoanById(selectedLoan.value.id) || null;
}

function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') {
    return currencyStore.formatWithCurrency(amount, currency as Currency);
  }
  return formatCurrency(amount, 'BDT');
}

const scheduleColumns = [
  { key: 'installment', label: '#', align: 'center' as const, width: '60px' },
  { key: 'date', label: 'Date' },
  { key: 'emi', label: 'EMI Amount', align: 'right' as const },
  { key: 'status', label: 'Status', align: 'center' as const },
];
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Loans" subtitle="Track your loans and repayment schedules">
      <template #actions>
        <button class="btn-primary" @click="showAddLoanModal = true">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Add Loan
        </button>
      </template>
    </PageHeader>

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Debt"
        :value="fmtCur(loanStore.totalDebt)"
        icon="💰"
        color="danger"
        trend="down"
        :change="-8.5"
      />
      <StatCard
        title="Monthly EMI"
        :value="fmtCur(loanStore.totalMonthlyEMI)"
        icon="📅"
        color="warning"
      />
      <StatCard
        title="Active Loans"
        :value="String(loanStore.activeLoanCount)"
        icon="🏦"
        color="primary"
      />
      <StatCard
        title="Next Payment"
        :value="nextPayment ? fmtCur(nextPayment.nextPaymentAmount) : '—'"
        icon="⏰"
        color="accent"
      />
    </div>

    <!-- Active Loans Grid -->
    <div v-if="activeLoans.length === 0">
      <EmptyState icon="🏦" title="No active loans" description="Add your first loan to start tracking repayments.">
        <template #action>
          <button class="btn-primary" @click="showAddLoanModal = true">Add Loan</button>
        </template>
      </EmptyState>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="loan in activeLoans"
        :key="loan.id"
        class="card-hover p-5 cursor-pointer animate-fade-in"
        @click="openDetail(loan)"
      >
        <!-- Header -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-lg bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-xl">
              {{ loanTypeIcon[loan.type] || '📋' }}
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">{{ loan.name }}</h3>
              <p class="text-sm text-surface-500 dark:text-surface-400">{{ loan.lenderName }}</p>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <Badge :variant="statusBadge(loan.status).variant">{{ statusBadge(loan.status).label }}</Badge>
            <span v-if="loan.currency && loan.currency !== 'BDT'" class="text-[10px] px-1.5 py-0.5 bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 rounded font-medium ml-1">{{ loan.currency }}</span>
          </div>
        </div>

        <!-- Amounts -->
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Principal Amount</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(loan.principalAmount, loan.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Current Balance</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(loan.currentBalance, loan.currency) }}</p>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-surface-500 dark:text-surface-400">Payoff Progress</span>
            <span class="text-xs font-medium tabular-nums" :class="loan.paidAmount / loan.principalAmount > 0.5 ? 'text-accent-600' : 'text-surface-500'">
              {{ ((loan.paidAmount / loan.principalAmount) * 100).toFixed(1) }}%
            </span>
          </div>
          <div class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-2.5 overflow-hidden">
            <div
              class="h-2.5 rounded-full transition-all duration-500"
              :class="(loan.paidAmount / loan.principalAmount) > 0.5 ? 'bg-accent-500' : 'bg-primary-500'"
              :style="{ width: `${Math.min((loan.paidAmount / loan.principalAmount) * 100, 100)}%` }"
            />
          </div>
        </div>

        <!-- Details Row -->
        <div class="grid grid-cols-3 gap-2 text-center border-t border-surface-100 dark:border-surface-700 pt-3">
          <div>
            <p class="text-xs text-surface-400">Interest Rate</p>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ loan.interestRate }}% p.a.</p>
          </div>
          <div>
            <p class="text-xs text-surface-400">EMI Amount</p>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ fmtCur(loan.emiAmount, loan.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-400">Tenure Left</p>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ remainingMonths(loan) }} mo</p>
          </div>
        </div>

        <!-- Next Payment -->
        <div class="mt-3 flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2">
          <span class="text-xs text-surface-500 dark:text-surface-400">Next Payment</span>
          <span class="text-sm font-medium text-primary-600 dark:text-primary-400 tabular-nums">
            {{ fmtCur(loan.nextPaymentAmount, loan.currency) }} on {{ formatDate(loan.nextPaymentDate, 'short') }}
          </span>
        </div>
      </div>
    </div>

    <!-- ============ LOAN DETAIL MODAL ============ -->
    <Modal v-if="selectedLoan" :is-open="showDetailModal" title="Loan Details" size="xl" @close="showDetailModal = false">
      <div class="space-y-6" v-if="selectedLoan">
        <!-- Loan Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-2xl">
            {{ loanTypeIcon[selectedLoan.type] || '📋' }}
          </div>
          <div>
            <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedLoan.name }}</h3>
            <p class="text-surface-500 dark:text-surface-400">{{ selectedLoan.lenderName }} &middot; {{ loanTypeLabel[selectedLoan.type] }} Loan</p>
          </div>
          <div class="flex items-center gap-1">
            <Badge :variant="statusBadge(selectedLoan.status).variant" class="ml-auto">{{ statusBadge(selectedLoan.status).label }}</Badge>
            <span v-if="selectedLoan.currency && selectedLoan.currency !== 'BDT'" class="text-[10px] px-1.5 py-0.5 bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 rounded font-medium ml-1">{{ selectedLoan.currency }}</span>
          </div>
        </div>

        <!-- Info Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Principal Amount</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedLoan.principalAmount, selectedLoan.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Current Balance</p>
            <p class="font-semibold text-danger-500 tabular-nums">{{ fmtCur(selectedLoan.currentBalance, selectedLoan.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Paid So Far</p>
            <p class="font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(selectedLoan.paidAmount, selectedLoan.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Remaining</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedLoan.principalAmount - selectedLoan.paidAmount, selectedLoan.currency) }}</p>
          </div>
        </div>

        <!-- Progress -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Repayment Progress</h4>
          <ProgressBar
            :value="selectedLoan.paidAmount"
            :max="selectedLoan.principalAmount"
            color="primary"
            size="md"
          />
          <div class="flex justify-between mt-2 text-xs text-surface-500 dark:text-surface-400">
            <span>{{ selectedLoan.paidInstallments }} of {{ selectedLoan.totalInstallments }} installments paid</span>
            <span>{{ remainingMonths(selectedLoan) }} months remaining</span>
          </div>
        </div>

        <!-- Breakdown -->
        <div class="grid grid-cols-2 gap-4">
          <div class="card p-4">
            <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-2">Principal vs Interest</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-surface-500 dark:text-surface-400">Principal Component</span>
                <span class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(Math.round(selectedLoan.paidAmount * 0.7), selectedLoan.currency) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-surface-500 dark:text-surface-400">Interest Component</span>
                <span class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(Math.round(selectedLoan.paidAmount * 0.3), selectedLoan.currency) }}</span>
              </div>
            </div>
          </div>
          <div class="card p-4">
            <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-2">Loan Details</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-surface-500 dark:text-surface-400">Interest Rate</span>
                <span class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedLoan.interestRate }}% p.a.</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-surface-500 dark:text-surface-400">EMI Amount</span>
                <span class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedLoan.emiAmount, selectedLoan.currency) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-surface-500 dark:text-surface-400">Start Date</span>
                <span class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedLoan.startDate, 'long') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Payment Schedule -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Upcoming Payment Schedule</h4>
          <DataTable
            :columns="scheduleColumns"
            :data="paymentSchedule"
            empty-message="No upcoming payments"
          >
            <template #cell-date="{ value }">
              {{ formatDate(value, 'short') }}
            </template>
            <template #cell-emi="{ value }">
              {{ fmtCur(value, selectedLoan?.currency) }}
            </template>
            <template #cell-status="{ value }">
              <Badge :variant="value === 'upcoming' ? 'warning' : 'neutral'">
                {{ value === 'upcoming' ? 'Upcoming' : 'Scheduled' }}
              </Badge>
            </template>
          </DataTable>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-primary" @click="openRecordPayment(selectedLoan)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
            Record Payment
          </button>
          <button class="btn-secondary" @click="openEditLoan(selectedLoan!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button class="btn-danger" @click="showConfirmCloseModal = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            Close Loan
          </button>
        </div>
      </div>
    </Modal>

    <!-- ============ RECORD PAYMENT MODAL ============ -->
    <Modal :is-open="showRecordPaymentModal" title="Record Payment" size="sm" @close="showRecordPaymentModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Payment Date</label>
          <input v-model="paymentForm.date" type="date" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Amount ({{ selectedLoan?.currency || 'BDT' }})</label>
          <input v-model.number="paymentForm.amount" type="number" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Bank Account</label>
          <select v-model="paymentForm.bankAccountId" class="input-field">
            <option value="">Select Bank Account</option>
            <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Payment Number</label>
          <input v-model.number="paymentForm.paymentNumber" type="number" class="input-field tabular-nums" min="1" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showRecordPaymentModal = false">Cancel</button>
          <button class="btn-primary" @click="submitPayment">Record Payment</button>
        </div>
      </div>
    </Modal>

    <!-- ============ ADD LOAN MODAL ============ -->
    <Modal :is-open="showAddLoanModal" title="Add New Loan" size="lg" @close="showAddLoanModal = false">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Loan Name</label>
            <input v-model="addLoanForm.name" type="text" class="input-field" placeholder="e.g. Home Loan" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Loan Type</label>
            <select v-model="addLoanForm.type" class="input-field">
              <option value="personal">Personal</option>
              <option value="home">Home</option>
              <option value="auto">Auto</option>
              <option value="education">Education</option>
              <option value="business">Business</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Lender Name</label>
            <input v-model="addLoanForm.lenderName" type="text" class="input-field" placeholder="e.g. Sonali Bank" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Currency</label>
            <select v-model="addLoanForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Principal Amount</label>
            <input v-model.number="addLoanForm.principalAmount" type="number" class="input-field tabular-nums" placeholder="0" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Interest Rate (%)</label>
            <input v-model.number="addLoanForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Term (months)</label>
            <input v-model.number="addLoanForm.termMonths" type="number" class="input-field tabular-nums" placeholder="0" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Start Date</label>
            <input v-model="addLoanForm.startDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">EMI Amount</label>
            <input v-model.number="addLoanForm.emiAmount" type="number" class="input-field tabular-nums" placeholder="0" />
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Bank Account</label>
            <select v-model="addLoanForm.bankAccountId" class="input-field">
              <option value="">Select Bank Account</option>
              <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showAddLoanModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddLoan">Add Loan</button>
        </div>
      </div>
    </Modal>

    <!-- ============ CONFIRM CLOSE MODAL ============ -->
    <Modal :is-open="showConfirmCloseModal" title="Close Loan" size="sm" @close="showConfirmCloseModal = false">
      <div class="space-y-4">
        <div class="bg-warning-50 dark:bg-warning-500/10 border border-warning-400/30 rounded-lg p-4">
          <p class="text-sm text-amber-800 dark:text-amber-300">
            Are you sure you want to mark this loan as <strong>completed</strong>? This action will change the loan status but won't delete it.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showConfirmCloseModal = false">Cancel</button>
          <button class="btn-danger" @click="closeLoan">Yes, Close Loan</button>
        </div>
      </div>
    </Modal>

    <!-- ============ EDIT LOAN MODAL ============ -->
    <Modal :is-open="showEditLoanModal" title="Edit Loan" size="lg" @close="showEditLoanModal = false">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Loan Name</label>
            <input v-model="editLoanForm.name" type="text" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Lender Name</label>
            <input v-model="editLoanForm.lenderName" type="text" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Currency</label>
            <select v-model="editLoanForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Interest Rate (%)</label>
            <input v-model.number="editLoanForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">EMI Amount</label>
            <input v-model.number="editLoanForm.emiAmount" type="number" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Current Balance</label>
            <input v-model.number="editLoanForm.currentBalance" type="number" min="0" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Next Payment Date</label>
            <input v-model="editLoanForm.nextPaymentDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Status</label>
            <select v-model="editLoanForm.status" class="input-field">
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
              <option value="defaulted">Defaulted</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showEditLoanModal = false">Cancel</button>
          <button class="btn-primary" @click="submitEditLoan">Save Changes</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
