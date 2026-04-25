import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Bill, BillPaymentHistory } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';

export const useBillStore = defineStore('bill', () => {
  // ==================== State ====================
  const bills = ref<Bill[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchBills(params?: {
    category?: string;
    status?: string;
    priority?: string;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      bills.value = await fetchAllPages<Bill>('/bill/', { params });
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch bills';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchBillById(id: string): Promise<Bill> {
    loading.value = true;
    error.value = null;
    try {
      const bill = await api.get<Bill>(`/bill/${id}/`);
      const index = bills.value.findIndex(b => b.id === id);
      if (index !== -1) {
        bills.value[index] = bill;
      } else {
        bills.value.push(bill);
      }
      return bill;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch bill';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchBillPaymentHistory(billId: string): Promise<BillPaymentHistory[]> {
    loading.value = true;
    error.value = null;
    try {
      return await fetchAllPages<BillPaymentHistory>(`/bill/${billId}/payment-history/`);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch payment history';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Computed ====================

  const totalBills = computed(() => bills.value.length);

  const activeBills = computed(() =>
    bills.value.filter(b => b.status !== 'cancelled')
  );

  const recurringBills = computed(() =>
    bills.value.filter(b => b.recurrence !== 'none' && b.status !== 'cancelled')
  );

  const upcomingBills = computed(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return bills.value
      .filter(b => {
        if (b.status === 'paid' || b.status === 'cancelled') return false;
        const due = new Date(b.dueDate);
        due.setHours(0, 0, 0, 0);
        return due >= now;
      })
      .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
  });

  const dueSoonBills = computed(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const week = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    return bills.value
      .filter(b => {
        if (b.status === 'paid' || b.status === 'cancelled') return false;
        const due = new Date(b.dueDate);
        due.setHours(0, 0, 0, 0);
        return due >= now && due <= week;
      })
      .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
  });

  const overdueBills = computed(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return bills.value
      .filter(b => {
        if (b.status === 'paid' || b.status === 'cancelled') return false;
        const due = new Date(b.dueDate);
        due.setHours(0, 0, 0, 0);
        const grace = (b.gracePeriodDays || 0) * 24 * 60 * 60 * 1000;
        return due.getTime() + grace < now.getTime();
      })
      .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
  });

  const paidBills = computed(() =>
    bills.value.filter(b => b.status === 'paid')
  );

  const autoPayBills = computed(() =>
    bills.value.filter(b => b.autoPayEnabled && b.status !== 'cancelled')
  );

  // Total outflow this month
  const totalDueThisMonth = computed(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    return bills.value
      .filter(b => {
        if (b.status === 'paid' || b.status === 'cancelled') return false;
        const due = new Date(b.dueDate);
        return due.getFullYear() === year && due.getMonth() === month;
      })
      .reduce((sum, b) => sum + (b.amount || 0), 0);
  });

  // Total paid this month
  const totalPaidThisMonth = computed(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    return bills.value
      .flatMap(b => b.paymentHistory)
      .filter(p => {
        const d = new Date(p.paymentDate);
        return d.getFullYear() === year && d.getMonth() === month;
      })
      .reduce((sum, p) => sum + p.amount, 0);
  });

  // High priority overdue
  const highPriorityOverdue = computed(() =>
    overdueBills.value.filter(b => b.priority === 'high')
  );

  // Category breakdown
  const billsByCategory = computed(() => {
    const map: Record<string, Bill[]> = {};
    bills.value.forEach(b => {
      if (!map[b.category]) map[b.category] = [];
      map[b.category].push(b);
    });
    return map;
  });

  const categoryTotals = computed(() => {
    const map = {} as Record<string, { count: number; totalDue: number; totalPaid: number }>;
    bills.value.filter(b => b.status !== 'cancelled').forEach(b => {
      if (!map[b.category]) map[b.category] = { count: 0, totalDue: 0, totalPaid: 0 };
      map[b.category].count++;
      if (b.status !== 'paid') map[b.category].totalDue += b.amount;
      map[b.category].totalPaid += b.totalPaidAmount;
    });
    return map;
  });

  // ==================== CRUD ====================

  async function addBill(data: Omit<Bill, 'id' | 'createdAt' | 'updatedAt'>): Promise<Bill> {
    error.value = null;
    try {
      const bill = await api.post<Bill>('/bill/', data);
      bills.value.push(bill);
      return bill;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create bill';
      throw err;
    }
  }

  async function updateBill(id: string, data: Partial<Bill>): Promise<Bill | null> {
    error.value = null;
    try {
      const updated = await api.put<Bill>(`/bill/${id}/`, data);
      const index = bills.value.findIndex(b => b.id === id);
      if (index !== -1) {
        bills.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update bill';
      throw err;
    }
  }

  async function deleteBill(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/bill/${id}/`);
      const index = bills.value.findIndex(b => b.id === id);
      if (index !== -1) {
        bills.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete bill';
      throw err;
    }
  }

  // ==================== Payment Actions ====================

  /**
   * Record a payment via POST /bill/{id}/pay.
   * The backend auto-updates totals and computes the next due date for recurring bills.
   */
  async function markAsPaid(
    id: string,
    data?: { amount?: number; paymentDate?: string; paymentMethod?: string; note?: string; referenceNumber?: string }
  ): Promise<Bill | null> {
    error.value = null;
    try {
      const updated = await api.post<Bill>(`/bill/${id}/pay/`, data || {});
      const index = bills.value.findIndex(b => b.id === id);
      if (index !== -1) {
        bills.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to record payment';
      throw err;
    }
  }

  async function skipBill(id: string): Promise<Bill | null> {
    return updateBill(id, { status: 'skipped' });
  }

  async function cancelBill(id: string): Promise<Bill | null> {
    return updateBill(id, { status: 'cancelled', autoPayEnabled: false });
  }

  async function restoreBill(id: string): Promise<Bill | null> {
    return updateBill(id, { status: 'upcoming' });
  }

  async function toggleAutoPay(id: string): Promise<Bill | null> {
    const bill = bills.value.find(b => b.id === id);
    if (!bill) return null;
    return updateBill(id, { autoPayEnabled: !bill.autoPayEnabled });
  }

  // ==================== Helpers ====================

  /**
   * Local helper — computes the next due date for a recurring bill.
   * This is client-side only; the backend also computes it on pay.
   */
  function computeNextDueDate(currentDueDate: string, recurrence: Bill['recurrence']): string | null {
    const d = new Date(currentDueDate);
    switch (recurrence) {
      case 'weekly':
        d.setDate(d.getDate() + 7);
        break;
      case 'biweekly':
        d.setDate(d.getDate() + 14);
        break;
      case 'monthly':
        d.setMonth(d.getMonth() + 1);
        break;
      case 'quarterly':
        d.setMonth(d.getMonth() + 3);
        break;
      case 'semiannually':
        d.setMonth(d.getMonth() + 6);
        break;
      case 'annually':
        d.setFullYear(d.getFullYear() + 1);
        break;
      default:
        return null;
    }
    return d.toISOString();
  }

  function daysUntilDue(bill: Bill): number {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const due = new Date(bill.dueDate);
    due.setHours(0, 0, 0, 0);
    return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  }

  function getLateFee(bill: Bill): number {
    if (bill.status !== 'overdue') return 0;
    const baseFee = bill.lateFeeAmount || 0;
    const percentFee = bill.lateFeePercent ? Math.round(bill.amount * bill.lateFeePercent / 100) : 0;
    return baseFee + percentFee;
  }

  function getBillById(id: string): Bill | undefined {
    return bills.value.find(b => b.id === id);
  }

  function getBillsByCategory(category: string): Bill[] {
    return bills.value.filter(b => b.category === category);
  }

  function getBillsForDateRange(start: string, end: string): Bill[] {
    const s = new Date(start).getTime();
    const e = new Date(end).getTime();
    return bills.value.filter(b => {
      const d = new Date(b.dueDate).getTime();
      return d >= s && d <= e;
    });
  }

  function searchBills(query: string): Bill[] {
    const q = query.toLowerCase().trim();
    if (!q) return bills.value;
    return bills.value.filter(b =>
      b.name.toLowerCase().includes(q) ||
      b.payeeName.toLowerCase().includes(q) ||
      b.description?.toLowerCase().includes(q) ||
      b.tags?.some(t => t.toLowerCase().includes(q)) ||
      b.notes?.toLowerCase().includes(q)
    );
  }

  function clearError() {
    error.value = null;
  }

  return {
    // State
    bills,
    loading,
    error,
    // Fetchers
    fetchBills,
    fetchBillById,
    fetchBillPaymentHistory,
    // Computed
    totalBills,
    activeBills,
    recurringBills,
    upcomingBills,
    dueSoonBills,
    overdueBills,
    paidBills,
    autoPayBills,
    totalDueThisMonth,
    totalPaidThisMonth,
    highPriorityOverdue,
    billsByCategory,
    categoryTotals,
    // CRUD
    addBill,
    updateBill,
    deleteBill,
    // Payment
    markAsPaid,
    skipBill,
    cancelBill,
    restoreBill,
    toggleAutoPay,
    // Helpers
    computeNextDueDate,
    daysUntilDue,
    getLateFee,
    getBillById,
    getBillsByCategory,
    getBillsForDateRange,
    searchBills,
    clearError,
  };
});
