<script setup lang="ts">
import { ref, computed } from 'vue';
import { useBillStore } from '../../stores/bill';
import { useBankStore } from '../../stores/bank';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate, generateId } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, Modal, Tabs, SearchInput, EmptyState } from '../ui';
import type { Bill, BillCategory, BillStatus, BillRecurrence, BillPaymentHistory } from '../../types';

const store = useBillStore();
const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ============ Tabs ============
type TabKey = 'all' | 'upcoming' | 'due_soon' | 'overdue' | 'paid' | 'auto_pay' | BillCategory;
const activeTab = ref<TabKey>('all');
const tabs = [
  { key: 'all', label: 'All Bills', icon: '📋' },
  { key: 'upcoming', label: 'Upcoming', icon: '📅' },
  { key: 'due_soon', label: 'Due Soon', icon: '⏰' },
  { key: 'overdue', label: 'Overdue', icon: '🔴' },
  { key: 'paid', label: 'Paid', icon: '✅' },
  { key: 'auto_pay', label: 'Auto-Pay', icon: '🔄' },
  { key: 'rent', label: 'Rent', icon: '🏠' },
  { key: 'utilities', label: 'Utilities', icon: '💡' },
  { key: 'subscriptions', label: 'Subscriptions', icon: '📺' },
  { key: 'loan_emi', label: 'Loan EMI', icon: '💰' },
  { key: 'insurance_premium', label: 'Insurance', icon: '🛡️' },
  { key: 'credit_card', label: 'Credit Card', icon: '💳' },
  { key: 'education', label: 'Education', icon: '📚' },
  { key: 'medical', label: 'Medical', icon: '🏥' },
  { key: 'vehicle', label: 'Vehicle', icon: '🚗' },
  { key: 'service_contract', label: 'Services', icon: '🔧' },
  { key: 'tax', label: 'Tax', icon: '🧾' },
  { key: 'other', label: 'Other', icon: '📎' },
];

// ============ Search & Sort ============
const searchQuery = ref('');
const sortBy = ref<'dueDate' | 'amount' | 'name'>('dueDate');
const sortDir = ref<'asc' | 'desc'>('asc');

// ============ Modals ============
const showDetailModal = ref(false);
const showAddModal = ref(false);
const showPayModal = ref(false);
const showDeleteConfirm = ref(false);
const selectedBillId = ref<string | null>(null);
const isEditMode = ref(false);

// ============ Config ============
const categoryConfig: Record<BillCategory, { label: string; icon: string; color: string }> = {
  rent: { label: 'Rent / Housing', icon: '🏠', color: '#8b5cf6' },
  utilities: { label: 'Utilities', icon: '💡', color: '#f59e0b' },
  subscriptions: { label: 'Subscriptions', icon: '📺', color: '#ec4899' },
  loan_emi: { label: 'Loan EMI', icon: '💰', color: '#ef4444' },
  insurance_premium: { label: 'Insurance Premium', icon: '🛡️', color: '#10b981' },
  credit_card: { label: 'Credit Card', icon: '💳', color: '#3b82f6' },
  medical: { label: 'Medical', icon: '🏥', color: '#06b6d4' },
  education: { label: 'Education', icon: '📚', color: '#6366f1' },
  vehicle: { label: 'Vehicle', icon: '🚗', color: '#f97316' },
  service_contract: { label: 'Service Contract', icon: '🔧', color: '#84cc16' },
  tax: { label: 'Tax', icon: '🧾', color: '#dc2626' },
  other: { label: 'Other', icon: '📎', color: '#64748b' },
};

const statusConfig: Record<BillStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  upcoming: { variant: 'info', label: 'Upcoming' },
  due_soon: { variant: 'warning', label: 'Due Soon' },
  overdue: { variant: 'danger', label: 'Overdue' },
  paid: { variant: 'success', label: 'Paid' },
  skipped: { variant: 'neutral', label: 'Skipped' },
  cancelled: { variant: 'neutral', label: 'Cancelled' },
};

const recurrenceLabels: Record<string, string> = {
  none: 'One-time', weekly: 'Weekly', biweekly: 'Bi-weekly',
  monthly: 'Monthly', quarterly: 'Quarterly', semiannually: 'Semi-annually', annually: 'Annually',
};

