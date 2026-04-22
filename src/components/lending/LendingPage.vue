<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLendingStore } from '../../stores/lending';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate, generateId } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, ProgressBar, Modal, EmptyState, Tabs } from '../ui';
import type { Lending, LendingStatus, Currency } from '../../types';

const lendingStore = useLendingStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ============ Tabs ============
const mainTabs = [
  { key: 'all', label: 'All Lending', icon: '📋' },
  { key: 'active', label: 'Active', icon: '✅' },
  { key: 'overdue', label: 'Overdue', icon: '⚠️' },
  { key: 'repaid', label: 'Repaid', icon: '💰' },
];
const activeTab = ref('all');

// ============ State ============
const selectedLending = ref<Lending | null>(null);
const showDetailModal = ref(false);
const showRecordRepaymentModal = ref(false);
const showAddLendingModal = ref(false);
const showEditLendingModal = ref(false);
const showConfirmDefaultModal = ref(false);
const showConfirmCancelModal = ref(false);

// ============ Form State ============
const repaymentForm = ref({
  amount: 0,
  note: '',
});

const addLendingForm = ref({
  borrowerName: '',
  borrowerPhone: '',
  borrowerEmail: '',
  relationship: 'friend' as Lending['relationship'],
  principalAmount: 0,
  interestRate: 0,
  issuedDate: new Date().toISOString().split('T')[0],
  dueDate: '',
  repaymentSchedule: 'lump_sum' as Lending['repaymentSchedule'],
  currency: 'BDT' as Currency,
  notes: '',
  tags: '',
});

const editLendingForm = ref({
  borrowerName: '',
  borrowerPhone: '',
  borrowerEmail: '',
  relationship: 'friend' as Lending['relationship'],
  currentBalance: 0,
  interestRate: 0,
  dueDate: '',
  status: 'active' as LendingStatus,
  currency: 'BDT' as Currency,
  notes: '',
  tags: '',
});

// ============ Helpers ============
const relationshipIcon: Record<string, string> = {
  family: '👨‍👩‍👧‍👦',
  friend: '🤝',
  colleague: '💼',
  business: '🏢',
  other: '👤',
};

const relationshipLabel: Record<string, string> = {
  family: 'Family',
  friend: 'Friend',
  colleague: 'Colleague',
  business: 'Business',
  other: 'Other',
};

function statusBadge(status: LendingStatus): { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string } {
  switch (status) {
    case 'active': return { variant: 'success', label: 'Active' };
    case 'partially_repaid': return { variant: 'info', label: 'Partial' };
    case 'fully_repaid': return { variant: 'success', label: 'Repaid' };
    case 'overdue': return { variant: 'danger', label: 'Overdue' };
    case 'defaulted': return { variant: 'danger', label: 'Defaulted' };
    case 'cancelled': return { variant: 'neutral', label: 'Cancelled' };
    default: return { variant: 'neutral', label: status };
  }
}

function scheduleLabel(schedule?: string): string {
  const map: Record<string, string> = {
    lump_sum: 'Lump Sum',
    monthly: 'Monthly',
    weekly: 'Weekly',
    custom: 'Custom',
  };
  return schedule ? map[schedule] || schedule : '—';
}

function repaymentPercent(l: Lending): number {
  if (l.totalRepayableAmount === 0) return 0;
  return Math.min(100, (l.totalRepaidAmount / l.totalRepayableAmount) * 100);
}

function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') {
    return currencyStore.formatWithCurrency(amount, currency as Currency);
  }
  return formatCurrency(amount, 'BDT');
}

// ============ Computed ============
const filteredLendings = computed(() => {
  switch (activeTab.value) {
    case 'active':
      return lendingStore.lendings.filter(l => l.status === 'active' || l.status === 'partially_repaid');
    case 'overdue':
      return lendingStore.overdueLendings;
    case 'repaid':
      return lendingStore.lendings.filter(l => l.status === 'fully_repaid');
    default:
      return [...lendingStore.lendings];
  }
});

// ============ Actions ============
function openDetail(lending: Lending) {
  selectedLending.value = lending;
  showDetailModal.value = true;
}

