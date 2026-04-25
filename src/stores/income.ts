// import { defineStore } from 'pinia';
// import { ref, computed } from 'vue';
// import type { Income, IncomeSource, IncomeCategory } from '../types';
// import { api, fetchAllPages, ApiError } from '../services/api-bridge';
// import { useCurrencyStore } from './currency';

// export const useIncomeStore = defineStore('income', () => {
//   // ==================== State ====================
//   const incomes = ref<Income[]>([]);
//   const incomeSources = ref<IncomeSource[]>([]);
//   const incomeCategories = ref<IncomeCategory[]>([]);

//   const loading = ref(false);
//   const error = ref<string | null>(null);

//   // ==================== Computed ====================

//   const totalMonthlyIncome = computed(() => {
//     const currencyStore = useCurrencyStore();
//     return incomes.value.reduce(
//       (sum, income) => sum + currencyStore.convertToBase(income.amount, income.currency || 'BDT'),
//       0,
//     );
//   });

//   const totalYearlyIncome = computed(() => {
//     // Sum the last 12 months of income records (or all available)
//     const currencyStore = useCurrencyStore();
//     const now = new Date();
//     const twelveMonthsAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
//     return incomes.value
//       .filter(i => new Date(i.date) >= twelveMonthsAgo)
//       .reduce(
//         (sum, income) => sum + currencyStore.convertToBase(income.amount, income.currency || 'BDT'),
//         0,
//       );
//   });

//   /**
//    * Expected income this month: sum of all recurring sources with monthlyAmount
//    * (salary, rental, etc.) — represents what's *supposed* to come in.
//    */
//   const expectedMonthlyIncome = computed(() => {
//     const currencyStore = useCurrencyStore();
//     return incomeSources.value
//       .filter(s => s.isActive && s.monthlyAmount && s.monthlyAmount > 0)
//       .reduce((sum, s) => sum + currencyStore.convertToBase(s.monthlyAmount!, s.currency || 'BDT'), 0);
//   });

//   /**
//    * Already received this month: sum of income records for the current month.
//    */
//   const receivedThisMonth = computed(() => {
//     const now = new Date();
//     const monthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
//     const currencyStore = useCurrencyStore();
//     return incomes.value
//       .filter(i => i.date.startsWith(monthStr))
//       .reduce(
//         (sum, i) => sum + currencyStore.convertToBase(i.amount, i.currency || 'BDT'),
//         0,
//       );
//   });

//   /**
//    * Upcoming (pending) income this month: expected minus received.
//    * Can be negative if one-time income boosts the total above recurring expected.
//    */
//   const pendingIncomeThisMonth = computed(() => {
//     return Math.max(0, expectedMonthlyIncome.value - receivedThisMonth.value);
//   });

//   /**
//    * List of recurring sources that haven't been received yet this month.
//    */
//   const pendingSources = computed(() => {
//     const now = new Date();
//     const monthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
//     return incomeSources.value
//       .filter(s => s.isActive && s.monthlyAmount && s.monthlyAmount > 0)
//       .filter(s => {
//         // Check if there's an income record for this source this month
//         return !incomes.value.some(
//           i => i.sourceId === s.id && i.date.startsWith(monthStr),
//         );
//       });
//   });

//   // ==================== Fetch Methods ====================

//   async function fetchIncomes(params?: {
//     sourceId?: string;
//     month?: string;
//     categoryId?: string;
//     dateFrom?: string;
//     dateTo?: string;
//   }): Promise<void> {
//     loading.value = true;
//     error.value = null;
//     try {
//       const items = await fetchAllPages<Income>('/income/', { params });
//       incomes.value = items;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to fetch incomes';
//       throw err;
//     } finally {
//       loading.value = false;
//     }
//   }

//   async function fetchIncomeSources(params?: {
//     type?: string;
//     isActive?: boolean;
//   }): Promise<void> {
//     loading.value = true;
//     error.value = null;
//     try {
//       const items = await api.get<IncomeSource[]>('/income/sources/', { params });
//       incomeSources.value = items;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to fetch income sources';
//       throw err;
//     } finally {
//       loading.value = false;
//     }
//   }