const priorityConfig = {
  high: { label: 'High', color: 'text-danger-500', dot: 'bg-danger-500' },
  medium: { label: 'Medium', color: 'text-warning-500', dot: 'bg-warning-500' },
  low: { label: 'Low', color: 'text-surface-400', dot: 'bg-surface-300' },
};

// ============ Helpers ============
function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') return currencyStore.formatWithCurrency(amount, currency as any);
  return formatCurrency(amount, 'BDT');
}

function daysText(days: number): { label: string; css: string } {
  if (days < 0) return { label: Math.abs(days) + 'd overdue', css: 'text-danger-500' };
  if (days === 0) return { label: 'Due today', css: 'text-danger-500 font-bold' };
  if (days <= 3) return { label: days + 'd left', css: 'text-danger-500' };
  if (days <= 7) return { label: days + 'd left', css: 'text-warning-500' };
  return { label: days + 'd left', css: 'text-surface-400' };
}

function getMonthSummary(): { month: string; due: number; paid: number } {
  const now = new Date();
  const month = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  return { month, due: store.totalDueThisMonth, paid: store.totalPaidThisMonth };
}

// ============ Computed: Filtered ============
const filteredBills = computed(() => {
  let list: Bill[];

  switch (activeTab.value) {
    case 'upcoming': list = store.upcomingBills.filter(b => store.daysUntilDue(b) > 7); break;
    case 'due_soon': list = store.dueSoonBills; break;
    case 'overdue': list = store.overdueBills; break;
    case 'paid': list = store.paidBills; break;
    case 'auto_pay': list = store.autoPayBills; break;
    default:
      if (activeTab.value === 'all') {
        list = store.activeBills;
      } else {
        list = store.getBillsByCategory(activeTab.value as BillCategory);
      }
  }

  // Search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(b =>
      b.name.toLowerCase().includes(q) ||
      b.payeeName.toLowerCase().includes(q) ||
      b.description?.toLowerCase().includes(q) ||
      b.tags?.some(t => t.toLowerCase().includes(q))
    );
  }

  // Sort
  list.sort((a, b) => {
    let cmp = 0;
    if (sortBy.value === 'dueDate') cmp = new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
    else if (sortBy.value === 'amount') cmp = a.amount - b.amount;
    else cmp = a.name.localeCompare(b.name);
    return sortDir.value === 'asc' ? cmp : -cmp;
  });

  return list;
});

const selectedBill = computed(() => {
  if (!selectedBillId.value) return null;
  return store.getBillById(selectedBillId.value) || null;
});

// ============ Add/Edit Form ============
interface BillForm {
  name: string;
  description: string;
  category: BillCategory;
  amount: number;
  currency: string;
  payeeName: string;
  payeeAccount: string;
  payeeWebsite: string;
  dueDate: string;
  gracePeriodDays: number;
  lateFeeAmount: number;
  lateFeePercent: number;
  recurrence: BillRecurrence;
  recurrenceDayOfMonth: number;
  endDate: string;
  autoPayEnabled: boolean;
  autoPayMethod: string;
  autoPayDayBefore: number;
  reminderDaysBefore: number;
  reminderEnabled: boolean;
  priority: 'low' | 'medium' | 'high';
  linkedEntityId: string;
  linkedEntityType: string;
  preferredPaymentAccountId: string;
  notes: string;
  tags: string;
}

const form = ref<BillForm>({
  name: '', description: '', category: 'utilities', amount: 0, currency: 'BDT',
  payeeName: '', payeeAccount: '', payeeWebsite: '',
  dueDate: new Date().toISOString().split('T')[0],
  gracePeriodDays: 0, lateFeeAmount: 0, lateFeePercent: 0,
  recurrence: 'monthly', recurrenceDayOfMonth: 1, endDate: '',
  autoPayEnabled: false, autoPayMethod: '', autoPayDayBefore: 0,
  reminderDaysBefore: 3, reminderEnabled: true,
  priority: 'medium', linkedEntityId: '', linkedEntityType: '', preferredPaymentAccountId: '',
  notes: '', tags: '',
});