function openRecordRepayment(lending: Lending) {
  selectedLending.value = lending;
  repaymentForm.value = {
    amount: lending.currentBalance,
    note: '',
  };
  showRecordRepaymentModal.value = true;
}

function submitRepayment() {
  if (!selectedLending.value) return;
  lendingStore.recordRepayment(selectedLending.value.id, repaymentForm.value.amount, repaymentForm.value.note || undefined);
  showRecordRepaymentModal.value = false;
  selectedLending.value = lendingStore.getLendingById(selectedLending.value.id) || null;
}

function submitAddLending() {
  const form = addLendingForm.value;
  const totalInterest = Math.round(form.principalAmount * (form.interestRate / 100));

  lendingStore.addLending({
    borrowerName: form.borrowerName,
    borrowerPhone: form.borrowerPhone || undefined,
    borrowerEmail: form.borrowerEmail || undefined,
    relationship: form.relationship,
    principalAmount: form.principalAmount,
    currentBalance: form.principalAmount,
    interestRate: form.interestRate,
    totalInterestAmount: totalInterest,
    totalRepayableAmount: form.principalAmount + totalInterest,
    totalRepaidAmount: 0,
    issuedDate: form.issuedDate,
    dueDate: form.dueDate || undefined,
    repaymentSchedule: form.repaymentSchedule,
    status: 'active',
    notes: form.notes || undefined,
    tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
    currency: form.currency,
  });
  showAddLendingModal.value = false;
  resetAddForm();
}

function resetAddForm() {
  addLendingForm.value = {
    borrowerName: '',
    borrowerPhone: '',
    borrowerEmail: '',
    relationship: 'friend',
    principalAmount: 0,
    interestRate: 0,
    issuedDate: new Date().toISOString().split('T')[0],
    dueDate: '',
    repaymentSchedule: 'lump_sum',
    currency: 'BDT',
    notes: '',
    tags: '',
  };
}

function openEditLending(lending: Lending) {
  selectedLending.value = lending;
  editLendingForm.value = {
    borrowerName: lending.borrowerName,
    borrowerPhone: lending.borrowerPhone || '',
    borrowerEmail: lending.borrowerEmail || '',
    relationship: lending.relationship,
    currentBalance: lending.currentBalance,
    interestRate: lending.interestRate,
    dueDate: lending.dueDate || '',
    status: lending.status,
    currency: lending.currency || 'BDT',
    notes: lending.notes || '',
    tags: lending.tags ? lending.tags.join(', ') : '',
  };
  showDetailModal.value = false;
  showEditLendingModal.value = true;
}

function submitEditLending() {
  if (!selectedLending.value) return;
  const l = selectedLending.value;
  lendingStore.updateLending(l.id, {
    borrowerName: editLendingForm.value.borrowerName,
    borrowerPhone: editLendingForm.value.borrowerPhone || undefined,
    borrowerEmail: editLendingForm.value.borrowerEmail || undefined,
    relationship: editLendingForm.value.relationship,
    currentBalance: editLendingForm.value.currentBalance,
    interestRate: editLendingForm.value.interestRate,
    dueDate: editLendingForm.value.dueDate || undefined,
    status: editLendingForm.value.status,
    currency: editLendingForm.value.currency,
    notes: editLendingForm.value.notes || undefined,
    tags: editLendingForm.value.tags ? editLendingForm.value.tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
  });
  showEditLendingModal.value = false;
  selectedLending.value = lendingStore.getLendingById(l.id) || null;
}

function confirmDefaulted() {
  if (!selectedLending.value) return;
  lendingStore.markAsDefaulted(selectedLending.value.id);
  showConfirmDefaultModal.value = false;
  showDetailModal.value = false;
  selectedLending.value = null;
}

function confirmCancelled() {
  if (!selectedLending.value) return;
  lendingStore.markAsCancelled(selectedLending.value.id);
  showConfirmCancelModal.value = false;
  showDetailModal.value = false;
  selectedLending.value = null;
}

function computedTotalInterest(): number {
  const form = addLendingForm.value;
  return Math.round(form.principalAmount * (form.interestRate / 100));
}

