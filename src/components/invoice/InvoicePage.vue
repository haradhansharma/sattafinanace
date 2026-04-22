<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useInvoiceStore } from '../../stores/invoice';
import { useBankStore } from '../../stores/bank';
import { useCurrencyStore } from '../../stores/currency';
import { formatDate, generateId } from '../../utils/formatters';
import type { Invoice, InvoiceItem, InvoiceStatus, Currency } from '../../types';
import { PageHeader, StatCard, Modal, Badge, Tabs, SearchInput, EmptyState } from '../ui';

const invoiceStore = useInvoiceStore();
const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ==================== Tabs ====================
const mainTabs = [
  { key: 'all', label: 'All Invoices', icon: '📋' },
  { key: 'sent', label: 'Sent', icon: '📤' },
  { key: 'received', label: 'Received', icon: '📥' },
  { key: 'drafts', label: 'Drafts', icon: '📝' },
  { key: 'pending', label: 'Pending', icon: '⏳' },
];
const activeTab = ref('all');

// ==================== Search & Filter ====================
const searchQuery = ref('');
const statusFilter = ref<string>('all');

// ==================== Modals ====================
const showCreateModal = ref(false);
const showDetailModal = ref(false);
const selectedInvoiceId = ref<string | null>(null);
const isEditMode = ref(false);

// ==================== Status Helpers ====================
function statusBadge(status: InvoiceStatus): { label: string; variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral' } {
  const map: Record<InvoiceStatus, { label: string; variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral' }> = {
    draft: { label: 'Draft', variant: 'neutral' },
    sent: { label: 'Sent', variant: 'info' },
    viewed: { label: 'Viewed', variant: 'warning' },
    paid: { label: 'Paid', variant: 'success' },
    overdue: { label: 'Overdue', variant: 'danger' },
    cancelled: { label: 'Cancelled', variant: 'neutral' },
  };
  return map[status];
}

function statusBorderClass(status: InvoiceStatus): string {
  const map: Record<InvoiceStatus, string> = {
    draft: 'border-l-surface-400 dark:border-l-surface-600',
    sent: 'border-l-primary-500',
    viewed: 'border-l-amber-400 dark:border-l-amber-500',
    paid: 'border-l-accent-500',
    overdue: 'border-l-danger-500',
    cancelled: 'border-l-surface-300 dark:border-l-surface-700',
  };
  return map[status];
}

// ==================== Computed: Filtered Invoices ====================
const filteredInvoices = computed(() => {
  let list: Invoice[];

  switch (activeTab.value) {
    case 'sent': list = invoiceStore.sentInvoices; break;
    case 'received': list = invoiceStore.receivedInvoices; break;
    case 'drafts': list = invoiceStore.invoices.filter(i => i.status === 'draft'); break;
    case 'pending': list = invoiceStore.pendingInvoices; break;
    default: list = [...invoiceStore.invoices];
  }

  // Status filter (only on 'all' tab)
  if (activeTab.value === 'all' && statusFilter.value !== 'all') {
    list = list.filter(i => i.status === statusFilter.value);
  }

  // Search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(i =>
      i.clientName.toLowerCase().includes(q) ||
      i.invoiceNumber.toLowerCase().includes(q) ||
      i.items.some(item => item.description.toLowerCase().includes(q))
    );
  }

  return list.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
});

// ==================== Computed: Stats ====================
const stats = computed(() => invoiceStore.getInvoiceStats());

// ==================== Selected Invoice ====================
const selectedInvoice = computed(() => {
  if (!selectedInvoiceId.value) return null;
  return invoiceStore.getInvoiceById(selectedInvoiceId.value) || null;
});

// ==================== Form State ====================
interface InvoiceFormItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
}

const form = ref({
  type: 'sent' as 'sent' | 'received',
  clientName: '',
  clientEmail: '',
  clientPhone: '',
  clientAddress: '',
  currency: 'BDT' as Currency,
  taxRate: 0,
  discountAmount: 0,
  issueDate: new Date().toISOString().split('T')[0],
  dueDate: '',
  notes: '',
  bankAccountId: '',
  items: [
    { id: generateId('item'), description: '', quantity: 1, unitPrice: 0 } as InvoiceFormItem,
  ],
});