function resetForm() {
  form.value = {
    name: '', description: '', category: 'utilities', amount: 0, currency: 'BDT',
    payeeName: '', payeeAccount: '', payeeWebsite: '',
    dueDate: new Date().toISOString().split('T')[0],
    gracePeriodDays: 0, lateFeeAmount: 0, lateFeePercent: 0,
    recurrence: 'monthly', recurrenceDayOfMonth: 1, endDate: '',
    autoPayEnabled: false, autoPayMethod: '', autoPayDayBefore: 0,
    reminderDaysBefore: 3, reminderEnabled: true,
    priority: 'medium', linkedEntityId: '', linkedEntityType: '', preferredPaymentAccountId: '',
    notes: '', tags: '',
  };
  isEditMode.value = false;
}

function openAddModal() {
  resetForm();
  showAddModal.value = true;
}

function openEditModal(bill: Bill) {
  isEditMode.value = true;
  showAddModal.value = true;
  showDetailModal.value = false;
  form.value = {
    name: bill.name,
    description: bill.description || '',
    category: bill.category,
    amount: bill.amount,
    currency: bill.currency || 'BDT',
    payeeName: bill.payeeName,
    payeeAccount: bill.payeeAccount || '',
    payeeWebsite: bill.payeeWebsite || '',
    dueDate: bill.dueDate.split('T')[0],
    gracePeriodDays: bill.gracePeriodDays || 0,
    lateFeeAmount: bill.lateFeeAmount || 0,
    lateFeePercent: bill.lateFeePercent || 0,
    recurrence: bill.recurrence,
    recurrenceDayOfMonth: bill.recurrenceDayOfMonth || 1,
    endDate: bill.endDate ? bill.endDate.split('T')[0] : '',
    autoPayEnabled: bill.autoPayEnabled,
    autoPayMethod: bill.autoPayMethod || '',
    autoPayDayBefore: bill.autoPayDayBefore || 0,
    reminderDaysBefore: bill.reminderDaysBefore,
    reminderEnabled: bill.reminderEnabled,
    priority: bill.priority,
    linkedEntityId: bill.linkedEntityId || '',
    linkedEntityType: bill.linkedEntityType || '',
    preferredPaymentAccountId: bill.preferredPaymentAccountId || '',
    notes: bill.notes || '',
    tags: (bill.tags || []).join(', '),
  };
  editingBillId.value = bill.id;
}

const editingBillId = ref<string | null>(null);

function saveBill() {
  if (!form.value.name.trim() || form.value.amount <= 0) return;
  const tags = form.value.tags ? form.value.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

  const baseData = {
    name: form.value.name.trim(),
    description: form.value.description.trim() || undefined,
    category: form.value.category,
    status: 'upcoming' as BillStatus,
    amount: form.value.amount,
    currency: form.value.currency as any,
    payeeName: form.value.payeeName.trim(),
    payeeAccount: form.value.payeeAccount.trim() || undefined,
    payeeWebsite: form.value.payeeWebsite.trim() || undefined,
    dueDate: new Date(form.value.dueDate).toISOString(),
    dueDateDayOfMonth: form.value.recurrence !== 'none' ? form.value.recurrenceDayOfMonth : undefined,
    gracePeriodDays: form.value.gracePeriodDays || undefined,
    lateFeeAmount: form.value.lateFeeAmount || undefined,
    lateFeePercent: form.value.lateFeePercent || undefined,
    recurrence: form.value.recurrence,
    recurrenceDayOfMonth: form.value.recurrence !== 'none' ? form.value.recurrenceDayOfMonth : undefined,
    endDate: form.value.endDate ? new Date(form.value.endDate).toISOString() : undefined,
    autoPayEnabled: form.value.autoPayEnabled,
    autoPayMethod: form.value.autoPayMethod || undefined,
    autoPayDayBefore: form.value.autoPayDayBefore || undefined,
    paymentHistory: [],
    totalPaidAmount: 0,
    totalPaymentsCount: 0,
    reminderDaysBefore: form.value.reminderDaysBefore,
    reminderEnabled: form.value.reminderEnabled,
    priority: form.value.priority,
    linkedEntityId: form.value.linkedEntityId || undefined,
    linkedEntityType: (form.value.linkedEntityType as any) || undefined,
    preferredPaymentAccountId: form.value.preferredPaymentAccountId || undefined,
    notes: form.value.notes.trim() || undefined,
    tags,
  };

  if (isEditMode.value && editingBillId.value) {
    store.updateBill(editingBillId.value, baseData);
  } else {
    store.addBill(baseData);
  }

  showAddModal.value = false;
  resetForm();
  editingBillId.value = null;
}

