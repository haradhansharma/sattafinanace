import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Budget } from '../types';
import { mockBudgets } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useBudgetStore = defineStore('budget', () => {
  const budgets = ref<Budget[]>(mockBudgets.map(b => ({ ...b })));

  function getCurrentBudget(): Budget | undefined {
    return budgets.value.find(b => b.month === '2026-04');
  }

  function getBudgetByMonth(month: string): Budget | undefined {
    return budgets.value.find(b => b.month === month);
  }

  function getBudgetOverStatus(): Budget[] {
    return budgets.value.filter(b => b.isOverBudget);
  }

  const totalBudgetAmount = computed(() => {
    const current = getCurrentBudget();
    return current?.totalBudgetAmount ?? 0;
  });

  const totalSpent = computed(() => {
    const current = getCurrentBudget();
    if (!current) return 0;
    return current.categories.reduce(
      (sum, cat) => sum + cat.spentAmount,
      0,
    );
  });

  const totalRemaining = computed(() => {
    const current = getCurrentBudget();
    return current?.remainingBalance ?? 0;
  });

  const isCurrentMonthOverBudget = computed(() => {
    const current = getCurrentBudget();
    return current?.isOverBudget ?? false;
  });

  const overBudgetCategories = computed(() => {
    const current = getCurrentBudget();
    if (!current) return [];
    return current.categories.filter(c => c.isOverBudget);
  });

  // ==================== CRUD ====================

  function addBudget(data: Omit<Budget, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const budget: Budget = {
      ...data,
      id: generateId('bgt'),
      createdAt: now,
      updatedAt: now,
    };
    budgets.value.push(budget);
    return budget;
  }

  function updateBudget(id: string, data: Partial<Budget>) {
    const index = budgets.value.findIndex(b => b.id === id);
    if (index === -1) return null;
    budgets.value[index] = {
      ...budgets.value[index],
      ...data,
      id: budgets.value[index].id,
      createdAt: budgets.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return budgets.value[index];
  }

  function deleteBudget(id: string) {
    const index = budgets.value.findIndex(b => b.id === id);
    if (index !== -1) {
      budgets.value.splice(index, 1);
    }
  }

  return {
    budgets,
    getCurrentBudget,
    getBudgetByMonth,
    getBudgetOverStatus,
    totalBudgetAmount,
    totalSpent,
    totalRemaining,
    isCurrentMonthOverBudget,
    overBudgetCategories,
    addBudget,
    updateBudget,
    deleteBudget,
  };
});
