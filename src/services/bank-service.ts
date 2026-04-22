import type { BankAccount, Transaction } from '../types';
import { mockBankAccounts } from '../pages/mock-data/bank-accounts';
import { mockTransactions } from '../pages/mock-data/transactions';
// import { apiBridge } from './api-bridge'; // Uncomment when backend ready

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

export const bankService = {
  async getAccounts(): Promise<BankAccount[]> {
    await delay(50);
    // TODO: Replace with: return apiBridge.get('/bank-accounts');
    return [...mockBankAccounts];
  },

  async getAccountById(id: string): Promise<BankAccount | undefined> {
    await delay(30);
    // TODO: Replace with: return apiBridge.get(`/bank-accounts/${id}`);
    return mockBankAccounts.find(a => a.id === id);
  },

  async createAccount(data: Omit<BankAccount, 'id' | 'createdAt' | 'updatedAt'>): Promise<BankAccount> {
    await delay(50);
    // TODO: Replace with: return apiBridge.post('/bank-accounts', data);
    return {
      ...data,
      id: `ba_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  async updateAccount(id: string, data: Partial<BankAccount>): Promise<BankAccount> {
    await delay(50);
    // TODO: Replace with: return apiBridge.put(`/bank-accounts/${id}`, data);
    const account = mockBankAccounts.find(a => a.id === id);
    if (!account) throw new Error('Account not found');
    return { ...account, ...data, updatedAt: new Date().toISOString() };
  },

  async deleteAccount(id: string): Promise<void> {
    await delay(50);
    // TODO: Replace with: return apiBridge.delete(`/bank-accounts/${id}`);
    console.log(`Deleted account ${id}`);
  },

  async getAccountBalance(accountId: string): Promise<number> {
    await delay(30);
    // TODO: Replace with: return apiBridge.get(`/bank-accounts/${accountId}/balance`);
    const account = mockBankAccounts.find(a => a.id === accountId);
    if (!account) return 0;
    const transactions = mockTransactions.filter(t => t.bankAccountId === accountId);
    const credits = transactions.filter(t => t.direction === 'credit').reduce((sum, t) => sum + t.amount, 0);
    const debits = transactions.filter(t => t.direction === 'debit').reduce((sum, t) => sum + t.amount, 0);
    return account.openingBalance + credits - debits;
  },

  async getTransactions(accountId?: string): Promise<Transaction[]> {
    await delay(50);
    // TODO: Replace with: return apiBridge.get(`/transactions${accountId ? `?accountId=${accountId}` : ''}`);
    if (accountId) {
      return mockTransactions
        .filter(t => t.bankAccountId === accountId)
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }
    return [...mockTransactions].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },

  async addTransaction(data: Omit<Transaction, 'id' | 'createdAt' | 'updatedAt'>): Promise<Transaction> {
    await delay(50);
    // TODO: Replace with: return apiBridge.post('/transactions', data);
    return {
      ...data,
      id: `txn_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  async deleteTransaction(id: string): Promise<void> {
    await delay(50);
    // TODO: Replace with: return apiBridge.delete(`/transactions/${id}`);
    console.log(`Deleted transaction ${id}`);
  },
};
