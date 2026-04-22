import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Investment, InvestmentCategory, InvestmentTransaction, InvestmentStatus } from '../types';
import { mockInvestments } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useInvestmentStore = defineStore('investment', () => {
  const investments = ref<Investment[]>(mockInvestments.map(i => ({
    ...i,
    transactions: i.transactions.map(t => ({ ...t })),
  })));

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

  // ==================== CRUD ====================

  function addInvestment(data: Omit<Investment, 'id' | 'createdAt' | 'updatedAt' | 'transactions'>) {
    const now = new Date().toISOString();
    const inv: Investment = {
      ...data,
      transactions: [],
      id: generateId('inv'),
      createdAt: now,
      updatedAt: now,
    };
    investments.value.push(inv);
    return inv;
  }

  function updateInvestment(id: string, data: Partial<Investment>) {
    const index = investments.value.findIndex(i => i.id === id);
    if (index === -1) return null;
    investments.value[index] = {
      ...investments.value[index],
      ...data,
      id: investments.value[index].id,
      createdAt: investments.value[index].createdAt,
      transactions: data.transactions ?? investments.value[index].transactions,
      updatedAt: new Date().toISOString(),
    };
    return investments.value[index];
  }

  function deleteInvestment(id: string) {
    const index = investments.value.findIndex(i => i.id === id);
    if (index !== -1) investments.value.splice(index, 1);
  }

  function addTransaction(investmentId: string, tx: Omit<InvestmentTransaction, 'id' | 'createdAt' | 'updatedAt' | 'investmentId'>) {
    const inv = investments.value.find(i => i.id === investmentId);
    if (!inv) return;

    const now = new Date().toISOString();
    const newTx: InvestmentTransaction = {
      ...tx,
      investmentId,
      id: generateId('itx'),
      createdAt: now,
      updatedAt: now,
    };
    inv.transactions.push(newTx);

    // Update investment based on transaction type
    switch (tx.type) {
      case 'buy':
        inv.investedAmount += tx.amount;
        inv.currentValue += tx.amount;
        break;
      case 'deposit':
        inv.totalDepositedSoFar = (inv.totalDepositedSoFar || 0) + tx.amount;
        inv.currentValue += tx.amount;
        inv.depositCount = (inv.depositCount || 0) + 1;
        break;
      case 'sell':
        inv.currentValue = Math.max(0, inv.currentValue - tx.amount);
        break;
      case 'withdrawal':
        inv.currentValue = Math.max(0, inv.currentValue - tx.amount);
        break;
      case 'dividend':
      case 'interest':
      case 'bonus':
        inv.totalReturns += tx.amount;
        break;
      case 'maturity':
        inv.totalReturns += tx.amount;
        inv.status = 'matured';
        break;
    }

    inv.updatedAt = now;
    return inv;
  }

  function updateStatus(id: string, status: InvestmentStatus) {
    const inv = investments.value.find(i => i.id === id);
    if (!inv) return;
    inv.status = status;
    inv.updatedAt = new Date().toISOString();
  }

  function getInvestmentById(id: string): Investment | undefined {
    return investments.value.find(i => i.id === id);
  }

  return {
    investments,
    activeInvestments,
    totalInvested,
    totalCurrentValue,
    totalReturns,
    totalUnrealizedGain,
    totalMonthlyIncome,
    investmentsByCategory,
    categoryTotals,
    addInvestment,
    updateInvestment,
    deleteInvestment,
    addTransaction,
    updateStatus,
    getInvestmentById,
  };
});
