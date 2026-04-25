import type { Loan } from '../types';
import { mockLoans } from '../mock-data/loans';
// import { apiBridge } from './api-bridge'; // Uncomment when backend ready

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

export const loanService = {
  async getLoans(): Promise<Loan[]> {
    await delay(50);
    // TODO: Replace with: return apiBridge.get('/loans');
    return [...mockLoans];
  },

  async getLoanById(id: string): Promise<Loan | undefined> {
    await delay(30);
    // TODO: Replace with: return apiBridge.get(`/loans/${id}`);
    return mockLoans.find(l => l.id === id);
  },

  async createLoan(data: Omit<Loan, 'id' | 'createdAt' | 'updatedAt'>): Promise<Loan> {
    await delay(50);
    // TODO: Replace with: return apiBridge.post('/loans', data);
    return {
      ...data,
      id: `loan_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  async updateLoan(id: string, data: Partial<Loan>): Promise<Loan> {
    await delay(50);
    // TODO: Replace with: return apiBridge.put(`/loans/${id}`, data);
    const loan = mockLoans.find(l => l.id === id);
    if (!loan) throw new Error('Loan not found');
    return { ...loan, ...data, updatedAt: new Date().toISOString() };
  },

  async deleteLoan(id: string): Promise<void> {
    await delay(50);
    // TODO: Replace with: return apiBridge.delete(`/loans/${id}`);
    console.log(`Deleted loan ${id}`);
  },
};
