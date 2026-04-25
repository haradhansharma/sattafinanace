/**
 * FinLife DataService
 * ==================
 * Centralized data access layer that acts as a backend-ready abstraction.
 * Currently backed by local mock data. When a real backend is available,
 * switch `dataSource` to `'api'` to route all calls through apiBridge.
 *
 * Components and stores should NOT import mock data directly — they use
 * this service (or the domain-specific services that wrap it).
 */

import { api } from './api-bridge';
import {
  mockUser,
  mockBankAccounts,
  mockTransactions,
  mockIncomes,
  mockIncomeSources,
  mockExpenses,
  mockExpenseCategories,
  mockCards,
  mockLoans,
  mockBudgets,
  mockInvoices,
  currencyList,
} from '../mock-data';
import type { Currency } from '../types';
import type { ExchangeRate } from '../mock-data/exchange-rates';

// ==================== Helpers ====================

const delay = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(resolve, ms));

type MockDataFn = () => unknown[];

// ==================== DataService Class ====================

class DataService {
  /** Toggle between local mock data and a real API backend. */
  dataSource: 'mock' | 'api' = 'mock';

  /** Simulated latency applied to every call (ms). */
  private latency = 50;

  // ---------- Mock data registry ----------
  // Maps entity names to factories that return a fresh copy of the data
  private mockRegistry: Record<string, MockDataFn> = {
    bankAccounts: () => [...mockBankAccounts],
    transactions: () =>
      [...mockTransactions].sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
      ),
    incomes: () =>
      [...mockIncomes].sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
      ),
    incomeSources: () => [...mockIncomeSources],
    expenses: () =>
      [...mockExpenses].sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
      ),
    expenseCategories: () => [...mockExpenseCategories],
    cards: () => [...mockCards],
    loans: () => [...mockLoans],
    budgets: () => [...mockBudgets],
    invoices: () =>
      [...mockInvoices].sort(
        (a, b) => new Date(b.issueDate).getTime() - new Date(a.issueDate).getTime(),
      ),
    exchangeRates: () => [...currencyList],
  };

  // ==================== Generic CRUD ====================

  /** Return all records for a given entity. */
  async getAll<T>(entity: string): Promise<T[]> {
    await delay(this.latency);
    if (this.dataSource === 'api') {
      return api.get<T[]>(`/${entity}`);
    }
    return (this.mockRegistry[entity]?.() ?? []) as T[];
  }

  /** Return a single record by id, or null if not found. */
  async getById<T>(entity: string, id: string): Promise<T | null> {
    await delay(this.latency);
    if (this.dataSource === 'api') {
      return api.get<T | null>(`/${entity}/${id}`);
    }
    const items = (this.mockRegistry[entity]?.() ?? []) as Array<{ id: string } & T>;
    const found = items.find(item => item.id === id);
    return (found as T) ?? null;
  }

  /** Create a new record. */
  async create<T>(entity: string, data: Omit<T, 'id' | 'createdAt' | 'updatedAt'>): Promise<T> {
    await delay(this.latency);
    if (this.dataSource === 'api') {
      return api.post<T>(`/${entity}`, data);
    }
    const now = new Date().toISOString();
    return {
      ...data,
      id: `${entity}_${Date.now()}`,
      createdAt: now,
      updatedAt: now,
    } as T;
  }

  /** Update an existing record. */
  async update<T extends { id: string }>(
    entity: string,
    id: string,
    data: Partial<T>,
  ): Promise<T> {
    await delay(this.latency);
    if (this.dataSource === 'api') {
      return api.put<T>(`/${entity}/${id}`, data);
    }
    const existing = await this.getById<T & { id: string }>(entity, id);
    if (!existing) throw new Error(`${entity} with id "${id}" not found`);
    return {
      ...existing,
      ...data,
      updatedAt: new Date().toISOString(),
    } as T;
  }

  /** Delete a record by id. */
  async remove(entity: string, id: string): Promise<void> {
    await delay(this.latency);
    if (this.dataSource === 'api') {
      await api.delete<void>(`/${entity}/${id}`);
      return;
    }
    // In mock mode this is a no-op; stores handle local removal
    console.log(`[DataService] Deleted ${entity}/${id}`);
  }

  // ==================== User ====================

  async getUser() {
    await delay(this.latency);
    if (this.dataSource === 'api') {
      return api.get('/user');
    }
    return { ...mockUser };
  }

  // ==================== Exchange Rates ====================

  async getExchangeRates(): Promise<ExchangeRate[]> {
    return this.getAll<ExchangeRate>('exchangeRates');
  }

  async getExchangeRate(currency: Currency): Promise<ExchangeRate | null> {
    await delay(this.latency);
    if (this.dataSource === 'api') {
      return api.get<ExchangeRate>(`/exchange-rates/${currency}`);
    }
    return currencyList.find(r => r.currency === currency) ?? null;
  }

  // ==================== Domain-Specific Shortcuts ====================
  // These provide typed convenience methods so callers don't have to
  // pass entity name strings.

  // -- Bank Accounts --
  async getBankAccounts() {
    return this.getAll<typeof mockBankAccounts[number]>('bankAccounts');
  }

  async getBankAccountById(id: string) {
    return this.getById<typeof mockBankAccounts[number]>('bankAccounts', id);
  }

  // -- Transactions --
  async getTransactions() {
    return this.getAll<typeof mockTransactions[number]>('transactions');
  }

  async getTransactionById(id: string) {
    return this.getById<typeof mockTransactions[number]>('transactions', id);
  }

  // -- Incomes --
  async getIncomes() {
    return this.getAll<typeof mockIncomes[number]>('incomes');
  }

  async getIncomeById(id: string) {
    return this.getById<typeof mockIncomes[number]>('incomes', id);
  }

  // -- Income Sources --
  async getIncomeSources() {
    return this.getAll<typeof mockIncomeSources[number]>('incomeSources');
  }

  // -- Expenses --
  async getExpenses() {
    return this.getAll<typeof mockExpenses[number]>('expenses');
  }

  async getExpenseById(id: string) {
    return this.getById<typeof mockExpenses[number]>('expenses', id);
  }

  // -- Expense Categories --
  async getExpenseCategories() {
    return this.getAll<typeof mockExpenseCategories[number]>('expenseCategories');
  }

  // -- Cards --
  async getCards() {
    return this.getAll<typeof mockCards[number]>('cards');
  }

  async getCardById(id: string) {
    return this.getById<typeof mockCards[number]>('cards', id);
  }

  // -- Loans --
  async getLoans() {
    return this.getAll<typeof mockLoans[number]>('loans');
  }

  async getLoanById(id: string) {
    return this.getById<typeof mockLoans[number]>('loans', id);
  }

  // -- Budgets --
  async getBudgets() {
    return this.getAll<typeof mockBudgets[number]>('budgets');
  }

  async getBudgetById(id: string) {
    return this.getById<typeof mockBudgets[number]>('budgets', id);
  }

  // -- Invoices --
  async getInvoices() {
    return this.getAll<typeof mockInvoices[number]>('invoices');
  }

  async getInvoiceById(id: string) {
    return this.getById<typeof mockInvoices[number]>('invoices', id);
  }
}

// ==================== Singleton Export ====================

export const dataService = new DataService();
