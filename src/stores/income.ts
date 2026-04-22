import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Income, IncomeSource, IncomeCategory } from '../types';
import { mockIncomes, mockIncomeSources, mockIncomeCategories } from '../mock-data';
import { useCurrencyStore } from './currency';
import { generateId } from '../utils/formatters';

export const useIncomeStore = defineStore('income', () => {
  const incomes = ref<Income[]>(mockIncomes.map(i => ({ ...i })));
  const incomeSources = ref<IncomeSource[]>(mockIncomeSources.map(s => ({ ...s })));
  const incomeCategories = ref<IncomeCategory[]>(mockIncomeCategories.map(c => ({ ...c })));

  const totalMonthlyIncome = computed(() => {
    const currencyStore = useCurrencyStore();
    return incomes.value.reduce((sum, income) => sum + currencyStore.convertToBase(income.amount, income.currency || 'BDT'), 0);
  });

  const totalYearlyIncome = computed(() => {
    // Sum the last 12 months of income records (or all available)
    const currencyStore = useCurrencyStore();
    const now = new Date();
    const twelveMonthsAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
    return incomes.value
      .filter(i => new Date(i.date) >= twelveMonthsAgo)
      .reduce((sum, income) => sum + currencyStore.convertToBase(income.amount, income.currency || 'BDT'), 0);
  });

  /**
   * Expected income this month: sum of all recurring sources with monthlyAmount
   * (salary, rental, etc.) — represents what's *supposed* to come in.
   */
  const expectedMonthlyIncome = computed(() => {
    return incomeSources.value
      .filter(s => s.isActive && s.monthlyAmount && s.monthlyAmount > 0)
      .reduce((sum, s) => sum + s.monthlyAmount!, 0);
  });

  /**
   * Already received this month: sum of income records for the current month.
   */
  const receivedThisMonth = computed(() => {
    const now = new Date();
    const monthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const currencyStore = useCurrencyStore();
    return incomes.value
      .filter(i => i.date.startsWith(monthStr))
      .reduce((sum, i) => sum + currencyStore.convertToBase(i.amount, i.currency || 'BDT'), 0);
  });

  /**
   * Upcoming (pending) income this month: expected minus received.
   * Can be negative if one-time income boosts the total above recurring expected.
   */
  const pendingIncomeThisMonth = computed(() => {
    return Math.max(0, expectedMonthlyIncome.value - receivedThisMonth.value);
  });

  /**
   * List of recurring sources that haven't been received yet this month.
   */
  const pendingSources = computed(() => {
    const now = new Date();
    const monthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    return incomeSources.value
      .filter(s => s.isActive && s.monthlyAmount && s.monthlyAmount > 0)
      .filter(s => {
        // Check if there's an income record for this source this month
        return !incomes.value.some(
          i => i.sourceId === s.id && i.date.startsWith(monthStr)
        );
      });
  });

  function getIncomesBySource(sourceId: string): Income[] {
    return incomes.value
      .filter(i => i.sourceId === sourceId)
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }

  function getIncomeByMonth(month: string): Income[] {
    // month format: 'YYYY-MM'
    return incomes.value
      .filter(i => i.date.startsWith(month))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }

  function getMonthlyTotalBySource(sourceId: string): number {
    const source = incomeSources.value.find(s => s.id === sourceId);
    return source?.monthlyAmount ?? 0;
  }

  function getIncomeCategoryById(categoryId: string): IncomeCategory | undefined {
    return incomeCategories.value.find(c => c.id === categoryId);
  }

  // ==================== Income CRUD ====================

  function addIncome(data: Omit<Income, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const income: Income = {
      ...data,
      id: generateId('inc'),
      createdAt: now,
      updatedAt: now,
    };
    incomes.value.push(income);
    return income;
  }

  function updateIncome(id: string, data: Partial<Income>) {
    const index = incomes.value.findIndex(i => i.id === id);
    if (index === -1) return null;
    incomes.value[index] = {
      ...incomes.value[index],
      ...data,
      id: incomes.value[index].id,
      createdAt: incomes.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return incomes.value[index];
  }

  function deleteIncome(id: string) {
    const index = incomes.value.findIndex(i => i.id === id);
    if (index !== -1) {
      incomes.value.splice(index, 1);
    }
  }

  // ==================== Income Source CRUD ====================

  function addIncomeSource(data: Omit<IncomeSource, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const source: IncomeSource = {
      ...data,
      id: generateId('incsrc'),
      createdAt: now,
      updatedAt: now,
    };
    incomeSources.value.push(source);
    return source;
  }

  function updateIncomeSource(id: string, data: Partial<IncomeSource>) {
    const index = incomeSources.value.findIndex(s => s.id === id);
    if (index === -1) return null;
    incomeSources.value[index] = {
      ...incomeSources.value[index],
      ...data,
      id: incomeSources.value[index].id,
      createdAt: incomeSources.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return incomeSources.value[index];
  }

  function deleteIncomeSource(id: string) {
    const index = incomeSources.value.findIndex(s => s.id === id);
    if (index !== -1) {
      incomeSources.value.splice(index, 1);
    }
  }

  // ==================== Income Category CRUD ====================

  function addIncomeCategory(data: Omit<IncomeCategory, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const category: IncomeCategory = {
      ...data,
      id: generateId('inc_cat'),
      createdAt: now,
      updatedAt: now,
    };
    incomeCategories.value.push(category);
    return category;
  }

  function updateIncomeCategory(id: string, data: Partial<IncomeCategory>) {
    const index = incomeCategories.value.findIndex(c => c.id === id);
    if (index === -1) return null;
    incomeCategories.value[index] = {
      ...incomeCategories.value[index],
      ...data,
      id: incomeCategories.value[index].id,
      createdAt: incomeCategories.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return incomeCategories.value[index];
  }

  function deleteIncomeCategory(id: string) {
    const index = incomeCategories.value.findIndex(c => c.id === id);
    if (index !== -1) {
      incomeCategories.value.splice(index, 1);
    }
  }

  return {
    incomes,
    incomeSources,
    incomeCategories,
    totalMonthlyIncome,
    totalYearlyIncome,
    expectedMonthlyIncome,
    receivedThisMonth,
    pendingIncomeThisMonth,
    pendingSources,
    getIncomesBySource,
    getIncomeByMonth,
    getMonthlyTotalBySource,
    getIncomeCategoryById,
    addIncome,
    updateIncome,
    deleteIncome,
    addIncomeSource,
    updateIncomeSource,
    deleteIncomeSource,
    addIncomeCategory,
    updateIncomeCategory,
    deleteIncomeCategory,
  };
});
