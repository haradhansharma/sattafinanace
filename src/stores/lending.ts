import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Lending } from '../types';
import { mockLendings } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useLendingStore = defineStore('lending', () => {
  const lendings = ref<Lending[]>(mockLendings.map(l => ({ ...l })));

  // ==================== Computed ====================

  const activeLendings = computed(() =>
    lendings.value.filter(l => l.status === 'active')
  );

  const overdueLendings = computed(() =>
    lendings.value.filter(l => l.status === 'overdue')
  );

  const totalLentAmount = computed(() =>
    lendings.value.reduce((sum, l) => sum + l.principalAmount, 0)
  );

  const totalOutstandingBalance = computed(() =>
    lendings.value
      .filter(l => l.status !== 'cancelled' && l.status !== 'fully_repaid')
      .reduce((sum, l) => sum + l.currentBalance, 0)
  );

  const totalRepaidAmount = computed(() =>
    lendings.value.reduce((sum, l) => sum + l.totalRepaidAmount, 0)
  );

  const totalInterestEarned = computed(() =>
    lendings.value.reduce((sum, l) => sum + l.totalInterestAmount - Math.max(0, l.currentBalance > 0 ? 0 : l.totalInterestAmount), 0)
  );

  const activeCount = computed(() => activeLendings.value.length);

  const overdueCount = computed(() => overdueLendings.value.length);

  // ==================== CRUD ====================

  function addLending(data: Omit<Lending, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const lending: Lending = {
      ...data,
      id: generateId('lend'),
      createdAt: now,
      updatedAt: now,
    };
    lendings.value.push(lending);
    return lending;
  }

  function updateLending(id: string, data: Partial<Lending>) {
    const index = lendings.value.findIndex(l => l.id === id);
    if (index === -1) return null;
    lendings.value[index] = {
      ...lendings.value[index],
      ...data,
      id: lendings.value[index].id,
      createdAt: lendings.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return lendings.value[index];
  }

  function deleteLending(id: string) {
    const index = lendings.value.findIndex(l => l.id === id);
    if (index !== -1) {
      lendings.value.splice(index, 1);
    }
  }

  function recordRepayment(id: string, amount: number, note?: string) {
    const lending = lendings.value.find(l => l.id === id);
    if (!lending) return;

    lending.totalRepaidAmount += amount;
    lending.currentBalance = Math.max(0, lending.currentBalance - amount);
    lending.updatedAt = new Date().toISOString();

    if (lending.currentBalance <= 0) {
      lending.currentBalance = 0;
      lending.status = 'fully_repaid';
    } else if (lending.status === 'overdue') {
      lending.status = 'partially_repaid';
    } else if (lending.totalRepaidAmount > 0 && lending.currentBalance < lending.principalAmount) {
      lending.status = 'partially_repaid';
    }
  }

  function markAsDefaulted(id: string) {
    const lending = lendings.value.find(l => l.id === id);
    if (!lending) return;
    lending.status = 'defaulted';
    lending.updatedAt = new Date().toISOString();
  }

  function markAsCancelled(id: string) {
    const lending = lendings.value.find(l => l.id === id);
    if (!lending) return;
    lending.status = 'cancelled';
    lending.updatedAt = new Date().toISOString();
  }

  function getLendingById(id: string): Lending | undefined {
    return lendings.value.find(l => l.id === id);
  }

  return {
    lendings,
    activeLendings,
    overdueLendings,
    totalLentAmount,
    totalOutstandingBalance,
    totalRepaidAmount,
    totalInterestEarned,
    activeCount,
    overdueCount,
    addLending,
    updateLending,
    deleteLending,
    recordRepayment,
    markAsDefaulted,
    markAsCancelled,
    getLendingById,
  };
});
