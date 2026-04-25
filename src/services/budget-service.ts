import type { Budget } from '../types';
import { mockBudgets } from '../mock-data/budgets';
// import { apiBridge } from './api-bridge'; // Uncomment when backend ready

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

export const budgetService = {
  async getBudgets(): Promise<Budget[]> {
    await delay(50);
    // TODO: Replace with: return apiBridge.get('/budgets');
    return [...mockBudgets].sort((a, b) => b.month.localeCompare(a.month));
  },

  async getBudgetById(id: string): Promise<Budget | undefined> {
    await delay(30);
    // TODO: Replace with: return apiBridge.get(`/budgets/${id}`);
    return mockBudgets.find(b => b.id === id);
  },

  async getBudgetByMonth(month: string): Promise<Budget | undefined> {
    await delay(40);
    // TODO: Replace with: return apiBridge.get(`/budgets?month=${month}`);
    return mockBudgets.find(b => b.month === month);
  },

  async createBudget(data: Omit<Budget, 'id' | 'createdAt' | 'updatedAt'>): Promise<Budget> {
    await delay(50);
    // TODO: Replace with: return apiBridge.post('/budgets', data);
    return {
      ...data,
      id: `bud_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  async updateBudget(id: string, data: Partial<Budget>): Promise<Budget> {
    await delay(50);
    // TODO: Replace with: return apiBridge.put(`/budgets/${id}`, data);
    const budget = mockBudgets.find(b => b.id === id);
    if (!budget) throw new Error('Budget not found');
    return { ...budget, ...data, updatedAt: new Date().toISOString() };
  },

  async deleteBudget(id: string): Promise<void> {
    await delay(50);
    // TODO: Replace with: return apiBridge.delete(`/budgets/${id}`);
    console.log(`Deleted budget ${id}`);
  },
};
