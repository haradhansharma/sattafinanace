// import { defineStore } from 'pinia';
// import { ref, computed } from 'vue';
// import type { Expense, ExpenseCategory } from '../types';
// import { api, fetchAllPages, ApiError } from '../services/api-bridge';
// import { useCurrencyStore } from './currency';

// export interface CategoryBreakdownItem {
//   categoryId: string;
//   categoryName: string;
//   categoryIcon?: string;
//   categoryColor?: string;
//   categoryType?: string;
//   total: number;
//   percentage: number;
// }

// export const useExpenseStore = defineStore('expense', () => {
//   // ==================== State ====================
//   const expenses = ref<Expense[]>([]);
//   const categories = ref<ExpenseCategory[]>([]);
//   const categoryBreakdown = ref<CategoryBreakdownItem[]>([]);

//   const loading = ref(false);
//   const error = ref<string | null>(null);

//   // ==================== Computed ====================

//   const totalMonthlyExpense = computed(() => {
//     const currencyStore = useCurrencyStore();
//     return expenses.value.reduce(
//       (sum, expense) => sum + currencyStore.convertToBase(expense.amount, expense.currency || 'BDT'),
//       0,
//     );
//   });

//   // ==================== Fetch Methods ====================

//   async function fetchExpenses(params?: {
//     categoryId?: string;
//     dateFrom?: string;
//     dateTo?: string;
//     isRecurring?: boolean;
//   }): Promise<void> {
//     loading.value = true;
//     error.value = null;
//     try {
//       const items = await fetchAllPages<Expense>('/expense/', { params });
//       expenses.value = items;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to fetch expenses';
//       throw err;
//     } finally {
//       loading.value = false;
//     }
//   }

//   async function fetchCategories(params?: { type?: string }): Promise<void> {
//     loading.value = true;
//     error.value = null;
//     try {
//       const items = await fetchAllPages<ExpenseCategory>('/expense/categories/', { params });
//       categories.value = items;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to fetch expense categories';
//       throw err;
//     } finally {
//       loading.value = false;
//     }
//   }

//   async function fetchCategoryBreakdown(dateFrom?: string, dateTo?: string): Promise<void> {
//     loading.value = true;
//     error.value = null;
//     try {
//       const items = await api.get<CategoryBreakdownItem[]>('/expense/category-breakdown/', {
//         params: { dateFrom, dateTo },
//       });
//       categoryBreakdown.value = items;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to fetch category breakdown';
//       throw err;
//     } finally {
//       loading.value = false;
//     }
//   }

//   // ==================== Helpers ====================

//   function getExpensesByCategory(categoryId: string): Expense[] {
//     return expenses.value
//       .filter(e => e.categoryId === categoryId)
//       .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
//   }

//   function getExpensesByDateRange(start: string, end: string): Expense[] {
//     const startDate = new Date(start).getTime();
//     const endDate = new Date(end).getTime();
//     return expenses.value
//       .filter(e => {
//         const d = new Date(e.date).getTime();
//         return d >= startDate && d <= endDate;
//       })
//       .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
//   }

//   function getCategoryBreakdown(): Array<{
//     category: ExpenseCategory;
//     total: number;
//     percentage: number;
//   }> {
//     const total = totalMonthlyExpense.value;
//     if (total === 0) return [];
//     const currencyStore = useCurrencyStore();

//     return categories.value
//       .map(category => {
//         const categoryExpenses = expenses.value.filter(e => e.categoryId === category.id);
//         const catTotal = categoryExpenses.reduce(
//           (sum, e) => sum + currencyStore.convertToBase(e.amount, e.currency || 'BDT'),
//           0,
//         );
//         return {
//           category,
//           total: catTotal,
//           percentage: (catTotal / total) * 100,
//         };
//       })
//       .filter(item => item.total > 0)
//       .sort((a, b) => b.total - a.total);
//   }

//   // ==================== Expense CRUD ====================

