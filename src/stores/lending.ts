import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Lending, LendingPayment } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';

export const useLendingStore = defineStore('lending', () => {
  // ==================== State ====================
  const lendings = ref<Lending[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchLendings(params?: { status?: string }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      lendings.value = await fetchAllPages<Lending>('/lending/', { params });
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch lendings';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchLendingById(id: string): Promise<Lending> {
    loading.value = true;
    error.value = null;
    try {
      const lending = await api.get<Lending>(`/lending/${id}/`);
      const index = lendings.value.findIndex(l => l.id === id);
      if (index !== -1) {
        lendings.value[index] = lending;
      } else {
        lendings.value.push(lending);
      }
      return lending;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch lending';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchLendingPayments(lendingId: string): Promise<LendingPayment[]> {
    loading.value = true;
    error.value = null;
    try {
      return await fetchAllPages<LendingPayment>(`/lending/${lendingId}/payments/`);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch lending payments';
      throw err;
    } finally {
      loading.value = false;
    }
  }

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

  async function addLending(data: Omit<Lending, 'id' | 'createdAt' | 'updatedAt'>): Promise<Lending> {
    error.value = null;
    try {
      const lending = await api.post<Lending>('/lending/', data);
      lendings.value.push(lending);
      return lending;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create lending';
      throw err;
    }
  }

  async function updateLending(id: string, data: Partial<Lending>): Promise<Lending | null> {
    error.value = null;
    try {
      const updated = await api.put<Lending>(`/lending/${id}/`, data);
      const index = lendings.value.findIndex(l => l.id === id);
      if (index !== -1) {
        lendings.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update lending';
      throw err;
    }
  }

  async function deleteLending(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/lending/${id}/`);
      const index = lendings.value.findIndex(l => l.id === id);
      if (index !== -1) {
        lendings.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete lending';
      throw err;
    }
  }

  // ==================== Payment Actions ====================

  async function recordRepayment(id: string, amount: number, note?: string): Promise<Lending | null> {
    error.value = null;
    try {
      await api.post<LendingPayment>(`/lending/${id}/payments/`, {
        amount,
        note,
        lendingId: id,
      });
      // Re-fetch to get updated totals
      return await fetchLendingById(id);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to record repayment';
      throw err;
    }
  }

  async function deletePayment(lendingId: string, paymentId: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/lending/${lendingId}/payments/${paymentId}/`);
      // Re-fetch to get updated totals
      await fetchLendingById(lendingId);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete payment';
      throw err;
    }
  }

  // ==================== Status Helpers ====================

  async function markAsDefaulted(id: string): Promise<Lending | null> {
    return updateLending(id, { status: 'defaulted' });
  }

  async function markAsCancelled(id: string): Promise<Lending | null> {
    return updateLending(id, { status: 'cancelled' });
  }

  // ==================== Helpers ====================

  function getLendingById(id: string): Lending | undefined {
    return lendings.value.find(l => l.id === id);
  }

  function clearError() {
    error.value = null;
  }

  return {
    // State
    lendings,
    loading,
    error,
    // Fetchers
    fetchLendings,
    fetchLendingById,
    fetchLendingPayments,
    // Computed
    activeLendings,
    overdueLendings,
    totalLentAmount,
    totalOutstandingBalance,
    totalRepaidAmount,
    totalInterestEarned,
    activeCount,
    overdueCount,
    // CRUD
    addLending,
    updateLending,
    deleteLending,
    // Payment
    recordRepayment,
    deletePayment,
    // Status helpers
    markAsDefaulted,
    markAsCancelled,
    // Helpers
    getLendingById,
    clearError,
  };
});
