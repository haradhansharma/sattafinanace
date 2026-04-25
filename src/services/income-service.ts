import type { Income, IncomeSource } from '../types';
import { mockIncomes } from '../mock-data/incomes';
import { mockIncomeSources } from '../mock-data/income-sources';
// import { apiBridge } from './api-bridge'; // Uncomment when backend ready

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

export const incomeService = {
  // ==================== Income CRUD ====================

  async getIncomes(): Promise<Income[]> {
    await delay(50);
    // TODO: Replace with: return apiBridge.get('/incomes');
    return [...mockIncomes].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },

  async getIncomeById(id: string): Promise<Income | undefined> {
    await delay(30);
    // TODO: Replace with: return apiBridge.get(`/incomes/${id}`);
    return mockIncomes.find(i => i.id === id);
  },

  async createIncome(data: Omit<Income, 'id' | 'createdAt' | 'updatedAt'>): Promise<Income> {
    await delay(50);
    // TODO: Replace with: return apiBridge.post('/incomes', data);
    return {
      ...data,
      id: `inc_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  async updateIncome(id: string, data: Partial<Income>): Promise<Income> {
    await delay(50);
    // TODO: Replace with: return apiBridge.put(`/incomes/${id}`, data);
    const income = mockIncomes.find(i => i.id === id);
    if (!income) throw new Error('Income not found');
    return { ...income, ...data, updatedAt: new Date().toISOString() };
  },

  async deleteIncome(id: string): Promise<void> {
    await delay(50);
    // TODO: Replace with: return apiBridge.delete(`/incomes/${id}`);
    console.log(`Deleted income ${id}`);
  },

  // ==================== Income Sources CRUD ====================

  async getSources(): Promise<IncomeSource[]> {
    await delay(50);
    // TODO: Replace with: return apiBridge.get('/income-sources');
    return [...mockIncomeSources];
  },

  async getSourceById(id: string): Promise<IncomeSource | undefined> {
    await delay(30);
    // TODO: Replace with: return apiBridge.get(`/income-sources/${id}`);
    return mockIncomeSources.find(s => s.id === id);
  },

  async createSource(data: Omit<IncomeSource, 'id' | 'createdAt' | 'updatedAt'>): Promise<IncomeSource> {
    await delay(50);
    // TODO: Replace with: return apiBridge.post('/income-sources', data);
    return {
      ...data,
      id: `isrc_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  async updateSource(id: string, data: Partial<IncomeSource>): Promise<IncomeSource> {
    await delay(50);
    // TODO: Replace with: return apiBridge.put(`/income-sources/${id}`, data);
    const source = mockIncomeSources.find(s => s.id === id);
    if (!source) throw new Error('Income source not found');
    return { ...source, ...data, updatedAt: new Date().toISOString() };
  },

  async deleteSource(id: string): Promise<void> {
    await delay(50);
    // TODO: Replace with: return apiBridge.delete(`/income-sources/${id}`);
    console.log(`Deleted income source ${id}`);
  },
};