//   async function addExpense(data: Omit<Expense, 'id' | 'createdAt' | 'updatedAt'>): Promise<Expense> {
//     error.value = null;
//     try {
//       const expense = await api.post<Expense>('/expense/', data);
//       expenses.value.push(expense);
//       return expense;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to create expense';
//       throw err;
//     }
//   }

//   async function updateExpense(id: string, data: Partial<Expense>): Promise<Expense | null> {
//     error.value = null;
//     try {
//       const updated = await api.put<Expense>(`/expense/${id}/`, data);
//       const index = expenses.value.findIndex(e => e.id === id);
//       if (index !== -1) {
//         expenses.value[index] = updated;
//       }
//       return updated;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to update expense';
//       throw err;
//     }
//   }

//   async function deleteExpense(id: string): Promise<void> {
//     error.value = null;
//     try {
//       await api.delete(`/expense/${id}/`);
//       const index = expenses.value.findIndex(e => e.id === id);
//       if (index !== -1) {
//         expenses.value.splice(index, 1);
//       }
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to delete expense';
//       throw err;
//     }
//   }

//   // ==================== Category CRUD ====================

//   async function addCategory(data: Omit<ExpenseCategory, 'id' | 'createdAt' | 'updatedAt'>): Promise<ExpenseCategory> {
//     error.value = null;
//     try {
//       const category = await api.post<ExpenseCategory>('/expense/categories/', data);
//       categories.value.push(category);
//       return category;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to create expense category';
//       throw err;
//     }
//   }

//   async function updateCategory(id: string, data: Partial<ExpenseCategory>): Promise<ExpenseCategory | null> {
//     error.value = null;
//     try {
//       const updated = await api.put<ExpenseCategory>(`/expense/categories/${id}/`, data);
//       const index = categories.value.findIndex(c => c.id === id);
//       if (index !== -1) {
//         categories.value[index] = updated;
//       }
//       return updated;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to update expense category';
//       throw err;
//     }
//   }

//   async function deleteCategory(id: string): Promise<void> {
//     error.value = null;
//     try {
//       await api.delete(`/expense/categories/${id}/`);
//       const index = categories.value.findIndex(c => c.id === id);
//       if (index !== -1) {
//         categories.value.splice(index, 1);
//       }
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to delete expense category';
//       throw err;
//     }
//   }

//   return {
//     // State
//     expenses,
//     categories,
//     categoryBreakdown,
//     loading,
//     error,
//     // Computed
//     totalMonthlyExpense,
//     // Fetch
//     fetchExpenses,
//     fetchCategories,
//     fetchCategoryBreakdown,
//     // Helpers
//     getExpensesByCategory,
//     getExpensesByDateRange,
//     getCategoryBreakdown,
//     // Expense CRUD
//     addExpense,
//     updateExpense,
//     deleteExpense,
//     // Category CRUD
//     addCategory,
//     updateCategory,
//     deleteCategory,
//   };
// });
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Expense, ExpenseCategory } from '../types';
import { api, fetchAllPages, ApiError } from '../services/api-bridge';
import { useCurrencyStore } from './currency';

export interface CategoryBreakdownItem {
  categoryId: string;
  categoryName: string;
  categoryIcon?: string;
  categoryColor?: string;
  categoryType?: string;
  total: number;
  percentage: number;
}