// ============ Pay Modal ============
const payForm = ref({
  amount: 0,
  paymentDate: new Date().toISOString().split('T')[0],
  paymentMethod: '',
  referenceNumber: '',
  note: '',
});

function openPayModal(bill: Bill) {
  payForm.value = {
    amount: bill.amount,
    paymentDate: new Date().toISOString().split('T')[0],
    paymentMethod: bill.preferredPaymentAccountId || '',
    referenceNumber: '',
    note: '',
  };
  payingBillId.value = bill.id;
  showPayModal.value = true;
}

const payingBillId = ref<string | null>(null);

function submitPayment() {
  if (!payingBillId.value || payForm.value.amount <= 0) return;
  store.markAsPaid(payingBillId.value, {
    amount: payForm.value.amount,
    paymentDate: new Date(payForm.value.paymentDate).toISOString(),
    paymentMethod: payForm.value.paymentMethod,
    referenceNumber: payForm.value.referenceNumber.trim() || undefined,
    note: payForm.value.note.trim() || undefined,
  });
  showPayModal.value = false;
  showDetailModal.value = false;
  selectedBillId.value = null;
}

// ============ Actions ============
function openDetail(id: string) {
  selectedBillId.value = id;
  showDetailModal.value = true;
}

function confirmDelete() {
  if (!selectedBillId.value) return;
  store.deleteBill(selectedBillId.value);
  showDeleteConfirm.value = false;
  showDetailModal.value = false;
  selectedBillId.value = null;
}

function handleCancel(billId: string) {
  store.cancelBill(billId);
  showDetailModal.value = false;
  selectedBillId.value = null;
}

function handleRestore(billId: string) {
  store.restoreBill(billId);
  showDetailModal.value = false;
  selectedBillId.value = null;
}

function handleToggleAutoPay(billId: string) {
  store.toggleAutoPay(billId);
}