//   async function fetchIncomeCategories(params?: { type?: string }): Promise<void> {
//     loading.value = true;
//     error.value = null;
//     try {
//       const items = await api.get<IncomeCategory[]>('/income/categories/', { params });
//       incomeCategories.value = items;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to fetch income categories';
//       throw err;
//     } finally {
//       loading.value = false;
//     }
//   }

//   // ==================== Helpers ====================

//   function getIncomesBySource(sourceId: string): Income[] {
//     return incomes.value
//       .filter(i => i.sourceId === sourceId)
//       .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
//   }

//   function getIncomeByMonth(month: string): Income[] {
//     // month format: 'YYYY-MM'
//     return incomes.value
//       .filter(i => i.date.startsWith(month))
//       .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
//   }

//   function getMonthlyTotalBySource(sourceId: string): number {
//     const source = incomeSources.value.find(s => s.id === sourceId);
//     return source?.monthlyAmount ?? 0;
//   }

//   function getIncomeCategoryById(categoryId: string): IncomeCategory | undefined {
//     return incomeCategories.value.find(c => c.id === categoryId);
//   }

//   // ==================== Income CRUD ====================

//   async function addIncome(data: Omit<Income, 'id' | 'createdAt' | 'updatedAt'>): Promise<Income> {
//     error.value = null;
//     try {
//       const income = await api.post<Income>('/income/', data);
//       incomes.value.push(income);
//       return income;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to create income';
//       throw err;
//     }
//   }

//   async function updateIncome(id: string, data: Partial<Income>): Promise<Income | null> {
//     error.value = null;
//     try {
//       const updated = await api.put<Income>(`/income/${id}/`, data);
//       const index = incomes.value.findIndex(i => i.id === id);
//       if (index !== -1) {
//         incomes.value[index] = updated;
//       }
//       return updated;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to update income';
//       throw err;
//     }
//   }

//   async function deleteIncome(id: string): Promise<void> {
//     error.value = null;
//     try {
//       await api.delete(`/income/${id}/`);
//       const index = incomes.value.findIndex(i => i.id === id);
//       if (index !== -1) {
//         incomes.value.splice(index, 1);
//       }
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to delete income';
//       throw err;
//     }
//   }

//   // ==================== Income Source CRUD ====================

//   async function addIncomeSource(data: Omit<IncomeSource, 'id' | 'createdAt' | 'updatedAt'>): Promise<IncomeSource> {
//     error.value = null;
//     try {
//       const source = await api.post<IncomeSource>('/income/sources/', data);
//       incomeSources.value.push(source);
//       return source;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to create income source';
//       throw err;
//     }
//   }

//   async function updateIncomeSource(id: string, data: Partial<IncomeSource>): Promise<IncomeSource | null> {
//     error.value = null;
//     try {
//       const updated = await api.put<IncomeSource>(`/income/sources/${id}/`, data);
//       const index = incomeSources.value.findIndex(s => s.id === id);
//       if (index !== -1) {
//         incomeSources.value[index] = updated;
//       }
//       return updated;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to update income source';
//       throw err;
//     }
//   }

//   async function deleteIncomeSource(id: string): Promise<void> {
//     error.value = null;
//     try {
//       await api.delete(`/income/sources/${id}/`);
//       const index = incomeSources.value.findIndex(s => s.id === id);
//       if (index !== -1) {
//         incomeSources.value.splice(index, 1);
//       }
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to delete income source';
//       throw err;
//     }
//   }

//   // ==================== Income Category CRUD ====================

//   async function addIncomeCategory(data: Omit<IncomeCategory, 'id' | 'createdAt' | 'updatedAt'>): Promise<IncomeCategory> {
//     error.value = null;
//     try {
//       const category = await api.post<IncomeCategory>('/income/categories/', data);
//       incomeCategories.value.push(category);
//       return category;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to create income category';
//       throw err;
//     }
//   }

