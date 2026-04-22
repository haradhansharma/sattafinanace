import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Bill, BillCategory, BillStatus, BillPaymentHistory } from '../types';
import { mockBills } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useBillStore = defineStore('bill', () => {
  const bills = ref<Bill[]>(mockBills.map(b => ({
    ...b,
    tags: b.tags || [],
    paymentHistory: b.paymentHistory || [],
  })));

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

  // High priority overdue
  const highPriorityOverdue = computed(() =>
    overdueBills.value.filter(b => b.priority === 'high')
  );

  // ==================== Query Methods ====================

  function getBillsByCategory(category: BillCategory): Bill[] {
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

  function getBillById(id: string): Bill | undefined {
    return bills.value.find(b => b.id === id);
  }

  // ==================== CRUD ====================

  function addBill(data: Omit<Bill, 'id' | 'createdAt' | 'updatedAt'>): Bill {
    const now = new Date().toISOString();
    const bill: Bill = {
      ...data,
      tags: data.tags || [],
      paymentHistory: data.paymentHistory || [],
      totalPaidAmount: data.totalPaidAmount || 0,
      totalPaymentsCount: data.totalPaymentsCount || 0,
      id: generateId('bill'),
      createdAt: now,
      updatedAt: now,
    };
    bills.value.push(bill);
    return bill;
  }

  function updateBill(id: string, data: Partial<Bill>): Bill | null {
    const index = bills.value.findIndex(b => b.id === id);
    if (index === -1) return null;
    bills.value[index] = {
      ...bills.value[index],
      ...data,
      id: bills.value[index].id,
      createdAt: bills.value[index].createdAt,
      tags: data.tags ?? bills.value[index].tags,
      paymentHistory: data.paymentHistory ?? bills.value[index].paymentHistory,
      updatedAt: new Date().toISOString(),
    };
    return bills.value[index];
  }

  function deleteBill(id: string) {
    const index = bills.value.findIndex(b => b.id === id);
    if (index !== -1) bills.value.splice(index, 1);
  }

  // ==================== Payment Actions ====================

  function markAsPaid(id: string, paymentData: Omit<BillPaymentHistory, 'id'>) {
    const bill = bills.value.find(b => b.id === id);
    if (!bill) return;

    const payment: BillPaymentHistory = {
      ...paymentData,
      id: generateId('bpay'),
    };

    bill.paymentHistory.push(payment);
    bill.totalPaidAmount += paymentData.amount;
    bill.totalPaymentsCount += 1;
    bill.lastPaidDate = paymentData.paymentDate;
    bill.lastPaidAmount = paymentData.amount;
    bill.status = 'paid';
    bill.updatedAt = new Date().toISOString();

    // For recurring bills, generate next due date
    if (bill.recurrence !== 'none' && !bill.endDate) {
      const nextDue = computeNextDueDate(bill.dueDate, bill.recurrence);
      if (nextDue) {
        bill.dueDate = nextDue;
        bill.status = 'upcoming';
      }
    }
  }

  function skipBill(id: string) {
    const bill = bills.value.find(b => b.id === id);
    if (!bill) return;
    bill.status = 'skipped';
    bill.updatedAt = new Date().toISOString();
  }

  function cancelBill(id: string) {
    const bill = bills.value.find(b => b.id === id);
    if (!bill) return;
    bill.status = 'cancelled';
    bill.autoPayEnabled = false;
    bill.updatedAt = new Date().toISOString();
  }

  function restoreBill(id: string) {
    const bill = bills.value.find(b => b.id === id);
    if (!bill) return;
    // Determine correct status based on due date
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const due = new Date(bill.dueDate);
    due.setHours(0, 0, 0, 0);
    if (due < now) {
      const grace = (bill.gracePeriodDays || 0) * 24 * 60 * 60 * 1000;
      bill.status = (due.getTime() + grace < now.getTime()) ? 'overdue' : 'due_soon';
    } else {
      const week = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      bill.status = due <= week ? 'due_soon' : 'upcoming';
    }
    bill.updatedAt = new Date().toISOString();
  }

  function toggleAutoPay(id: string) {
    const bill = bills.value.find(b => b.id === id);
    if (!bill) return;
    bill.autoPayEnabled = !bill.autoPayEnabled;
    bill.updatedAt = new Date().toISOString();
  }

  // ==================== Helpers ====================

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

  return {
    bills,
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
    billsByCategory,
    categoryTotals,
    highPriorityOverdue,
    getBillsByCategory,
    getBillsForDateRange,
    searchBills,
    getBillById,
    addBill,
    updateBill,
    deleteBill,
    markAsPaid,
    skipBill,
    cancelBill,
    restoreBill,
    toggleAutoPay,
    daysUntilDue,
    getLateFee,
  };
});
