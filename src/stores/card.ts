import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Card } from '../types';
import { mockCards } from '../mock-data';
import { useCurrencyStore } from './currency';
import { generateId } from '../utils/formatters';

export const useCardStore = defineStore('card', () => {
  const cards = ref<Card[]>(mockCards.map(c => ({ ...c })));

  function getCardById(id: string): Card | undefined {
    return cards.value.find(c => c.id === id);
  }

  function getCardsByType(type: 'debit' | 'credit'): Card[] {
    return cards.value.filter(c => c.type === type);
  }

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

  function addCard(data: Omit<Card, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const card: Card = {
      ...data,
      id: generateId('card'),
      createdAt: now,
      updatedAt: now,
    };
    cards.value.push(card);
    return card;
  }

  function updateCard(id: string, data: Partial<Card>) {
    const index = cards.value.findIndex(c => c.id === id);
    if (index === -1) return null;
    cards.value[index] = {
      ...cards.value[index],
      ...data,
      id: cards.value[index].id,
      createdAt: cards.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return cards.value[index];
  }

  function deleteCard(id: string) {
    const index = cards.value.findIndex(c => c.id === id);
    if (index !== -1) {
      cards.value.splice(index, 1);
    }
  }

  return {
    cards,
    getCardById,
    getCardsByType,
    totalCreditUtilization,
    totalDebitBalance,
    totalCreditBalance,
    totalCreditLimit,
    addCard,
    updateCard,
    deleteCard,
  };
});