//   async function updateIncomeCategory(id: string, data: Partial<IncomeCategory>): Promise<IncomeCategory | null> {
//     error.value = null;
//     try {
//       const updated = await api.put<IncomeCategory>(`/income/categories/${id}/`, data);
//       const index = incomeCategories.value.findIndex(c => c.id === id);
//       if (index !== -1) {
//         incomeCategories.value[index] = updated;
//       }
//       return updated;
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to update income category';
//       throw err;
//     }
//   }

//   async function deleteIncomeCategory(id: string): Promise<void> {
//     error.value = null;
//     try {
//       await api.delete(`/income/categories/${id}/`);
//       const index = incomeCategories.value.findIndex(c => c.id === id);
//       if (index !== -1) {
//         incomeCategories.value.splice(index, 1);
//       }
//     } catch (err) {
//       error.value = err instanceof ApiError ? err.message : 'Failed to delete income category';
//       throw err;
//     }
//   }

//   return {
//     // State
//     incomes,
//     incomeSources,
//     incomeCategories,
//     loading,
//     error,
//     // Computed
//     totalMonthlyIncome,
//     totalYearlyIncome,
//     expectedMonthlyIncome,
//     receivedThisMonth,
//     pendingIncomeThisMonth,
//     pendingSources,
//     // Fetch
//     fetchIncomes,
//     fetchIncomeSources,
//     fetchIncomeCategories,
//     // Helpers
//     getIncomesBySource,
//     getIncomeByMonth,
//     getMonthlyTotalBySource,
//     getIncomeCategoryById,
//     // Income CRUD
//     addIncome,
//     updateIncome,
//     deleteIncome,
//     // Income Source CRUD
//     addIncomeSource,
//     updateIncomeSource,
//     deleteIncomeSource,
//     // Income Category CRUD
//     addIncomeCategory,
//     updateIncomeCategory,
//     deleteIncomeCategory,
//   };
// });
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Income, IncomeSource, IncomeCategory } from '../types';
import { api, fetchAllPages, ApiError } from '../services/api-bridge';
import { useCurrencyStore } from './currency';