// ==================== Computed Form Totals ====================
const formSubtotal = computed(() =>
  form.value.items.reduce((sum, item) => sum + (item.quantity * item.unitPrice), 0)
);

const formTaxAmount = computed(() =>
  Math.round((formSubtotal.value * form.value.taxRate) / 100)
);

const formTotalAmount = computed(() =>
  formSubtotal.value + formTaxAmount.value - form.value.discountAmount
);

// ==================== Form Methods ====================
function resetForm() {
  form.value = {
    type: 'sent',
    clientName: '',
    clientEmail: '',
    clientPhone: '',
    clientAddress: '',
    currency: 'BDT',
    taxRate: 0,
    discountAmount: 0,
    issueDate: new Date().toISOString().split('T')[0],
    dueDate: '',
    notes: '',
    bankAccountId: '',
    items: [
      { id: generateId('item'), description: '', quantity: 1, unitPrice: 0 },
    ],
  };
  isEditMode.value = false;
}

function openCreateModal() {
  resetForm();
  showCreateModal.value = true;
}

function openEditModal(invoice: Invoice) {
  isEditMode.value = true;
  showCreateModal.value = true;
  showDetailModal.value = false;

  const dueDate = invoice.dueDate || '';
  form.value = {
    type: invoice.type,
    clientName: invoice.clientName,
    clientEmail: invoice.clientEmail || '',
    clientPhone: invoice.clientPhone || '',
    clientAddress: invoice.clientAddress || '',
    currency: invoice.currency || 'BDT',
    taxRate: invoice.taxRate,
    discountAmount: invoice.discountAmount,
    issueDate: invoice.issueDate || new Date().toISOString().split('T')[0],
    dueDate,
    notes: invoice.notes || '',
    bankAccountId: invoice.bankAccountId || '',
    items: invoice.items.map(item => ({
      id: item.id,
      description: item.description,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
    })),
  };

  // Store the invoice id for editing
  editingInvoiceId.value = invoice.id;
}

const editingInvoiceId = ref<string | null>(null);

function addFormItem() {
  form.value.items.push({ id: generateId('item'), description: '', quantity: 1, unitPrice: 0 });
}

function removeFormItem(index: number) {
  if (form.value.items.length <= 1) return;
  form.value.items.splice(index, 1);
}

function saveAsDraft() {
  saveInvoice('draft');
}

function saveAndSend() {
  saveInvoice('sent');
}

function saveInvoice(status: 'draft' | 'sent') {
  if (!form.value.clientName.trim()) return;
  const hasValidItem = form.value.items.some(item => item.description.trim() && item.unitPrice > 0);
  if (!hasValidItem) return;

  const invoiceItems: InvoiceItem[] = form.value.items
    .filter(item => item.description.trim())
    .map(item => ({
      id: item.id,
      description: item.description,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      total: item.quantity * item.unitPrice,
    }));

  const subtotal = invoiceItems.reduce((sum, item) => sum + item.total, 0);
  const taxAmount = Math.round((subtotal * form.value.taxRate) / 100);
  const totalAmount = subtotal + taxAmount - form.value.discountAmount;

  const baseData = {
    type: form.value.type,
    clientName: form.value.clientName.trim(),
    clientEmail: form.value.clientEmail.trim() || undefined,
    clientPhone: form.value.clientPhone.trim() || undefined,
    clientAddress: form.value.clientAddress.trim() || undefined,
    items: invoiceItems,
    subtotal,
    taxRate: form.value.taxRate,
    taxAmount,
    discountAmount: form.value.discountAmount,
    totalAmount,
    currency: form.value.currency,
    status: status as InvoiceStatus,
    issueDate: status === 'sent' ? form.value.issueDate : '',
    dueDate: status === 'sent' ? form.value.dueDate : '',
    notes: form.value.notes.trim() || undefined,
    bankAccountId: form.value.bankAccountId || undefined,
  };

  if (isEditMode.value && editingInvoiceId.value) {
    invoiceStore.updateInvoice(editingInvoiceId.value, baseData);
  } else {
    invoiceStore.addInvoice(baseData);
  }

  showCreateModal.value = false;
  resetForm();
  editingInvoiceId.value = null;
}

