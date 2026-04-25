import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { BankAccount, Transaction } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';
import { useCurrencyStore } from './currency';

export const useBankStore = defineStore('bank', () => {
  // ==================== State ====================
  const bankAccounts = ref<BankAccount[]>([]);
  const transactions = ref<Transaction[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchAccounts(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      bankAccounts.value = await fetchAllPages<BankAccount>('/bank/accounts/');
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch bank accounts';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchTransactions(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      // Use the global "all transactions" endpoint (one request instead of N per account)
      transactions.value = await fetchAllPages<Transaction>('/bank/transactions/');
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch transactions';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchAccountTransactions(accountId: string): Promise<Transaction[]> {
    loading.value = true;
    error.value = null;
    try {
      const txs = await fetchAllPages<Transaction>(`/bank/accounts/${accountId}/transactions/`);
      // Replace transactions for this account in local state
      transactions.value = [
        ...transactions.value.filter(t => t.bankAccountId !== accountId),
        ...txs,
      ];
      return txs;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch account transactions';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchAll(): Promise<void> {
    await fetchAccounts();
    await fetchTransactions();
  }

  // ==================== Helpers (work with local state) ====================

  /**
   * Transaction-based accounting: balance = openingBalance + sum(credits) - sum(debits)
   */
  function getAccountBalance(accountId: string): number {
    const account = bankAccounts.value.find(a => a.id === accountId);
    if (!account) return 0;

    const accountTxs = transactions.value.filter(t => t.bankAccountId === accountId);
    const currencyStore = useCurrencyStore();
    const credits = accountTxs
      .filter(t => t.direction === 'credit')
      .reduce((sum, t) => sum + currencyStore.convertToBase(t.amount, t.currency || 'BDT'), 0);
    const debits = accountTxs
      .filter(t => t.direction === 'debit')
      .reduce((sum, t) => sum + currencyStore.convertToBase(t.amount, t.currency || 'BDT'), 0);

    return account.openingBalance + credits - debits;
  }

  function getAccountTransactions(accountId: string): Transaction[] {
    return transactions.value
      .filter(t => t.bankAccountId === accountId)
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }

  function getRecentTransactions(limit = 10): Transaction[] {
    return [...transactions.value]
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, limit);
  }

  // ==================== Computed ====================

  const totalBalance = computed(() => {
    return bankAccounts.value.reduce((sum, account) => {
      return sum + getAccountBalance(account.id);
    }, 0);
  });

  // ==================== Account CRUD ====================

  async function addAccount(data: Omit<BankAccount, 'id' | 'createdAt' | 'updatedAt'>): Promise<BankAccount> {
    error.value = null;
    try {
      const account = await api.post<BankAccount>('/bank/accounts/', data);
      bankAccounts.value.unshift(account);
      return account;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create bank account';
      throw err;
    }
  }

  async function updateAccount(id: string, data: Partial<BankAccount>): Promise<BankAccount | null> {
    error.value = null;
    try {
      const updated = await api.put<BankAccount>(`/bank/accounts/${id}/`, data);
      const index = bankAccounts.value.findIndex(a => a.id === id);
      if (index !== -1) {
        bankAccounts.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update bank account';
      throw err;
    }
  }

  async function deleteAccount(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/bank/accounts/${id}/`);
      const index = bankAccounts.value.findIndex(a => a.id === id);
      if (index !== -1) {
        bankAccounts.value.splice(index, 1);
      }
      // Remove related transactions from local state
      transactions.value = transactions.value.filter(t => t.bankAccountId !== id);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete bank account';
      throw err;
    }
  }

  // ==================== Transaction CRUD ====================

  async function addTransaction(data: Omit<Transaction, 'id' | 'createdAt' | 'updatedAt'>): Promise<Transaction> {
    error.value = null;
    try {
      const txn = await api.post<Transaction>('/bank/transactions/', data);
      transactions.value.unshift(txn);
      return txn;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create transaction';
      throw err;
    }
  }

  async function updateTransaction(id: string, data: Partial<Transaction>): Promise<Transaction | null> {
    error.value = null;
    try {
      const updated = await api.put<Transaction>(`/bank/transactions/${id}/`, data);
      const index = transactions.value.findIndex(t => t.id === id);
      if (index !== -1) {
        transactions.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update transaction';
      throw err;
    }
  }

  async function deleteTransaction(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/bank/transactions/${id}/`);
      const index = transactions.value.findIndex(t => t.id === id);
      if (index !== -1) {
        transactions.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete transaction';
      throw err;
    }
  }

  // ==================== Transfer ====================

  async function createTransfer(data: {
    fromAccountId: string;
    toAccountId: string;
    amount: number;
    description?: string;
    date?: string;
  }): Promise<Transaction> {
    error.value = null;
    try {
      const txn = await api.post<Transaction>('/bank/transfer/', data);
      transactions.value.unshift(txn);
      return txn;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create transfer';
      throw err;
    }
  }

  return {
    // State
    bankAccounts,
    transactions,
    loading,
    error,
    // Fetchers
    fetchAccounts,
    fetchTransactions,
    fetchAccountTransactions,
    fetchAll,
    // Helpers
    getAccountBalance,
    getAccountTransactions,
    getRecentTransactions,
    // Computed
    totalBalance,
    // Account CRUD
    addAccount,
    updateAccount,
    deleteAccount,
    // Transaction CRUD
    addTransaction,
    updateTransaction,
    deleteTransaction,
    // Transfer
    createTransfer,
  };
});
