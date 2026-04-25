import type { Expense, ExpenseCategory } from '../types';
import { dataService } from './data-service';

export const expenseService = {
  // ==================== Expense CRUD ====================

  async getExpenses(): Promise<Expense[]> {
    return dataService.getAll<Expense>('expenses');
  },

  async getExpenseById(id: string): Promise<Expense | undefined> {
    return dataService.getById<Expense>('expenses', id) ?? undefined;
  },

  async createExpense(data: Omit<Expense, 'id' | 'createdAt' | 'updatedAt'>): Promise<Expense> {
    return dataService.create<Expense>('expenses', data);
  },

  async updateExpense(id: string, data: Partial<Expense>): Promise<Expense> {
    return dataService.update<Expense & { id: string }>('expenses', id, data);
  },

  async deleteExpense(id: string): Promise<void> {
    return dataService.remove('expenses', id);
  },

  // ==================== Expense Categories CRUD ====================

  async getCategories(): Promise<ExpenseCategory[]> {
    return dataService.getAll<ExpenseCategory>('expenseCategories');
  },

  async getCategoryById(id: string): Promise<ExpenseCategory | undefined> {
    return dataService.getById<ExpenseCategory>('expenseCategories', id) ?? undefined;
  },

  async createCategory(data: Omit<ExpenseCategory, 'id' | 'createdAt' | 'updatedAt'>): Promise<ExpenseCategory> {
    return dataService.create<ExpenseCategory>('expenseCategories', data);
  },

  async updateCategory(id: string, data: Partial<ExpenseCategory>): Promise<ExpenseCategory> {
    return dataService.update<ExpenseCategory & { id: string }>('expenseCategories', id, data);
  },

  async deleteCategory(id: string): Promise<void> {
    return dataService.remove('expenseCategories', id);
  },

  // ==================== Query Methods ====================

  async getExpensesByDateRange(start: string, end: string): Promise<Expense[]> {
    const allExpenses = await dataService.getAll<Expense>('expenses');
    const startDate = new Date(start);
    const endDate = new Date(end);
    return allExpenses
      .filter(e => {
        const date = new Date(e.date);
        return date >= startDate && date <= endDate;
      })
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },

  async getCategoryBreakdown(start?: string, end?: string): Promise<(ExpenseCategory & { total: number; count: number })[]> {
    let filteredExpenses = await dataService.getAll<Expense>('expenses');
    const categories = await dataService.getAll<ExpenseCategory>('expenseCategories');

    if (start && end) {
      const startDate = new Date(start);
      const endDate = new Date(end);
      filteredExpenses = filteredExpenses.filter(e => {
        const date = new Date(e.date);
        return date >= startDate && date <= endDate;
      });
    }

    return categories
      .map(cat => {
        const expenses = filteredExpenses.filter(e => e.categoryId === cat.id);
        const total = expenses.reduce((sum, e) => sum + e.amount, 0);
        return { ...cat, total, count: expenses.length };
      })
      .filter(c => c.total > 0)
      .sort((a, b) => b.total - a.total);
  },
};