// ==================== Detail Modal ====================
function openDetailModal(id: string) {
  selectedInvoiceId.value = id;
  showDetailModal.value = true;
}

function handleSendInvoice(id: string) {
  invoiceStore.sendInvoice(id);
}

function handleMarkAsPaid(id: string) {
  invoiceStore.markAsPaid(id);
}

function handleCancelInvoice(id: string) {
  invoiceStore.cancelInvoice(id);
}

function handleDeleteInvoice(id: string) {
  if (confirm('Are you sure you want to delete this invoice?')) {
    invoiceStore.deleteInvoice(id);
    showDetailModal.value = false;
  }
}

// ==================== Format Helpers ====================
function formatAmount(amount: number, currency?: Currency): string {
  return currencyStore.formatWithCurrency(amount, currency || 'BDT');
}

function formatBaseAmount(amount: number, currency?: Currency): string {
  const base = currencyStore.convertToBase(amount, currency || 'BDT');
  return currencyStore.formatWithCurrency(base, currencyStore.baseCurrency);
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Invoices" subtitle="Manage your invoices and billing">
      <template #actions>
        <button @click="openCreateModal" class="btn-primary">
          <span>+ New Invoice</span>
        </button>
      </template>
    </PageHeader>

    <!-- Stat Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      <StatCard
        title="Total Sent"
        :value="formatBaseAmount(invoiceStore.totalSentAmount)"
        :change="undefined"
        icon="📤"
        color="primary"
      />
      <StatCard
        title="Total Received"
        :value="formatBaseAmount(invoiceStore.totalReceivedAmount)"
        :change="undefined"
        icon="📥"
        color="warning"
      />
      <StatCard
        title="Pending Payment"
        :value="formatBaseAmount(invoiceStore.totalPendingAmount)"
        :change="undefined"
        icon="⏳"
        color="warning"
      />
      <StatCard
        title="Overdue"
        :value="formatBaseAmount(invoiceStore.totalOverdueAmount)"
        :change="undefined"
        icon="⚠️"
        color="danger"
      />
      <StatCard
        title="Active"
        :value="String(stats.activeCount)"
        :change="undefined"
        icon="🔄"
        color="accent"
      />
    </div>

    <!-- Tabs -->
    <Tabs :tabs="mainTabs" v-model:activeTab="activeTab" />

    <!-- Search + Filter Bar -->
    <div class="flex flex-col sm:flex-row gap-4">
      <div class="flex-1">
        <SearchInput v-model="searchQuery" placeholder="Search invoices by client, number..." />
      </div>
      <div v-if="activeTab === 'all'" class="w-full sm:w-48">
        <select v-model="statusFilter" class="input-field">
          <option value="all">All Status</option>
          <option value="draft">Draft</option>
          <option value="sent">Sent</option>
          <option value="viewed">Viewed</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
    </div>

    <!-- Invoice List -->
    <div v-if="filteredInvoices.length === 0">
      <EmptyState
        icon="📄"
        title="No invoices found"
        :description="searchQuery ? 'Try adjusting your search criteria' : 'Create your first invoice to get started'"
      >
        <template #action>
          <button @click="openCreateModal" class="btn-primary mt-4">
            <span>+ New Invoice</span>
          </button>
        </template>
      </EmptyState>
    </div>
    <div v-else class="space-y-3 max-h-[calc(100vh-420px)] overflow-y-auto pr-1">
      <div
        v-for="invoice in filteredInvoices"
        :key="invoice.id"
        class="card border-l-4 p-4 hover:shadow-md transition-all duration-200 cursor-pointer"
        :class="[
          statusBorderClass(invoice.status),
          invoice.status === 'cancelled' ? 'opacity-60' : '',
        ]"
        @click="openDetailModal(invoice.id)"
      >
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <!-- Left: Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap mb-1">
              <span class="font-bold text-surface-900 dark:text-white text-sm">{{ invoice.invoiceNumber }}</span>
              <Badge :variant="statusBadge(invoice.status).variant" size="sm">
                {{ statusBadge(invoice.status).label }}
              </Badge>
              <Badge :variant="invoice.type === 'sent' ? 'info' : 'warning'" size="sm">
                {{ invoice.type === 'sent' ? '↗ Sent' : '↙ Received' }}
              </Badge>
            </div>
            <p class="text-sm text-surface-700 dark:text-surface-300 font-medium truncate">{{ invoice.clientName }}</p>
            <div class="flex items-center gap-4 mt-1.5 text-xs text-surface-500 dark:text-surface-400">
              <span v-if="invoice.issueDate">Issued: {{ formatDate(invoice.issueDate, 'short') }}</span>
              <span v-if="invoice.dueDate">Due: {{ formatDate(invoice.dueDate, 'short') }}</span>
            </div>
          </div>

          <!-- Right: Amount + Actions -->
          <div class="flex items-center gap-4 lg:gap-6">
            <div class="text-right">
              <p class="font-bold text-surface-900 dark:text-white text-lg tabular-nums">
                {{ formatAmount(invoice.totalAmount, invoice.currency) }}
              </p>
              <p
                v-if="invoice.currency && invoice.currency !== currencyStore.baseCurrency"
                class="text-[11px] text-surface-400 tabular-nums"
              >
                ≈ {{ formatBaseAmount(invoice.totalAmount, invoice.currency) }}
              </p>
            </div>

            <!-- Quick Actions -->
            <div class="flex gap-2 shrink-0" @click.stop>
              <button
                v-if="invoice.status === 'draft'"
                @click.stop="handleSendInvoice(invoice.id)"
                class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-500/30 transition-colors font-medium"
              >
                Send
              </button>
              <button
                v-if="invoice.type === 'received' && ['sent', 'viewed', 'overdue'].includes(invoice.status)"
                @click.stop="handleMarkAsPaid(invoice.id)"
                class="text-xs px-3 py-1.5 rounded-lg bg-accent-50 dark:bg-accent-500/20 text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-500/30 transition-colors font-medium"
              >
                Pay
              </button>
              <button
                v-if="invoice.type === 'sent' && ['sent', 'viewed'].includes(invoice.status)"
                @click.stop="handleMarkAsPaid(invoice.id)"
                class="text-xs px-3 py-1.5 rounded-lg bg-accent-50 dark:bg-accent-500/20 text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-500/30 transition-colors font-medium"
              >
                Mark Paid
              </button>
              <button
                @click.stop="openDetailModal(invoice.id)"
                class="text-xs px-3 py-1.5 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium"
              >
                View
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Create/Edit Invoice Modal ==================== -->
    <Modal
      :is-open="showCreateModal"
      :title="isEditMode ? 'Edit Invoice' : 'New Invoice'"
      size="xl"
      @close="showCreateModal = false"
    >
      <form @submit.prevent="saveAndSend" class="space-y-5">
        <!-- Type Toggle -->
        <div class="flex gap-3">
          <button
            type="button"
            @click="form.type = 'sent'"
            class="flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors"
            :class="form.type === 'sent'
              ? 'bg-primary-100 dark:bg-primary-500/20 text-primary-700 dark:text-primary-400 border-2 border-primary-500'
              : 'bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400 border-2 border-transparent'"
          >
            ↗ Sent (I'm billing someone)
          </button>
          <button
            type="button"
            @click="form.type = 'received'"
            class="flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors"
            :class="form.type === 'received'
              ? 'bg-warning-50 dark:bg-warning-500/20 text-amber-700 dark:text-amber-400 border-2 border-amber-500'
              : 'bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400 border-2 border-transparent'"
          >
            ↙ Received (Someone billed me)
          </button>
        </div>

        <!-- Client Info -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Client Information</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="field-label">Client Name <span class="text-danger-500">*</span></label>
              <input v-model="form.clientName" type="text" placeholder="Client or company name" class="input-field" />
            </div>
            <div>
              <label class="field-label">Email</label>
              <input v-model="form.clientEmail" type="email" placeholder="email@example.com" class="input-field" />
            </div>
            <div>
              <label class="field-label">Phone</label>
              <input v-model="form.clientPhone" type="tel" placeholder="+880 ..." class="input-field" />
            </div>
            <div>
              <label class="field-label">Address</label>
              <input v-model="form.clientAddress" type="text" placeholder="Client address" class="input-field" />
            </div>
          </div>
        </div>

        <!-- Items -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <h4 class="text-sm font-semibold text-surface-900 dark:text-white">Line Items</h4>
            <button type="button" @click="addFormItem" class="text-xs px-3 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-500/30 transition-colors font-medium">
              + Add Item
            </button>
          </div>
          <div class="space-y-2">
            <div
              v-for="(item, index) in form.items"
              :key="item.id"
              class="grid grid-cols-12 gap-2 items-end"
            >
              <div class="col-span-12 sm:col-span-5">
                <label v-if="index === 0" class="field-label">Description</label>
                <input v-model="item.description" type="text" placeholder="Item description" class="input-field text-sm" />
              </div>
              <div class="col-span-4 sm:col-span-2">
                <label v-if="index === 0" class="field-label">Qty</label>
                <input v-model.number="item.quantity" type="number" min="1" class="input-field text-sm" />
              </div>
              <div class="col-span-4 sm:col-span-2">
                <label v-if="index === 0" class="field-label">Unit Price</label>
                <input v-model.number="item.unitPrice" type="number" min="0" class="input-field text-sm" />
              </div>
              <div class="col-span-3 sm:col-span-2 flex items-center gap-2">
                <div class="flex-1">
                  <label v-if="index === 0" class="field-label">Total</label>
                  <div class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums py-2">
                    {{ formatAmount(item.quantity * item.unitPrice, form.currency) }}
                  </div>
                </div>
                <button
                  v-if="form.items.length > 1"
                  type="button"
                  @click="removeFormItem(index)"
                  class="p-2 text-danger-400 hover:text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-500/20 rounded-lg transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Totals -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4 space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-surface-500 dark:text-surface-400">Subtotal</span>
            <span class="text-surface-900 dark:text-white font-medium tabular-nums">{{ formatAmount(formSubtotal, form.currency) }}</span>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label text-xs">Tax Rate (%)</label>
              <input v-model.number="form.taxRate" type="number" min="0" max="100" class="input-field text-sm" />
            </div>
            <div>
              <label class="field-label text-xs">Tax Amount</label>
              <div class="py-2 text-sm font-medium text-surface-900 dark:text-white tabular-nums">
                {{ formatAmount(formTaxAmount, form.currency) }}
              </div>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label text-xs">Discount</label>
              <input v-model.number="form.discountAmount" type="number" min="0" class="input-field text-sm" />
            </div>
            <div>
              <label class="field-label text-xs">Total Amount</label>
              <div class="py-2 text-lg font-bold text-primary-600 dark:text-primary-400 tabular-nums">
                {{ formatAmount(formTotalAmount, form.currency) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Dates, Currency, Bank, Notes -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="field-label">Currency</label>
            <select v-model="form.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div>
            <label class="field-label">Issue Date</label>
            <input v-model="form.issueDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Due Date</label>
            <input v-model="form.dueDate" type="date" class="input-field" />
          </div>
          <div v-if="form.type === 'sent'">
            <label class="field-label">Bank Account (for payment)</label>
            <select v-model="form.bankAccountId" class="input-field">
              <option value="">Select Account</option>
              <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">
                {{ acc.bankName }} - {{ acc.accountNumber }}
              </option>
            </select>
          </div>
        </div>

        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="form.notes" rows="2" placeholder="Additional notes..." class="input-field resize-none"></textarea>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" @click="showCreateModal = false" class="btn-secondary">Cancel</button>
          <button type="button" @click="saveAsDraft" class="btn-secondary">
            Save Draft
          </button>
          <button type="submit" class="btn-primary">
            {{ isEditMode ? 'Update Invoice' : 'Save & Send' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- ==================== Invoice Detail Modal ==================== -->
    <Modal
      :is-open="showDetailModal"
      title="Invoice Details"
      size="xl"
      @close="showDetailModal = false"
    >
      <div v-if="selectedInvoice" class="space-y-5">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedInvoice.invoiceNumber }}</h3>
              <Badge :variant="statusBadge(selectedInvoice.status).variant">
                {{ statusBadge(selectedInvoice.status).label }}
              </Badge>
              <Badge :variant="selectedInvoice.type === 'sent' ? 'info' : 'warning'" size="sm">
                {{ selectedInvoice.type === 'sent' ? '↗ Sent' : '↙ Received' }}
              </Badge>
            </div>
            <p class="text-sm text-surface-500 dark:text-surface-400 mt-1">
              Created: {{ formatDate(selectedInvoice.createdAt, 'long') }}
            </p>
          </div>
          <div class="text-right">
            <p class="text-2xl font-bold text-surface-900 dark:text-white tabular-nums">
              {{ formatAmount(selectedInvoice.totalAmount, selectedInvoice.currency) }}
            </p>
            <p
              v-if="selectedInvoice.currency && selectedInvoice.currency !== currencyStore.baseCurrency"
              class="text-xs text-surface-400 tabular-nums mt-0.5"
            >
              ≈ {{ formatBaseAmount(selectedInvoice.totalAmount, selectedInvoice.currency) }}
            </p>
          </div>
        </div>

        <!-- Client Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-2">
            {{ selectedInvoice.type === 'sent' ? 'Bill To' : 'Billed By' }}
          </h4>
          <p class="font-medium text-surface-900 dark:text-white">{{ selectedInvoice.clientName }}</p>
          <p v-if="selectedInvoice.clientEmail" class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">{{ selectedInvoice.clientEmail }}</p>
          <p v-if="selectedInvoice.clientPhone" class="text-sm text-surface-500 dark:text-surface-400">{{ selectedInvoice.clientPhone }}</p>
          <p v-if="selectedInvoice.clientAddress" class="text-sm text-surface-500 dark:text-surface-400">{{ selectedInvoice.clientAddress }}</p>
        </div>

        <!-- Dates -->
        <div class="grid grid-cols-3 gap-4">
          <div v-if="selectedInvoice.issueDate">
            <p class="text-xs text-surface-500 dark:text-surface-400">Issue Date</p>
            <p class="text-sm font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInvoice.issueDate) }}</p>
          </div>
          <div v-if="selectedInvoice.dueDate">
            <p class="text-xs text-surface-500 dark:text-surface-400">Due Date</p>
            <p class="text-sm font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInvoice.dueDate) }}</p>
          </div>
          <div v-if="selectedInvoice.paidDate">
            <p class="text-xs text-surface-500 dark:text-surface-400">Paid Date</p>
            <p class="text-sm font-medium text-accent-600 dark:text-accent-400">{{ formatDate(selectedInvoice.paidDate) }}</p>
          </div>
        </div>

        <!-- Items Table -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-2">Items</h4>
          <div class="border border-surface-200 dark:border-surface-700 rounded-lg overflow-hidden">
            <table class="w-full text-sm">
              <thead class="bg-surface-100 dark:bg-surface-800">
                <tr>
                  <th class="text-left px-4 py-2 text-xs font-medium text-surface-500 dark:text-surface-400">Description</th>
                  <th class="text-center px-3 py-2 text-xs font-medium text-surface-500 dark:text-surface-400 w-20">Qty</th>
                  <th class="text-right px-3 py-2 text-xs font-medium text-surface-500 dark:text-surface-400 w-28">Unit Price</th>
                  <th class="text-right px-4 py-2 text-xs font-medium text-surface-500 dark:text-surface-400 w-28">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in selectedInvoice.items"
                  :key="item.id"
                  class="border-t border-surface-200 dark:border-surface-700"
                >
                  <td class="px-4 py-2.5 text-surface-900 dark:text-white">{{ item.description }}</td>
                  <td class="px-3 py-2.5 text-center text-surface-600 dark:text-surface-400 tabular-nums">{{ item.quantity }}</td>
                  <td class="px-3 py-2.5 text-right text-surface-600 dark:text-surface-400 tabular-nums">{{ formatAmount(item.unitPrice, selectedInvoice.currency) }}</td>
                  <td class="px-4 py-2.5 text-right font-medium text-surface-900 dark:text-white tabular-nums">{{ formatAmount(item.total, selectedInvoice.currency) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Totals -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4 space-y-1.5 max-w-xs ml-auto">
          <div class="flex justify-between text-sm">
            <span class="text-surface-500 dark:text-surface-400">Subtotal</span>
            <span class="text-surface-900 dark:text-white tabular-nums">{{ formatAmount(selectedInvoice.subtotal, selectedInvoice.currency) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-surface-500 dark:text-surface-400">Tax ({{ selectedInvoice.taxRate }}%)</span>
            <span class="text-surface-900 dark:text-white tabular-nums">{{ formatAmount(selectedInvoice.taxAmount, selectedInvoice.currency) }}</span>
          </div>
          <div v-if="selectedInvoice.discountAmount > 0" class="flex justify-between text-sm">
            <span class="text-surface-500 dark:text-surface-400">Discount</span>
            <span class="text-accent-600 dark:text-accent-400 tabular-nums">-{{ formatAmount(selectedInvoice.discountAmount, selectedInvoice.currency) }}</span>
          </div>
          <div class="flex justify-between text-base font-bold pt-2 border-t border-surface-200 dark:border-surface-700">
            <span class="text-surface-900 dark:text-white">Total</span>
            <span class="text-primary-600 dark:text-primary-400 tabular-nums">{{ formatAmount(selectedInvoice.totalAmount, selectedInvoice.currency) }}</span>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedInvoice.notes">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedInvoice.notes }}</p>
        </div>

        <!-- Payment Note -->
        <div v-if="selectedInvoice.status === 'paid' && selectedInvoice.paidDate" class="bg-accent-50 dark:bg-accent-500/10 border border-accent-200 dark:border-accent-500/30 rounded-lg p-3">
          <p class="text-sm text-accent-700 dark:text-accent-400 font-medium">✓ Payment received on {{ formatDate(selectedInvoice.paidDate) }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-2 pt-4 border-t border-surface-200 dark:border-surface-700">
          <!-- Draft actions -->
          <template v-if="selectedInvoice.status === 'draft'">
            <button @click="openEditModal(selectedInvoice)" class="btn-secondary text-sm">Edit</button>
            <button @click="handleSendInvoice(selectedInvoice.id)" class="btn-primary text-sm">Send Invoice</button>
            <button @click="handleCancelInvoice(selectedInvoice.id)" class="text-sm px-4 py-2 rounded-lg bg-danger-50 dark:bg-danger-500/20 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/30 transition-colors font-medium">Cancel</button>
          </template>

          <!-- Sent actions -->
          <template v-else-if="selectedInvoice.status === 'sent'">
            <button
              v-if="selectedInvoice.type === 'received'"
              @click="handleMarkAsPaid(selectedInvoice.id)"
              class="btn-primary text-sm"
            >Mark as Paid</button>
            <button
              v-else-if="selectedInvoice.type === 'sent'"
              @click="handleMarkAsPaid(selectedInvoice.id)"
              class="btn-primary text-sm"
            >Mark as Paid</button>
            <button @click="handleCancelInvoice(selectedInvoice.id)" class="text-sm px-4 py-2 rounded-lg bg-danger-50 dark:bg-danger-500/20 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/30 transition-colors font-medium">Cancel</button>
          </template>

          <!-- Viewed actions -->
          <template v-else-if="selectedInvoice.status === 'viewed'">
            <button
              v-if="selectedInvoice.type === 'received'"
              @click="handleMarkAsPaid(selectedInvoice.id)"
              class="btn-primary text-sm"
            >Mark as Paid</button>
            <button
              v-else
              @click="handleMarkAsPaid(selectedInvoice.id)"
              class="btn-primary text-sm"
            >Mark as Paid</button>
            <button @click="handleCancelInvoice(selectedInvoice.id)" class="text-sm px-4 py-2 rounded-lg bg-danger-50 dark:bg-danger-500/20 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/30 transition-colors font-medium">Cancel</button>
          </template>

          <!-- Overdue actions -->
          <template v-else-if="selectedInvoice.status === 'overdue'">
            <button
              @click="handleMarkAsPaid(selectedInvoice.id)"
              class="btn-primary text-sm"
            >Mark as Paid</button>
            <button @click="handleCancelInvoice(selectedInvoice.id)" class="text-sm px-4 py-2 rounded-lg bg-danger-50 dark:bg-danger-500/20 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/30 transition-colors font-medium">Cancel</button>
          </template>

          <!-- Paid / Cancelled: View only + delete -->
          <template v-else>
            <button
              @click="handleDeleteInvoice(selectedInvoice.id)"
              class="text-sm px-4 py-2 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium"
            >Delete</button>
          </template>
        </div>
      </div>
    </Modal>
  </div>
</template>
