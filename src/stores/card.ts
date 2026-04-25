import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Card } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';
import { useCurrencyStore } from './currency';

export const useCardStore = defineStore('card', () => {
  // ==================== State ====================
  const cards = ref<Card[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchCards(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      cards.value = await fetchAllPages<Card>('/card/');
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch cards';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Helpers (work with local state) ====================

  function getCardById(id: string): Card | undefined {
    return cards.value.find(c => c.id === id);
  }

  function getCardsByType(type: 'debit' | 'credit'): Card[] {
    return cards.value.filter(c => c.type === type);
  }

  // ==================== Computed ====================

  const totalCreditUtilization = computed(() => {
    const creditCards = cards.value.filter(c => c.type === 'credit' && c.isActive);
    if (creditCards.length === 0) return 0;
    const currencyStore = useCurrencyStore();

    const totalBalance = creditCards.reduce((sum, c) => sum + currencyStore.convertToBase(c.currentBalance, c.currency || 'BDT'), 0);
    const totalLimit = creditCards.reduce((sum, c) => sum + currencyStore.convertToBase(c.creditLimit ?? 0, c.currency || 'BDT'), 0);

    if (totalLimit === 0) return 0;
    return (totalBalance / totalLimit) * 100;
  });

  const totalDebitBalance = computed(() => {
    const currencyStore = useCurrencyStore();
    return cards.value
      .filter(c => c.type === 'debit' && c.isActive)
      .reduce((sum, c) => sum + currencyStore.convertToBase(c.currentBalance, c.currency || 'BDT'), 0);
  });

  const totalCreditBalance = computed(() => {
    const currencyStore = useCurrencyStore();
    return cards.value
      .filter(c => c.type === 'credit' && c.isActive)
      .reduce((sum, c) => sum + currencyStore.convertToBase(c.currentBalance, c.currency || 'BDT'), 0);
  });

  const totalCreditLimit = computed(() => {
    const currencyStore = useCurrencyStore();
    return cards.value
      .filter(c => c.type === 'credit' && c.isActive)
      .reduce((sum, c) => sum + currencyStore.convertToBase(c.creditLimit ?? 0, c.currency || 'BDT'), 0);
  });

  // ==================== CRUD ====================

  async function addCard(data: Omit<Card, 'id' | 'createdAt' | 'updatedAt'>): Promise<Card> {
    error.value = null;
    try {
      const card = await api.post<Card>('/card/', data);
      cards.value.unshift(card);
      return card;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create card';
      throw err;
    }
  }

  async function updateCard(id: string, data: Partial<Card>): Promise<Card | null> {
    error.value = null;
    try {
      const updated = await api.put<Card>(`/card/${id}/`, data);
      const index = cards.value.findIndex(c => c.id === id);
      if (index !== -1) {
        cards.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update card';
      throw err;
    }
  }

  async function deleteCard(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/card/${id}/`);
      const index = cards.value.findIndex(c => c.id === id);
      if (index !== -1) {
        cards.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete card';
      throw err;
    }
  }

  return {
    // State
    cards,
    loading,
    error,
    // Fetchers
    fetchCards,
    // Helpers
    getCardById,
    getCardsByType,
    // Computed
    totalCreditUtilization,
    totalDebitBalance,
    totalCreditBalance,
    totalCreditLimit,
    // CRUD
    addCard,
    updateCard,
    deleteCard,
  };
});
