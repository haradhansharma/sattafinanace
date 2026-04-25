import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Loan, LoanPayment } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';

export const useLoanStore = defineStore('loan', () => {
  // ==================== State ====================
  const loans = ref<Loan[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchLoans(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      loans.value = await fetchAllPages<Loan>('/loan/');
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch loans';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchLoanPayments(loanId: string): Promise<LoanPayment[]> {
    loading.value = true;
    error.value = null;
    try {
      const payments = await fetchAllPages<LoanPayment>(`/loan/${loanId}/payments/`);
      // Update payments on the local loan object
      const index = loans.value.findIndex(l => l.id === loanId);
      if (index !== -1) {
        loans.value[index] = { ...loans.value[index], payments };
      }
      return payments;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch loan payments';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchLoanById(loanId: string): Promise<Loan> {
    loading.value = true;
    error.value = null;
    try {
      const loan = await api.get<Loan>(`/loan/${loanId}/`);
      const index = loans.value.findIndex(l => l.id === loanId);
      if (index !== -1) {
        loans.value[index] = loan;
      } else {
        loans.value.push(loan);
      }
      return loan;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch loan';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Helpers (work with local state) ====================

  function getActiveLoans(): Loan[] {
    return loans.value.filter(l => l.status === 'active');
  }

  function getLoanById(id: string): Loan | undefined {
    return loans.value.find(l => l.id === id);
  }

  function getLoansByType(type: Loan['type']): Loan[] {
    return loans.value.filter(l => l.type === type);
  }

  // ==================== Computed ====================

  const totalDebt = computed(() => {
    return getActiveLoans().reduce((sum, l) => sum + l.currentBalance, 0);
  });

  const totalMonthlyEMI = computed(() => {
    return getActiveLoans().reduce((sum, l) => sum + l.emiAmount, 0);
  });

  const totalPaidAmount = computed(() => {
    return loans.value.reduce((sum, l) => sum + l.paidAmount, 0);
  });

  const totalPrincipal = computed(() => {
    return loans.value.reduce((sum, l) => sum + l.principalAmount, 0);
  });

  const activeLoanCount = computed(() => {
    return getActiveLoans().length;
  });

  // ==================== Loan CRUD ====================

  async function addLoan(data: Omit<Loan, 'id' | 'createdAt' | 'updatedAt'>): Promise<Loan> {
    error.value = null;
    try {
      const loan = await api.post<Loan>('/loan/', data);
      loans.value.push(loan);
      return loan;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create loan';
      throw err;
    }
  }

  async function updateLoan(id: string, data: Partial<Loan>): Promise<Loan | null> {
    error.value = null;
    try {
      const updated = await api.put<Loan>(`/loan/${id}/`, data);
      const index = loans.value.findIndex(l => l.id === id);
      if (index !== -1) {
        loans.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update loan';
      throw err;
    }
  }

  async function deleteLoan(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/loan/${id}/`);
      const index = loans.value.findIndex(l => l.id === id);
      if (index !== -1) {
        loans.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete loan';
      throw err;
    }
  }

  // ==================== Payment CRUD ====================

  async function addPayment(
    loanId: string,
    data: Omit<LoanPayment, 'id' | 'createdAt' | 'updatedAt'>
  ): Promise<LoanPayment> {
    error.value = null;
    try {
      const payment = await api.post<LoanPayment>(`/loan/${loanId}/payments/`, data);
      const index = loans.value.findIndex(l => l.id === loanId);
      if (index !== -1) {
        loans.value[index] = {
          ...loans.value[index],
          payments: [...loans.value[index].payments, payment],
        };
      }
      return payment;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create loan payment';
      throw err;
    }
  }

  async function deletePayment(loanId: string, paymentId: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/loan/${loanId}/payments/${paymentId}/`);
      const index = loans.value.findIndex(l => l.id === loanId);
      if (index !== -1) {
        loans.value[index] = {
          ...loans.value[index],
          payments: loans.value[index].payments.filter(p => p.id !== paymentId),
        };
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete loan payment';
      throw err;
    }
  }

  return {
    // State
    loans,
    loading,
    error,
    // Fetchers
    fetchLoans,
    fetchLoanPayments,
    fetchLoanById,
    // Helpers
    getActiveLoans,
    getLoanById,
    getLoansByType,
    // Computed
    totalDebt,
    totalMonthlyEMI,
    totalPaidAmount,
    totalPrincipal,
    activeLoanCount,
    // Loan CRUD
    addLoan,
    updateLoan,
    deleteLoan,
    // Payment CRUD
    addPayment,
    deletePayment,
  };
});