function computedTotalRepayable(): number {
  const form = addLendingForm.value;
  return form.principalAmount + Math.round(form.principalAmount * (form.interestRate / 100));
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Lending" subtitle="Track money you've lent to others">
      <template #actions>
        <button class="btn-primary" @click="showAddLendingModal = true">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Add Lending
        </button>
      </template>
    </PageHeader>

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Total Lent" :value="fmtCur(lendingStore.totalLentAmount)" icon="💸" color="primary" />
      <StatCard title="Outstanding" :value="fmtCur(lendingStore.totalOutstandingBalance)" icon="⏳" color="danger" />
      <StatCard title="Repaid" :value="fmtCur(lendingStore.totalRepaidAmount)" icon="✅" color="accent" />
      <StatCard title="Interest Earned" :value="fmtCur(lendingStore.totalInterestEarned)" icon="📈" color="warning" />
    </div>

    <!-- Tabs -->
    <Tabs :tabs="mainTabs" v-model:activeTab="activeTab" />

    <!-- Empty State -->
    <div v-if="filteredLendings.length === 0">
      <EmptyState icon="🤝" title="No lending records" description="Add your first lending entry to track money owed to you.">
        <template #action>
          <button class="btn-primary" @click="showAddLendingModal = true">Add Lending</button>
        </template>
      </EmptyState>
    </div>

    <!-- Lending Cards Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="lending in filteredLendings"
        :key="lending.id"
        class="card-hover p-5 cursor-pointer animate-fade-in"
        :class="lending.status === 'cancelled' ? 'opacity-60' : ''"
        @click="openDetail(lending)"
      >
        <!-- Header -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-lg bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-xl">
              {{ relationshipIcon[lending.relationship] || '👤' }}
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">{{ lending.borrowerName }}</h3>
              <div class="flex items-center gap-2 mt-0.5">
                <Badge :variant="lending.relationship === 'family' ? 'info' : lending.relationship === 'business' ? 'warning' : 'neutral'" size="sm">
                  {{ relationshipLabel[lending.relationship] }}
                </Badge>
                <Badge :variant="statusBadge(lending.status).variant" size="sm">{{ statusBadge(lending.status).label }}</Badge>
              </div>
            </div>
          </div>
        </div>

        <!-- Amounts -->
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Principal</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(lending.principalAmount, lending.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Outstanding</p>
            <p class="text-sm font-semibold tabular-nums" :class="lending.currentBalance > 0 ? 'text-danger-500' : 'text-accent-600 dark:text-accent-400'">
              {{ fmtCur(lending.currentBalance, lending.currency) }}
            </p>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-surface-500 dark:text-surface-400">Repayment Progress</span>
            <span class="text-xs font-medium tabular-nums" :class="repaymentPercent(lending) > 50 ? 'text-accent-600' : 'text-surface-500'">
              {{ repaymentPercent(lending).toFixed(1) }}%
            </span>
          </div>
          <ProgressBar :value="lending.totalRepaidAmount" :max="lending.totalRepayableAmount || lending.principalAmount" color="primary" size="sm" />
        </div>

        <!-- Details Row -->
        <div class="grid grid-cols-3 gap-2 text-center border-t border-surface-100 dark:border-surface-700 pt-3">
          <div>
            <p class="text-xs text-surface-400">Interest Rate</p>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300 tabular-nums">{{ lending.interestRate > 0 ? lending.interestRate + '%' : 'Free' }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-400">Issued</p>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">{{ formatDate(lending.issuedDate, 'short') }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-400">Schedule</p>
            <p class="text-sm font-medium text-surface-700 dark:text-surface-300">{{ scheduleLabel(lending.repaymentSchedule) }}</p>
          </div>
        </div>

        <!-- Due Date -->
        <div v-if="lending.dueDate && (lending.status === 'active' || lending.status === 'overdue')" class="mt-3 flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2">
          <span class="text-xs text-surface-500 dark:text-surface-400">Due Date</span>
          <span class="text-sm font-medium tabular-nums" :class="lending.status === 'overdue' ? 'text-danger-500' : 'text-primary-600 dark:text-primary-400'">
            {{ formatDate(lending.dueDate, 'short') }}
          </span>
        </div>
      </div>
    </div>

    <!-- ============ LENDING DETAIL MODAL ============ -->
    <Modal v-if="selectedLending" :is-open="showDetailModal" title="Lending Details" size="lg" @close="showDetailModal = false">
      <div class="space-y-5" v-if="selectedLending">
        <!-- Borrower Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-2xl">
            {{ relationshipIcon[selectedLending.relationship] || '👤' }}
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedLending.borrowerName }}</h3>
            <p class="text-surface-500 dark:text-surface-400">{{ relationshipLabel[selectedLending.relationship] }}</p>
          </div>
          <Badge :variant="statusBadge(selectedLending.status).variant">{{ statusBadge(selectedLending.status).label }}</Badge>
        </div>

        <!-- Borrower Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Borrower Information</h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedLending.borrowerPhone">
              <span class="text-xs text-surface-400">Phone</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedLending.borrowerPhone }}</p>
            </div>
            <div v-if="selectedLending.borrowerEmail">
              <span class="text-xs text-surface-400">Email</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedLending.borrowerEmail }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Relationship</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ relationshipLabel[selectedLending.relationship] }}</p>
            </div>
          </div>
        </div>

        <!-- Financial Breakdown -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Principal</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedLending.principalAmount, selectedLending.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Interest</p>
            <p class="font-semibold text-warning-600 dark:text-warning-400 tabular-nums">{{ fmtCur(selectedLending.totalInterestAmount, selectedLending.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Repayable</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedLending.totalRepayableAmount, selectedLending.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Repaid</p>
            <p class="font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ fmtCur(selectedLending.totalRepaidAmount, selectedLending.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Outstanding</p>
            <p class="font-semibold text-danger-500 tabular-nums">{{ fmtCur(selectedLending.currentBalance, selectedLending.currency) }}</p>
          </div>
        </div>

        <!-- Progress -->
        <div>
          <ProgressBar :value="selectedLending.totalRepaidAmount" :max="selectedLending.totalRepayableAmount || selectedLending.principalAmount" color="primary" size="md" />
          <div class="flex justify-between mt-2 text-xs text-surface-500 dark:text-surface-400">
            <span>{{ repaymentPercent(selectedLending).toFixed(1) }}% repaid</span>
            <span>{{ fmtCur(selectedLending.totalRepaidAmount, selectedLending.currency) }} of {{ fmtCur(selectedLending.totalRepayableAmount, selectedLending.currency) }}</span>
          </div>
        </div>

        <!-- Key Info -->
        <div class="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-xs text-surface-400">Interest Rate</span>
            <p class="font-medium text-surface-900 dark:text-white">{{ selectedLending.interestRate > 0 ? selectedLending.interestRate + '% p.a.' : 'Interest-free' }}</p>
          </div>
          <div>
            <span class="text-xs text-surface-400">Issued Date</span>
            <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedLending.issuedDate, 'long') }}</p>
          </div>
          <div>
            <span class="text-xs text-surface-400">Due Date</span>
            <p class="font-medium" :class="selectedLending.status === 'overdue' ? 'text-danger-500' : 'text-surface-900 dark:text-white'">
              {{ selectedLending.dueDate ? formatDate(selectedLending.dueDate, 'long') : '—' }}
            </p>
          </div>
        </div>

        <!-- Notes & Tags -->
        <div v-if="selectedLending.notes || (selectedLending.tags && selectedLending.tags.length > 0)">
          <div v-if="selectedLending.notes">
            <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
            <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedLending.notes }}</p>
          </div>
          <div v-if="selectedLending.tags && selectedLending.tags.length > 0" class="flex flex-wrap gap-1.5 mt-2">
            <span v-for="tag in selectedLending.tags" :key="tag" class="text-xs px-2 py-0.5 bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400 rounded-full">{{ tag }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button
            v-if="selectedLending.status === 'active' || selectedLending.status === 'partially_repaid' || selectedLending.status === 'overdue'"
            class="btn-primary"
            @click="openRecordRepayment(selectedLending)"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
            Record Repayment
          </button>
          <button class="btn-secondary" @click="openEditLending(selectedLending!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button
            v-if="selectedLending.status === 'active' || selectedLending.status === 'overdue'"
            class="text-sm px-4 py-2 rounded-lg bg-warning-50 dark:bg-warning-500/20 text-amber-700 dark:text-amber-400 hover:bg-warning-100 dark:hover:bg-warning-500/30 transition-colors font-medium"
            @click="showConfirmDefaultModal = true"
          >
            Mark Defaulted
          </button>
          <button
            v-if="selectedLending.status !== 'fully_repaid' && selectedLending.status !== 'cancelled' && selectedLending.status !== 'defaulted'"
            class="text-sm px-4 py-2 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium"
            @click="showConfirmCancelModal = true"
          >
            Cancel
          </button>
        </div>
      </div>
    </Modal>

    <!-- ============ RECORD REPAYMENT MODAL ============ -->
    <Modal :is-open="showRecordRepaymentModal" title="Record Repayment" size="sm" @close="showRecordRepaymentModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Amount ({{ selectedLending?.currency || 'BDT' }})</label>
          <input v-model.number="repaymentForm.amount" type="number" class="input-field tabular-nums" placeholder="0" :max="selectedLending?.currentBalance" />
          <p class="text-xs text-surface-400 mt-1">Outstanding: {{ fmtCur(selectedLending?.currentBalance || 0, selectedLending?.currency) }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Note (optional)</label>
          <input v-model="repaymentForm.note" type="text" class="input-field" placeholder="e.g. Partial repayment via bKash" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showRecordRepaymentModal = false">Cancel</button>
          <button class="btn-primary" @click="submitRepayment">Record Repayment</button>
        </div>
      </div>
    </Modal>

    <!-- ============ ADD LENDING MODAL ============ -->
    <Modal :is-open="showAddLendingModal" title="Add New Lending" size="lg" @close="showAddLendingModal = false">
      <div class="space-y-5">
        <!-- Borrower Info -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>👤</span> Borrower Information
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Borrower Name</label>
              <input v-model="addLendingForm.borrowerName" type="text" class="input-field" placeholder="Full name" />
            </div>
            <div>
              <label class="field-label">Relationship</label>
              <select v-model="addLendingForm.relationship" class="input-field">
                <option value="friend">Friend</option>
                <option value="family">Family</option>
                <option value="colleague">Colleague</option>
                <option value="business">Business</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Phone (optional)</label>
              <input v-model="addLendingForm.borrowerPhone" type="tel" class="input-field" placeholder="+880 ..." />
            </div>
            <div>
              <label class="field-label">Email (optional)</label>
              <input v-model="addLendingForm.borrowerEmail" type="email" class="input-field" placeholder="email@example.com" />
            </div>
          </div>
        </div>

        <!-- Loan Details -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>💰</span> Loan Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Principal Amount</label>
              <input v-model.number="addLendingForm.principalAmount" type="number" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Interest Rate (%) — 0 for interest-free</label>
              <input v-model.number="addLendingForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" placeholder="0" />
            </div>
            <div>
              <label class="field-label">Currency</label>
              <select v-model="addLendingForm.currency" class="input-field">
                <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
              </select>
            </div>
            <div>
              <label class="field-label">Repayment Schedule</label>
              <select v-model="addLendingForm.repaymentSchedule" class="input-field">
                <option value="lump_sum">Lump Sum</option>
                <option value="monthly">Monthly</option>
                <option value="weekly">Weekly</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label class="field-label">Issued Date</label>
              <input v-model="addLendingForm.issuedDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Due Date (optional)</label>
              <input v-model="addLendingForm.dueDate" type="date" class="input-field" />
            </div>
          </div>
        </div>

        <!-- Computed Summary -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4 space-y-2">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-2">Summary</h4>
          <div class="flex justify-between text-sm">
            <span class="text-surface-500 dark:text-surface-400">Interest Amount</span>
            <span class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(computedTotalInterest()) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-surface-500 dark:text-surface-400">Total Repayable</span>
            <span class="font-bold text-primary-600 dark:text-primary-400 tabular-nums">{{ fmtCur(computedTotalRepayable()) }}</span>
          </div>
        </div>

        <!-- Notes & Tags -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Notes</label>
            <textarea v-model="addLendingForm.notes" rows="2" placeholder="Additional notes..." class="input-field resize-none"></textarea>
          </div>
          <div>
            <label class="field-label">Tags (comma-separated)</label>
            <input v-model="addLendingForm.tags" type="text" class="input-field" placeholder="e.g. personal, interest-free" />
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showAddLendingModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddLending">Add Lending</button>
        </div>
      </div>
    </Modal>

    <!-- ============ EDIT LENDING MODAL ============ -->
    <Modal :is-open="showEditLendingModal" title="Edit Lending" size="lg" @close="showEditLendingModal = false">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Borrower Name</label>
            <input v-model="editLendingForm.borrowerName" type="text" class="input-field" />
          </div>
          <div>
            <label class="field-label">Relationship</label>
            <select v-model="editLendingForm.relationship" class="input-field">
              <option value="friend">Friend</option>
              <option value="family">Family</option>
              <option value="colleague">Colleague</option>
              <option value="business">Business</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label class="field-label">Phone</label>
            <input v-model="editLendingForm.borrowerPhone" type="tel" class="input-field" />
          </div>
          <div>
            <label class="field-label">Email</label>
            <input v-model="editLendingForm.borrowerEmail" type="email" class="input-field" />
          </div>
          <div>
            <label class="field-label">Current Balance</label>
            <input v-model.number="editLendingForm.currentBalance" type="number" min="0" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Interest Rate (%)</label>
            <input v-model.number="editLendingForm.interestRate" type="number" step="0.1" class="input-field tabular-nums" />
          </div>
          <div>
            <label class="field-label">Due Date</label>
            <input v-model="editLendingForm.dueDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Currency</label>
            <select v-model="editLendingForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div>
            <label class="field-label">Status</label>
            <select v-model="editLendingForm.status" class="input-field">
              <option value="active">Active</option>
              <option value="partially_repaid">Partially Repaid</option>
              <option value="fully_repaid">Fully Repaid</option>
              <option value="overdue">Overdue</option>
              <option value="defaulted">Defaulted</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="editLendingForm.notes" rows="2" class="input-field resize-none"></textarea>
        </div>
        <div>
          <label class="field-label">Tags (comma-separated)</label>
          <input v-model="editLendingForm.tags" type="text" class="input-field" />
        </div>
        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showEditLendingModal = false">Cancel</button>
          <button class="btn-primary" @click="submitEditLending">Save Changes</button>
        </div>
      </div>
    </Modal>

    <!-- ============ CONFIRM DEFAULT MODAL ============ -->
    <Modal :is-open="showConfirmDefaultModal" title="Mark as Defaulted" size="sm" @close="showConfirmDefaultModal = false">
      <div class="space-y-4">
        <div class="bg-danger-50 dark:bg-danger-500/10 border border-danger-400/30 rounded-lg p-4">
          <p class="text-sm text-red-800 dark:text-red-300">
            Are you sure you want to mark this lending as <strong>defaulted</strong>? This indicates the borrower has failed to repay.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showConfirmDefaultModal = false">Cancel</button>
          <button class="btn-danger" @click="confirmDefaulted">Mark Defaulted</button>
        </div>
      </div>
    </Modal>

    <!-- ============ CONFIRM CANCEL MODAL ============ -->
    <Modal :is-open="showConfirmCancelModal" title="Cancel Lending" size="sm" @close="showConfirmCancelModal = false">
      <div class="space-y-4">
        <div class="bg-warning-50 dark:bg-warning-500/10 border border-warning-400/30 rounded-lg p-4">
          <p class="text-sm text-amber-800 dark:text-amber-300">
            Are you sure you want to <strong>cancel</strong> this lending record? This action changes the status but keeps the record.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showConfirmCancelModal = false">Cancel</button>
          <button class="btn-danger" @click="confirmCancelled">Yes, Cancel Lending</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
