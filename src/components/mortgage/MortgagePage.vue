<script setup lang="ts">
import { ref, computed } from 'vue';
import { useMortgageStore } from '../../stores/mortgage';
import { useBankStore } from '../../stores/bank';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate, generateId } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, ProgressBar, Modal, DataTable, EmptyState, Tabs } from '../ui';
import type { Mortgage, MortgageProperty, MortgageStatus, Currency, AmortizationEntry, HeldMortgage, HeldMortgageStatus, HeldMortgageCollateral } from '../../types';

const mortgageStore = useMortgageStore();
const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ============ Tab State ============
type TabKey = 'my_mortgages' | 'held_mortgages';
const activeTab = ref<TabKey>('my_mortgages');
const tabItems = [
  { key: 'my_mortgages', label: 'My Mortgages', icon: '🏠' },
  { key: 'held_mortgages', label: 'Mortgages I Hold', icon: '🏘️' },
];

// ============ My Mortgage State ============
const selectedMortgage = ref<Mortgage | null>(null);
const showDetailModal = ref(false);
const showRecordPaymentModal = ref(false);
const showAddMortgageModal = ref(false);
const showConfirmCloseModal = ref(false);
const showEditMortgageModal = ref(false);

// ============ Held Mortgage State ============
const selectedHeldMortgage = ref<HeldMortgage | null>(null);
const showHeldDetailModal = ref(false);
const showHeldRecordPaymentModal = ref(false);
const showAddHeldMortgageModal = ref(false);
const showHeldEditModal = ref(false);
const showHeldConfirmCloseModal = ref(false);
const showHeldConfirmForecloseModal = ref(false);

// ============ My Mortgage Form State ============
const paymentForm = ref({
  date: new Date().toISOString().split('T')[0],
  amount: 0,
});

const addMortgageForm = ref({
  propertyName: '',
  propertyType: 'apartment' as MortgageProperty['propertyType'],
  address: '',
  sizeSqft: undefined as number | undefined,
  purchasePrice: 0,
  currentMarketValue: undefined as number | undefined,
  purchaseDate: new Date().toISOString().split('T')[0],
  lenderName: '',
  loanAmount: 0,
  downPayment: 0,
  interestRate: 0,
  interestType: 'fixed' as 'fixed' | 'variable',
  termMonths: 0,
  emiAmount: 0,
  startDate: new Date().toISOString().split('T')[0],
  bankAccountId: '',
  propertyTaxAnnual: 0,
  insuranceAnnual: 0,
  currency: 'BDT' as Currency,
  notes: '',
});

const editMortgageForm = ref({
  lenderName: '',
  interestRate: 0,
  currentBalance: 0,
  nextPaymentDate: '',
  status: 'active' as MortgageStatus,
  currentMarketValue: undefined as number | undefined,
  currency: 'BDT' as Currency,
  notes: '',
});

// ============ Held Mortgage Form State ============
const heldPaymentForm = ref({
  amount: 0,
  note: '',
});

const addHeldForm = ref({
  borrowerName: '',
  borrowerPhone: '',
  borrowerEmail: '',
  borrowerAddress: '',
  relationship: 'family' as HeldMortgage['relationship'],
  collateralName: '',
  collateralType: 'apartment' as HeldMortgageCollateral['propertyType'],
  collateralAddress: '',
  collateralSizeSqft: undefined as number | undefined,
  appraisedValue: 0,
  currentValue: 0,
  collateralDocuments: '',
  loanAmount: 0,
  interestRate: 0,
  interestType: 'fixed' as 'fixed' | 'variable',
  termMonths: 0,
  expectedMonthlyPayment: 0,
  startDate: new Date().toISOString().split('T')[0],
  bankAccountId: '',
  latePaymentPenaltyRate: 2,
  gracePeriodDays: 10,
  currency: 'BDT' as Currency,
  notes: '',
});

const editHeldForm = ref({
  borrowerName: '',
  interestRate: 0,
  currentBalance: 0,
  nextPaymentDueDate: '',
  status: 'active' as HeldMortgageStatus,
  currentValue: 0,
  currency: 'BDT' as Currency,
  notes: '',
});

// ============ Helpers ============
const propertyTypeIcon: Record<string, string> = {
  apartment: '🏠',
  house: '🏡',
  land: '🏗️',
  commercial: '🏢',
  condo: '🏘️',
};

const propertyTypeLabel: Record<string, string> = {
  apartment: 'Apartment',
  house: 'House',
  land: 'Land',
  commercial: 'Commercial',
  condo: 'Condo',
};

const relationshipIcon: Record<string, string> = {
  family: '👨‍👩‍👧',
  friend: '🤝',
  business: '💼',
  colleague: '👔',
  other: '👤',
};

const relationshipLabel: Record<string, string> = {
  family: 'Family',
  friend: 'Friend',
  business: 'Business',
  colleague: 'Colleague',
  other: 'Other',
};

function statusBadge(status: MortgageStatus): { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string } {
  switch (status) {
    case 'active': return { variant: 'success', label: 'Active' };
    case 'completed': return { variant: 'info', label: 'Completed' };
    case 'defaulted': return { variant: 'danger', label: 'Defaulted' };
    case 'paused': return { variant: 'warning', label: 'Paused' };
    case 'in_review': return { variant: 'warning', label: 'In Review' };
    default: return { variant: 'neutral', label: status };
  }
}

function heldStatusBadge(status: HeldMortgageStatus): { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string } {
  switch (status) {
    case 'active': return { variant: 'success', label: 'Active' };
    case 'completed': return { variant: 'info', label: 'Completed' };
    case 'defaulted': return { variant: 'danger', label: 'Defaulted' };
    case 'foreclosed': return { variant: 'danger', label: 'Foreclosed' };
    case 'paused': return { variant: 'warning', label: 'Paused' };
    case 'in_review': return { variant: 'warning', label: 'In Review' };
    default: return { variant: 'neutral', label: status };
  }
}

function remainingMonths(m: Mortgage): number {
  return m.totalInstallments - m.paidInstallments;
}

function payoffPercent(m: Mortgage): number {
  if (m.loanAmount - m.downPayment === 0) return 100;
  return Math.min(100, (m.paidAmount / (m.loanAmount - m.downPayment)) * 100);
}

function appreciationPercent(m: Mortgage): number {
  if (!m.property.currentMarketValue || m.property.purchasePrice === 0) return 0;
  return ((m.property.currentMarketValue - m.property.purchasePrice) / m.property.purchasePrice) * 100;
}

function heldRemainingMonths(hm: HeldMortgage): number {
  return hm.totalInstallments - hm.receivedInstallments;
}

function heldPayoffPercent(hm: HeldMortgage): number {
  if (hm.loanAmount === 0) return 100;
  return Math.min(100, (hm.totalReceivedAmount / hm.loanAmount) * 100);
}