const monthSummary = getMonthSummary();
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Bills" subtitle="Track recurring and one-time bills with due dates & payment history">
      <template #actions>
        <button class="btn-primary" @click="openAddModal()">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Add Bill
        </button>
      </template>
    </PageHeader>

    <!-- Stat Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      <StatCard title="Due This Month" :value="fmtCur(monthSummary.due)" icon="📅" color="primary" />
      <StatCard title="Paid This Month" :value="fmtCur(monthSummary.paid)" icon="✅" color="success" />
      <StatCard title="Upcoming" :value="String(store.upcomingBills.length)" icon="📋" color="info" />
      <StatCard title="Overdue" :value="String(store.overdueBills.length)" :color="store.overdueBills.length > 0 ? 'danger' : 'success'" icon="🔴" />
      <StatCard title="Auto-Pay" :value="String(store.autoPayBills.length)" icon="🔄" color="warning" />
    </div>

    <!-- Overdue Alert -->
    <div v-if="store.overdueBills.length > 0" class="bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/30 rounded-xl p-4">
      <div class="flex items-center gap-3 mb-2">
        <svg class="w-5 h-5 text-danger-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
        <h4 class="font-semibold text-danger-700 dark:text-danger-300">Overdue Bills ({{ store.overdueBills.length }})</h4>
      </div>
      <div class="space-y-2">
        <div v-for="bill in store.overdueBills.slice(0, 5)" :key="bill.id" class="flex items-center justify-between text-sm">
          <span class="text-danger-600 dark:text-danger-400">
            {{ categoryConfig[bill.category]?.icon }} {{ bill.name }}
            <span class="ml-1 font-medium">{{ fmtCur(bill.amount, bill.currency) }}</span>
            <span v-if="store.getLateFee(bill) > 0" class="ml-1 text-xs">(+{{ fmtCur(store.getLateFee(bill)) }} late fee)</span>
          </span>
          <button @click="openDetail(bill.id)" class="text-danger-600 dark:text-danger-400 hover:underline text-xs font-medium">Pay Now</button>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs :tabs="tabs" v-model:activeTab="activeTab" />

    <!-- Search + Sort -->
    <div class="flex flex-col sm:flex-row gap-3">
      <div class="flex-1">
        <SearchInput v-model="searchQuery" placeholder="Search bills by name, payee, tags..." />
      </div>
      <div class="flex gap-2">
        <select v-model="sortBy" class="input-field w-auto text-sm">
          <option value="dueDate">Sort: Due Date</option>
          <option value="amount">Sort: Amount</option>
          <option value="name">Sort: Name</option>
        </select>
        <button @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'" class="px-3 py-2 rounded-lg border border-surface-200 dark:border-surface-700 text-surface-600 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors text-sm">
          {{ sortDir === 'asc' ? '↑' : '↓' }}
        </button>
      </div>
    </div>

    <!-- Bill List -->
    <div v-if="filteredBills.length === 0">
      <EmptyState icon="📋" title="No bills found" :description="searchQuery ? 'Try adjusting your search or filter' : 'Add your first bill to start tracking'">
        <template #action>
          <button class="btn-primary" @click="openAddModal()">Add Bill</button>
        </template>
      </EmptyState>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="bill in filteredBills"
        :key="bill.id"
        class="card border-l-4 p-4 hover:shadow-md transition-all duration-200 cursor-pointer"
        :style="{ borderLeftColor: categoryConfig[bill.category]?.color }"
        :class="{
          'opacity-50': bill.status === 'paid' || bill.status === 'cancelled' || bill.status === 'skipped',
          'bg-danger-50/50 dark:bg-danger-500/5': bill.status === 'overdue',
        }"
        @click="openDetail(bill.id)"
      >
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <!-- Left: Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap mb-1">
              <span class="font-bold text-surface-900 dark:text-white text-sm">{{ bill.name }}</span>
              <span class="text-xs px-1.5 py-0.5 rounded-full shrink-0" :style="{ backgroundColor: categoryConfig[bill.category]?.color + '18', color: categoryConfig[bill.category]?.color }">
                {{ categoryConfig[bill.category]?.icon }} {{ categoryConfig[bill.category]?.label }}
              </span>
              <Badge :variant="statusConfig[bill.status]?.variant || 'neutral'" size="sm">
                {{ statusConfig[bill.status]?.label }}
              </Badge>
              <span v-if="bill.recurrence !== 'none'" class="text-xs px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-700 text-surface-500 shrink-0">🔄 {{ recurrenceLabels[bill.recurrence] }}</span>
              <span v-if="bill.autoPayEnabled" class="text-xs px-1.5 py-0.5 rounded bg-primary-50 dark:bg-primary-500/15 text-primary-600 dark:text-primary-400 shrink-0">Auto-Pay</span>
            </div>
            <div class="flex items-center gap-3 text-xs text-surface-500 dark:text-surface-400">
              <span>{{ bill.payeeName }}</span>
              <span>Due: {{ formatDate(bill.dueDate, 'short') }}</span>
            </div>
            <!-- Progress bar for payment history -->
            <div v-if="bill.paymentHistory.length > 0" class="mt-2 flex items-center gap-2">
              <div class="flex-1 h-1.5 rounded-full bg-surface-200 dark:bg-surface-700 overflow-hidden max-w-[120px]">
                <div class="h-full rounded-full bg-accent-500 transition-all" :style="{ width: Math.min(100, (bill.totalPaymentsCount / Math.max(bill.totalPaymentsCount + 1, 1)) * 100) + '%' }"></div>
              </div>
              <span class="text-xs text-surface-400">{{ bill.totalPaymentsCount }} payments</span>
            </div>
          </div>

          <!-- Right: Amount + Actions -->
          <div class="flex items-center gap-4 lg:gap-6">
            <div class="text-right">
              <p class="font-bold text-surface-900 dark:text-white text-lg tabular-nums">{{ fmtCur(bill.amount, bill.currency) }}</p>
              <p class="text-xs" :class="daysText(store.daysUntilDue(bill)).css">
                {{ daysText(store.daysUntilDue(bill)).label }}
              </p>
              <p v-if="store.getLateFee(bill) > 0" class="text-xs text-danger-500">+{{ fmtCur(store.getLateFee(bill)) }} late fee</p>
            </div>

            <!-- Quick Actions -->
            <div class="flex gap-2 shrink-0" @click.stop>
              <button
                v-if="bill.status === 'overdue' || bill.status === 'upcoming' || bill.status === 'due_soon'"
                @click.stop="openPayModal(bill)"
                class="text-xs px-3 py-1.5 rounded-lg bg-accent-50 dark:bg-accent-500/20 text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-500/30 transition-colors font-medium"
              >
                Pay
              </button>
              <button
                v-if="bill.status === 'paid'"
                @click.stop="openPayModal(bill)"
                class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-500/30 transition-colors font-medium"
              >
                Pay Again
              </button>
              <button
                @click.stop="openDetail(bill.id)"
                class="text-xs px-3 py-1.5 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium"
              >
                View
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== DETAIL MODAL ==================== -->
    <Modal v-if="selectedBill" :is-open="showDetailModal" :title="selectedBill.name" size="xl" @close="showDetailModal = false">
      <div class="space-y-5" v-if="selectedBill">
        <!-- Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl" :style="{ backgroundColor: categoryConfig[selectedBill.category]?.color + '20' }">
            {{ categoryConfig[selectedBill.category]?.icon }}
          </div>
          <div class="flex-1">
            <h3 class="text-lg font-bold text-surface-900 dark:text-white">{{ selectedBill.name }}</h3>
            <p class="text-sm text-surface-500">
              {{ categoryConfig[selectedBill.category]?.label }}
              <span class="mx-1">&middot;</span>
              <span :class="priorityConfig[selectedBill.priority]?.color">{{ priorityConfig[selectedBill.priority]?.label }} priority</span>
              <span v-if="selectedBill.recurrence !== 'none'" class="mx-1">&middot;</span>
              <span v-if="selectedBill.recurrence !== 'none'">🔄 {{ recurrenceLabels[selectedBill.recurrence] }}</span>
            </p>
          </div>
          <Badge :variant="statusConfig[selectedBill.status]?.variant || 'neutral'">
            {{ statusConfig[selectedBill.status]?.label }}
          </Badge>
        </div>

        <!-- Amount + Due Info -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Amount</p>
            <p class="font-bold text-surface-900 dark:text-white text-lg">{{ fmtCur(selectedBill.amount, selectedBill.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Due Date</p>
            <p class="font-semibold text-surface-900 dark:text-white">{{ formatDate(selectedBill.dueDate, 'long') }}</p>
            <p class="text-xs mt-0.5" :class="daysText(store.daysUntilDue(selectedBill)).css">{{ daysText(store.daysUntilDue(selectedBill)).label }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Payee</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ selectedBill.payeeName }}</p>
            <p v-if="selectedBill.payeeAccount" class="text-xs text-surface-400 truncate">{{ selectedBill.payeeAccount }}</p>
          </div>
          <div v-if="selectedBill.totalPaidAmount > 0" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Paid</p>
            <p class="font-semibold text-accent-600 dark:text-accent-400">{{ fmtCur(selectedBill.totalPaidAmount, selectedBill.currency) }}</p>
            <p class="text-xs text-surface-400">{{ selectedBill.totalPaymentsCount }} payments</p>
          </div>
          <div v-if="selectedBill.gracePeriodDays" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Grace Period</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ selectedBill.gracePeriodDays }} days</p>
          </div>
          <div v-if="store.getLateFee(selectedBill) > 0" class="bg-danger-50 dark:bg-danger-500/10 rounded-lg p-3">
            <p class="text-xs text-danger-400 mb-1">Late Fee</p>
            <p class="font-semibold text-danger-600 dark:text-danger-400">{{ fmtCur(store.getLateFee(selectedBill)) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Auto-Pay</p>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full" :class="selectedBill.autoPayEnabled ? 'bg-green-500' : 'bg-surface-300'"></span>
              <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ selectedBill.autoPayEnabled ? 'Enabled' : 'Disabled' }}</p>
            </div>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Reminder</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ selectedBill.reminderEnabled ? selectedBill.reminderDaysBefore + 'd before' : 'Off' }}</p>
          </div>
          <div v-if="selectedBill.endDate" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">End Date</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ formatDate(selectedBill.endDate, 'short') }}</p>
          </div>
        </div>

        <!-- Description -->
        <div v-if="selectedBill.description">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Description</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedBill.description }}</p>
        </div>

        <!-- Payment History -->
        <div v-if="selectedBill.paymentHistory.length > 0">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-2">Payment History ({{ selectedBill.paymentHistory.length }})</h4>
          <div class="space-y-2 max-h-[200px] overflow-y-auto">
            <div v-for="p in [...selectedBill.paymentHistory].reverse()" :key="p.id" class="flex items-center justify-between p-2.5 rounded-lg bg-surface-50 dark:bg-surface-700/30 text-sm">
              <div>
                <p class="font-medium text-surface-900 dark:text-white">{{ fmtCur(p.amount, selectedBill.currency) }}</p>
                <p class="text-xs text-surface-400">{{ formatDate(p.paymentDate, 'short') }}</p>
              </div>
              <div class="text-right">
                <p v-if="p.referenceNumber" class="text-xs text-surface-400">{{ p.referenceNumber }}</p>
                <p v-if="p.note" class="text-xs text-surface-400">{{ p.note }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Tags -->
        <div v-if="selectedBill.tags && selectedBill.tags.length > 0">
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in selectedBill.tags" :key="tag" class="text-sm px-2.5 py-1 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">{{ tag }}</span>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedBill.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedBill.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button
            v-if="selectedBill.status !== 'paid' && selectedBill.status !== 'cancelled'"
            class="btn-primary"
            @click="openPayModal(selectedBill)"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
            Mark as Paid
          </button>
          <button
            v-if="selectedBill.autoPayEnabled"
            class="btn-secondary text-sm"
            @click="handleToggleAutoPay(selectedBill.id)"
          >
            Disable Auto-Pay
          </button>
          <button
            v-else-if="selectedBill.status !== 'cancelled'"
            class="btn-secondary text-sm"
            @click="handleToggleAutoPay(selectedBill.id)"
          >
            Enable Auto-Pay
          </button>
          <button class="btn-secondary text-sm" @click="openEditModal(selectedBill)">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button
            v-if="selectedBill.status === 'paid' || selectedBill.status === 'skipped'"
            class="btn-secondary text-sm"
            @click="handleRestore(selectedBill.id)"
          >
            Restore
          </button>
          <button
            v-if="selectedBill.status !== 'cancelled'"
            class="text-sm px-4 py-2 rounded-lg bg-danger-50 dark:bg-danger-500/20 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/30 transition-colors font-medium"
            @click="handleCancel(selectedBill.id)"
          >
            Cancel
          </button>
          <button
            class="text-sm px-4 py-2 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium"
            @click="showDeleteConfirm = true"
          >
            Delete
          </button>
        </div>
      </div>
    </Modal>

    <!-- ==================== ADD/EDIT BILL MODAL ==================== -->
    <Modal :is-open="showAddModal" :title="isEditMode ? 'Edit Bill' : 'Add New Bill'" size="xl" @close="showAddModal = false">
      <form @submit.prevent="saveBill" class="space-y-5">
        <!-- Name & Payee -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="field-label">Bill Name <span class="text-danger-500">*</span></label>
            <input v-model="form.name" type="text" class="input-field" placeholder="e.g., WASA Water Bill" />
          </div>
          <div>
            <label class="field-label">Category <span class="text-danger-500">*</span></label>
            <select v-model="form.category" class="input-field">
              <option v-for="(cfg, key) in categoryConfig" :key="key" :value="key">{{ cfg.icon }} {{ cfg.label }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Priority</label>
            <select v-model="form.priority" class="input-field">
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div>
            <label class="field-label">Amount (BDT) <span class="text-danger-500">*</span></label>
            <input v-model.number="form.amount" type="number" class="input-field" placeholder="0" min="0" />
          </div>
          <div>
            <label class="field-label">Due Date <span class="text-danger-500">*</span></label>
            <input v-model="form.dueDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Payee Name <span class="text-danger-500">*</span></label>
            <input v-model="form.payeeName" type="text" class="input-field" placeholder="e.g., WASA, DESCO, Netflix" />
          </div>
          <div>
            <label class="field-label">Payee Account</label>
            <input v-model="form.payeeAccount" type="text" class="input-field" placeholder="Account number or reference" />
          </div>
        </div>

        <!-- Recurrence & Dates -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Recurrence</h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Frequency</label>
              <select v-model="form.recurrence" class="input-field">
                <option value="none">One-time</option>
                <option value="weekly">Weekly</option>
                <option value="biweekly">Bi-weekly</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="semiannually">Semi-annually</option>
                <option value="annually">Annually</option>
              </select>
            </div>
            <div v-if="form.recurrence !== 'none'">
              <label class="field-label">Day of Month</label>
              <input v-model.number="form.recurrenceDayOfMonth" type="number" class="input-field" min="1" max="31" />
            </div>
            <div v-if="form.recurrence !== 'none'">
              <label class="field-label">End Date (optional)</label>
              <input v-model="form.endDate" type="date" class="input-field" />
            </div>
          </div>
        </div>

        <!-- Fees & Grace -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Late Fees & Grace Period</h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Grace Period (days)</label>
              <input v-model.number="form.gracePeriodDays" type="number" class="input-field" min="0" />
            </div>
            <div>
              <label class="field-label">Late Fee (BDT)</label>
              <input v-model.number="form.lateFeeAmount" type="number" class="input-field" min="0" />
            </div>
            <div>
              <label class="field-label">Late Fee (%)</label>
              <input v-model.number="form.lateFeePercent" type="number" class="input-field" min="0" max="100" />
            </div>
          </div>
        </div>

        <!-- Auto-Pay & Reminder -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Payment & Reminder</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="flex items-center gap-3">
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="form.autoPayEnabled" class="sr-only peer">
                <div class="w-9 h-5 bg-surface-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
              <span class="text-sm text-surface-700 dark:text-surface-300">Auto-Pay</span>
            </div>
            <div v-if="form.autoPayEnabled">
              <label class="field-label">Pay From Account</label>
              <select v-model="form.autoPayMethod" class="input-field">
                <option value="">Select Account</option>
                <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
              </select>
            </div>
            <div class="flex items-center gap-3">
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="form.reminderEnabled" class="sr-only peer">
                <div class="w-9 h-5 bg-surface-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
              <span class="text-sm text-surface-700 dark:text-surface-300">Reminder</span>
            </div>
            <div v-if="form.reminderEnabled">
              <label class="field-label">Remind before (days)</label>
              <input v-model.number="form.reminderDaysBefore" type="number" class="input-field" min="0" />
            </div>
          </div>
        </div>

        <!-- Notes & Tags -->
        <div>
          <label class="field-label">Description</label>
          <textarea v-model="form.description" class="input-field" rows="2" placeholder="Brief description..."></textarea>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Tags (comma separated)</label>
            <input v-model="form.tags" type="text" class="input-field" placeholder="utility, monthly, desco" />
          </div>
          <div>
            <label class="field-label">Notes</label>
            <input v-model="form.notes" type="text" class="input-field" placeholder="Additional notes..." />
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showAddModal = false">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="!form.name.trim() || form.amount <= 0">
            {{ isEditMode ? 'Update Bill' : 'Add Bill' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- ==================== PAY MODAL ==================== -->
    <Modal :is-open="showPayModal" title="Mark Bill as Paid" size="md" @close="showPayModal = false">
      <form @submit.prevent="submitPayment" class="space-y-4">
        <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-4 text-center">
          <p class="text-sm text-surface-500">Payment Amount</p>
          <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ fmtCur(payForm.amount) }}</p>
        </div>
        <div>
          <label class="field-label">Amount</label>
          <input v-model.number="payForm.amount" type="number" class="input-field" min="0" />
        </div>
        <div>
          <label class="field-label">Payment Date</label>
          <input v-model="payForm.paymentDate" type="date" class="input-field" />
        </div>
        <div>
          <label class="field-label">Paid From</label>
          <select v-model="payForm.paymentMethod" class="input-field">
            <option value="">Select Account</option>
            <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">Reference Number</label>
          <input v-model="payForm.referenceNumber" type="text" class="input-field" placeholder="Transaction ref, cheque no..." />
        </div>
        <div>
          <label class="field-label">Note</label>
          <input v-model="payForm.note" type="text" class="input-field" placeholder="Optional note..." />
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showPayModal = false">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="payForm.amount <= 0">Confirm Payment</button>
        </div>
      </form>
    </Modal>

    <!-- ==================== DELETE CONFIRM ==================== -->
    <Modal :is-open="showDeleteConfirm" title="Delete Bill" size="sm" @close="showDeleteConfirm = false">
      <div class="space-y-4">
        <div class="flex items-center gap-3 p-4 bg-danger-50 dark:bg-danger-500/10 rounded-lg">
          <svg class="w-6 h-6 text-danger-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
          <p class="text-sm text-danger-700 dark:text-danger-300">
            Are you sure you want to delete <strong>"{{ selectedBill?.name }}"</strong>? This will also delete its payment history.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
          <button class="btn-danger" @click="confirmDelete">Delete</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
