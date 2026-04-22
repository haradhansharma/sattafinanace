import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Expense, ExpenseCategory } from '../types';
import { mockExpenses, mockExpenseCategories } from '../mock-data';
import { useCurrencyStore } from './currency';
import { generateId } from '../utils/formatters';

export const useExpenseStore = defineStore('expense', () => {
  const expenses = ref<Expense[]>(mockExpenses.map(e => ({ ...e })));
  const categories = ref<ExpenseCategory[]>(mockExpenseCategories.map(c => ({ ...c })));

  const totalMonthlyExpense = computed(() => {
    const currencyStore = useCurrencyStore();
    return expenses.value.reduce((sum, expense) => sum + currencyStore.convertToBase(expense.amount, expense.currency || 'BDT'), 0);
  });

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

  function addExpense(data: Omit<Expense, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const expense: Expense = {
      ...data,
      id: generateId('exp'),
      createdAt: now,
      updatedAt: now,
    };
    expenses.value.push(expense);
    return expense;
  }

  function updateExpense(id: string, data: Partial<Expense>) {
    const index = expenses.value.findIndex(e => e.id === id);
    if (index === -1) return null;
    expenses.value[index] = {
      ...expenses.value[index],
      ...data,
      id: expenses.value[index].id,
      createdAt: expenses.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return expenses.value[index];
  }

  function deleteExpense(id: string) {
    const index = expenses.value.findIndex(e => e.id === id);
    if (index !== -1) {
      expenses.value.splice(index, 1);
    }
  }

  // ==================== Category CRUD ====================

  function addCategory(data: Omit<ExpenseCategory, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const category: ExpenseCategory = {
      ...data,
      id: generateId('exp_cat'),
      createdAt: now,
      updatedAt: now,
    };
    categories.value.push(category);
    return category;
  }

  function updateCategory(id: string, data: Partial<ExpenseCategory>) {
    const index = categories.value.findIndex(c => c.id === id);
    if (index === -1) return null;
    categories.value[index] = {
      ...categories.value[index],
      ...data,
      id: categories.value[index].id,
      createdAt: categories.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return categories.value[index];
  }

  function deleteCategory(id: string) {
    const index = categories.value.findIndex(c => c.id === id);
    if (index !== -1) {
      categories.value.splice(index, 1);
    }
  }

  return {
    expenses,
    categories,
    totalMonthlyExpense,
    getExpensesByCategory,
    getExpensesByDateRange,
    getCategoryBreakdown,
    addExpense,
    updateExpense,
    deleteExpense,
    addCategory,
    updateCategory,
    deleteCategory,
  };
});