function heldCollateralCoverage(hm: HeldMortgage): number {
  if (hm.collateral.currentValue === 0) return 0;
  return (hm.currentBalance / hm.collateral.currentValue) * 100;
}

function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') {
    return currencyStore.formatWithCurrency(amount, currency as Currency);
  }
  return formatCurrency(amount, 'BDT');
}

// ============ My Mortgage Amortization ============
const amortizationSchedule = computed<AmortizationEntry[]>(() => {
  if (!selectedMortgage.value) return [];
  const full = mortgageStore.generateAmortizationSchedule(selectedMortgage.value);
  const start = selectedMortgage.value.paidInstallments;
  return full.slice(start, start + 24);
});

const amortColumns = [
  { key: 'installment', label: '#', align: 'center' as const, width: '70px' },
  { key: 'date', label: 'Date' },
  { key: 'emiAmount', label: 'EMI', align: 'right' as const },
  { key: 'principalComponent', label: 'Principal', align: 'right' as const },
  { key: 'interestComponent', label: 'Interest', align: 'right' as const },
  { key: 'remainingBalance', label: 'Balance', align: 'right' as const },
];

// ============ Held Mortgage Amortization ============
const heldAmortizationSchedule = computed<AmortizationEntry[]>(() => {
  if (!selectedHeldMortgage.value) return [];
  const full = mortgageStore.generateHeldAmortizationSchedule(selectedHeldMortgage.value);
  const start = selectedHeldMortgage.value.receivedInstallments;
  return full.slice(start, start + 24);
});

const heldAmortColumns = [
  { key: 'installment', label: '#', align: 'center' as const, width: '70px' },
  { key: 'date', label: 'Date' },
  { key: 'emiAmount', label: 'Payment', align: 'right' as const },
  { key: 'principalComponent', label: 'Principal', align: 'right' as const },
  { key: 'interestComponent', label: 'Interest', align: 'right' as const },
  { key: 'remainingBalance', label: 'Balance', align: 'right' as const },
];

// Held payment history columns
const heldPaymentColumns = [
  { key: 'paymentNumber', label: '#', align: 'center' as const, width: '70px' },
  { key: 'paymentDate', label: 'Date' },
  { key: 'amount', label: 'Amount', align: 'right' as const },
  { key: 'principalComponent', label: 'Principal', align: 'right' as const },
  { key: 'interestComponent', label: 'Interest', align: 'right' as const },
  { key: 'note', label: 'Note' },
];

// ============ My Mortgage Actions ============
function openDetail(mortgage: Mortgage) {
  selectedMortgage.value = mortgage;
  showDetailModal.value = true;
}

function openRecordPayment(mortgage: Mortgage) {
  selectedMortgage.value = mortgage;
  paymentForm.value = {
    date: new Date().toISOString().split('T')[0],
    amount: mortgage.emiAmount,
  };
  showRecordPaymentModal.value = true;
}

function submitPayment() {
  if (!selectedMortgage.value) return;
  mortgageStore.recordPayment(selectedMortgage.value.id, paymentForm.value.amount);
  showRecordPaymentModal.value = false;
  selectedMortgage.value = mortgageStore.getMortgageById(selectedMortgage.value.id) || null;
}

function submitAddMortgage() {
  const form = addMortgageForm.value;
  const downPaymentPercent = form.purchasePrice > 0 ? (form.downPayment / form.purchasePrice) * 100 : 0;
  const nextPayment = new Date(form.startDate);
  nextPayment.setMonth(nextPayment.getMonth() + 1);

  mortgageStore.addMortgage({
    property: {
      name: form.propertyName,
      propertyType: form.propertyType,
      address: form.address,
      sizeSqft: form.sizeSqft,
      purchasePrice: form.purchasePrice,
      currentMarketValue: form.currentMarketValue || form.purchasePrice,
      purchaseDate: form.purchaseDate,
    },
    lenderName: form.lenderName,
    loanAmount: form.loanAmount,
    downPayment: form.downPayment,
    downPaymentPercent: Math.round(downPaymentPercent * 10) / 10,
    currentBalance: form.loanAmount - form.downPayment,
    interestRate: form.interestRate,
    interestType: form.interestType,
    termMonths: form.termMonths,
    emiAmount: form.emiAmount,
    startDate: new Date(form.startDate).toISOString(),
    nextPaymentDate: nextPayment.toISOString(),
    paidAmount: 0,
    paidInstallments: 0,
    totalInstallments: form.termMonths,
    status: 'active',
    escrow: {
      propertyTaxAnnual: form.propertyTaxAnnual,
      insuranceAnnual: form.insuranceAnnual,
      monthlyEscrow: Math.round((form.propertyTaxAnnual + form.insuranceAnnual) / 12),
    },
    bankAccountId: form.bankAccountId || undefined,
    currency: form.currency,
    notes: form.notes || undefined,
  });
  showAddMortgageModal.value = false;
  resetAddForm();
}

function resetAddForm() {
  addMortgageForm.value = {
    propertyName: '',
    propertyType: 'apartment',
    address: '',
    sizeSqft: undefined,
    purchasePrice: 0,
    currentMarketValue: undefined,
    purchaseDate: new Date().toISOString().split('T')[0],
    lenderName: '',
    loanAmount: 0,
    downPayment: 0,
    interestRate: 0,
    interestType: 'fixed',
    termMonths: 0,
    emiAmount: 0,
    startDate: new Date().toISOString().split('T')[0],
    bankAccountId: '',
    propertyTaxAnnual: 0,
    insuranceAnnual: 0,
    currency: 'BDT',
    notes: '',
  };
}

function closeMortgage() {
  if (!selectedMortgage.value) return;
  mortgageStore.updateMortgage(selectedMortgage.value.id, { status: 'completed' });
  showConfirmCloseModal.value = false;
  showDetailModal.value = false;
  selectedMortgage.value = null;
}

function openEditMortgage(mortgage: Mortgage) {
  selectedMortgage.value = mortgage;
  editMortgageForm.value = {
    lenderName: mortgage.lenderName,
    interestRate: mortgage.interestRate,
    currentBalance: mortgage.currentBalance,
    nextPaymentDate: mortgage.nextPaymentDate.split('T')[0],
    status: mortgage.status,
    currentMarketValue: mortgage.property.currentMarketValue,
    currency: mortgage.currency || 'BDT',
    notes: mortgage.notes || '',
  };
  showDetailModal.value = false;
  showEditMortgageModal.value = true;
}

function submitEditMortgage() {
  if (!selectedMortgage.value) return;
  const m = selectedMortgage.value;
  mortgageStore.updateMortgage(m.id, {
    lenderName: editMortgageForm.value.lenderName,
    interestRate: editMortgageForm.value.interestRate,
    currentBalance: editMortgageForm.value.currentBalance,
    nextPaymentDate: new Date(editMortgageForm.value.nextPaymentDate).toISOString(),
    status: editMortgageForm.value.status,
    currency: editMortgageForm.value.currency,
    notes: editMortgageForm.value.notes || undefined,
    property: {
      ...m.property,
      currentMarketValue: editMortgageForm.value.currentMarketValue,
    },
  });
  showEditMortgageModal.value = false;
  selectedMortgage.value = mortgageStore.getMortgageById(m.id) || null;
}