export const useIncomeStore = defineStore('income', () => {
  // ==================== State ====================
  const incomes = ref<Income[]>([]);
  const incomeSources = ref<IncomeSource[]>([]);
  const incomeCategories = ref<IncomeCategory[]>([]);

  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Computed ====================

  const totalMonthlyIncome = computed(() => {
    const currencyStore = useCurrencyStore();
    return incomes.value.reduce(
      (sum, income) => sum + currencyStore.convertToBase(income.amount, income.currency || 'BDT'),
      0,
    );
  });

  const totalYearlyIncome = computed(() => {
    // Sum the last 12 months of income records (or all available)
    const currencyStore = useCurrencyStore();
    const now = new Date();
    const twelveMonthsAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
    return incomes.value
      .filter(i => new Date(i.date) >= twelveMonthsAgo)
      .reduce(
        (sum, income) => sum + currencyStore.convertToBase(income.amount, income.currency || 'BDT'),
        0,
      );
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
      .reduce(
        (sum, i) => sum + currencyStore.convertToBase(i.amount, i.currency || 'BDT'),
        0,
      );
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
          i => i.sourceId === s.id && i.date.startsWith(monthStr),
        );
      });
  });

  // ==================== Fetch Methods ====================

  async function fetchIncomes(params?: {
    sourceId?: string;
    month?: string;
    categoryId?: string;
    dateFrom?: string;
    dateTo?: string;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const items = await fetchAllPages<Income>('/income/', { params });
      incomes.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch incomes';
    } finally {
      loading.value = false;
    }
  }

  async function fetchIncomeSources(params?: {
    type?: string;
    isActive?: boolean;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const items = await fetchAllPages<IncomeSource>('/income/sources/', { params });
      incomeSources.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch income sources';
    } finally {
      loading.value = false;
    }
  }

  async function fetchIncomeCategories(params?: { type?: string }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const items = await fetchAllPages<IncomeCategory>('/income/categories/', { params });
      incomeCategories.value = items;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch income categories';
    } finally {
      loading.value = false;
    }
  }

  // ==================== Helpers ====================

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

  async function addIncome(data: Omit<Income, 'id' | 'createdAt' | 'updatedAt'>): Promise<Income> {
    error.value = null;
    try {
      const income = await api.post<Income>('/income/', data);
      incomes.value.unshift(income);
      return income;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create income';
      throw err;
    }
  }

  async function updateIncome(id: string, data: Partial<Income>): Promise<Income | null> {
    error.value = null;
    try {
      const updated = await api.put<Income>(`/income/${id}/`, data);
      const index = incomes.value.findIndex(i => i.id === id);
      if (index !== -1) {
        incomes.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update income';
      throw err;
    }
  }

  async function deleteIncome(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/income/${id}/`);
      const index = incomes.value.findIndex(i => i.id === id);
      if (index !== -1) {
        incomes.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete income';
      throw err;
    }
  }

  // ==================== Income Source CRUD ====================

  async function addIncomeSource(data: Omit<IncomeSource, 'id' | 'createdAt' | 'updatedAt'>): Promise<IncomeSource> {
    error.value = null;
    try {
      const source = await api.post<IncomeSource>('/income/sources/', data);
      incomeSources.value.unshift(source);
      return source;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create income source';
      throw err;
    }
  }

  async function updateIncomeSource(id: string, data: Partial<IncomeSource>): Promise<IncomeSource | null> {
    error.value = null;
    try {
      const updated = await api.put<IncomeSource>(`/income/sources/${id}/`, data);
      const index = incomeSources.value.findIndex(s => s.id === id);
      if (index !== -1) {
        incomeSources.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update income source';
      throw err;
    }
  }

  async function deleteIncomeSource(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/income/sources/${id}/`);
      const index = incomeSources.value.findIndex(s => s.id === id);
      if (index !== -1) {
        incomeSources.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete income source';
      throw err;
    }
  }

  // ==================== Income Category CRUD ====================

  async function addIncomeCategory(data: Omit<IncomeCategory, 'id' | 'createdAt' | 'updatedAt'>): Promise<IncomeCategory> {
    error.value = null;
    try {
      const category = await api.post<IncomeCategory>('/income/categories/', data);
      incomeCategories.value.unshift(category);
      return category;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create income category';
      throw err;
    }
  }

  async function updateIncomeCategory(id: string, data: Partial<IncomeCategory>): Promise<IncomeCategory | null> {
    error.value = null;
    try {
      const updated = await api.put<IncomeCategory>(`/income/categories/${id}/`, data);
      const index = incomeCategories.value.findIndex(c => c.id === id);
      if (index !== -1) {
        incomeCategories.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update income category';
      throw err;
    }
  }

  async function deleteIncomeCategory(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/income/categories/${id}/`);
      const index = incomeCategories.value.findIndex(c => c.id === id);
      if (index !== -1) {
        incomeCategories.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete income category';
      throw err;
    }
  }

  return {
    // State
    incomes,
    incomeSources,
    incomeCategories,
    loading,
    error,
    // Computed
    totalMonthlyIncome,
    totalYearlyIncome,
    expectedMonthlyIncome,
    receivedThisMonth,
    pendingIncomeThisMonth,
    pendingSources,
    // Fetch
    fetchIncomes,
    fetchIncomeSources,
    fetchIncomeCategories,
    // Helpers
    getIncomesBySource,
    getIncomeByMonth,
    getMonthlyTotalBySource,
    getIncomeCategoryById,
    // Income CRUD
    addIncome,
    updateIncome,
    deleteIncome,
    // Income Source CRUD
    addIncomeSource,
    updateIncomeSource,
    deleteIncomeSource,
    // Income Category CRUD
    addIncomeCategory,
    updateIncomeCategory,
    deleteIncomeCategory,
  };
});
