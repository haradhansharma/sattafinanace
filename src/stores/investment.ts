import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Investment, InvestmentCategory, InvestmentTransaction, InvestmentStatus } from '../types';
import { api, fetchAllPages, ApiError } from '../services/api-bridge';

export const useInvestmentStore = defineStore('investment', () => {
  // ==================== State ====================
  const investments = ref<Investment[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Computed ====================

  const activeInvestments = computed(() =>
    investments.value.filter(i => i.status === 'active')
  );

  const totalInvested = computed(() =>
    investments.value.reduce((sum, i) => sum + i.investedAmount + (i.totalDepositedSoFar || 0), 0)
  );

  const totalCurrentValue = computed(() =>
    investments.value.reduce((sum, i) => sum + i.currentValue, 0)
  );

  const totalReturns = computed(() =>
    investments.value.reduce((sum, i) => sum + i.totalReturns, 0)
  );

  const totalUnrealizedGain = computed(() =>
    investments.value.filter(i => i.status === 'active').reduce((sum, i) => {
      return sum + (i.currentValue - (i.investedAmount + (i.totalDepositedSoFar || 0)));
    }, 0)
  );

  const totalMonthlyIncome = computed(() => {
    // Interest from FDR/bonds/sanchaypatra + dividends from stocks
    return activeInvestments.value.reduce((sum, i) => {
      if (i.category === 'fdr' || i.category === 'sanchaypatra' || i.category === 'bond') {
        return sum + (i.investedAmount * (i.interestRate || 0) / 100 / 12);
      }
      if (i.category === 'dps' && i.monthlyDepositAmount) {
        return sum + (i.currentValue * (i.interestRate || 0) / 100 / 12);
      }
      if (i.category === 'stock' && i.dividendYield && i.currentValue) {
        return sum + (i.currentValue * i.dividendYield / 100 / 12);
      }
      return sum;
    }, 0);
  });

  // Category breakdowns
  const investmentsByCategory = computed(() => {
    const map: Record<InvestmentCategory, Investment[]> = {
      fdr: [], dps: [], sanchaypatra: [], stock: [],
      mutual_fund: [], gold: [], bond: [], other: [],
    };
    investments.value.forEach(i => {
      if (map[i.category]) map[i.category].push(i);
    });
    return map;
  });

  const categoryTotals = computed(() => {
    const map = {} as Record<string, { invested: number; current: number; returns: number }>;
    investments.value.forEach(i => {
      if (!map[i.category]) map[i.category] = { invested: 0, current: 0, returns: 0 };
      map[i.category].invested += i.investedAmount + (i.totalDepositedSoFar || 0);
      map[i.category].current += i.currentValue;
      map[i.category].returns += i.totalReturns;
    });
    return map;
  });

  // ==================== Fetch Methods ====================

  async function fetchInvestments(params?: { category?: InvestmentCategory; status?: InvestmentStatus }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const items = await fetchAllPages<Investment>('/investment/', { params });
      investments.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch investments';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchInvestmentById(id: string): Promise<Investment> {
    loading.value = true;
    error.value = null;
    try {
      const investment = await api.get<Investment>(`/investment/${id}/`);
      const idx = investments.value.findIndex(i => i.id === investment.id);
      if (idx !== -1) {
        investments.value[idx] = investment;
      } else {
        investments.value.push(investment);
      }
      return investment;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch investment';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function getInvestmentById(id: string): Investment | undefined {
    return investments.value.find(i => i.id === id);
  }

  // ==================== CRUD ====================

  async function addInvestment(data: any): Promise<Investment> {
    error.value = null;
    try {
      const inv = await api.post<Investment>('/investment/', data);
      investments.value.push(inv);
      return inv;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create investment';
      throw err;
    }
  }

  async function updateInvestment(id: string, data: Partial<Investment>): Promise<Investment | null> {
    error.value = null;
    try {
      const updated = await api.put<Investment>(`/investment/${id}/`, data);
      const index = investments.value.findIndex(i => i.id === id);
      if (index !== -1) {
        investments.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update investment';
      throw err;
    }
  }

  async function deleteInvestment(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/investment/${id}/`);
      const index = investments.value.findIndex(i => i.id === id);
      if (index !== -1) {
        investments.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete investment';
      throw err;
    }
  }

  async function updateStatus(id: string, status: InvestmentStatus): Promise<Investment | null> {
    return updateInvestment(id, { status });
  }

  // ==================== Transactions ====================

  async function addTransaction(investmentId: string, txData: any): Promise<InvestmentTransaction> {
    error.value = null;
    try {
      const tx = await api.post<InvestmentTransaction>(`/investment/${investmentId}/transactions/`, txData);
      // Update local state: re-fetch the investment to get fresh computed fields
      await fetchInvestmentById(investmentId);
      return tx;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create transaction';
      throw err;
    }
  }

  async function deleteTransaction(investmentId: string, txId: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/investment/${investmentId}/transactions/${txId}/`);
      // Re-fetch investment to get updated state
      await fetchInvestmentById(investmentId);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete transaction';
      throw err;
    }
  }

  async function fetchTransactions(investmentId: string): Promise<InvestmentTransaction[]> {
    loading.value = true;
    error.value = null;
    try {
      return await fetchAllPages<InvestmentTransaction>(`/investment/${investmentId}/transactions/`);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch transactions';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    investments,
    loading,
    error,
    activeInvestments,
    totalInvested,
    totalCurrentValue,
    totalReturns,
    totalUnrealizedGain,
    totalMonthlyIncome,
    investmentsByCategory,
    categoryTotals,
    fetchInvestments,
    fetchInvestmentById,
    getInvestmentById,
    addInvestment,
    updateInvestment,
    deleteInvestment,
    updateStatus,
    addTransaction,
    deleteTransaction,
    fetchTransactions,
  };
});