export const useExpenseStore = defineStore('expense', () => {
  // ==================== State ====================
  const expenses = ref<Expense[]>([]);
  const categories = ref<ExpenseCategory[]>([]);
  const categoryBreakdown = ref<CategoryBreakdownItem[]>([]);

  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Computed ====================

  const totalMonthlyExpense = computed(() => {
    const currencyStore = useCurrencyStore();
    return expenses.value.reduce(
      (sum, expense) => sum + currencyStore.convertToBase(expense.amount, expense.currency || 'BDT'),
      0,
    );
  });

  // ==================== Fetch Methods ====================

  async function fetchExpenses(params?: {
    categoryId?: string;
    dateFrom?: string;
    dateTo?: string;
    isRecurring?: boolean;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const items = await fetchAllPages<Expense>('/expense/', { params });
      expenses.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch expenses';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchCategories(params?: { type?: string }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const items = await fetchAllPages<ExpenseCategory>('/expense/categories/', { params });
      categories.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch expense categories';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchCategoryBreakdown(dateFrom?: string, dateTo?: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const items = await api.get<CategoryBreakdownItem[]>('/expense/category-breakdown/', {
        params: { dateFrom, dateTo },
      });
      categoryBreakdown.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch category breakdown';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Helpers ====================

  function getExpensesByCategory(categoryId: string): Expense[] {
    return expenses.value
      .filter(e => e.categoryId === categoryId)
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }

  function getExpensesByDateRange(start: string, end: string): Expense[] {
    const startDate = new Date(start).getTime();
    const endDate = new Date(end).getTime();
    return expenses.value
      .filter(e => {
        const d = new Date(e.date).getTime();
        return d >= startDate && d <= endDate;
      })
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }

  function getCategoryBreakdown(): Array<{
    category: ExpenseCategory;
    total: number;
    percentage: number;
  }> {
    const total = totalMonthlyExpense.value;
    if (total === 0) return [];
    const currencyStore = useCurrencyStore();

    return categories.value
      .map(category => {
        const categoryExpenses = expenses.value.filter(e => e.categoryId === category.id);
        const catTotal = categoryExpenses.reduce(
          (sum, e) => sum + currencyStore.convertToBase(e.amount, e.currency || 'BDT'),
          0,
        );
        return {
          category,
          total: catTotal,
          percentage: (catTotal / total) * 100,
        };
      })
      .filter(item => item.total > 0)
      .sort((a, b) => b.total - a.total);
  }

  // ==================== Expense CRUD ====================

  async function addExpense(data: Omit<Expense, 'id' | 'createdAt' | 'updatedAt'>): Promise<Expense> {
    error.value = null;
    try {
      const expense = await api.post<Expense>('/expense/', data);
      expenses.value.unshift(expense);
      return expense;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create expense';
      throw err;
    }
  }

  async function updateExpense(id: string, data: Partial<Expense>): Promise<Expense | null> {
    error.value = null;
    try {
      const updated = await api.put<Expense>(`/expense/${id}/`, data);
      const index = expenses.value.findIndex(e => e.id === id);
      if (index !== -1) {
        expenses.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update expense';
      throw err;
    }
  }

  async function deleteExpense(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/expense/${id}/`);
      const index = expenses.value.findIndex(e => e.id === id);
      if (index !== -1) {
        expenses.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete expense';
      throw err;
    }
  }

  // ==================== Category CRUD ====================

  async function addCategory(data: Omit<ExpenseCategory, 'id' | 'createdAt' | 'updatedAt'>): Promise<ExpenseCategory> {
    error.value = null;
    try {
      const category = await api.post<ExpenseCategory>('/expense/categories/', data);
      categories.value.unshift(category);
      return category;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create expense category';
      throw err;
    }
  }

  async function updateCategory(id: string, data: Partial<ExpenseCategory>): Promise<ExpenseCategory | null> {
    error.value = null;
    try {
      const updated = await api.put<ExpenseCategory>(`/expense/categories/${id}/`, data);
      const index = categories.value.findIndex(c => c.id === id);
      if (index !== -1) {
        categories.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update expense category';
      throw err;
    }
  }

  async function deleteCategory(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/expense/categories/${id}/`);
      const index = categories.value.findIndex(c => c.id === id);
      if (index !== -1) {
        categories.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete expense category';
      throw err;
    }
  }

  return {
    // State
    expenses,
    categories,
    categoryBreakdown,
    loading,
    error,
    // Computed
    totalMonthlyExpense,
    // Fetch
    fetchExpenses,
    fetchCategories,
    fetchCategoryBreakdown,
    // Helpers
    getExpensesByCategory,
    getExpensesByDateRange,
    getCategoryBreakdown,
    // Expense CRUD
    addExpense,
    updateExpense,
    deleteExpense,
    // Category CRUD
    addCategory,
    updateCategory,
    deleteCategory,
  };
});
