import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { BankAccount, Transaction } from '../types';
import { mockBankAccounts } from '../mock-data/bank-accounts';
import { mockTransactions } from '../mock-data/transactions';
import { useCurrencyStore } from './currency';
import { generateId } from '../utils/formatters';

export const useBankStore = defineStore('bank', () => {
  const bankAccounts = ref<BankAccount[]>(mockBankAccounts.map(a => ({ ...a })));
  const transactions = ref<Transaction[]>(mockTransactions.map(t => ({ ...t })));

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

  const totalBalance = computed(() => {
    return bankAccounts.value.reduce((sum, account) => {
      return sum + getAccountBalance(account.id);
    }, 0);
  });

  function getRecentTransactions(limit = 10): Transaction[] {
    return [...transactions.value]
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, limit);
  }

  // ==================== Account CRUD ====================

  function addAccount(data: Omit<BankAccount, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const account: BankAccount = {
      ...data,
      id: generateId('bank'),
      createdAt: now,
      updatedAt: now,
    };
    bankAccounts.value.push(account);
    return account;
  }

  function updateAccount(id: string, data: Partial<BankAccount>) {
    const index = bankAccounts.value.findIndex(a => a.id === id);
    if (index === -1) return null;
    bankAccounts.value[index] = {
      ...bankAccounts.value[index],
      ...data,
      id: bankAccounts.value[index].id,
      createdAt: bankAccounts.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return bankAccounts.value[index];
  }

  function deleteAccount(id: string) {
    const index = bankAccounts.value.findIndex(a => a.id === id);
    if (index !== -1) {
      bankAccounts.value.splice(index, 1);
      // Also remove related transactions
      transactions.value = transactions.value.filter(t => t.bankAccountId !== id);
    }
  }

  // ==================== Transaction CRUD ====================

  function addTransaction(data: Omit<Transaction, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const txn: Transaction = {
      ...data,
      id: generateId('txn'),
      createdAt: now,
      updatedAt: now,
    };
    transactions.value.push(txn);
    return txn;
  }

  function updateTransaction(id: string, data: Partial<Transaction>) {
    const index = transactions.value.findIndex(t => t.id === id);
    if (index === -1) return null;
    transactions.value[index] = {
      ...transactions.value[index],
      ...data,
      id: transactions.value[index].id,
      createdAt: transactions.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return transactions.value[index];
  }

  function deleteTransaction(id: string) {
    const index = transactions.value.findIndex(t => t.id === id);
    if (index !== -1) {
      transactions.value.splice(index, 1);
    }
  }

  return {
    bankAccounts,
    transactions,
    getAccountBalance,
    getAccountTransactions,
    totalBalance,
    getRecentTransactions,
    addAccount,
    updateAccount,
    deleteAccount,
    addTransaction,
    updateTransaction,
    deleteTransaction,
  };
});
