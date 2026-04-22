import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Invoice, InvoiceStatus } from '../types';
import { mockInvoices } from '../mock-data/invoices';
import { useCurrencyStore } from './currency';
import { generateId } from '../utils/formatters';

export const useInvoiceStore = defineStore('invoice', () => {
  const invoices = ref<Invoice[]>(mockInvoices.map(i => ({ ...i, items: i.items.map(it => ({ ...it })) })));

  // ==================== Computed: Filtered Lists ====================

  const sentInvoices = computed(() =>
    invoices.value.filter(i => i.type === 'sent').sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  );

  const receivedInvoices = computed(() =>
    invoices.value.filter(i => i.type === 'received').sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  );

  const activeInvoices = computed(() =>
    invoices.value.filter(i => ['draft', 'sent', 'viewed'].includes(i.status))
  );

  const pendingInvoices = computed(() =>
    invoices.value
      .filter(i => i.type === 'received' && ['sent', 'viewed', 'overdue'].includes(i.status))
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  );

  const paidInvoices = computed(() =>
    invoices.value.filter(i => i.status === 'paid')
  );

  const overdueInvoices = computed(() =>
    invoices.value.filter(i => i.status === 'overdue')
  );

  const cancelledInvoices = computed(() =>
    invoices.value.filter(i => i.status === 'cancelled')
  );

  // ==================== Computed: Totals ====================

  const totalSentAmount = computed(() => {
    const currencyStore = useCurrencyStore();
    return sentInvoices.value.reduce((sum, inv) => sum + currencyStore.convertToBase(inv.totalAmount, inv.currency || 'BDT'), 0);
  });

  const totalReceivedAmount = computed(() => {
    const currencyStore = useCurrencyStore();
    return receivedInvoices.value.reduce((sum, inv) => sum + currencyStore.convertToBase(inv.totalAmount, inv.currency || 'BDT'), 0);
  });

  const totalPendingAmount = computed(() => {
    const currencyStore = useCurrencyStore();
    return pendingInvoices.value.reduce((sum, inv) => sum + currencyStore.convertToBase(inv.totalAmount, inv.currency || 'BDT'), 0);
  });

  const totalOverdueAmount = computed(() => {
    const currencyStore = useCurrencyStore();
    return overdueInvoices.value.reduce((sum, inv) => sum + currencyStore.convertToBase(inv.totalAmount, inv.currency || 'BDT'), 0);
  });

  // ==================== Computed: Next Invoice Number ====================

  const nextInvoiceNumber = computed(() => {
    const year = new Date().getFullYear();
    const existingNumbers = invoices.value
      .map(inv => {
        const match = inv.invoiceNumber.match(/INV-\d{4}-(\d+)/);
        return match ? parseInt(match[1]) : 0;
      })
      .filter(n => n > 0);

    const nextNum = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1;
    return `INV-${year}-${String(nextNum).padStart(3, '0')}`;
  });

  // ==================== Methods ====================

  function addInvoice(data: Omit<Invoice, 'id' | 'createdAt' | 'updatedAt' | 'invoiceNumber'>) {
    const now = new Date().toISOString();
    const invoice: Invoice = {
      ...data,
      id: generateId('inv'),
      invoiceNumber: nextInvoiceNumber.value,
      createdAt: now,
      updatedAt: now,
    };
    invoices.value.push(invoice);
    return invoice;
  }

  function updateInvoice(id: string, data: Partial<Invoice>) {
    const index = invoices.value.findIndex(i => i.id === id);
    if (index === -1) return null;
    invoices.value[index] = {
      ...invoices.value[index],
      ...data,
      id: invoices.value[index].id,
      createdAt: invoices.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return invoices.value[index];
  }

  function deleteInvoice(id: string) {
    const index = invoices.value.findIndex(i => i.id === id);
    if (index !== -1) {
      invoices.value.splice(index, 1);
    }
  }

  function sendInvoice(id: string) {
    const index = invoices.value.findIndex(i => i.id === id);
    if (index === -1) return;
    const inv = invoices.value[index];
    if (inv.status !== 'draft') return;

    const today = new Date();
    const dueDate = new Date(today);
    dueDate.setDate(dueDate.getDate() + 15);

    invoices.value[index] = {
      ...inv,
      status: 'sent',
      issueDate: today.toISOString().split('T')[0],
      dueDate: dueDate.toISOString().split('T')[0],
      updatedAt: new Date().toISOString(),
    };
  }

  function markAsPaid(id: string) {
    const index = invoices.value.findIndex(i => i.id === id);
    if (index === -1) return;
    const inv = invoices.value[index];
    if (inv.status === 'paid' || inv.status === 'cancelled' || inv.status === 'draft') return;

    invoices.value[index] = {
      ...inv,
      status: 'paid',
      paidDate: new Date().toISOString().split('T')[0],
      updatedAt: new Date().toISOString(),
    };
  }

  function cancelInvoice(id: string) {
    const index = invoices.value.findIndex(i => i.id === id);
    if (index === -1) return;
    const inv = invoices.value[index];
    if (inv.status === 'paid' || inv.status === 'cancelled') return;

    invoices.value[index] = {
      ...inv,
      status: 'cancelled',
      updatedAt: new Date().toISOString(),
    };
  }

  function getInvoiceById(id: string): Invoice | undefined {
    return invoices.value.find(i => i.id === id);
  }

  function getInvoiceStats() {
    const counts: Record<InvoiceStatus, number> = {
      draft: 0,
      sent: 0,
      viewed: 0,
      paid: 0,
      overdue: 0,
      cancelled: 0,
    };
    invoices.value.forEach(inv => {
      counts[inv.status]++;
    });
    return {
      counts,
      total: invoices.value.length,
      sentCount: sentInvoices.value.length,
      receivedCount: receivedInvoices.value.length,
      activeCount: activeInvoices.value.length,
      pendingCount: pendingInvoices.value.length,
      overdueCount: overdueInvoices.value.length,
      paidCount: paidInvoices.value.length,
      cancelledCount: cancelledInvoices.value.length,
    };
  }

  return {
    invoices,
    sentInvoices,
    receivedInvoices,
    activeInvoices,
    pendingInvoices,
    paidInvoices,
    overdueInvoices,
    cancelledInvoices,
    totalSentAmount,
    totalReceivedAmount,
    totalPendingAmount,
    totalOverdueAmount,
    nextInvoiceNumber,
    addInvoice,
    updateInvoice,
    deleteInvoice,
    sendInvoice,
    markAsPaid,
    cancelInvoice,
    getInvoiceById,
    getInvoiceStats,
  };
});
