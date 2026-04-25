import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Invoice, InvoiceItem, InvoiceStatus } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';
import { useCurrencyStore } from './currency';

export const useInvoiceStore = defineStore('invoice', () => {
  // ==================== State ====================
  const invoices = ref<Invoice[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchInvoices(params?: {
    type?: string;
    status?: string;
    clientName?: string;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      invoices.value = await fetchAllPages<Invoice>('/invoice/', { params });
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch invoices';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchInvoiceById(id: string): Promise<Invoice> {
    loading.value = true;
    error.value = null;
    try {
      const invoice = await api.get<Invoice>(`/invoice/${id}/`);
      const index = invoices.value.findIndex(i => i.id === id);
      if (index !== -1) {
        invoices.value[index] = invoice;
      } else {
        invoices.value.push(invoice);
      }
      return invoice;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch invoice';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Computed: Filtered Lists ====================

  const sentInvoices = computed(() =>
    invoices.value
      .filter(i => i.type === 'sent')
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  );

  const receivedInvoices = computed(() =>
    invoices.value
      .filter(i => i.type === 'received')
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
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

  // ==================== CRUD ====================

  async function addInvoice(data: Omit<Invoice, 'id' | 'createdAt' | 'updatedAt' | 'invoiceNumber'>): Promise<Invoice> {
    error.value = null;
    try {
      const invoice = await api.post<Invoice>('/invoice/', data);
      invoices.value.push(invoice);
      return invoice;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create invoice';
      throw err;
    }
  }

  async function updateInvoice(id: string, data: Partial<Invoice>): Promise<Invoice | null> {
    error.value = null;
    try {
      const updated = await api.put<Invoice>(`/invoice/${id}/`, data);
      const index = invoices.value.findIndex(i => i.id === id);
      if (index !== -1) {
        invoices.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update invoice';
      throw err;
    }
  }

  async function deleteInvoice(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/invoice/${id}/`);
      const index = invoices.value.findIndex(i => i.id === id);
      if (index !== -1) {
        invoices.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete invoice';
      throw err;
    }
  }

  // ==================== Item Sub-Resource CRUD ====================

  async function addItem(invoiceId: string, data: Omit<InvoiceItem, 'id'>): Promise<Invoice | null> {
    error.value = null;
    try {
      await api.post<InvoiceItem>(`/invoice/${invoiceId}/items/`, data);
      return await fetchInvoiceById(invoiceId);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to add invoice item';
      throw err;
    }
  }

  async function updateItem(
    invoiceId: string,
    itemId: string,
    data: Partial<InvoiceItem>
  ): Promise<Invoice | null> {
    error.value = null;
    try {
      await api.put<InvoiceItem>(`/invoice/${invoiceId}/items/${itemId}/`, data);
      return await fetchInvoiceById(invoiceId);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update invoice item';
      throw err;
    }
  }

  async function deleteItem(invoiceId: string, itemId: string): Promise<Invoice | null> {
    error.value = null;
    try {
      await api.delete(`/invoice/${invoiceId}/items/${itemId}/`);
      return await fetchInvoiceById(invoiceId);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete invoice item';
      throw err;
    }
  }

  // ==================== Status Helpers ====================

  async function sendInvoice(id: string): Promise<Invoice | null> {
    return updateInvoice(id, { status: 'sent' });
  }

  async function markAsPaid(id: string): Promise<Invoice | null> {
    return updateInvoice(id, { status: 'paid' });
  }

  async function cancelInvoice(id: string): Promise<Invoice | null> {
    return updateInvoice(id, { status: 'cancelled' });
  }

  // ==================== Helpers ====================

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

  function clearError() {
    error.value = null;
  }

  return {
    // State
    invoices,
    loading,
    error,
    // Fetchers
    fetchInvoices,
    fetchInvoiceById,
    // Computed
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
    // CRUD
    addInvoice,
    updateInvoice,
    deleteInvoice,
    // Item sub-resource CRUD
    addItem,
    updateItem,
    deleteItem,
    // Status helpers
    sendInvoice,
    markAsPaid,
    cancelInvoice,
    // Helpers
    getInvoiceById,
    getInvoiceStats,
    clearError,
  };
});