function computedDownPaymentPercent(): number {
  const form = addMortgageForm.value;
  if (form.purchasePrice === 0) return 0;
  return Math.round((form.downPayment / form.purchasePrice) * 100 * 10) / 10;
}

function computedMonthlyEscrow(): number {
  return Math.round((addMortgageForm.value.propertyTaxAnnual + addMortgageForm.value.insuranceAnnual) / 12);
}

// ============ Held Mortgage Actions ============
function openHeldDetail(hm: HeldMortgage) {
  selectedHeldMortgage.value = hm;
  showHeldDetailModal.value = true;
}

function openHeldRecordPayment(hm: HeldMortgage) {
  selectedHeldMortgage.value = hm;
  heldPaymentForm.value = {
    amount: hm.expectedMonthlyPayment,
    note: '',
  };
  showHeldRecordPaymentModal.value = true;
}

function submitHeldPayment() {
  if (!selectedHeldMortgage.value) return;
  mortgageStore.recordHeldPayment(selectedHeldMortgage.value.id, heldPaymentForm.value.amount, heldPaymentForm.value.note || undefined);
  showHeldRecordPaymentModal.value = false;
  selectedHeldMortgage.value = mortgageStore.getHeldMortgageById(selectedHeldMortgage.value.id) || null;
}

function openAddHeldMortgage() {
  resetAddHeldForm();
  showAddHeldMortgageModal.value = true;
}

function submitAddHeldMortgage() {
  const form = addHeldForm.value;
  const nextDue = new Date(form.startDate);
  nextDue.setMonth(nextDue.getMonth() + 1);

  mortgageStore.addHeldMortgage({
    borrowerName: form.borrowerName,
    borrowerPhone: form.borrowerPhone || undefined,
    borrowerEmail: form.borrowerEmail || undefined,
    borrowerAddress: form.borrowerAddress || undefined,
    relationship: form.relationship,
    collateral: {
      name: form.collateralName,
      propertyType: form.collateralType,
      address: form.collateralAddress,
      sizeSqft: form.collateralSizeSqft,
      appraisedValue: form.appraisedValue,
      currentValue: form.currentValue || form.appraisedValue,
      documents: form.collateralDocuments || undefined,
    },
    loanAmount: form.loanAmount,
    currentBalance: form.loanAmount,
    interestRate: form.interestRate,
    interestType: form.interestType,
    termMonths: form.termMonths,
    expectedMonthlyPayment: form.expectedMonthlyPayment,
    startDate: new Date(form.startDate).toISOString(),
    nextPaymentDueDate: nextDue.toISOString(),
    totalReceivedAmount: 0,
    totalInterestEarned: 0,
    receivedInstallments: 0,
    totalInstallments: form.termMonths,
    status: 'active',
    latePaymentPenaltyRate: form.latePaymentPenaltyRate,
    gracePeriodDays: form.gracePeriodDays,
    bankAccountId: form.bankAccountId || undefined,
    currency: form.currency,
    notes: form.notes || undefined,
  });
  showAddHeldMortgageModal.value = false;
}

function resetAddHeldForm() {
  addHeldForm.value = {
    borrowerName: '',
    borrowerPhone: '',
    borrowerEmail: '',
    borrowerAddress: '',
    relationship: 'family',
    collateralName: '',
    collateralType: 'apartment',
    collateralAddress: '',
    collateralSizeSqft: undefined,
    appraisedValue: 0,
    currentValue: 0,
    collateralDocuments: '',
    loanAmount: 0,
    interestRate: 0,
    interestType: 'fixed',
    termMonths: 0,
    expectedMonthlyPayment: 0,
    startDate: new Date().toISOString().split('T')[0],
    bankAccountId: '',
    latePaymentPenaltyRate: 2,
    gracePeriodDays: 10,
    currency: 'BDT',
    notes: '',
  };
}

function openEditHeldMortgage(hm: HeldMortgage) {
  selectedHeldMortgage.value = hm;
  editHeldForm.value = {
    borrowerName: hm.borrowerName,
    interestRate: hm.interestRate,
    currentBalance: hm.currentBalance,
    nextPaymentDueDate: hm.nextPaymentDueDate.split('T')[0],
    status: hm.status,
    currentValue: hm.collateral.currentValue,
    currency: hm.currency || 'BDT',
    notes: hm.notes || '',
  };
  showHeldDetailModal.value = false;
  showHeldEditModal.value = true;
}

function submitEditHeldMortgage() {
  if (!selectedHeldMortgage.value) return;
  const hm = selectedHeldMortgage.value;
  mortgageStore.updateHeldMortgage(hm.id, {
    borrowerName: editHeldForm.value.borrowerName,
    interestRate: editHeldForm.value.interestRate,
    currentBalance: editHeldForm.value.currentBalance,
    nextPaymentDueDate: new Date(editHeldForm.value.nextPaymentDueDate).toISOString(),
    status: editHeldForm.value.status,
    currency: editHeldForm.value.currency,
    notes: editHeldForm.value.notes || undefined,
    collateral: {
      ...hm.collateral,
      currentValue: editHeldForm.value.currentValue,
    },
  });
  showHeldEditModal.value = false;
  selectedHeldMortgage.value = mortgageStore.getHeldMortgageById(hm.id) || null;
}

function completeHeldMortgage() {
  if (!selectedHeldMortgage.value) return;
  mortgageStore.updateHeldMortgageStatus(selectedHeldMortgage.value.id, 'completed');
  showHeldConfirmCloseModal.value = false;
  showHeldDetailModal.value = false;
  selectedHeldMortgage.value = null;
}

