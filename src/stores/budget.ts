import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Budget, BudgetCategory } from '../types';
import { api, fetchAllPages, ApiError } from '../services/api-bridge';

function getCurrentMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

export const useBudgetStore = defineStore('budget', () => {
  // ==================== State ====================
  const budgets = ref<Budget[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Computed ====================

  function getCurrentBudget(): Budget | undefined {
    return budgets.value.find(b => b.month === getCurrentMonth());
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

  // ==================== Fetch Methods ====================

  async function fetchBudgets(month?: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const params = month ? { month } : undefined;
      const items = await fetchAllPages<Budget>('/budget/', { params });
      budgets.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch budgets';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Get current month budget. First checks local state; if not found, calls the API.
   */
  async function fetchCurrentBudget(): Promise<Budget | undefined> {
    const local = getCurrentBudget();
    if (local) return local;

    loading.value = true;
    error.value = null;
    try {
      const budget = await api.get<Budget>('/budget/current/');
      // Upsert into local state
      const idx = budgets.value.findIndex(b => b.id === budget.id);
      if (idx !== -1) {
        budgets.value[idx] = budget;
      } else {
        budgets.value.push(budget);
      }
      return budget;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch current budget';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchBudgetById(id: string): Promise<Budget> {
    loading.value = true;
    error.value = null;
    try {
      const budget = await api.get<Budget>(`/budget/${id}/`);
      const idx = budgets.value.findIndex(b => b.id === budget.id);
      if (idx !== -1) {
        budgets.value[idx] = budget;
      } else {
        budgets.value.push(budget);
      }
      return budget;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch budget';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== CRUD ====================

  async function addBudget(data: any): Promise<Budget> {
    error.value = null;
    try {
      const budget = await api.post<Budget>('/budget/', data);
      budgets.value.push(budget);
      return budget;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create budget';
      throw err;
    }
  }

  async function updateBudget(id: string, data: Partial<Budget>): Promise<Budget | null> {
    error.value = null;
    try {
      const updated = await api.put<Budget>(`/budget/${id}/`, data);
      const index = budgets.value.findIndex(b => b.id === id);
      if (index !== -1) {
        budgets.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update budget';
      throw err;
    }
  }

  async function deleteBudget(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/budget/${id}/`);
      const index = budgets.value.findIndex(b => b.id === id);
      if (index !== -1) {
        budgets.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete budget';
      throw err;
    }
  }

  // ==================== Category CRUD ====================

  async function addCategory(budgetId: string, data: any): Promise<BudgetCategory> {
    error.value = null;
    try {
      const category = await api.post<BudgetCategory>(`/budget/${budgetId}/categories/`, data);
      const budget = budgets.value.find(b => b.id === budgetId);
      if (budget) {
        budget.categories.push(category);
      }
      return category;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to add budget category';
      throw err;
    }
  }

  async function updateCategory(budgetId: string, categoryId: string, data: Partial<BudgetCategory>): Promise<BudgetCategory | null> {
    error.value = null;
    try {
      const updated = await api.put<BudgetCategory>(`/budget/${budgetId}/categories/${categoryId}/`, data);
      const budget = budgets.value.find(b => b.id === budgetId);
      if (budget) {
        const catIdx = budget.categories.findIndex(c => c.id === categoryId);
        if (catIdx !== -1) {
          budget.categories[catIdx] = updated;
        }
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update budget category';
      throw err;
    }
  }

  async function deleteCategory(budgetId: string, categoryId: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/budget/${budgetId}/categories/${categoryId}/`);
      const budget = budgets.value.find(b => b.id === budgetId);
      if (budget) {
        const catIdx = budget.categories.findIndex(c => c.id === categoryId);
        if (catIdx !== -1) {
          budget.categories.splice(catIdx, 1);
        }
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete budget category';
      throw err;
    }
  }

  return {
    budgets,
    loading,
    error,
    getCurrentBudget,
    getBudgetByMonth,
    getBudgetOverStatus,
    totalBudgetAmount,
    totalSpent,
    totalRemaining,
    isCurrentMonthOverBudget,
    overBudgetCategories,
    fetchBudgets,
    fetchCurrentBudget,
    fetchBudgetById,
    addBudget,
    updateBudget,
    deleteBudget,
    addCategory,
    updateCategory,
    deleteCategory,
  };
});
