import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Loan } from '../types';
import { mockLoans } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useLoanStore = defineStore('loan', () => {
  const loans = ref<Loan[]>(mockLoans.map(l => ({ ...l, payments: l.payments ? l.payments.map(p => ({ ...p })) : [] })));

  function getActiveLoans(): Loan[] {
    return loans.value.filter(l => l.status === 'active');
  }

  function getLoanById(id: string): Loan | undefined {
    return loans.value.find(l => l.id === id);
  }

  function getLoansByType(type: Loan['type']): Loan[] {
    return loans.value.filter(l => l.type === type);
  }

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

  // ==================== CRUD ====================

  function addLoan(data: Omit<Loan, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const loan: Loan = {
      ...data,
      id: generateId('loan'),
      createdAt: now,
      updatedAt: now,
    };
    loans.value.push(loan);
    return loan;
  }

  function updateLoan(id: string, data: Partial<Loan>) {
    const index = loans.value.findIndex(l => l.id === id);
    if (index === -1) return null;
    loans.value[index] = {
      ...loans.value[index],
      ...data,
      id: loans.value[index].id,
      createdAt: loans.value[index].createdAt,
      payments: data.payments ?? loans.value[index].payments,
      updatedAt: new Date().toISOString(),
    };
    return loans.value[index];
  }

  function deleteLoan(id: string) {
    const index = loans.value.findIndex(l => l.id === id);
    if (index !== -1) {
      loans.value.splice(index, 1);
    }
  }

  return {
    loans,
    getActiveLoans,
    getLoanById,
    getLoansByType,
    totalDebt,
    totalMonthlyEMI,
    totalPaidAmount,
    totalPrincipal,
    activeLoanCount,
    addLoan,
    updateLoan,
    deleteLoan,
  };
});