function forecloseHeldMortgage() {
  if (!selectedHeldMortgage.value) return;
  mortgageStore.updateHeldMortgageStatus(selectedHeldMortgage.value.id, 'foreclosed');
  showHeldConfirmForecloseModal.value = false;
  showHeldDetailModal.value = false;
  selectedHeldMortgage.value = null;
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Mortgage" subtitle="Manage home loans and mortgages you hold against others' properties">
      <template #actions>
        <button v-if="activeTab === 'my_mortgages'" class="btn-primary" @click="showAddMortgageModal = true">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Add Mortgage
        </button>
        <button v-else class="btn-primary" @click="openAddHeldMortgage">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Add Held Mortgage
        </button>
      </template>
    </PageHeader>

    <!-- Tabs -->
    <Tabs :tabs="tabItems" :active-tab="activeTab" @update:active-tab="(k: string) => activeTab = k as TabKey" />

    <!-- ======================== MY MORTGAGES TAB ======================== -->
    <div v-if="activeTab === 'my_mortgages'" class="space-y-6">
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Outstanding" :value="fmtCur(mortgageStore.totalMortgageDebt)" icon="🏠" color="danger" />
        <StatCard title="Monthly EMI" :value="fmtCur(mortgageStore.totalMonthlyEMI)" icon="📅" color="warning" />
        <StatCard title="Monthly Escrow" :value="fmtCur(mortgageStore.totalEscrowMonthly)" icon="🛡️" color="info" />
        <StatCard title="Property Equity" :value="fmtCur(mortgageStore.totalEquity)" icon="📈" color="accent" />
      </div>

      <!-- Empty State -->
      <div v-if="mortgageStore.mortgages.length === 0">
        <EmptyState icon="🏠" title="No mortgages yet" description="Add your first mortgage to start tracking home loans.">
          <template #action>
            <button class="btn-primary" @click="showAddMortgageModal = true">Add Mortgage</button>
          </template>
        </EmptyState>
      </div>

      <!-- Mortgage Cards Grid -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div
          v-for="mortgage in mortgageStore.mortgages"
          :key="mortgage.id"
          class="card-hover p-5 cursor-pointer animate-fade-in"
          @click="openDetail(mortgage)"
        >
          <!-- Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-lg bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-xl">
                {{ propertyTypeIcon[mortgage.property.propertyType] || '🏠' }}
              </div>
              <div>
                <h3 class="font-semibold text-surface-900 dark:text-white">{{ mortgage.property.name }}</h3>
                <p class="text-sm text-surface-500 dark:text-surface-400">{{ mortgage.lenderName }}</p>
              </div>
            </div>
            <Badge :variant="statusBadge(mortgage.status).variant">{{ statusBadge(mortgage.status).label }}</Badge>
          </div>

          <!-- Amounts -->
          <div class="grid grid-cols-3 gap-3 mb-4">
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400">Loan Amount</p>
              <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(mortgage.loanAmount, mortgage.currency) }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400">Balance</p>
              <p class="text-sm font-semibold text-danger-500 tabular-nums">{{ fmtCur(mortgage.currentBalance, mortgage.currency) }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400">Property Value</p>
              <p class="text-sm font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(mortgage.property.currentMarketValue || mortgage.property.purchasePrice, mortgage.currency) }}</p>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="mb-4">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-surface-500 dark:text-surface-400">Payoff Progress</span>
              <span class="text-xs font-medium tabular-nums" :class="payoffPercent(mortgage) > 50 ? 'text-accent-600' : 'text-surface-500'">
                {{ payoffPercent(mortgage).toFixed(1) }}%
              </span>
            </div>
            <ProgressBar :value="mortgage.paidAmount" :max="mortgage.loanAmount - mortgage.downPayment" color="primary" size="sm" />
          </div>

          <!-- Details Row -->
          <div class="grid grid-cols-3 gap-2 text-center border-t border-surface-100 dark:border-surface-700 pt-3">
            <div>
              <p class="text-xs text-surface-400">Interest Rate</p>
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ mortgage.interestRate }}% {{ mortgage.interestType === 'variable' ? '(var.)' : '' }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">EMI</p>
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ fmtCur(mortgage.emiAmount, mortgage.currency) }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">Remaining</p>
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ remainingMonths(mortgage) }} mo</p>
            </div>
          </div>

          <!-- Next Payment -->
          <div class="mt-3 flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2">
            <span class="text-xs text-surface-500 dark:text-surface-400">Next Payment</span>
            <span class="text-sm font-medium text-primary-600 dark:text-primary-400 tabular-nums">
              {{ fmtCur(mortgage.emiAmount, mortgage.currency) }} on {{ formatDate(mortgage.nextPaymentDate, 'short') }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================== HELD MORTGAGES TAB ======================== -->
    <div v-else class="space-y-6">
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Outstanding Loans" :value="fmtCur(mortgageStore.totalHeldOutstanding)" icon="🏘️" color="warning" />
        <StatCard title="Monthly Income" :value="fmtCur(mortgageStore.totalMonthlyIncome)" icon="💰" color="accent" />
        <StatCard title="Interest Earned" :value="fmtCur(mortgageStore.totalInterestEarnedHeld)" icon="📈" color="success" />
        <StatCard title="Collateral Value" :value="fmtCur(mortgageStore.totalCollateralValue)" icon="🏗️" color="info" />
      </div>

      <!-- Empty State -->
      <div v-if="mortgageStore.heldMortgages.length === 0">
        <EmptyState icon="🏘️" title="No held mortgages yet" description="Track mortgages where others have mortgaged their property to you.">
          <template #action>
            <button class="btn-primary" @click="openAddHeldMortgage">Add Held Mortgage</button>
          </template>
        </EmptyState>
      </div>

      <!-- Held Mortgage Cards Grid -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div
          v-for="hm in mortgageStore.heldMortgages"
          :key="hm.id"
          class="card-hover p-5 cursor-pointer animate-fade-in"
          @click="openHeldDetail(hm)"
        >
          <!-- Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-lg bg-accent-100 dark:bg-accent-500/20 flex items-center justify-center text-xl">
                {{ relationshipIcon[hm.relationship] || '👤' }}
              </div>
              <div>
                <h3 class="font-semibold text-surface-900 dark:text-white">{{ hm.borrowerName }}</h3>
                <p class="text-sm text-surface-500 dark:text-surface-400">{{ relationshipLabel[hm.relationship] }} &middot; {{ hm.collateral.name }}</p>
              </div>
            </div>
            <Badge :variant="heldStatusBadge(hm.status).variant">{{ heldStatusBadge(hm.status).label }}</Badge>
          </div>

          <!-- Amounts -->
          <div class="grid grid-cols-3 gap-3 mb-4">
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400">Loan Given</p>
              <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(hm.loanAmount, hm.currency) }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400">Outstanding</p>
              <p class="text-sm font-semibold text-warning-600 dark:text-warning-400 tabular-nums">{{ fmtCur(hm.currentBalance, hm.currency) }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400">Collateral Value</p>
              <p class="text-sm font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(hm.collateral.currentValue, hm.currency) }}</p>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="mb-4">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-surface-500 dark:text-surface-400">Recovery Progress</span>
              <span class="text-xs font-medium tabular-nums" :class="heldPayoffPercent(hm) > 50 ? 'text-accent-600' : 'text-surface-500'">
                {{ heldPayoffPercent(hm).toFixed(1) }}%
              </span>
            </div>
            <ProgressBar :value="hm.totalReceivedAmount" :max="hm.loanAmount" color="accent" size="sm" />
          </div>

          <!-- Details Row -->
          <div class="grid grid-cols-3 gap-2 text-center border-t border-surface-100 dark:border-surface-700 pt-3">
            <div>
              <p class="text-xs text-surface-400">Interest Rate</p>
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ hm.interestRate }}% {{ hm.interestType === 'variable' ? '(var.)' : '' }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">Monthly Payment</p>
              <p class="text-sm font-medium text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(hm.expectedMonthlyPayment, hm.currency) }}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">Interest Earned</p>
              <p class="text-sm font-medium text-success-600 dark:text-success-400 tabular-nums">{{ fmtCur(hm.totalInterestEarned, hm.currency) }}</p>
            </div>
          </div>

          <!-- Next Due -->
          <div class="mt-3 flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2">
            <span class="text-xs text-surface-500 dark:text-surface-400">Next Due</span>
            <span class="text-sm font-medium text-accent-600 dark:text-accent-400 tabular-nums">
              {{ fmtCur(hm.expectedMonthlyPayment, hm.currency) }} on {{ formatDate(hm.nextPaymentDueDate, 'short') }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================== MY MORTGAGE DETAIL MODAL ======================== -->
    <Modal v-if="selectedMortgage" :is-open="showDetailModal" title="Mortgage Details" size="xl" @close="showDetailModal = false">
      <div class="space-y-6" v-if="selectedMortgage">
        <!-- Property Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-2xl">
            {{ propertyTypeIcon[selectedMortgage.property.propertyType] || '🏠' }}
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedMortgage.property.name }}</h3>
            <p class="text-surface-500 dark:text-surface-400">{{ selectedMortgage.lenderName }} &middot; {{ propertyTypeLabel[selectedMortgage.property.propertyType] }}</p>
          </div>
          <Badge :variant="statusBadge(selectedMortgage.status).variant" class="ml-auto">{{ statusBadge(selectedMortgage.status).label }}</Badge>
        </div>

        <!-- Property Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Property Information</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Address</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedMortgage.property.address }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Size</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedMortgage.property.sizeSqft ? selectedMortgage.property.sizeSqft.toLocaleString() + ' sqft' : '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Purchase Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedMortgage.property.purchaseDate, 'long') }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Purchase Price</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedMortgage.property.purchasePrice, selectedMortgage.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Current Market Value</span>
              <p class="font-medium text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(selectedMortgage.property.currentMarketValue || selectedMortgage.property.purchasePrice, selectedMortgage.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Appreciation</span>
              <p class="font-medium" :class="appreciationPercent(selectedMortgage) >= 0 ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
                {{ appreciationPercent(selectedMortgage) >= 0 ? '+' : '' }}{{ appreciationPercent(selectedMortgage).toFixed(1) }}%
              </p>
            </div>
          </div>
        </div>

        <!-- Loan Details -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Loan Amount</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedMortgage.loanAmount, selectedMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Down Payment</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedMortgage.downPayment, selectedMortgage.currency) }} ({{ selectedMortgage.downPaymentPercent }}%)</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Interest Rate</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ selectedMortgage.interestRate }}% p.a. ({{ selectedMortgage.interestType }})</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Term / EMI</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ selectedMortgage.termMonths }} mo / {{ fmtCur(selectedMortgage.emiAmount, selectedMortgage.currency) }}</p>
          </div>
        </div>

        <!-- Financial Overview -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Outstanding Balance</p>
            <p class="font-semibold text-danger-500 tabular-nums">{{ fmtCur(selectedMortgage.currentBalance, selectedMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Paid So Far</p>
            <p class="font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(selectedMortgage.paidAmount, selectedMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Interest (est.)</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(Math.round(selectedMortgage.paidAmount * 0.3), selectedMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Remaining</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ remainingMonths(selectedMortgage) }} months</p>
          </div>
        </div>

        <!-- Progress -->
        <div>
          <ProgressBar :value="selectedMortgage.paidAmount" :max="selectedMortgage.loanAmount - selectedMortgage.downPayment" color="primary" size="md" />
          <div class="flex justify-between mt-2 text-xs text-surface-500 dark:text-surface-400">
            <span>{{ selectedMortgage.paidInstallments }} of {{ selectedMortgage.totalInstallments }} installments paid</span>
            <span>{{ remainingMonths(selectedMortgage) }} months remaining</span>
          </div>
        </div>

        <!-- Escrow Info -->
        <div class="card p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Escrow Details</h4>
          <div class="grid grid-cols-3 gap-4">
            <div class="text-center">
              <p class="text-xs text-surface-400 mb-1">Property Tax (annual)</p>
              <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedMortgage.escrow.propertyTaxAnnual, selectedMortgage.currency) }}</p>
            </div>
            <div class="text-center">
              <p class="text-xs text-surface-400 mb-1">Insurance (annual)</p>
              <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedMortgage.escrow.insuranceAnnual, selectedMortgage.currency) }}</p>
            </div>
            <div class="text-center">
              <p class="text-xs text-surface-400 mb-1">Monthly Escrow</p>
              <p class="font-semibold text-primary-600 dark:text-primary-400 tabular-nums">{{ fmtCur(selectedMortgage.escrow.monthlyEscrow, selectedMortgage.currency) }}</p>
            </div>
          </div>
        </div>

        <!-- Amortization Table -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Amortization Schedule (Next 24 months)</h4>
          <div class="max-h-64 overflow-y-auto">
            <DataTable :columns="amortColumns" :data="amortizationSchedule" empty-message="No upcoming payments">
              <template #cell-date="{ value }">
                {{ formatDate(value, 'short') }}
              </template>
              <template #cell-emiAmount="{ value }">
                {{ fmtCur(value, selectedMortgage?.currency) }}
              </template>
              <template #cell-principalComponent="{ value }">
                <span class="text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(value, selectedMortgage?.currency) }}</span>
              </template>
              <template #cell-interestComponent="{ value }">
                <span class="text-warning-600 dark:text-warning-400 tabular-nums">{{ fmtCur(value, selectedMortgage?.currency) }}</span>
              </template>
              <template #cell-remainingBalance="{ value }">
                {{ fmtCur(value, selectedMortgage?.currency) }}
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedMortgage.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedMortgage.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button v-if="selectedMortgage.status === 'active'" class="btn-primary" @click="openRecordPayment(selectedMortgage!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
            Record Payment
          </button>
          <button class="btn-secondary" @click="openEditMortgage(selectedMortgage!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button v-if="selectedMortgage.status === 'active'" class="btn-danger" @click="showConfirmCloseModal = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            Close Mortgage
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== HELD MORTGAGE DETAIL MODAL ======================== -->
    <Modal v-if="selectedHeldMortgage" :is-open="showHeldDetailModal" title="Held Mortgage Details" size="xl" @close="showHeldDetailModal = false">
      <div class="space-y-6" v-if="selectedHeldMortgage">
        <!-- Borrower & Collateral Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl bg-accent-100 dark:bg-accent-500/20 flex items-center justify-center text-2xl">
            {{ relationshipIcon[selectedHeldMortgage.relationship] || '👤' }}
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedHeldMortgage.borrowerName }}</h3>
            <p class="text-surface-500 dark:text-surface-400">{{ relationshipLabel[selectedHeldMortgage.relationship] }} &middot; {{ selectedHeldMortgage.collateral.name }}</p>
          </div>
          <Badge :variant="heldStatusBadge(selectedHeldMortgage.status).variant" class="ml-auto">{{ heldStatusBadge(selectedHeldMortgage.status).label }}</Badge>
        </div>

        <!-- Borrower Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Borrower Information</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Phone</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedHeldMortgage.borrowerPhone || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Email</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedHeldMortgage.borrowerEmail || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Address</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedHeldMortgage.borrowerAddress || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Relationship</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ relationshipIcon[selectedHeldMortgage.relationship] }} {{ relationshipLabel[selectedHeldMortgage.relationship] }}</p>
            </div>
          </div>
        </div>

        <!-- Collateral Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Collateral Property</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Property Type</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ propertyTypeIcon[selectedHeldMortgage.collateral.propertyType] }} {{ propertyTypeLabel[selectedHeldMortgage.collateral.propertyType] }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Address</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedHeldMortgage.collateral.address }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Size</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedHeldMortgage.collateral.sizeSqft ? selectedHeldMortgage.collateral.sizeSqft.toLocaleString() + ' sqft' : '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Appraised Value</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedHeldMortgage.collateral.appraisedValue, selectedHeldMortgage.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Current Value</span>
              <p class="font-medium text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(selectedHeldMortgage.collateral.currentValue, selectedHeldMortgage.currency) }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Loan-to-Value</span>
              <p class="font-medium" :class="heldCollateralCoverage(selectedHeldMortgage) < 80 ? 'text-success-600' : heldCollateralCoverage(selectedHeldMortgage) < 100 ? 'text-warning-600' : 'text-danger-500'">
                {{ heldCollateralCoverage(selectedHeldMortgage).toFixed(1) }}%
              </p>
            </div>
          </div>
          <div v-if="selectedHeldMortgage.collateral.documents" class="mt-3 pt-3 border-t border-surface-200 dark:border-surface-700">
            <span class="text-xs text-surface-400">Documents</span>
            <p class="text-sm font-medium text-surface-900 dark:text-white mt-0.5">{{ selectedHeldMortgage.collateral.documents }}</p>
          </div>
        </div>

        <!-- Loan Financials -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Loan Given</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedHeldMortgage.loanAmount, selectedHeldMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Outstanding</p>
            <p class="font-semibold text-warning-600 dark:text-warning-400 tabular-nums">{{ fmtCur(selectedHeldMortgage.currentBalance, selectedHeldMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Interest Rate</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ selectedHeldMortgage.interestRate }}% p.a. ({{ selectedHeldMortgage.interestType }})</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Term</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ selectedHeldMortgage.termMonths }} months</p>
          </div>
        </div>

        <!-- Income Overview -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Received</p>
            <p class="font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(selectedHeldMortgage.totalReceivedAmount, selectedHeldMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Interest Earned</p>
            <p class="font-semibold text-success-600 dark:text-success-400 tabular-nums">{{ fmtCur(selectedHeldMortgage.totalInterestEarned, selectedHeldMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Monthly Payment</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedHeldMortgage.expectedMonthlyPayment, selectedHeldMortgage.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Grace Period</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ selectedHeldMortgage.gracePeriodDays }} days ({{ selectedHeldMortgage.latePaymentPenaltyRate }}% penalty)</p>
          </div>
        </div>

        <!-- Progress -->
        <div>
          <ProgressBar :value="selectedHeldMortgage.totalReceivedAmount" :max="selectedHeldMortgage.loanAmount" color="accent" size="md" />
          <div class="flex justify-between mt-2 text-xs text-surface-500 dark:text-surface-400">
            <span>{{ selectedHeldMortgage.receivedInstallments }} of {{ selectedHeldMortgage.totalInstallments }} payments received</span>
            <span>{{ heldRemainingMonths(selectedHeldMortgage) }} months remaining</span>
          </div>
        </div>

        <!-- Payment History -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Payment History</h4>
          <div class="max-h-64 overflow-y-auto">
            <DataTable :columns="heldPaymentColumns" :data="[...selectedHeldMortgage.payments].reverse()" empty-message="No payments received yet">
              <template #cell-paymentDate="{ value }">
                {{ formatDate(value, 'short') }}
              </template>
              <template #cell-amount="{ value }">
                {{ fmtCur(value, selectedHeldMortgage?.currency) }}
              </template>
              <template #cell-principalComponent="{ value }">
                <span class="text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(value, selectedHeldMortgage?.currency) }}</span>
              </template>
              <template #cell-interestComponent="{ value }">
                <span class="text-success-600 dark:text-success-400 tabular-nums">{{ fmtCur(value, selectedHeldMortgage?.currency) }}</span>
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Projected Amortization -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Projected Amortization (Next 24 months)</h4>
          <div class="max-h-64 overflow-y-auto">
            <DataTable :columns="heldAmortColumns" :data="heldAmortizationSchedule" empty-message="No upcoming payments">
              <template #cell-date="{ value }">
                {{ formatDate(value, 'short') }}
              </template>
              <template #cell-emiAmount="{ value }">
                {{ fmtCur(value, selectedHeldMortgage?.currency) }}
              </template>
              <template #cell-principalComponent="{ value }">
                <span class="text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(value, selectedHeldMortgage?.currency) }}</span>
              </template>
              <template #cell-interestComponent="{ value }">
                <span class="text-success-600 dark:text-success-400 tabular-nums">{{ fmtCur(value, selectedHeldMortgage?.currency) }}</span>
              </template>
              <template #cell-remainingBalance="{ value }">
                {{ fmtCur(value, selectedHeldMortgage?.currency) }}
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedHeldMortgage.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedHeldMortgage.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button v-if="selectedHeldMortgage.status === 'active'" class="btn-primary" @click="openHeldRecordPayment(selectedHeldMortgage!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
            Record Received Payment
          </button>
          <button class="btn-secondary" @click="openEditHeldMortgage(selectedHeldMortgage!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button v-if="selectedHeldMortgage.status === 'active'" class="btn-danger" @click="showHeldConfirmForecloseModal = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21h18M3 7v1a3 3 0 006 0V7m0 1a3 3 0 006 0V7m0 1a3 3 0 006 0V7H3l2-4h14l2 4"/></svg>
            Foreclose
          </button>
          <button v-if="selectedHeldMortgage.status === 'active'" class="btn-secondary" @click="showHeldConfirmCloseModal = true" style="border-color: var(--color-accent-500); color: var(--color-accent-600);">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            Mark Completed
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== RECORD PAYMENT MODAL (My Mortgage) ======================== -->
    <Modal :is-open="showRecordPaymentModal" title="Record Mortgage Payment" size="sm" @close="showRecordPaymentModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Payment Date</label>
          <input v-model="paymentForm.date" type="date" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Amount ({{ selectedMortgage?.currency || 'BDT' }})</label>
          <input v-model.number="paymentForm.amount" type="number" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showRecordPaymentModal = false">Cancel</button>
          <button class="btn-primary" @click="submitPayment">Record Payment</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== RECORD RECEIVED PAYMENT MODAL (Held Mortgage) ======================== -->
    <Modal :is-open="showHeldRecordPaymentModal" title="Record Received Payment" size="sm" @close="showHeldRecordPaymentModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Amount ({{ selectedHeldMortgage?.currency || 'BDT' }})</label>
          <input v-model.number="heldPaymentForm.amount" type="number" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Note</label>
          <input v-model="heldPaymentForm.note" type="text" class="input-field" placeholder="e.g. Bank transfer, Cash, bKash" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showHeldRecordPaymentModal = false">Cancel</button>
          <button class="btn-primary" @click="submitHeldPayment">Record Payment</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== ADD MY MORTGAGE MODAL ======================== -->
    <Modal :is-open="showAddMortgageModal" title="Add New Mortgage" size="xl" @close="showAddMortgageModal = false">
      <div class="space-y-5">
        <!-- Property Details Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>🏠</span> Property Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Property Name</label>
              <input v-model="addMortgageForm.propertyName" type="text" class="input-field" placeholder="e.g. Dhanmondi Apartment" />
            </div>
            <div>
              <label class="field-label">Property Type</label>
              <select v-model="addMortgageForm.propertyType" class="input-field">
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="land">Land</option>
                <option value="commercial">Commercial</option>
                <option value="condo">Condo</option>
              </select>
            </div>
            <div class="md:col-span-2">
              <label class="field-label">Address</label>
              <input v-model="addMortgageForm.address" type="text" class="input-field" placeholder="Full property address" />
            </div>
            <div>
              <label class="field-label">Size (sqft)</label>
              <input v-model.number="addMortgageForm.sizeSqft" type="number" class="input-field tabular-nums" placeholder="e.g. 1500" />
            </div>
            <div>
              <label class="field-label">Purchase Price</label>
              <input v-model.number="addMortgageForm.purchasePrice" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Current Market Value (optional)</label>
              <input v-model.number="addMortgageForm.currentMarketValue" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Purchase Date</label>
              <input v-model="addMortgageForm.purchaseDate" type="date" class="input-field" />
            </div>
          </div>
        </div>

        <!-- Loan Details Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>🏦</span> Loan Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Lender Name</label>
              <input v-model="addMortgageForm.lenderName" type="text" class="input-field" placeholder="e.g. Sonali Bank" />
            </div>
            <div>
              <label class="field-label">Currency</label>
              <select v-model="addMortgageForm.currency" class="input-field">
                <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
              </select>
            </div>
            <div>
              <label class="field-label">Loan Amount</label>
              <input v-model.number="addMortgageForm.loanAmount" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Down Payment ({{ computedDownPaymentPercent() }}%)</label>
              <input v-model.number="addMortgageForm.downPayment" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Interest Rate (%)</label>
              <input v-model.number="addMortgageForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Interest Type</label>
              <select v-model="addMortgageForm.interestType" class="input-field">
                <option value="fixed">Fixed</option>
                <option value="variable">Variable</option>
              </select>
            </div>
            <div>
              <label class="field-label">Term (months)</label>
              <input v-model.number="addMortgageForm.termMonths" type="number" class="input-field tabular-nums" placeholder="e.g. 240" />
            </div>
            <div>
              <label class="field-label">EMI Amount</label>
              <input v-model.number="addMortgageForm.emiAmount" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Start Date</label>
              <input v-model="addMortgageForm.startDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Bank Account</label>
              <select v-model="addMortgageForm.bankAccountId" class="input-field">
                <option value="">Select Bank Account</option>
                <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Escrow Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>🛡️</span> Escrow Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Property Tax (annual)</label>
              <input v-model.number="addMortgageForm.propertyTaxAnnual" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Insurance (annual)</label>
              <input v-model.number="addMortgageForm.insuranceAnnual" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Monthly Escrow</label>
              <div class="py-2.5 px-3 bg-surface-100 dark:bg-surface-800 rounded-lg text-sm font-medium text-surface-900 dark:text-white tabular-nums">
                {{ fmtCur(computedMonthlyEscrow()) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="addMortgageForm.notes" rows="2" placeholder="Additional notes..." class="input-field resize-none"></textarea>
        </div>

        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showAddMortgageModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddMortgage">Add Mortgage</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== ADD HELD MORTGAGE MODAL ======================== -->
    <Modal :is-open="showAddHeldMortgageModal" title="Add Held Mortgage" size="xl" @close="showAddHeldMortgageModal = false">
      <div class="space-y-5">
        <!-- Borrower Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>👤</span> Borrower Information
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Borrower Name</label>
              <input v-model="addHeldForm.borrowerName" type="text" class="input-field" placeholder="Full name" />
            </div>
            <div>
              <label class="field-label">Relationship</label>
              <select v-model="addHeldForm.relationship" class="input-field">
                <option value="family">Family</option>
                <option value="friend">Friend</option>
                <option value="business">Business</option>
                <option value="colleague">Colleague</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Phone</label>
              <input v-model="addHeldForm.borrowerPhone" type="text" class="input-field" placeholder="+880 1xxx-xxxxxx" />
            </div>
            <div>
              <label class="field-label">Email</label>
              <input v-model="addHeldForm.borrowerEmail" type="email" class="input-field" placeholder="email@example.com" />
            </div>
            <div class="md:col-span-2">
              <label class="field-label">Address</label>
              <input v-model="addHeldForm.borrowerAddress" type="text" class="input-field" placeholder="Borrower's address" />
            </div>
          </div>
        </div>

        <!-- Collateral Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>🏗️</span> Collateral Property
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Property Name</label>
              <input v-model="addHeldForm.collateralName" type="text" class="input-field" placeholder="e.g. Gulshan Plot" />
            </div>
            <div>
              <label class="field-label">Property Type</label>
              <select v-model="addHeldForm.collateralType" class="input-field">
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="land">Land</option>
                <option value="commercial">Commercial</option>
                <option value="condo">Condo</option>
              </select>
            </div>
            <div class="md:col-span-2">
              <label class="field-label">Address</label>
              <input v-model="addHeldForm.collateralAddress" type="text" class="input-field" placeholder="Full collateral property address" />
            </div>
            <div>
              <label class="field-label">Size (sqft)</label>
              <input v-model.number="addHeldForm.collateralSizeSqft" type="number" class="input-field tabular-nums" placeholder="e.g. 2000" />
            </div>
            <div>
              <label class="field-label">Appraised Value</label>
              <input v-model.number="addHeldForm.appraisedValue" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Current Value</label>
              <input v-model.number="addHeldForm.currentValue" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Document Reference</label>
              <input v-model="addHeldForm.collateralDocuments" type="text" class="input-field" placeholder="e.g. Deed No. 1234/2025" />
            </div>
          </div>
        </div>

        <!-- Loan Terms Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>💰</span> Loan Terms
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Currency</label>
              <select v-model="addHeldForm.currency" class="input-field">
                <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
              </select>
            </div>
            <div>
              <label class="field-label">Loan Amount</label>
              <input v-model.number="addHeldForm.loanAmount" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Interest Rate (%)</label>
              <input v-model.number="addHeldForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Interest Type</label>
              <select v-model="addHeldForm.interestType" class="input-field">
                <option value="fixed">Fixed</option>
                <option value="variable">Variable</option>
              </select>
            </div>
            <div>
              <label class="field-label">Term (months)</label>
              <input v-model.number="addHeldForm.termMonths" type="number" class="input-field tabular-nums" placeholder="e.g. 60" />
            </div>
            <div>
              <label class="field-label">Expected Monthly Payment</label>
              <input v-model.number="addHeldForm.expectedMonthlyPayment" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Start Date</label>
              <input v-model="addHeldForm.startDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Bank Account</label>
              <select v-model="addHeldForm.bankAccountId" class="input-field">
                <option value="">Select Bank Account</option>
                <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Penalty / Grace Section -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>⚠️</span> Penalty & Grace Period
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Late Penalty Rate (%/month)</label>
              <input v-model.number="addHeldForm.latePaymentPenaltyRate" type="number" step="0.1" class="input-field tabular-nums" placeholder="e.g. 2" />
            </div>
            <div>
              <label class="field-label">Grace Period (days)</label>
              <input v-model.number="addHeldForm.gracePeriodDays" type="number" class="input-field tabular-nums" placeholder="e.g. 10" />
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="addHeldForm.notes" rows="2" placeholder="Additional notes..." class="input-field resize-none"></textarea>
        </div>

        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showAddHeldMortgageModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddHeldMortgage">Add Held Mortgage</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== CONFIRM CLOSE MODAL (My Mortgage) ======================== -->
    <Modal :is-open="showConfirmCloseModal" title="Close Mortgage" size="sm" @close="showConfirmCloseModal = false">
      <div class="space-y-4">
        <div class="bg-warning-50 dark:bg-warning-500/10 border border-warning-400/30 rounded-lg p-4">
          <p class="text-sm text-amber-800 dark:text-amber-300">
            Are you sure you want to mark this mortgage as <strong>completed</strong>? This action will change the mortgage status but won't delete it.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showConfirmCloseModal = false">Cancel</button>
          <button class="btn-danger" @click="closeMortgage">Yes, Close Mortgage</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== CONFIRM COMPLETE MODAL (Held Mortgage) ======================== -->
    <Modal :is-open="showHeldConfirmCloseModal" title="Complete Held Mortgage" size="sm" @close="showHeldConfirmCloseModal = false">
      <div class="space-y-4">
        <div class="bg-accent-50 dark:bg-accent-500/10 border border-accent-400/30 rounded-lg p-4">
          <p class="text-sm text-amber-800 dark:text-amber-300">
            Are you sure you want to mark this held mortgage as <strong>completed</strong>? The borrower has fully repaid the loan.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showHeldConfirmCloseModal = false">Cancel</button>
          <button class="btn-primary" @click="completeHeldMortgage">Yes, Mark Completed</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== CONFIRM FORECLOSE MODAL (Held Mortgage) ======================== -->
    <Modal :is-open="showHeldConfirmForecloseModal" title="Foreclose Held Mortgage" size="sm" @close="showHeldConfirmForecloseModal = false">
      <div class="space-y-4">
        <div class="bg-danger-50 dark:bg-danger-500/10 border border-danger-400/30 rounded-lg p-4">
          <p class="text-sm text-red-800 dark:text-red-300">
            Are you sure you want to <strong>foreclose</strong> this mortgage? This means the borrower has defaulted and you are claiming the collateral property. This action cannot be undone.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showHeldConfirmForecloseModal = false">Cancel</button>
          <button class="btn-danger" @click="forecloseHeldMortgage">Yes, Foreclose</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== EDIT MY MORTGAGE MODAL ======================== -->
    <Modal :is-open="showEditMortgageModal" title="Edit Mortgage" size="lg" @close="showEditMortgageModal = false">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Lender Name</label>
            <input v-model="editMortgageForm.lenderName" type="text" class="input-field" />
          </div>
          <div>
            <label class="field-label">Currency</label>
            <select v-model="editMortgageForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div>
            <label class="field-label">Interest Rate (%)</label>
            <input v-model.number="editMortgageForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Current Balance</label>
            <input v-model.number="editMortgageForm.currentBalance" type="number" min="0" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Next Payment Date</label>
            <input v-model="editMortgageForm.nextPaymentDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Current Market Value</label>
            <input v-model.number="editMortgageForm.currentMarketValue" type="number" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Status</label>
            <select v-model="editMortgageForm.status" class="input-field">
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
              <option value="defaulted">Defaulted</option>
              <option value="in_review">In Review</option>
            </select>
          </div>
        </div>
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="editMortgageForm.notes" rows="2" class="input-field resize-none"></textarea>
        </div>
        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showEditMortgageModal = false">Cancel</button>
          <button class="btn-primary" @click="submitEditMortgage">Save Changes</button>
        </div>
      </div>
    </Modal>

    <!-- ======================== EDIT HELD MORTGAGE MODAL ======================== -->
    <Modal :is-open="showHeldEditModal" title="Edit Held Mortgage" size="lg" @close="showHeldEditModal = false">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Borrower Name</label>
            <input v-model="editHeldForm.borrowerName" type="text" class="input-field" />
          </div>
          <div>
            <label class="field-label">Currency</label>
            <select v-model="editHeldForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div>
            <label class="field-label">Interest Rate (%)</label>
            <input v-model.number="editHeldForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Current Balance</label>
            <input v-model.number="editHeldForm.currentBalance" type="number" min="0" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Next Payment Due Date</label>
            <input v-model="editHeldForm.nextPaymentDueDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Collateral Current Value</label>
            <input v-model.number="editHeldForm.currentValue" type="number" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Status</label>
            <select v-model="editHeldForm.status" class="input-field">
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
              <option value="defaulted">Defaulted</option>
              <option value="foreclosed">Foreclosed</option>
              <option value="in_review">In Review</option>
            </select>
          </div>
        </div>
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="editHeldForm.notes" rows="2" class="input-field resize-none"></textarea>
        </div>
        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showHeldEditModal = false">Cancel</button>
          <button class="btn-primary" @click="submitEditHeldMortgage">Save Changes</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
